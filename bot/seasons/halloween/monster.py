import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands
from constants import Colour

log = logging.getLogger(__name__)

with open(Path("bot/resources/halloween/monster.json"), "r", encoding="utf8") as f:
    TEXT_OPTIONS = json.load(f) # Data for a mad-lib style generation of text

class MonsterBio(commands.Cog):
    """A cog that generates a spooky monster biography."""

    def generate_name(length):
        return "".join([random.choice(TEXT_OPTIONS["monster_type"][i]) for i in range(length)])

    @commands.command(brief="Sends your monster bio!")
    async def monsterbio(self, ctx: commands.Context) -> None:
        """Sends a description of a monster."""
        random.seed(ctx.message.author.id)
        name = self.generate_name(random.randint(2, len(TEXT_OPTIONS["monster_type"])))
        species = selfgenerate_name(random.randint(2, len(TEXT_OPTIONS["monster_type"])))
        biography_text = random.choice(TEXT_OPTIONS["biography_text"])
        words = {"monster_name": name, "monster_species": species}
        for key, value in biography_text.items():
            if key == "text":
                continue
            if value > 1:
                words[key] = random.sample(TEXT_OPTIONS[key], value)
            else:
                words[key] = random.choice(TEXT_OPTIONS[key])
        embed = discord.Embed(
            title=f"{name}'s Biography",
            color=random.choice([Colours.orange, Colours.purple]), description=biography_text["text"].format(**words)
        )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Monster bio Cog load."""
    bot.add_cog(MonsterBio(bot))
    log.info("MonsterBio cog loaded!")
