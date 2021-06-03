import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import arrow
import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import (
    AdventOfCode as AocConfig, Channels, Colours, Emojis, Month, Roles, WHITELISTED_CHANNELS,
)
from bot.exts.christmas.advent_of_code import _helpers
from bot.utils.decorators import InChannelCheckFailure, in_month, whitelist_override, with_role
from bot.utils.extensions import invoke_help_command

log = logging.getLogger(__name__)

AOC_REQUEST_HEADER = {"user-agent": "PythonDiscord AoC Event Bot"}

AOC_WHITELIST_RESTRICTED = WHITELISTED_CHANNELS + (Channels.advent_of_code_commands,)

# Some commands can be run in the regular advent of code channel
# They aren't spammy and foster discussion
AOC_WHITELIST = AOC_WHITELIST_RESTRICTED + (Channels.advent_of_code,)


class AdventOfCode(commands.Cog):
    """Advent of Code festivities! Ho Ho Ho!"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self._base_url = f"https://adventofcode.com/{AocConfig.year}"
        self.global_leaderboard_url = f"https://adventofcode.com/{AocConfig.year}/leaderboard"

        self.about_aoc_filepath = Path("./bot/resources/advent_of_code/about.json")
        self.cached_about_aoc = self._build_about_embed()

        notification_coro = _helpers.new_puzzle_notification(self.bot)
        self.notification_task = self.bot.loop.create_task(notification_coro)
        self.notification_task.set_name("Daily AoC Notification")
        self.notification_task.add_done_callback(_helpers.background_task_callback)

        status_coro = _helpers.countdown_status(self.bot)
        self.status_task = self.bot.loop.create_task(status_coro)
        self.status_task.set_name("AoC Status Countdown")
        self.status_task.add_done_callback(_helpers.background_task_callback)

    @commands.group(name="adventofcode", aliases=("aoc",))
    @whitelist_override(channels=AOC_WHITELIST)
    async def adventofcode_group(self, ctx: commands.Context) -> None:
        """All of the Advent of Code commands."""
        if not ctx.invoked_subcommand:
            await invoke_help_command(ctx)

    @adventofcode_group.command(
        name="subscribe",
        aliases=("sub", "notifications", "notify", "notifs"),
        brief="Notifications for new days"
    )
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_subscribe(self, ctx: commands.Context) -> None:
        """Assign the role for notifications about new days being ready."""
        current_year = datetime.now().year
        if current_year != AocConfig.year:
            await ctx.send(f"You can't subscribe to {current_year}'s Advent of Code announcements yet!")
            return

        role = ctx.guild.get_role(AocConfig.role_id)
        unsubscribe_command = f"{ctx.prefix}{ctx.command.root_parent} unsubscribe"

        if role not in ctx.author.roles:
            await ctx.author.add_roles(role)
            await ctx.send(
                "Okay! You have been __subscribed__ to notifications about new Advent of Code tasks. "
                f"You can run `{unsubscribe_command}` to disable them again for you."
            )
        else:
            await ctx.send(
                "Hey, you already are receiving notifications about new Advent of Code tasks. "
                f"If you don't want them any more, run `{unsubscribe_command}` instead."
            )

    @in_month(Month.DECEMBER)
    @adventofcode_group.command(name="unsubscribe", aliases=("unsub",), brief="Notifications for new days")
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_unsubscribe(self, ctx: commands.Context) -> None:
        """Remove the role for notifications about new days being ready."""
        role = ctx.guild.get_role(AocConfig.role_id)

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send("Okay! You have been __unsubscribed__ from notifications about new Advent of Code tasks.")
        else:
            await ctx.send("Hey, you don't even get any notifications about new Advent of Code tasks currently anyway.")

    @adventofcode_group.command(name="countdown", aliases=("count", "c"), brief="Return time left until next day")
    @whitelist_override(channels=AOC_WHITELIST)
    async def aoc_countdown(self, ctx: commands.Context) -> None:
        """Return time left until next day."""
        if not _helpers.is_in_advent():
            datetime_now = arrow.now(_helpers.EST)

            # Calculate the delta to this & next year's December 1st to see which one is closest and not in the past
            this_year = arrow.get(datetime(datetime_now.year, 12, 1), _helpers.EST)
            next_year = arrow.get(datetime(datetime_now.year + 1, 12, 1), _helpers.EST)
            deltas = (dec_first - datetime_now for dec_first in (this_year, next_year))
            delta = min(delta for delta in deltas if delta >= timedelta())  # timedelta() gives 0 duration delta

            # Add a finer timedelta if there's less than a day left
            if delta.days == 0:
                delta_str = f"approximately {delta.seconds // 3600} hours"
            else:
                delta_str = f"{delta.days} days"

            await ctx.send(
                "The Advent of Code event is not currently running. "
                f"The next event will start in {delta_str}."
            )
            return

        tomorrow, time_left = _helpers.time_left_to_est_midnight()

        hours, minutes = time_left.seconds // 3600, time_left.seconds // 60 % 60

        await ctx.send(f"There are {hours} hours and {minutes} minutes left until day {tomorrow.day}.")

    @adventofcode_group.command(name="about", aliases=("ab", "info"), brief="Learn about Advent of Code")
    @whitelist_override(channels=AOC_WHITELIST)
    async def about_aoc(self, ctx: commands.Context) -> None:
        """Respond with an explanation of all things Advent of Code."""
        await ctx.send(embed=self.cached_about_aoc)

    @adventofcode_group.command(name="join", aliases=("j",), brief="Learn how to join the leaderboard (via DM)")
    @whitelist_override(channels=AOC_WHITELIST)
    async def join_leaderboard(self, ctx: commands.Context) -> None:
        """DM the user the information for joining the Python Discord leaderboard."""
        current_year = datetime.now().year
        if current_year != AocConfig.year:
            await ctx.send(f"The Python Discord leaderboard for {current_year} is not yet available!")
            return

        author = ctx.author
        log.info(f"{author.name} ({author.id}) has requested a PyDis AoC leaderboard code")

        if AocConfig.staff_leaderboard_id and any(r.id == Roles.helpers for r in author.roles):
            join_code = AocConfig.leaderboards[AocConfig.staff_leaderboard_id].join_code
        else:
            try:
                join_code = await _helpers.get_public_join_code(author)
            except _helpers.FetchingLeaderboardFailed:
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

    @in_month(Month.DECEMBER)
    @adventofcode_group.command(
        name="leaderboard",
        aliases=("board", "lb"),
        brief="Get a snapshot of the PyDis private AoC leaderboard",
    )
    @whitelist_override(channels=AOC_WHITELIST_RESTRICTED)
    async def aoc_leaderboard(self, ctx: commands.Context) -> None:
        """Get the current top scorers of the Python Discord Leaderboard."""
        async with ctx.typing():
            try:
                leaderboard = await _helpers.fetch_leaderboard()
            except _helpers.FetchingLeaderboardFailed:
                await ctx.send(":x: Unable to fetch leaderboard!")
                return

            number_of_participants = leaderboard["number_of_participants"]

            top_count = min(AocConfig.leaderboard_displayed_members, number_of_participants)
            header = f"Here's our current top {top_count}! {Emojis.christmas_tree * 3}"

            table = f"```\n{leaderboard['top_leaderboard']}\n```"
            info_embed = _helpers.get_summary_embed(leaderboard)

            await ctx.send(content=f"{header}\n\n{table}", embed=info_embed)

    @in_month(Month.DECEMBER)
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
        except _helpers.FetchingLeaderboardFailed:
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

    @with_role(Roles.admin)
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
            except _helpers.FetchingLeaderboardFailed:
                await ctx.send(":x: Something went wrong while trying to refresh the cache!")
            else:
                await ctx.send("\N{OK Hand Sign} Refreshed leaderboard cache!")

    def cog_unload(self) -> None:
        """Cancel season-related tasks on cog unload."""
        log.debug("Unloading the cog and canceling the background task.")
        self.notification_task.cancel()
        self.status_task.cancel()

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
