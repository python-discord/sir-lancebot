import json
import logging
from pathlib import Path

from discord import User
from discord.ext import commands


log = logging.getLogger(__name__)
with Path('bot/resources/evergreen/github.json').open(encoding='utf-8') as file:
    data = json.load(file)
    github_accounts = data


class Github(commands.Cog):
    """Commands involving Github account linking."""

    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    @commands.group(name="github", invoke_without_command=True)
    async def github(self, ctx: commands.context, user_to_search: User = None) -> None:
        """Returns the user's linked Github if no parameter is passed in, otherwise fetches the given user's Github."""
        if user_to_search is None:
            author = str(ctx.message.author)[:-5]
            await ctx.send(f"The Github account for {author} is: {fetch_acct(author)}")
        else:
            user_to_search = user_to_search.display_name
            await ctx.send(f"The Github account for {user_to_search} is: {fetch_acct(user_to_search)}")

    @github.command(name="link")
    async def link(self, ctx: commands.context, git_acct: str) -> None:
        """Links a Github account to a Discord user."""
        author = str(ctx.message.author)[:-5]
        github_accounts.update({author: git_acct})
        update_resource()
        await ctx.send(f"Account: {git_acct} linked to {author} successfully")

    @github.command(name="unlink")
    async def unlink(self, ctx: commands.context) -> None:
        """Unlinks the user's Github account."""
        author = str(ctx.message.author)[:-5]
        del github_accounts[author]
        update_resource()
        await ctx.send(f"Github account for user: {author} has been removed.")


def fetch_acct(discord_acct: str) -> str:
    """Fetches a Github account for the specified user."""
    try:
        return github_accounts[discord_acct]
    except KeyError:
        return "not found."


def update_resource() -> None:
    """Updates the json file."""
    with Path('bot/resources/evergreen/github.json').open(mode='w', encoding='utf-8') as outfile:
        json.dump(github_accounts, outfile, indent=4)


def setup(bot: commands.Bot) -> None:
    """Loads the Github cog."""
    bot.add_cog(Github(bot))
    log.info("Github cog loaded")
