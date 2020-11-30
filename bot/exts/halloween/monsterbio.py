import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)

with open(Path("bot/resources/halloween/monster.json"), "r", encoding="utf8") as f:
    TEXT_OPTIONS = json.load(f)  # Data for a mad-lib style generation of text


class MonsterBio(commands.Cog):
    """A cog that generates a spooky monster biography."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def generate_name(self, seeded_random: random.Random) -> str:
        """Generates a name (for either monster species or monster name)."""
        n_candidate_strings = seeded_random.randint(2, len(TEXT_OPTIONS["monster_type"]))
        return "".join(seeded_random.choice(TEXT_OPTIONS["monster_type"][i]) for i in range(n_candidate_strings))

    @commands.command(brief="Sends your monster bio!")
    async def monsterbio(self, ctx: commands.Context) -> None:
        """Sends a description of a monster."""
        seeded_random = random.Random(ctx.message.author.id)  # Seed a local Random instance rather than the system one

        name = self.generate_name(seeded_random)
        species = self.generate_name(seeded_random)
        biography_text = seeded_random.choice(TEXT_OPTIONS["biography_text"])
        words = {"monster_name": name, "monster_species": species}
        for key, value in biography_text.items():
            if key == "text":
                continue

            options = seeded_random.sample(TEXT_OPTIONS[key], value)
            words[key] = ' '.join(options)

        embed = discord.Embed(
            title=f"{name}'s Biography",
            color=seeded_random.choice([Colours.orange, Colours.purple]),
            description=biography_text["text"].format_map(words),
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Monster bio Cog load."""
    bot.add_cog(MonsterBio(bot))
