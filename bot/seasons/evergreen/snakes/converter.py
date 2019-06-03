import json
import logging
import random

import discord
from discord.ext.commands import Converter
from fuzzywuzzy import fuzz

from bot.seasons.evergreen.snakes.utils import SNAKE_RESOURCES
from bot.utils import disambiguate

log = logging.getLogger(__name__)


class Snake(Converter):
    snakes = None
    special_cases = None

    async def convert(self, ctx, name):
        await self.build_list()
        name = name.lower()

        if name == 'python':
            return 'Python (programming language)'

        def get_potential(iterable, *, threshold=80):
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
    async def build_list(cls):
        # Get all the snakes
        if cls.snakes is None:
            with (SNAKE_RESOURCES / "snake_names.json").open() as snakefile:
                cls.snakes = json.load(snakefile)

        # Get the special cases
        if cls.special_cases is None:
            with (SNAKE_RESOURCES / "special_snakes.json").open() as snakefile:
                special_cases = json.load(snakefile)
            cls.special_cases = {snake['name'].lower(): snake for snake in special_cases}

    @classmethod
    async def random(cls):
        """
        This is stupid. We should find a way to
        somehow get the global session into a
        global context, so I can get it from here.
        :return:
        """
        await cls.build_list()
        names = [snake['scientific'] for snake in cls.snakes]
        return random.choice(names)
