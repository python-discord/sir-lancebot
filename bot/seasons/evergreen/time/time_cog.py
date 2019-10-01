import asyncio
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import arrow
import discord
import pytz
from discord.ext import commands
from fuzzywuzzy import fuzz, process

from bot.utils.persist import sqlite

log = logging.getLogger(__name__)

db = sqlite(Path("bot", "resources", "evergreen", "member_timezones.sqlite"))


class Time(commands.Cog):
    """Commands relating to Time and Timezones."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.timezones = self.get_timezones()

    @staticmethod
    def get_timezones() -> Dict[str, list]:
        """Fetch pytz timezones data."""
        zone_tab = pytz.open_resource('zone.tab')
        try:
            data = {}
            for line in zone_tab:
                line = line.decode('UTF-8')
                if line.startswith('#'):
                    continue
                code, coordinates, zone = line.split(None, 4)[:3]
                if zone not in pytz.all_timezones_set:
                    continue
                try:
                    data[code].append(zone)
                except KeyError:
                    data[code] = [zone]
            return data
        finally:
            zone_tab.close()

    @staticmethod
    def timezone_names() -> Dict[str, list]:
        """Get timezone names."""
        tznames = {}
        for tz in pytz.all_timezones:
            name = pytz.timezone(tz).localize(datetime.datetime.now()).tzname()
            try:
                tznames[name].append(tz)
            except KeyError:
                tznames[name] = [tz]
        return tznames

    def match_timezone(self, query: str) -> List[Tuple[str, int]]:
        """Find the closest matching timezone based on the query."""
        # try it as-is first
        try:
            pytz.timezone(query)
            return [(query, 100), ]
        except pytz.UnknownTimeZoneError:
            pass

        # check if in tz names
        tz_names = self.timezone_names()
        if query.upper() in tz_names:
            return [(tz, 100) for tz in tz_names[query.upper()]]

        # fuzzymatch against all timezones as last resort

        matches = process.extractBests(
            query, tz_names.keys(), scorer=fuzz.ratio, score_cutoff=80
        )

        commontz_matches = process.extractBests(
            query, pytz.common_timezones, scorer=fuzz.partial_ratio, score_cutoff=90
        )

        if commontz_matches:
            matches.extend(commontz_matches)

        fullmatches = [(tz, 100) for tz, s in matches if s == 100]
        if len(fullmatches) == 1:
            return fullmatches

        return matches

    @staticmethod
    def get_timezone(member_id: int) -> Optional[str]:
        """Get the stored timezone for a member based on their ID."""
        cursor = db.cursor()
        cursor.execute("SELECT timezone FROM member_timezones WHERE member_id = ?", [member_id])
        result = cursor.fetchone()
        if result:
            return result[0]

    @staticmethod
    def set_timezone(member_id: int, timezone: str) -> None:
        """Store a timezone for a member."""
        with db:
            db.execute(
                "INSERT INTO member_timezones "
                "VALUES(:member_id, :timezone) "
                "ON CONFLICT(member_id) DO UPDATE SET "
                "member_id = excluded.member_id, "
                "timezone = excluded.timezone "
                "WHERE member_id = :member_id",
                {"member_id": member_id, "timezone": timezone}
            )

    @staticmethod
    async def send_tz_list(
        ctx: commands.Context,
        title: str = "View All Available Timezones Names",
        description: Optional[str] = None
    ) -> None:
        """Send an embed with a link to all the possible timezones."""
        if description:
            embed = discord.Embed(description=description)
        else:
            embed = discord.Embed()
        embed.set_author(
            name=title,
            url="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        )
        await ctx.send(embed=embed)

    async def valid_timezone(self, ctx: commands.Context, timezone: str) -> Union[str, bool, None]:
        """Ensure a given timezone is valid and disambiguate if necessary."""
        # detect utc offset values
        try:
            tzoffset = datetime.timedelta(hours=float(timezone))
            datetime.timezone(tzoffset)
        except (ValueError, TypeError):
            pass
        else:
            return timezone

        # try matching if not an offset
        results = self.match_timezone(timezone)

        if not results:
            return None

        if len(results) == 1:
            return results[0][0]

        result_str = [f"{tz} ({s}%)" for tz, s in results]
        results = [tz for tz, s in results]
        joined_results = "\n".join(result_str)

        which_msg = await ctx.send(
            f"Which of these matches?\n\n{joined_results}\n\nTo stop, reply with 'cancel'."
        )

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            reply_msg = await ctx.bot.wait_for('message', check=check, timeout=20)
            reply = reply_msg.content
        except asyncio.TimeoutError:
            reply = "cancel"

        await which_msg.delete()

        if reply.lower() == 'cancel':
            return False

        return process.extractOne(reply, results, scorer=fuzz.partial_ratio, score_cutoff=95)[0]

    @commands.group(invoke_without_command=True)
    async def time(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """Show the member's local time."""
        member = member or ctx.author
        timezone = self.get_timezone(member.id)
        if not timezone:
            await self.send_tz_list(
                ctx,
                f"{member.display_name} has not set a timezone yet.",
                "Set one with:\n```.time set SomeTimeZone```"
            )
            return
        time = arrow.now(timezone).format("HH:mm, dddd")
        embed = discord.Embed(description=time)
        embed.set_author(name=f"Time for {member.display_name}")
        embed.set_footer(text=timezone)
        await ctx.send(embed=embed)

    @time.error
    async def time_error_handler(self, ctx: commands.Context, error: discord.DiscordException) -> None:
        """Handle argument errors for the time command, as the general error is too vague."""
        if isinstance(error, commands.UserInputError):
            await ctx.send("I couldn't find that member, sorry!")
        else:
            log.exception(type(error).__name__, exc_info=error)

    @time.command(name="list")
    async def time_list(self, ctx: commands.Context) -> None:
        """Provide a link to see all timezones."""
        await self.send_tz_list(ctx)

    @time.command(name="set")
    async def time_set(self, ctx: commands.Context, *, timezone: str = None) -> None:
        """Set your timezone for the time command."""
        timezone = await self.valid_timezone(ctx, timezone)
        if timezone is False:
            await ctx.send("Cancelled")
            return

        self.set_timezone(ctx.author.id, timezone)
        time = arrow.now(timezone).format("HH:mm, dddd")
        embed = discord.Embed(description=time)
        embed.set_author(name=f"Timezone Set for {ctx.author.display_name}")
        embed.set_footer(text=timezone)
        await ctx.send(embed=embed)
