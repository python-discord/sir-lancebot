import collections
import json
import logging
from pathlib import Path
from random import choice

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path("bot/resources/valentines/valenstates.json"), "r") as file:
    STATES = json.load(file)


class MyValenstate(commands.Cog):
    """A Cog to find your most likely Valentine's vacation destination."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def levenshtein(self, source: str, goal: str) -> int:
        """Calculates the Levenshtein Distance between source and goal."""
        if len(source) < len(goal):
            return self.levenshtein(goal, source)
        if len(source) == 0:
            return len(goal)
        if len(goal) == 0:
            return len(source)

        pre_row = list(range(0, len(source) + 1))
        for i, source_c in enumerate(source):
            cur_row = [i + 1]
            for j, goal_c in enumerate(goal):
                if source_c != goal_c:
                    cur_row.append(min(pre_row[j], pre_row[j + 1], cur_row[j]) + 1)
                else:
                    cur_row.append(min(pre_row[j], pre_row[j + 1], cur_row[j]))
            pre_row = cur_row
        return pre_row[-1]

    @commands.command()
    async def myvalenstate(self, ctx: commands.Context, *, name: str = None) -> None:
        """Find the vacation spot(s) with the most matching characters to the invoking user."""
        eq_chars = collections.defaultdict(int)
        if name is None:
            author = ctx.message.author.name.lower().replace(' ', '')
        else:
            author = name.lower().replace(' ', '')

        for state in STATES.keys():
            lower_state = state.lower().replace(' ', '')
            eq_chars[state] = self.levenshtein(author, lower_state)

        matches = [x for x, y in eq_chars.items() if y == min(eq_chars.values())]
        valenstate = choice(matches)
        matches.remove(valenstate)

        embed_title = "But there are more!"
        if len(matches) > 1:
            leftovers = f"{', '.join(matches[:len(matches)-2])}, and {matches[len(matches)-1]}"
            embed_text = f"You have {len(matches)} more matches, these being {leftovers}."
        elif len(matches) == 1:
            embed_title = "But there's another one!"
            leftovers = str(matches)
            embed_text = f"You have another match, this being {leftovers}."
        else:
            embed_title = "You have a true match!"
            embed_text = "This state is your true Valenstate! There are no states that would suit" \
                         " you better"

        embed = discord.Embed(
            title=f'Your Valenstate is {valenstate} \u2764',
            description=f'{STATES[valenstate]["text"]}',
            colour=Colours.pink
        )
        embed.add_field(name=embed_title, value=embed_text)
        embed.set_image(url=STATES[valenstate]["flag"])
        await ctx.channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Valenstate Cog load."""
    bot.add_cog(MyValenstate(bot))
    log.info("MyValenstate cog loaded")
