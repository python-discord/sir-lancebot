from asyncio import TimeoutError
from pathlib import Path
from random import choice
# from json import loads
# from typing import Literal
from typing import List

from discord import Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

# Defining a json file with the story templates as a global variable
madlibs_stories = Path("bot/exts/fun/madlibs/madlibs_templates.json")

with madlibs_stories as file:
    random_template = choice(file["templates"])


class Madlibs(commands.Cog):
    """
    Cog for the Madlibs game.

    Madlibs is a game where the player is asked to enter a word that
    fits a random part of speech (e.g. noun, adjective, verb, plural noun, etc.).
    The bot chooses a random number of user inputs to use for the game and a random story.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def create_embed(random_template: List) -> Embed:
        """
        Helper method that creates the embed where the game information is shown.

        This includes what part of speech the word that the user enters has to fit
        and how many inputs the users has left
        """
        i = 0

        part_of_speech = random_template["blanks"][i]
        inputs_left = random_template["blanks"][len("blanks") - 1]

        madlibs_embed = Embed(
            title="Madlibs",
            color=Colours.python_blue,
        )
        madlibs_embed.add_field(
            name="Enter a word that fits the given part of speech!",
            value=f"Please enter a {part_of_speech}!"
        )
        madlibs_embed.set_footer(text=f"Inputs remaining: {inputs_left}")

        i += 1

        return madlibs_embed

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
        filtered_blanks = [min_length < len(random_template["blanks"]) < max_length]

        if not filtered_blanks:
            filter_not_found_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="Sorry, we could not generate a game for you because "
                + "you entered invalid numbers for the filters.",
                color=Colours.soft_red,
            )
            await ctx.send(embed=filter_not_found_embed)
            return

        # with madlibs_stories as file:
        #     file = loads(file)

            self.create_embed()

            try:
                await self.bot.wait_for(event='on_message', timeout=60.0)
            except TimeoutError:
                timeout_embed = Embed(title=choice(NEGATIVE_REPLIES),
                                      description='Looks like the bot timed out!')
                await ctx.send(embed=timeout_embed)
                return

            # word = message.content()


def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    bot.add_cog(Madlibs(bot))
