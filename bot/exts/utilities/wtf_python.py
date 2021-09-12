import logging
import random
import re
from enum import Enum
from functools import partial
from io import StringIO
from typing import Optional

from discord import Embed, File
from discord.ext import commands, tasks
from rapidfuzz import process

from bot import constants
from bot.bot import Bot

log = logging.getLogger(__name__)

WTF_PYTHON_RAW_URL = "http://raw.githubusercontent.com/satwikkansal/wtfpython/master/"
BASE_URL = "https://github.com/satwikkansal/wtfpython"
FETCH_TRIES = 3

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

MINIMUM_CERTAINTY = 50


class Action(Enum):
    """Represents an action to perform on an extension."""

    # Need to be partial otherwise they are considered to be function definitions.
    LOAD = partial(Bot.load_extension)
    UNLOAD = partial(Bot.unload_extension)


class WTFPython(commands.Cog):
    """Cog that allows getting WTF Python entries from the WTF Python repository."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.fetch_readme.start()

        self.headers: dict[str, str] = dict()
        self.raw = None

    @tasks.loop(hours=1)
    async def fetch_readme(self) -> None:
        """Gets the content of README.md from the WTF Python Repository."""
        failed_tries = 0

        for x in range(FETCH_TRIES):
            async with self.bot.http_session.get(f"{WTF_PYTHON_RAW_URL}README.md") as resp:
                log.trace("Fetching the latest WTF Python README.md")

                if resp.status == 200:
                    self.raw = await resp.text()
                    self.parse_readme(self.raw)
                    log.debug(
                        "Successfully fetched the latest WTF Python README.md, "
                        "breaking out of retry loop"
                    )
                    break

                else:
                    failed_tries += 1
                    log.debug(
                        "Failed to get latest WTF Python README.md on try "
                        f"{x}/{FETCH_TRIES}. Status code {resp.status}"
                    )

        if failed_tries == 3:
            log.error("Couldn't fetch WTF Python README.md after 3 tries, unloading extension.")
            action = Action.UNLOAD
        else:
            action = Action.LOAD

        verb = action.name.lower()
        ext = "bot.exts.utilities.wtf_python"

        try:
            action.value(self.bot, ext)
        except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotLoaded):
            log.debug(f"Extension `{ext}` is already {verb}ed.")
        else:
            log.debug(f"Extension {verb}ed: `{ext}`.")

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
            match = re.findall(r"\[▶ (.*)\]\((.*)\)", header)
            if match:
                self.headers[match[0][0]] = f"{BASE_URL}{match[0][1]}"

    def fuzzy_match_header(self, query: str) -> Optional[str]:
        """
        Returns the fuzzy match of a query if its ratio is above "MINIMUM_CERTAINTY" else returns None.

        "MINIMUM_CERTAINTY" is the lowest score at which the fuzzy match will return a result.
        The certainty returned by rapidfuzz.process.extractOne is a score between 0 and 100,
        with 100 being a perfect match.
        """
        match, certainty, _ = process.extractOne(query, self.headers.keys())
        log.debug(f"{match = }, {certainty = }")
        return match if certainty > MINIMUM_CERTAINTY else None

    def readme_file(self, header: str) -> File:
        """Create a markdown file from the readme using the matched header."""
        toc_end = self.raw.find("<!-- tocstop -->")
        header_start = self.raw.find(header, toc_end)
        header_stop = self.raw.find("\n---\n", header_start)
        content = self.raw[header_start:header_stop]
        content_file = StringIO(content)
        embed_file = File(content_file, "WTF_content.md")

        return embed_file

    @commands.command(aliases=("wtf", "WTF"))
    async def wtf_python(self, ctx: commands.Context, *, query: str) -> None:
        """
        Search WTF python.

        Gets the link of the fuzzy matched query from https://github.com/satwikkansal/wtfpython.
        Usage:
            --> .wtf wild imports
        """
        match = self.fuzzy_match_header(query)
        if match:
            embed_file = self.readme_file(match)
            embed = Embed(
                title=f"WTF Python Search Result For {query}",
                colour=constants.Colours.dark_green,
                description=f"[Go to Repository Section]({self.headers[match]})",
            )
            embed.set_thumbnail(url=f"{WTF_PYTHON_RAW_URL}images/logo.png")
            await ctx.send(embed=embed, file=embed_file)
            return
        else:
            embed = Embed(
                title=random.choice(constants.ERROR_REPLIES),
                description=ERROR_MESSAGE,
                colour=constants.Colours.soft_red,
            )
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the WTFPython Cog."""
    bot.add_cog(WTFPython(bot))
