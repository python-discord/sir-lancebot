import random
from pathlib import Path

import yaml
from discord.ext.commands import Cog, Context, command

from bot.bot import Bot


class WonderTwins(Cog):
    """Cog for a Wonder Twins inspired command."""

    def __init__(self):
        with open(Path.cwd() / "bot" / "resources" / "fun" / "wonder_twins.yaml", encoding="utf-8") as f:
            info = yaml.safe_load(f)
            self.water_types = info["water_types"]
            self.objects = info["objects"]
            self.adjectives = info["adjectives"]

    @staticmethod
    def append_onto(phrase: str, insert_word: str) -> str:
        """Appends one word onto the end of another phrase in order to format with the proper determiner."""
        if insert_word.endswith("s"):
            phrase = phrase.split()
            del phrase[0]
            phrase = " ".join(phrase)

        insert_word = insert_word.split()[-1]
        return " ".join([phrase, insert_word])

    def format_phrase(self) -> str:
        """Creates a transformation phrase from available words."""
        adjective = random.choice((None, random.choice(self.adjectives)))
        object_name = random.choice(self.objects)
        water_type = random.choice(self.water_types)

        if adjective:
            object_name = self.append_onto(adjective, object_name)
        return f"{object_name} of {water_type}"

    @command(name="formof", aliases=("wondertwins", "wondertwin", "fo"))
    async def form_of(self, ctx: Context) -> None:
        """Command to send a Wonder Twins inspired phrase to the user invoking the command."""
        await ctx.send(f"Form of {self.format_phrase()}!")


async def setup(bot: Bot) -> None:
    """Load the WonderTwins cog."""
    await bot.add_cog(WonderTwins())
