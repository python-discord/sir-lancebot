import json
from asyncio import TimeoutError
from pathlib import Path
from random import choice
from typing import TypedDict

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

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
        self.edited_content = {}

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

    @commands.Cog.listener()
    async def on_message_edit(self, _: discord.Message, after: discord.Message) -> None:
        """A listener that checks for edits to messages from the user."""
        self.edited_content[after.id] = after.content

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

        loading_embed = discord.Embed(
            title="Madlibs", description="Loading your Madlibs game...", color=Colours.python_blue
        )
        original_message = await ctx.send(embed=loading_embed)

        submitted_words = {}

        for i, part_of_speech in enumerate(random_template["blanks"]):
            inputs_left = len(random_template["blanks"]) - i

            madlibs_embed = self.madlibs_embed(part_of_speech, inputs_left)
            await original_message.edit(embed=madlibs_embed)

            try:
                message = await self.bot.wait_for(event="message", check=author_check, timeout=TIMEOUT)
            except TimeoutError:
                timeout_embed = discord.Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="Uh oh! You took too long to respond! Please try again later.",
                    color=Colours.soft_red
                )

                await ctx.send(embed=timeout_embed)
                return

            word = message.content

            submitted_words[message.id] = word

        blanks = []
        for msg_id in submitted_words:
            blanks.append(self.edited_content.pop(msg_id, submitted_words[msg_id]))

        story = []
        for value, blank in zip(random_template["value"], blanks):
            story.append(f"{value}__{blank}__")

        story.append(random_template["value"][-1])

        story_embed = discord.Embed(
            title=random_template["title"],
            description="".join(story),
            color=Colours.bright_green
        )

        story_embed.set_footer(text=f"Generated for {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=story_embed)


def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    bot.add_cog(Madlibs(bot))
