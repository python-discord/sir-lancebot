import logging
import random
import re
from typing import Dict, Optional

from discord import Embed
from discord.ext import commands, tasks
from fuzzywuzzy import process

from bot import constants
from bot.bot import Bot

log = logging.getLogger(__name__)

WTF_PYTHON_RAW_URL = ("http://raw.githubusercontent.com/satwikkansal/"
                      "wtfpython/master/README.md")
BASE_URL = "https://github.com/satwikkansal/wtfpython"
THUMBNAIL = "https://raw.githubusercontent.com/satwikkansal/wtfpython/master/images/logo.png"

ERROR_MESSAGE = f"""
Unknown WTF Python Query. Please try to reformulate your query.

**Examples**:
```md
{constants.Client.prefix}wtf wild imports
{constants.Client.prefix}wtf subclass
{constants.Client.prefix}wtf del
```
If the problem persists send a message in <#{constants.Channels.dev_contrib}>
"""


class WTFPython(commands.Cog):
    """Cog that allows users to retrieve issues from GitHub."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.get_wtf_python_readme.start()

        self.headers: Dict[str] = dict()

    @tasks.loop(hours=1)
    async def get_wtf_python_readme(self) -> None:
        """Gets the content of README.md from the WTF Python Repository."""
        async with self.bot.http_session.get(WTF_PYTHON_RAW_URL) as resp:
            if resp.status == 200:
                self.raw = await resp.text()
                await self.parse_readme(self.raw)
            else:
                log.debug(f"Failed to get latest WTF Python README.md. Status code {resp.status}")

    async def parse_readme(self, data: str) -> None:
        """
        Parses the README.md into a dict.

        It parses the readme into the `self.headers` dict,
        where the key is the heading and the value is the
        link to the heading.
        """
        table_of_contents = re.findall(
            r"\[👀 Examples\]\(#-examples\)\n([\w\W]*)<!-- tocstop -->", data
        )[0].split("\n")
        table_of_contents = list(map(str.strip, table_of_contents))

        for header in table_of_contents:
            match = re.findall(r"\[▶ (.*)\]\((.*)\)", header)
            if match:
                self.headers.update(
                    {
                        match[0][0]: f"{BASE_URL}{match[0][1]}"
                    }
                )

    def fuzzy_match_header(self, query: str) -> Optional[str]:
        """Returns the fuzzy match of a query if its ratio is above 90 else returns None."""
        match, certainty = process.extractOne(query, self.headers.keys())
        return match if certainty > 90 else None

    @staticmethod
    async def make_embed(query: str, link: str) -> Embed:
        """Generates a embed for a search."""
        embed = Embed(
            title=f"WTF Python Search Result For {query}",
            colour=constants.Colours.dark_green,
            description=f"[Go to Repository Section]({link})"
        )
        embed.set_thumbnail(url=THUMBNAIL)
        return embed

    @commands.command(aliases=("wtf",))
    async def wtf_python(self, ctx: commands.Context, *query: str) -> None:
        """
        Search wtf python.

        Gets the link of the fuzzy matched query from https://github.com/satwikkansal/wtfpython.
        Usage:
            --> .wtf wild imports
        """
        query = " ".join(query)
        match = self.fuzzy_match_header(query)
        if not match:
            embed = Embed(
                title=random.choice(constants.ERROR_REPLIES),
                description=ERROR_MESSAGE,
                colour=constants.Colours.soft_red
            )
        else:
            embed = await self.make_embed(query, self.headers[match])
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load WTFPython Cog."""
    bot.add_cog(WTFPython(bot))
