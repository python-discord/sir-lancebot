import collections
import json
import logging
from pathlib import Path
from random import choice

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path('bot', 'resources', 'valentines', 'valenstates.json'), 'r') as file:
    STATES = json.load(file)


class MyValenstate:
    def __init__(self, bot):
        self.bot = bot

    def levenshtein(self, source, goal):
        """
        Calculates the Levenshtein Distance between source and goal.
        """
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
    async def myvalenstate(self, ctx, *, name=None):
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
        leftovers = f"{', '.join(matches[:len(matches)-2])}, and {matches[len(matches)-1]}"

        embed = discord.Embed(
            title=f'Your Valenstate is {valenstate} \u2764',
            description=f'{STATES[valenstate]["text"]}',
            colour=Colours.pink
        )

        if len(matches) > 1:
            embed.add_field(
                name="But there are more!",
                value=f"You have {len(matches)} more matches, these being {leftovers}."
            )
        embed.set_image(
            url=STATES[valenstate]["flag"]
        )
        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(MyValenstate(bot))
    log.debug("MyValenstate cog loaded")
