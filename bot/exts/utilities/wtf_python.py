import functools
import logging
import random
import re
from enum import Enum
from typing import Dict, Optional

from discord import Embed
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

MINIMUM_CERTAINTY = 75


class Action(Enum):
    """Represents an action to perform on an extension."""

    # Need to be partial otherwise they are considered to be function definitions.
    LOAD = functools.partial(Bot.load_extension)
    UNLOAD = functools.partial(Bot.unload_extension)


class WTFPython(commands.Cog):
    """Cog that allows getting WTF Python entries from the WTF Python repository."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.get_WTF_python_readme.start()

        self.headers: Dict[str] = dict()

    @tasks.loop(hours=1)
    async def get_wtf_python_readme(self) -> None:
        """Gets the content of README.md from the WTF Python Repository."""
        failed_tries = 0

        for x in range(FETCH_TRIES):
            async with self.bot.http_session.get(f"{WTF_PYTHON_RAW_URL}README.md") as resp:
                log.trace("Fetching the latest WTF Python README.md")

                if resp.status == 200:
                    raw = await resp.text()
                    self.parse_readme(raw)
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
        ext = "bot.exts.evergreen.wtf_python"

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
        """Returns the fuzzy match of a query if its ratio is above "MINIMUM_CERTAINTY" else returns None."""
        match, certainty = process.extractOne(query, self.headers.keys())
        return match if certainty > MINIMUM_CERTAINTY else None

    @commands.command(aliases=("wtf", "WTF"))
    async def wtf_python(self, ctx: commands.Context, *, query: str) -> None:
        """
        Search WTF python.

        Gets the link of the fuzzy matched query from https://github.com/satwikkansal/wtfpython.
        Usage:
            --> .wtf wild imports
        """
        match = self.fuzzy_match_header(query)
        if not match:
            embed = Embed(
                title=random.choice(constants.ERROR_REPLIES),
                description=ERROR_MESSAGE,
                colour=constants.Colours.soft_red,
            )
        else:
            embed = Embed(
                title=f"WTF Python Search Result For {query}",
                colour=constants.Colours.dark_green,
                description=f"[Go to Repository Section]({self.headers[match]})",
            )
            embed.set_thumbnail(url=f"{WTF_PYTHON_RAW_URL}images/logo.png")
        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load WTFPython Cog."""
    bot.add_cog(WTFPython(bot))
