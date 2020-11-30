import json
import logging
import random
from typing import Iterable, List

import discord
from discord.ext.commands import Context, Converter
from fuzzywuzzy import fuzz

from bot.exts.evergreen.snakes._utils import SNAKE_RESOURCES
from bot.utils import disambiguate

log = logging.getLogger(__name__)


class Snake(Converter):
    """Snake converter for the Snakes Cog."""

    snakes = None
    special_cases = None

    async def convert(self, ctx: Context, name: str) -> str:
        """Convert the input snake name to the closest matching Snake object."""
        await self.build_list()
        name = name.lower()

        if name == 'python':
            return 'Python (programming language)'

        def get_potential(iterable: Iterable, *, threshold: int = 80) -> List[str]:
            nonlocal name
            potential = []

            for item in iterable:
                original, item = item, item.lower()

                if name == item:
                    return [original]

                a, b = fuzz.ratio(name, item), fuzz.partial_ratio(name, item)
                if a >= threshold or b >= threshold:
                    potential.append(original)

            return potential

        # Handle special cases
        if name.lower() in self.special_cases:
            return self.special_cases.get(name.lower(), name.lower())

        names = {snake['name']: snake['scientific'] for snake in self.snakes}
        all_names = names.keys() | names.values()
        timeout = len(all_names) * (3 / 4)

        embed = discord.Embed(
            title='Found multiple choices. Please choose the correct one.', colour=0x59982F)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        name = await disambiguate(ctx, get_potential(all_names), timeout=timeout, embed=embed)
        return names.get(name, name)

    @classmethod
    async def build_list(cls) -> None:
        """Build list of snakes from the static snake resources."""
        # Get all the snakes
        if cls.snakes is None:
            with (SNAKE_RESOURCES / "snake_names.json").open(encoding="utf8") as snakefile:
                cls.snakes = json.load(snakefile)

        # Get the special cases
        if cls.special_cases is None:
            with (SNAKE_RESOURCES / "special_snakes.json").open(encoding="utf8") as snakefile:
                special_cases = json.load(snakefile)
            cls.special_cases = {snake['name'].lower(): snake for snake in special_cases}

    @classmethod
    async def random(cls) -> str:
        """
        Get a random Snake from the loaded resources.

        This is stupid. We should find a way to somehow get the global session into a global context,
        so I can get it from here.
        """
        await cls.build_list()
        names = [snake['scientific'] for snake in cls.snakes]
        return random.choice(names)
