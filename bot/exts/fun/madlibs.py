import json
from asyncio import TimeoutError
from pathlib import Path
from random import choice
from typing import TypedDict

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

# import json
# from typing import Literal
# from typing import List

TIMEOUT = 60.0


class MadlibsTemplate(TypedDict):
    title: str
    blanks: list[str]
    value: list[str]


class Madlibs(commands.Cog):
    """
    Cog for the Madlibs game.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.templates = self._load_templates()

    @staticmethod
    def _load_templates() -> list[MadlibsTemplate]:
        madlibs_stories = Path("bot/resources/fun/madlibs_templates (1).json")

        with open(madlibs_stories) as file:
            return json.load(file)["templates"]

    @staticmethod
    def madlibs_embed(part_of_speech: str, number_of_inputs: int) -> discord.Embed:
        """Method to have the bot send an embed with the game information."""
        madlibs_embed = discord.Embed(
            title="Madlibs",
            color=Colours.python_blue,
        )

        madlibs_embed.add_field(
            name="Enter a word that fits the given part of speech!",
            value=f"Part of speech: {part_of_speech}"
        )

        madlibs_embed.set_footer(text=f"Inputs remaining: {number_of_inputs}")

        return madlibs_embed

    @commands.command()
    async def madlibs(
        self,
        ctx: commands.Context,
    ) -> None:
        """Play Madlibs with the bot!

        Madlibs is a game where the player is asked to enter a word that
        fits a random part of speech (e.g. noun, adjective, verb, plural noun, etc.).
        The bot chooses a random number of user inputs (within the specified bounds
        of the command arguments) to use for the game and a random story.
        """
        random_template = choice(self.templates)

        def author_check(message: discord.Message):
            return message.channel.id == ctx.channel.id and message.author.id == ctx.author.id

        # Send the first necessary embed, because we do this outside of the
        # loop we need to skip the first item in the actual loop.
        madlibs_embed = self.madlibs_embed(random_template["blanks"][0], len(random_template["blanks"]))
        original_message = await ctx.send(embed=madlibs_embed)

        for i, part_of_speech in enumerate(random_template["blanks"][1:], start=1):
            inputs_left = len(random_template["blanks"]) - i

            try:
                message = await self.bot.wait_for(event="message", check=author_check, timeout=TIMEOUT)
            except TimeoutError:
                timeout_embed = discord.Embed(
                    title="Timeout!",
                    description="Uh oh! Looks like the bot timed out! Please try again later.",
                    color=Colours.soft_red
                )

                await ctx.send(embed=timeout_embed)
                return

            word = message.content
            submitted_words = []
            submitted_words += word

            # str_template = ' '.join(random_template["value"])
            # for word, blank in zip(submitted_words, random_template["value"]):
            #     word_in_story = blank.replace("", word)

            # random_template["value"] += submitted_words

            madlibs_embed = self.madlibs_embed(part_of_speech, inputs_left)
            await original_message.edit(embed=madlibs_embed)

        str_template = " ".join(random_template["value"])
        str_template_with_words = str_template.join(submitted_words)

        story_embed = discord.Embed(
            title=random_template["title"],
            description=str_template_with_words,
            color=Colours.bright_green,
        )

        await ctx.send(embed=story_embed)


def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    bot.add_cog(Madlibs(bot))
