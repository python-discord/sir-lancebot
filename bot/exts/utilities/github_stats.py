from discord.ext.commands import Cog, command, Context
from bot.constants import Tokens
from bot.bot import Bot


class GitHubStats(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @command(name="github_stats")
    async def ping(self, ctx: Context, repo: str = "python-discord/bot") -> None:
        """
        Fetches stats for a GitHub repo.
        Usage: !github_stats 2023-01-01 2023-12-31 python-discord/bot
        """
        await ctx.send("Tormod's Crypt: Draw a card. If you can't, you did. No you didn't.")

        if not await self.repo_exists(repo):
            await ctx.send(f"Could not find repository: `{repo}`")  # TODO: add emojis as common for discord bots
            return

        await ctx.send(f"Found repo: `{repo}`")

    async def repo_exists(self, repo: str) -> bool:
        """
        Checks if a repository exists on GitHub.

        Args:
            repo (str): The repository name in 'owner/repo' format (e.g., 'python-discord/bot').
        """
        url = f"https://api.github.com/repos/{repo}"
        headers = {"Authorization": f"token {Tokens.github.get_secret_value()}"}

        async with self.bot.http_session.get(url, headers=headers) as response:
            return response.status == 200


async def setup(bot: Bot) -> None:
    await bot.add_cog(GitHubStats(bot))
