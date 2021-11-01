import logging
import random
from datetime import datetime

from async_rediscache import RedisCache
from discord.ext import commands

import bot.exts.events.hacktoberfest._utils as utils
from bot.constants import Client, Month
from bot.utils.decorators import in_month
from bot.utils.extensions import invoke_help_command

log = logging.getLogger()


class Hacktoberfest(commands.Cog):
    """Cog containing all Hacktober-related commands."""

    # Cache for `.hacktoberfest stats`which maps the discord user ID (as string) to their GitHub account
    linked_accounts = RedisCache()

    # Caches for `.hacktoberfest issue`
    cache_normal = None
    cache_timer_normal = datetime(1, 1, 1)
    cache_beginner = None
    cache_timer_beginner = datetime(1, 1, 1)

    @commands.group(aliases=('hacktober',))
    async def hacktoberfest(self, ctx: commands.Context) -> None:
        """Commands related to Hacktoberfest."""
        if not ctx.invoked_subcommand:
            await invoke_help_command(ctx)
            return

    @in_month(Month.OCTOBER)
    @hacktoberfest.command(aliases=('issues',))
    async def issue(self, ctx: commands.Context, option: str = "") -> None:
        """
        Get a random python hacktober issue from Github.

        If the command is run with beginner (`.hacktoberfest issue beginner`):
        It will also narrow it down to the "first good issue" label.
        """
        async with ctx.typing():
            issues = await utils.get_issues(ctx, option)
            if issues is None:
                return
            issue = random.choice(issues["items"])
            embed = utils.format_issues_embed(issue)
        await ctx.send(embed=embed)

    @in_month(Month.SEPTEMBER, Month.OCTOBER, Month.NOVEMBER)
    @hacktoberfest.group(invoke_without_command=True)
    async def stats(self, ctx: commands.Context, github_username: str = None) -> None:
        """
        Display an embed for a user's Hacktoberfest contributions.

        If invoked without a subcommand or github_username, get the invoking user's stats if they've
        linked their Discord name to GitHub using `.hacktoberfest stats link`. If invoked with a github_username,
        get that user's contributions.
        """
        if not github_username:
            author_id, author_mention = utils.author_mention_from_context(ctx)

            if not (github_username := await self.linked_accounts.get(author_id)):
                # User hasn't linked a GitHub account, so send a message informing them of such.
                command_string = Client.prefix + " ".join(ctx.invoked_parents)
                msg = (
                    f"{author_mention}, you have not linked a GitHub account\n\n"
                    f"You can link your GitHub account using:\n```\n{command_string} link github_username\n```\n"
                    f"Or query GitHub stats directly using:\n```\n{command_string} github_username\n```"
                )
                await ctx.send(msg)
                return
            log.info(f"Getting stats for {author_id}'s linked GitHub account: '{github_username}'")
        else:
            log.info(f"Getting stats for '{github_username}' as requested by {ctx.author.id}")
        await utils.get_stats(ctx, github_username)

    @in_month(Month.SEPTEMBER, Month.OCTOBER, Month.NOVEMBER)
    @stats.command()
    async def link(self, ctx: commands.Context, github_username: str) -> None:
        """
        Link the invoking user's Github github_username to their Discord ID.

        Linked users are stored in Redis: User ID => GitHub Username.
        """
        author_id, author_mention = utils.author_mention_from_context(ctx)

        # If author has changed their linked GitHub username
        if old_username := await self.linked_accounts.get(author_id):
            log.info(f"{author_id} has changed their github link from '{old_username}' to '{github_username}'")
            await ctx.send(f"{author_mention}, your GitHub username has been updated to: '{github_username}'")

        # Author linked GitHub username for the first time
        else:
            log.info(f"{author_id} has added a github link to '{github_username}'")
            await ctx.send(f"{author_mention}, your GitHub username has been added")

        await self.linked_accounts.set(author_id, github_username)

    @in_month(Month.SEPTEMBER, Month.OCTOBER, Month.NOVEMBER)
    @stats.command()
    async def unlink(self, ctx: commands.Context) -> None:
        """Remove the invoking user's account link from the log."""
        author_id, author_mention = utils.author_mention_from_context(ctx)

        stored_user = await self.linked_accounts.pop(author_id, None)
        if stored_user:
            await ctx.send(f"{author_mention}, your GitHub profile has been unlinked")
            log.info(f"{author_id} has unlinked their GitHub account")
        else:
            await ctx.send(f"{author_mention}, you do not currently have a linked GitHub account")
            log.info(f"{author_id} tried to unlink their GitHub account but no account was linked")

    @hacktoberfest.command()
    async def timeleft(self, ctx: commands.Context) -> None:
        """
        Calculates the time left until the end of Hacktober.

        Whilst in October, displays the days, hours and minutes left.
        Only displays the days left until the beginning and end whilst in a different month.

        This factors in that Hacktoberfest starts when it is October anywhere in the world
        and ends with the same rules. It treats the start as UTC+14:00 and the end as
        UTC-12.
        """
        now, end, start = utils.load_date()
        diff = end - now
        days, seconds = diff.days, diff.seconds
        if utils.in_hacktober():
            minutes = seconds // 60
            hours, minutes = divmod(minutes, 60)

            await ctx.send(
                f"There are {days} days, {hours} hours and {minutes}"
                f" minutes left until the end of Hacktober."
            )
        else:
            start_diff = start - now
            start_days = start_diff.days
            await ctx.send(
                f"It is not currently Hacktober. However, the next one will start in {start_days} days "
                f"and will finish in {days} days."
            )
