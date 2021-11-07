import logging
import random
import re
from typing import Optional

import rapidfuzz
from discord import Embed, File
from discord.ext import commands, tasks

from bot import constants
from bot.bot import Bot

log = logging.getLogger(__name__)

WTF_PYTHON_RAW_URL = "http://raw.githubusercontent.com/satwikkansal/wtfpython/master/"
BASE_URL = "https://github.com/satwikkansal/wtfpython"
LOGO_PATH = "./bot/resources/utilities/wtf_python_logo.jpg"

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

MINIMUM_CERTAINTY = 55


class WTFPython(commands.Cog):
    """Cog that allows getting WTF Python entries from the WTF Python repository."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.headers: dict[str, str] = {}
        self.fetch_readme.start()

    @tasks.loop(minutes=60)
    async def fetch_readme(self) -> None:
        """Gets the content of README.md from the WTF Python Repository."""
        async with self.bot.http_session.get(f"{WTF_PYTHON_RAW_URL}README.md") as resp:
            log.trace("Fetching the latest WTF Python README.md")
            if resp.status == 200:
                raw = await resp.text()
                self.parse_readme(raw)

    def parse_readme(self, data: str) -> None:
        """
        Parses the README.md into a dict.

        It parses the readme into the `self.headers` dict,
        where the key is the heading and the value is the
        link to the heading.
        """
        # Match the start of examples, until the end of the table of contents (toc)
        table_of_contents = re.search(
            r"\[👀 Examples\]\(#-examples\)\n([\w\W]*)<!-- tocstop -->", data
        )[0].split("\n")

        for header in list(map(str.strip, table_of_contents)):
            match = re.search(r"\[▶ (.*)\]\((.*)\)", header)
            if match:
                hyper_link = match[0].split("(")[1].replace(")", "")
                self.headers[match[0]] = f"{BASE_URL}/{hyper_link}"

    def fuzzy_match_header(self, query: str) -> Optional[str]:
        """
        Returns the fuzzy match of a query if its ratio is above "MINIMUM_CERTAINTY" else returns None.

        "MINIMUM_CERTAINTY" is the lowest score at which the fuzzy match will return a result.
        The certainty returned by rapidfuzz.process.extractOne is a score between 0 and 100,
        with 100 being a perfect match.
        """
        match, certainty, _ = rapidfuzz.process.extractOne(query, self.headers.keys())
        return match if certainty > MINIMUM_CERTAINTY else None

    @commands.command(aliases=("wtf", "WTF"))
    async def wtf_python(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
        """
        Search WTF Python repository.

        Gets the link of the fuzzy matched query from https://github.com/satwikkansal/wtfpython.
        Usage:
            --> .wtf wild imports
        """
        if query is None:
            no_query_embed = Embed(
                title="WTF Python?!",
                colour=constants.Colours.dark_green,
                description="A repository filled with suprising snippets that can make you say WTF?!\n\n"
                f"[Go to the Repository]({BASE_URL})"
            )
            logo = File(LOGO_PATH, filename="wtf_logo.jpg")
            no_query_embed.set_thumbnail(url="attachment://wtf_logo.jpg")
            await ctx.send(embed=no_query_embed, file=logo)
            return

        if len(query) > 50:
            embed = Embed(
                title=random.choice(constants.ERROR_REPLIES),
                description=ERROR_MESSAGE,
                colour=constants.Colours.soft_red,
            )
            match = None
        else:
            match = self.fuzzy_match_header(query)

        if not match:
            embed = Embed(
                title=random.choice(constants.ERROR_REPLIES),
                description=ERROR_MESSAGE,
                colour=constants.Colours.soft_red,
            )
            await ctx.send(embed=embed)
            return

        embed = Embed(
            title="WTF Python?!",
            colour=constants.Colours.dark_green,
            description=f"""Search result for '{query}': {match.split("]")[0].replace("[", "")}
            [Go to Repository Section]({self.headers[match]})""",
        )
        logo = File(LOGO_PATH, filename="wtf_logo.jpg")
        embed.set_thumbnail(url="attachment://wtf_logo.jpg")
        await ctx.send(embed=embed, file=logo)

    def cog_unload(self) -> None:
        """Unload the cog and cancel the task."""
        self.fetch_readme.cancel()


def setup(bot: Bot) -> None:
    """Load the WTFPython Cog."""
    bot.add_cog(WTFPython(bot))
