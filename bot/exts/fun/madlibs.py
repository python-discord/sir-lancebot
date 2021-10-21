from asyncio import TimeoutError
from json import load
from pathlib import Path
from random import choice
# import json
# from typing import Literal
# from typing import List

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

TIMEOUT = 60.0


class Madlibs(commands.Cog):
    """
    Cog for the Madlibs game.

    Madlibs is a game where the player is asked to enter a word that
    fits a random part of speech (e.g. noun, adjective, verb, plural noun, etc.).
    The bot chooses a random number of user inputs (within the specified bounds
    of the command arguments) to use for the game and a random story.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.templates = self._load_templates()

    @staticmethod
    def _load_templates() -> list:
        madlibs_stories = Path("bot/resources/fun/madlibs_templates.json")

        with open(madlibs_stories) as file:
            return load(file)

    @commands.command()
    async def madlibs(
        self,
        ctx: commands.Context,
        min_length: int = 5,
        max_length: int = 15
    ) -> None:
        """
        Play Madlibs with the bot, where you have to enter a word that fits the part of speech that you are given!

        The arguments for this command mean:
        - min_length: the minimum number of inputs you would like in your game
        - max_length: the maximum number of inputs you would like in your game
        """
        current_input = 0
        number_of_inputs = 0

        random_template = choice(self._load_templates)

        filtered_blanks = min_length < len(random_template["blanks"]) < max_length

        if not filtered_blanks:
            filter_not_found_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="Sorry, we could not generate a game for you because "
                            "you entered invalid numbers for the filters.",
                color=Colours.soft_red,
            )
            await ctx.send(embed=filter_not_found_embed)
            return

        while number_of_inputs != 0:
            part_of_speech = random_template["blanks"][current_input]
            inputs_left = random_template["blanks"][number_of_inputs]

            madlibs_embed = Embed(
                title="Madlibs",
                color=Colours.python_blue,
            )

            madlibs_embed.add_field(
                name="Enter a word that fits the given part of speech!",
                value=f"Please enter a {part_of_speech}!"
            )

            madlibs_embed.set_footer(text=f"Inputs remaining: {inputs_left}")

            current_input += 1
            number_of_inputs -= 1

            await ctx.send(embed=madlibs_embed)

            try:
                await self.bot.wait_for(event='message', timeout=TIMEOUT)
            except TimeoutError:
                Embed(title=choice(NEGATIVE_REPLIES),
                      description='Uh oh! Looks like the bot timed out! Please try again later.')

        Embed(
            title="Here's your story!",
            description=random_template["value"]
        )


def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    bot.add_cog(Madlibs(bot))
