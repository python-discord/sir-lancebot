import json
import logging
import random
import re
from pathlib import Path

from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot", "resources", "easter", "bunny_names.json"), "r", encoding="utf8") as f:
    BUNNY_NAMES = json.load(f)


class BunnyNameGenerator(commands.Cog):
    """Generate a random bunny name, or bunnify your Discord username!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bunnyname(self, ctx):
        """Picks a random bunny name from a JSON file"""

        await ctx.send(random.choice(BUNNY_NAMES["names"]))

    @commands.command()
    async def bunnifyme(self, ctx):
        """Gets your Discord username and bunnifies it"""

        def filter_name(displayname):
            """Turns separators into whitespace"""

            if displayname.find('_') != -1:
                displayname = displayname.replace('_', ' ')
            if displayname.find('.') != -1:
                displayname = displayname.replace('.', ' ')

            return displayname

        def find_spaces(displayname):
            """
            Check if Discord name contains spaces so we can bunnify an individual word in the name.

            Spaces should not be bunnified so we remove them from
            the list that is returned from the pattern matching.
            """

            contains_spaces = re.findall(r'^\w+|\s+|\w+$', displayname)
            if len(contains_spaces) > 1:
                contains_spaces.remove(' ')
                displayname = contains_spaces
                return displayname

        def find_vowels(displayname):
            """
            Finds vowels in the user's display name.

            If the Discord name contains a vowel and the letter y,
            it will match one or more of these patterns.
            Only the most recently matched pattern will apply the changes.
            """

            new_name = None

            option1 = re.sub(r'a.+y', 'patchy', displayname)
            option2 = re.sub(r'e.+y', 'ears', displayname)
            option3 = re.sub(r'i.+y', 'ditsy', displayname)
            option4 = re.sub(r'o.+y', 'oofy', displayname)
            option5 = re.sub(r'u.+y', 'uffy', displayname)

            if option1 != displayname:
                new_name = option1
            if option2 != displayname:
                new_name = option2
            if option3 != displayname:
                new_name = option3
            if option4 != displayname:
                new_name = option4
            if option5 != displayname:
                new_name = option5

            return new_name

        def append_name(displayname):
            """Adds a suffix to the end of the Discord name"""

            extensions = ['foot', 'ear', 'nose', 'tail']
            suffix = random.choice(extensions)
            appended_name = displayname + suffix

            return appended_name

        username = ctx.message.author.display_name
        username_filtered = filter_name(username)  # Filter username before pattern matching

        spaces_pattern = find_spaces(username_filtered)  # Does the name contain spaces?

        vowels_pattern = find_vowels(username_filtered)  # Does the name contain vowels?
        # If so, does it match any of the patterns in this function?

        unmatched_name = append_name(username_filtered)  # Default if name doesn't match the above patterns

        if spaces_pattern is not None:
            replacements = ['Cotton', 'Fluff', 'Floof' 'Bounce', 'Snuffle', 'Nibble', 'Cuddle', 'Velvetpaw', 'Carrot']
            word_to_replace = random.choice(spaces_pattern)
            substitute = random.choice(replacements)
            bunnified_name = username_filtered.replace(word_to_replace, substitute)
        elif vowels_pattern is not None:
            bunnified_name = vowels_pattern
        elif unmatched_name:
            bunnified_name = unmatched_name

        await ctx.send(bunnified_name)


def setup(bot):
    """Cog load."""

    bot.add_cog(BunnyNameGenerator(bot))
    log.info("BunnyNameGenerator cog loaded.")
