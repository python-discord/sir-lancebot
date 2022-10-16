import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import arrow
import discord
from async_rediscache import RedisCache
from discord.ext import commands, tasks

from bot.bot import Bot
from bot.constants import (
    AdventOfCode as AocConfig, Channels, Client, Colours, Emojis, Month, PYTHON_PREFIX, Roles, WHITELISTED_CHANNELS
)
from bot.exts.events.advent_of_code import _helpers
from bot.exts.events.advent_of_code.views.dayandstarview import AoCDropdownView
from bot.utils import members
from bot.utils.decorators import InChannelCheckFailure, in_month, whitelist_override, with_role
from bot.utils.exceptions import MovedCommandError

log = logging.getLogger(__name__)

AOC_REQUEST_HEADER = {"user-agent": "PythonDiscord AoC Event Bot"}

AOC_WHITELIST_RESTRICTED = WHITELISTED_CHANNELS + (Channels.advent_of_code_commands,)

# Some commands can be run in the regular advent of code channel
# They aren't spammy and foster discussion
AOC_WHITELIST = AOC_WHITELIST_RESTRICTED + (Channels.advent_of_code,)


class AdventOfCode(commands.Cog):
    """Advent of Code festivities! Ho Ho Ho!"""

    # Redis Cache for linking Discord IDs to Advent of Code usernames
    # RedisCache[member_id: aoc_username_string]
    account_links = RedisCache()

    # A dict with keys of member_ids to block from getting the role
    # RedisCache[member_id: None]
    completionist_block_list = RedisCache()

    def __init__(self, bot: Bot):
        self.bot = bot

        self._base_url = f"https://adventofcode.com/{AocConfig.year}"
        self.global_leaderboard_url = f"https://adventofcode.com/{AocConfig.year}/leaderboard"

        self.about_aoc_filepath = Path("./bot/resources/events/advent_of_code/about.json")
        self.cached_about_aoc = self._build_about_embed()

        notification_coro = _helpers.new_puzzle_notification(self.bot)
        self.notification_task = self.bot.loop.create_task(notification_coro)
        self.notification_task.set_name("Daily AoC Notification")
        self.notification_task.add_done_callback(_helpers.background_task_callback)

        status_coro = _helpers.countdown_status(self.bot)
        self.status_task = self.bot.loop.create_task(status_coro)
        self.status_task.set_name("AoC Status Countdown")
        self.status_task.add_done_callback(_helpers.background_task_callback)

        # Don't start task while event isn't running
        # self.completionist_task.start()

    @tasks.loop(minutes=10.0)
    async def completionist_task(self) -> None:
        """
        Give members who have completed all 50 AoC stars the completionist role.

        Runs on a schedule, as defined in the task.loop decorator.
        """
        guild = self.bot.get_guild(Client.guild)
        completionist_role = guild.get_role(Roles.aoc_completionist)
        if completionist_role is None:
            log.warning("Could not find the AoC completionist role; cancelling completionist task.")
            self.completionist_task.cancel()
            return

        aoc_name_to_member_id = {
            aoc_name: member_id
            for member_id, aoc_name in await self.account_links.items()
        }

        try:
            leaderboard = await _helpers.fetch_leaderboard()
        except _helpers.FetchingLeaderboardFailedError:
            await self.bot.log_to_dev_log("Unable to fetch AoC leaderboard during role sync.")
            return

        placement_leaderboard = json.loads(leaderboard["placement_leaderboard"])

        for member_aoc_info in placement_leaderboard.values():
            if not member_aoc_info["stars"] == 50:
                # Only give the role to people who have completed all 50 stars
                continue

            aoc_name = member_aoc_info["name"] or f"Anonymous #{member_aoc_info['id']}"

            member_id = aoc_name_to_member_id.get(aoc_name)
            if not member_id:
                log.debug(f"Could not find member_id for {member_aoc_info['name']}, not giving role.")
                continue

            member = await members.get_or_fetch_member(guild, member_id)
            if member is None:
                log.debug(f"Could not find {member_id}, not giving role.")
                continue

            if completionist_role in member.roles:
                log.debug(f"{member.name} ({member.mention}) already has the completionist role.")
                continue

            if not await self.completionist_block_list.contains(member_id):
                log.debug(f"Giving completionist role to {member.name} ({member.mention}).")
                await members.handle_role_change(member, member.add_roles, completionist_role)

    @commands.group(name="adventofcode", aliases=("aoc",))
    @whitelist_override(channels=AOC_WHITELIST)
    async def adventofcode_group(self, ctx: commands.Context) -> None:
        """All of the Advent of Code commands."""
        if not ctx.invoked_subcommand:
            await self.bot.invoke_help_command(ctx)

    @with_role(Roles.admins)
    @adventofcode_group.command(
        name="block",
        brief="Block a user from getting the completionist role.",
    )
    async def block_from_role(self, ctx: commands.Context, member: discord.Member) -> None:
        """Block the given member from receiving the AoC completionist role, removing it from them if needed."""
        completionist_role = ctx.guild.get_role(Roles.aoc_completionist)
        if completionist_role in member.roles:
            await member.remove_roles(completionist_role)

        await self.completionist_block_list.set(member.id, "sentinel")
        await ctx.send(f":+1: Blocked {member.mention} from getting the AoC completionist role.")

    @commands.guild_only()
    @adventofcode_group.command(
        name="subscribe",
        aliases=("sub", "notifications", "notify", "notifs", "unsubscribe", "unsub"),
        help=f"NOTE: This command has been moved to {PYTHON_PREFIX}subscribe",
    )
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_subscribe(self, ctx: commands.Context) -> None:
        """
        Deprecated role command.

        This command has been moved to bot, and will be removed in the future.
        """
        raise MovedCommandError(f"{PYTHON_PREFIX}subscribe")

    @adventofcode_group.command(name="countdown", aliases=("count", "c"), brief="Return time left until next day")
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_countdown(self, ctx: commands.Context) -> None:
        """Return time left until next day."""
        if _helpers.is_in_advent():
            tomorrow, _ = _helpers.time_left_to_est_midnight()
            next_day_timestamp = int(tomorrow.timestamp())

            await ctx.send(f"Day {tomorrow.day} starts <t:{next_day_timestamp}:R>.")
            return

        datetime_now = arrow.now(_helpers.EST)
        # Calculate the delta to this & next year's December 1st to see which one is closest and not in the past
        this_year = arrow.get(datetime(datetime_now.year, 12, 1), _helpers.EST)
        next_year = arrow.get(datetime(datetime_now.year + 1, 12, 1), _helpers.EST)
        deltas = (dec_first - datetime_now for dec_first in (this_year, next_year))
        delta = min(delta for delta in deltas if delta >= timedelta())  # timedelta() gives 0 duration delta

        next_aoc_timestamp = int((datetime_now + delta).timestamp())

        await ctx.send(
            "The Advent of Code event is not currently running. "
            f"The next event will start <t:{next_aoc_timestamp}:R>."
        )

    @adventofcode_group.command(name="about", aliases=("ab", "info"), brief="Learn about Advent of Code")
    @whitelist_override(channels=AOC_WHITELIST)
    async def about_aoc(self, ctx: commands.Context) -> None:
        """Respond with an explanation of all things Advent of Code."""
        await ctx.send(embed=self.cached_about_aoc)

    @commands.guild_only()
    @adventofcode_group.command(name="join", aliases=("j",), brief="Learn how to join the leaderboard (via DM)")
    @whitelist_override(channels=AOC_WHITELIST)
    async def join_leaderboard(self, ctx: commands.Context) -> None:
        """DM the user the information for joining the Python Discord leaderboard."""
        current_date = datetime.now()
        allowed_months = (Month.NOVEMBER.value, Month.DECEMBER.value)
        if not (
            current_date.month in allowed_months and current_date.year == AocConfig.year or
            current_date.month == Month.JANUARY.value and current_date.year == AocConfig.year + 1
        ):
            # Only allow joining the leaderboard in the run up to AOC and the January following.
            await ctx.send(f"The Python Discord leaderboard for {current_date.year} is not yet available!")
            return

        author = ctx.author
        log.info(f"{author.name} ({author.id}) has requested a PyDis AoC leaderboard code")

        if AocConfig.staff_leaderboard_id and any(r.id == Roles.helpers for r in author.roles):
            join_code = AocConfig.leaderboards[AocConfig.staff_leaderboard_id].join_code
        else:
            try:
                join_code = await _helpers.get_public_join_code(author)
            except _helpers.FetchingLeaderboardFailedError:
                await ctx.send(":x: Failed to get join code! Notified maintainers.")
                return

        if not join_code:
            log.error(f"Failed to get a join code for user {author} ({author.id})")
            error_embed = discord.Embed(
                title="Unable to get join code",
                description="Failed to get a join code to one of our boards. Please notify staff.",
                colour=discord.Colour.red(),
            )
            await ctx.send(embed=error_embed)
            return

        info_str = [
            "To join our leaderboard, follow these steps:",
            "• Log in on https://adventofcode.com",
            "• Head over to https://adventofcode.com/leaderboard/private",
            f"• Use this code `{join_code}` to join the Python Discord leaderboard!",
        ]
        try:
            await author.send("\n".join(info_str))
        except discord.errors.Forbidden:
            log.debug(f"{author.name} ({author.id}) has disabled DMs from server members")
            await ctx.send(f":x: {author.mention}, please (temporarily) enable DMs to receive the join code")
        else:
            await ctx.message.add_reaction(Emojis.envelope)

    @in_month(Month.NOVEMBER, Month.DECEMBER, Month.JANUARY)
    @adventofcode_group.command(
        name="link",
        aliases=("connect",),
        brief="Tie your Discord account with your Advent of Code name."
    )
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_link_account(self, ctx: commands.Context, *, aoc_name: str = None) -> None:
        """
        Link your Discord Account to your Advent of Code name.

        Stored in a Redis Cache with the format of `Discord ID: Advent of Code Name`
        """
        cache_items = await self.account_links.items()
        cache_aoc_names = [value for _, value in cache_items]

        if aoc_name:
            # Let's check the current values in the cache to make sure it isn't already tied to a different account
            if aoc_name == await self.account_links.get(ctx.author.id):
                await ctx.reply(f"{aoc_name} is already tied to your account.")
                return
            elif aoc_name in cache_aoc_names:
                log.info(
                    f"{ctx.author} ({ctx.author.id}) tried to connect their account to {aoc_name},"
                    " but it's already connected to another user."
                )
                await ctx.reply(
                    f"{aoc_name} is already tied to another account."
                    " Please contact an admin if you believe this is an error."
                )
                return

            # Update an existing link
            if old_aoc_name := await self.account_links.get(ctx.author.id):
                log.info(f"Changing link for {ctx.author} ({ctx.author.id}) from {old_aoc_name} to {aoc_name}.")
                await self.account_links.set(ctx.author.id, aoc_name)
                await ctx.reply(f"Your linked account has been changed to {aoc_name}.")
            else:
                # Create a new link
                log.info(f"Linking {ctx.author} ({ctx.author.id}) to account {aoc_name}.")
                await self.account_links.set(ctx.author.id, aoc_name)
                await ctx.reply(f"You have linked your Discord ID to {aoc_name}.")
        else:
            # User has not supplied a name, let's check if they're in the cache or not
            if cache_name := await self.account_links.get(ctx.author.id):
                await ctx.reply(f"You have already linked an Advent of Code account: {cache_name}.")
            else:
                await ctx.reply(
                    "You have not linked an Advent of Code account."
                    " Please re-run the command with one specified."
                )

    @in_month(Month.NOVEMBER, Month.DECEMBER, Month.JANUARY)
    @adventofcode_group.command(
        name="unlink",
        aliases=("disconnect",),
        brief="Tie your Discord account with your Advent of Code name."
    )
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_unlink_account(self, ctx: commands.Context) -> None:
        """
        Unlink your Discord ID with your Advent of Code leaderboard name.

        Deletes the entry that was Stored in the Redis cache.
        """
        if aoc_cache_name := await self.account_links.get(ctx.author.id):
            log.info(f"Unlinking {ctx.author} ({ctx.author.id}) from Advent of Code account {aoc_cache_name}")
            await self.account_links.delete(ctx.author.id)
            await ctx.reply(f"We have removed the link between your Discord ID and {aoc_cache_name}.")
        else:
            log.info(f"Attempted to unlink {ctx.author} ({ctx.author.id}), but no link was found.")
            await ctx.reply("You don't have an Advent of Code account linked.")

    @in_month(Month.DECEMBER, Month.JANUARY)
    @adventofcode_group.command(
        name="dayandstar",
        aliases=("daynstar", "daystar"),
        brief="Get a view that lets you filter the leaderboard by day and star",
    )
    @whitelist_override(channels=AOC_WHITELIST_RESTRICTED)
    async def aoc_day_and_star_leaderboard(
            self,
            ctx: commands.Context,
            maximum_scorers_day_and_star: Optional[int] = 10
    ) -> None:
        """Have the bot send a View that will let you filter the leaderboard by day and star."""
        if maximum_scorers_day_and_star > AocConfig.max_day_and_star_results or maximum_scorers_day_and_star <= 0:
            raise commands.BadArgument(
                f"The maximum number of results you can query is {AocConfig.max_day_and_star_results}"
            )
        async with ctx.typing():
            try:
                leaderboard = await _helpers.fetch_leaderboard()
            except _helpers.FetchingLeaderboardFailedError:
                await ctx.send(":x: Unable to fetch leaderboard!")
                return
        # This is a dictionary that contains solvers in respect of day, and star.
        # e.g. 1-1 means the solvers of the first star of the first day and their completion time
        per_day_and_star = json.loads(leaderboard['leaderboard_per_day_and_star'])
        view = AoCDropdownView(
            day_and_star_data=per_day_and_star,
            maximum_scorers=maximum_scorers_day_and_star,
            original_author=ctx.author
        )
        message = await ctx.send(
            content="Please select a day and a star to filter by!",
            view=view
        )
        await view.wait()
        await message.edit(view=None)

    @in_month(Month.DECEMBER, Month.JANUARY)
    @adventofcode_group.command(
        name="leaderboard",
        aliases=("board", "lb"),
        brief="Get a snapshot of the PyDis private AoC leaderboard",
    )
    @whitelist_override(channels=AOC_WHITELIST_RESTRICTED)
    async def aoc_leaderboard(self, ctx: commands.Context, *, aoc_name: Optional[str] = None) -> None:
        """
        Get the current top scorers of the Python Discord Leaderboard.

        Additionally you can specify an `aoc_name` that will append the
        specified profile's personal stats to the top of the leaderboard
        """
        # Strip quotes from the AoC username if needed (e.g. "My Name" -> My Name)
        # This is to keep compatibility with those already used to wrapping the AoC name in quotes
        # Note: only strips one layer of quotes to allow names with quotes at the start and end
        #      e.g. ""My Name"" -> "My Name"
        if aoc_name and aoc_name.startswith('"') and aoc_name.endswith('"'):
            aoc_name = aoc_name[1:-1]

        # Check if an advent of code account is linked in the Redis Cache if aoc_name is not given
        if (aoc_cache_name := await self.account_links.get(ctx.author.id)) and aoc_name is None:
            aoc_name = aoc_cache_name

        async with ctx.typing():
            try:
                leaderboard = await _helpers.fetch_leaderboard(self_placement_name=aoc_name)
            except _helpers.FetchingLeaderboardFailedError:
                await ctx.send(":x: Unable to fetch leaderboard!")
                return

        number_of_participants = leaderboard["number_of_participants"]

        top_count = min(AocConfig.leaderboard_displayed_members, number_of_participants)
        self_placement_header = " (and your personal stats compared to the top 10)" if aoc_name else ""
        header = f"Here's our current top {top_count}{self_placement_header}! {Emojis.christmas_tree * 3}"
        table = "```\n" \
                f"{leaderboard['placement_leaderboard'] if aoc_name else leaderboard['top_leaderboard']}" \
                "\n```"
        info_embed = _helpers.get_summary_embed(leaderboard)

        await ctx.send(content=f"{header}\n\n{table}", embed=info_embed)
        return

    @in_month(Month.DECEMBER, Month.JANUARY)
    @adventofcode_group.command(
        name="global",
        aliases=("globalboard", "gb"),
        brief="Get a link to the global leaderboard",
    )
    @whitelist_override(channels=AOC_WHITELIST_RESTRICTED)
    async def aoc_global_leaderboard(self, ctx: commands.Context) -> None:
        """Get a link to the global Advent of Code leaderboard."""
        url = self.global_leaderboard_url
        global_leaderboard = discord.Embed(
            title="Advent of Code — Global Leaderboard",
            description=f"You can find the global leaderboard [here]({url})."
        )
        global_leaderboard.set_thumbnail(url=_helpers.AOC_EMBED_THUMBNAIL)
        await ctx.send(embed=global_leaderboard)

    @adventofcode_group.command(
        name="stats",
        aliases=("dailystats", "ds"),
        brief="Get daily statistics for the Python Discord leaderboard"
    )
    @whitelist_override(channels=AOC_WHITELIST_RESTRICTED)
    async def private_leaderboard_daily_stats(self, ctx: commands.Context) -> None:
        """Send an embed with daily completion statistics for the Python Discord leaderboard."""
        try:
            leaderboard = await _helpers.fetch_leaderboard()
        except _helpers.FetchingLeaderboardFailedError:
            await ctx.send(":x: Can't fetch leaderboard for stats right now!")
            return

        # The daily stats are serialized as JSON as they have to be cached in Redis
        daily_stats = json.loads(leaderboard["daily_stats"])
        async with ctx.typing():
            lines = ["Day   ⭐  ⭐⭐ |   %⭐    %⭐⭐\n================================"]
            for day, stars in daily_stats.items():
                star_one = stars["star_one"]
                star_two = stars["star_two"]
                p_star_one = star_one / leaderboard["number_of_participants"]
                p_star_two = star_two / leaderboard["number_of_participants"]
                lines.append(
                    f"{day:>2}) {star_one:>4}  {star_two:>4} | {p_star_one:>7.2%} {p_star_two:>7.2%}"
                )
            table = "\n".join(lines)
            info_embed = _helpers.get_summary_embed(leaderboard)
            await ctx.send(f"```\n{table}\n```", embed=info_embed)

    @with_role(Roles.admins)
    @adventofcode_group.command(
        name="refresh",
        aliases=("fetch",),
        brief="Force a refresh of the leaderboard cache.",
    )
    async def refresh_leaderboard(self, ctx: commands.Context) -> None:
        """
        Force a refresh of the leaderboard cache.

        Note: This should be used sparingly, as we want to prevent sending too
        many requests to the Advent of Code server.
        """
        async with ctx.typing():
            try:
                await _helpers.fetch_leaderboard(invalidate_cache=True)
            except _helpers.FetchingLeaderboardFailedError:
                await ctx.send(":x: Something went wrong while trying to refresh the cache!")
            else:
                await ctx.send("\N{OK Hand Sign} Refreshed leaderboard cache!")

    def cog_unload(self) -> None:
        """Cancel season-related tasks on cog unload."""
        log.debug("Unloading the cog and canceling the background task.")
        self.notification_task.cancel()
        self.status_task.cancel()
        self.completionist_task.cancel()

    def _build_about_embed(self) -> discord.Embed:
        """Build and return the informational "About AoC" embed from the resources file."""
        embed_fields = json.loads(self.about_aoc_filepath.read_text("utf8"))

        about_embed = discord.Embed(
            title=self._base_url,
            colour=Colours.soft_green,
            url=self._base_url,
            timestamp=datetime.utcnow()
        )
        about_embed.set_author(name="Advent of Code", url=self._base_url)
        for field in embed_fields:
            about_embed.add_field(**field)

        about_embed.set_footer(text="Last Updated")
        return about_embed

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Custom error handler if an advent of code command was posted in the wrong channel."""
        if isinstance(error, InChannelCheckFailure):
            await ctx.send(f":x: Please use <#{Channels.advent_of_code_commands}> for aoc commands instead.")
            error.handled = True
