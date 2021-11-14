import json
from asyncio import TimeoutError
from pathlib import Path
from random import choice
from typing import TypedDict

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours

TIMEOUT = 60.0


class MadlibsTemplate(TypedDict):
    """Structure of a template in the madlibs JSON file."""

    title: str
    blanks: list[str]
    value: list[str]


class Madlibs(commands.Cog):
    """Cog for the Madlibs game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.templates = self._load_templates()

    @staticmethod
    def _load_templates() -> list[MadlibsTemplate]:
        madlibs_stories = Path("bot/resources/fun/madlibs_templates.json")

        with open(madlibs_stories) as file:
            return json.load(file)

    @staticmethod
    def madlibs_embed(part_of_speech: str, number_of_inputs: int) -> discord.Embed:
        """Method to have the bot send an embed with the game information."""
        madlibs_embed = discord.Embed(title="Madlibs", color=Colours.python_blue)

        madlibs_embed.add_field(
            name="Enter a word that fits the given part of speech!",
            value=f"Part of speech: {part_of_speech}"
        )

        madlibs_embed.set_footer(text=f"Inputs remaining: {number_of_inputs}")

        return madlibs_embed

    @commands.command()
    async def madlibs(self, ctx: commands.Context) -> None:
        """
        Play Madlibs with the bot!

        Madlibs is a game where the player is asked to enter a word that
        fits a random part of speech (e.g. noun, adjective, verb, plural noun, etc.)
        a random amount of times, depending on the story chosen by the bot at the beginning.
        """
        random_template = choice(self.templates)

        def author_check(message: discord.Message) -> bool:
            return message.channel.id == ctx.channel.id and message.author.id == ctx.author.id

        original_message = await ctx.send("Loading your Madlibs game...")

        submitted_words = []

        for i, part_of_speech in enumerate(random_template["blanks"]):
            inputs_left = len(random_template["blanks"]) - i

            madlibs_embed = self.madlibs_embed(part_of_speech, inputs_left)
            await original_message.edit(embed=madlibs_embed)

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
            submitted_words.append(f" __{word}__")

        story = []
        for value, blank in zip(random_template["value"], submitted_words):
            story.append(f"{value}{blank}")

        story.append(random_template["value"][-1])

        story_embed = discord.Embed(
            title=random_template["title"],
            description="".join(story),
            color=Colours.bright_green,
        )

        story_embed.set_footer(text=f"Generated for {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=story_embed)


def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    bot.add_cog(Madlibs(bot))
