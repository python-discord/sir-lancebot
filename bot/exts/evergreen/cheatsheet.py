import random
import re
import typing as t
from urllib.parse import quote_plus

from discord import Embed
from discord.ext import commands
from discord.ext.commands import BucketType, Context

from bot.constants import Channels, Colours, ERROR_REPLIES

ERROR_MESSAGE = """
Unknown cheat sheet. Please try to reformulate your query.

**Examples**:
```md
.cht read json
.cht hello world
.cht lambda
```
If the problem persists send a message in <#{channel}>
"""


class ChtSh(commands.Cog):
    """Commands that sends a result of a cht.sh search in code blocks."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def fmt_error_embed() -> Embed:
        """If the cht.sh search returned 404, overwrite it to send a custom error embed."""
        embed = Embed(colour=Colours.soft_red)
        embed.title = random.choice(ERROR_REPLIES)
        embed.description = ERROR_MESSAGE.format(channel=Channels.dev_contrib)
        return embed

    def result_fmt(self, url: str, body_text: str) -> t.Tuple[bool, t.Union[str, Embed]]:
        """Format Result."""
        if body_text.startswith("#  404 NOT FOUND"):
            embed = self.fmt_error_embed()
            return True, embed

        body_space = min(1986 - len(url), 1000)

        if len(body_text) > body_space:
            description = f"**Result Of cht.sh**\n" \
                          f"```python\n{body_text[:body_space]}\n" \
                          f"... (truncated - too many lines)```\n" \
                          f"Full results: {url} "
        else:
            description = f"**Result Of cht.sh**\n" \
                          f"```python\n{body_text}```\n" \
                          f"{url}"
        return False, description

    @commands.command(
        name="cheat",
        aliases=("cht.sh", "cheatsheet", "cheat-sheet", "cht"),
    )
    @commands.cooldown(1, 10, BucketType.user)
    async def cheat_sheet(
            self, ctx: Context, *search_terms: str
    ) -> None:
        """
        Search cheat.sh.

        Gets a post from https://cheat.sh/python/ by default.
        Usage:
        --> .cht read json
        """
        url = f'https://cheat.sh/python/{quote_plus(" ".join(search_terms))}'
        headers = {
            'User-Agent': 'curl/7.68.0'
        }

        escape_tt = str.maketrans({"`": "\\`"})
        ansi_re = re.compile(r"\x1b\[.*?m")

        async with self.bot.http_session.get(url, headers=headers) as response:
            result = ansi_re.sub("", await response.text()).translate(escape_tt)

        is_embed, desciprtion = self.result_fmt(url, result)
        if is_embed:
            await ctx.send(embed=desciprtion)
        else:
            await ctx.send(content=desciprtion)


def setup(bot: commands.Bot) -> None:
    """Load the ChtSh cog."""
    bot.add_cog(ChtSh(bot))
