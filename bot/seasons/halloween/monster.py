import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

with open(Path("bot/resources/halloween/monster.json"), "r", encoding="utf8") as f:
    data = json.load(f)

PUMPKIN_ORANGE = discord.Color(0xFF7518)
OTHER_PURPLE = discord.Color(0xB734EB)


class MonsterBio(commands.Cog):
    """A cog that generates a spooky monster biography."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel = None

    @commands.command(brief="Sends your monster bio!")
    async def monsterbio(self, ctx: commands.Context) -> None:
        """Sends a description of a monster."""
        random.seed(ctx.message.author.id)
        name_length = random.randint(2, len(data["monster_type"]))
        species_length = random.randint(2, len(data["monster_type"]))
        name = species = ""
        for i in range(name_length):
            name += random.choice(data["monster_type"][i])
        for i in range(species_length):
            species += random.choice(data["monster_type"][i])
        format = random.choice(data["format"])
        words = {"monster_name": name, "monster_species": species}
        for key, value in format.items():
            if key == "text":
                continue
            if value > 1:
                words[key] = random.sample(data[key], value)
            else:
                words[key] = random.choice(data[key])
        embed = discord.Embed(
            title=f"{name}'s Biography",
            color=random.choice([PUMPKIN_ORANGE, OTHER_PURPLE]), description=format["text"].format(**words)
        )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Monster bio Cog load."""
    bot.add_cog(MonsterBio(bot))
    log.info("MonsterBio cog loaded!")
