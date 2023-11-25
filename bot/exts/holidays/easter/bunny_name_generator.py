import json
import random
import re
from pathlib import Path

from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot

log = get_logger(__name__)

BUNNY_NAMES = json.loads(Path("bot/resources/holidays/easter/bunny_names.json").read_text("utf8"))


class BunnyNameGenerator(commands.Cog):
    """Generate a random bunny name, or bunnify your Discord username!"""

    @staticmethod
    def find_separators(displayname: str) -> list[str] | None:
        """Check if Discord name contains spaces so we can bunnify an individual word in the name."""
        new_name = re.split(r"[_.\s]", displayname)
        if displayname not in new_name:
            return new_name
        return None

    @staticmethod
    def find_vowels(displayname: str) -> str | None:
        """
        Finds vowels in the user's display name.

        If the Discord name contains a vowel and the letter y, it will match one or more of these patterns.

        Only the most recently matched pattern will apply the changes.
        """
        expressions = [
            ("a.+y", "patchy"),
            ("e.+y", "ears"),
            ("i.+y", "ditsy"),
            ("o.+y", "oofy"),
            ("u.+y", "uffy"),
        ]

        for exp, vowel_sub in expressions:
            new_name = re.sub(exp, vowel_sub, displayname)
            if new_name != displayname:
                return new_name
        return None

    @staticmethod
    def append_name(displayname: str) -> str:
        """Adds a suffix to the end of the Discord name."""
        extensions = ["foot", "ear", "nose", "tail"]
        suffix = random.choice(extensions)
        appended_name = displayname + suffix

        return appended_name

    @commands.command()
    async def bunnyname(self, ctx: commands.Context) -> None:
        """Picks a random bunny name from a JSON file."""
        await ctx.send(random.choice(BUNNY_NAMES["names"]))

    @commands.command()
    async def bunnifyme(self, ctx: commands.Context) -> None:
        """Gets your Discord username and bunnifies it."""
        username = ctx.author.display_name

        # If name contains spaces or other separators, get the individual words to randomly bunnify
        spaces_in_name = self.find_separators(username)

        # If name contains vowels, see if it matches any of the patterns in this function
        # If there are matches, the bunnified name is returned.
        vowels_in_name = self.find_vowels(username)

        # Default if the checks above return None
        unmatched_name = self.append_name(username)

        if spaces_in_name is not None:
            replacements = ["Cotton", "Fluff", "Floof", "Bounce", "Snuffle", "Nibble", "Cuddle", "Velvetpaw", "Carrot"]
            word_to_replace = random.choice(spaces_in_name)
            substitute = random.choice(replacements)
            bunnified_name = username.replace(word_to_replace, substitute)
        elif vowels_in_name is not None:
            bunnified_name = vowels_in_name
        elif unmatched_name:
            bunnified_name = unmatched_name

        await ctx.send(bunnified_name)


async def setup(bot: Bot) -> None:
    """Load the Bunny Name Generator Cog."""
    await bot.add_cog(BunnyNameGenerator())
