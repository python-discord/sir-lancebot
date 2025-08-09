import json
import asyncio
import discord

from pathlib import Path
from random import choice
from typing import TypedDict
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

TIMEOUT = 120


class MadlibsTemplate(TypedDict):
    """Structure of a template in the madlibs_templates JSON file."""

    title: str
    blanks: list[str]
    value: list[str]


class Madlibs(commands.Cog):
    """Cog for the Madlibs game."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.templates = self._load_templates()
        self.edited_content = {}
        self.submitted_words = {}
        self.view = None
        self.wait_task: asyncio.Task | None = None
        self.end_game = False
        self.checks = set()

    @staticmethod
    def _load_templates() -> list[MadlibsTemplate]:
        madlibs_stories = Path("bot/resources/fun/madlibs_templates.json")

        with open(madlibs_stories) as file:
            return json.load(file)

    @staticmethod
    def madlibs_embed(part_of_speech: str, number_of_inputs: int) -> discord.Embed:
        """Method to generate an embed with the game information."""
        madlibs_embed = discord.Embed(title="Madlibs", color=Colours.python_blue)

        madlibs_embed.add_field(
            name="Enter a word that fits the given part of speech!",
            value=f"Part of speech: {part_of_speech}\n\nMake sure not to spam, or you may get auto-muted!"
        )

        madlibs_embed.set_footer(text=f"Inputs remaining: {number_of_inputs}")

        return madlibs_embed

    @commands.Cog.listener()
    async def on_message_edit(self, _: discord.Message, after: discord.Message) -> None:
        """A listener that checks for message edits from the user."""
        for check in self.checks:
            if check(after):
                break
        else:
            return

        self.edited_content[after.id] = after.content

    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def madlibs(self, ctx: commands.Context) -> None:
        """
        Play Madlibs with the bot!

        Madlibs is a game where the player is asked to enter a word that
        fits a random part of speech (e.g. noun, adjective, verb, plural noun, etc.)
        a random amount of times, depending on the story chosen by the bot at the beginning.
        """
        random_template = choice(self.templates)

        self.end_game = False

        def author_check(message: discord.Message) -> bool:
            if message.channel.id != ctx.channel.id or message.author.id != ctx.author.id:
                return False

            # Ignore commands while a game is running
            prefix = ctx.prefix or ""
            if prefix and message.content.startswith(prefix):
                return False

            return True

        self.checks.add(author_check)

        loading_embed = discord.Embed(
            title="Madlibs", description="Loading your Madlibs game...", color=Colours.python_blue
        )
        original_message = await ctx.send(embed=loading_embed)

        for i, part_of_speech in enumerate(random_template["blanks"]):
            inputs_left = len(random_template["blanks"]) - i

            self.view = MadlibsView(ctx, self, part_of_speech, i)

            madlibs_embed = self.madlibs_embed(part_of_speech, inputs_left)
            await original_message.edit(embed=madlibs_embed, view=self.view)

            self.wait_task = asyncio.create_task(
                self.bot.wait_for("message", timeout=TIMEOUT, check=author_check)
            )
            try:
                message = await self.wait_task
                self.submitted_words[i] = message.content
            except asyncio.CancelledError:
                if self.end_game:
                    if self.view:
                        # clean up and exit early
                        self.view.stop()

                        for child in view.children:
                            if isinstance(child, discord.ui.Button):
                                child.disabled = True

                        await original_message.edit(view=self.view)
                        self.checks.remove(author_check)

                        return
                # else: "Choose for me" set self.submitted_words[i]; just continue
            except asyncio.TimeoutError:
                if self.end_game:
                    # If we ended the game around the same time, don't show timeout
                    self.checks.remove(author_check)
                    return

                timeout_embed = discord.Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="Uh oh! You took too long to respond!",
                    color=Colours.soft_red
                )

                await ctx.send(ctx.author.mention, embed=timeout_embed)

                self.view.stop()
                for child in view.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True

                await original_message.edit(view=self.view)

                for j in self.submitted_words:
                    self.edited_content.pop(j, self.submitted_words[j])

                self.checks.remove(author_check)

                return
            finally:
                # Clean up so the next iteration doesn't see an old task
                self.wait_task = None

        blanks = [self.submitted_words[j] for j in range(len(random_template["blanks"]))]

        self.checks.remove(author_check)

        story = []
        for value, blank in zip(random_template["value"], blanks, strict=False):
            story.append(f"{value}__{blank}__")

        # In each story template, there is always one more "value"
        # (fragment from the story) than there are blanks (words that the player enters)
        # so we need to compensate by appending the last line of the story again.
        story.append(random_template["value"][-1])

        story_embed = discord.Embed(
            title=random_template["title"],
            description="".join(story),
            color=Colours.bright_green
        )

        story_embed.set_footer(text=f"Generated for {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=story_embed)

        if self.wait_task and not self.wait_task.done():
            self.wait_task.cancel()

        for child in self.view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        await original_message.edit(view=self.view)

    @madlibs.error
    async def handle_madlibs_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Error handler for the Madlibs command."""
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send("You are already playing Madlibs!")
            error.handled = True


class MadlibsView(discord.ui.View):

    def __init__(self, ctx: commands.Context, cog: "Madlibs", part_of_speech: str, index: int):
        super().__init__(timeout=120)
        self.disabled = None
        self.ctx = ctx
        self.cog = cog
        self.word_bank = self._load_word_bank()
        self.part_of_speech = part_of_speech
        self.index = index

    @staticmethod
    def _load_word_bank() -> dict[str, list[str]]:
        word_bank = Path("bot/resources/fun/madlibs_word_bank.json")

        with open(word_bank) as file:
            return json.load(file)

    @discord.ui.button(style=discord.ButtonStyle.green, label="Choose for me")
    async def random_word_button(self, interaction: discord.Interaction, *_) -> None:
        """Button that randomly chooses a word for the user if they cannot think of a word."""
        if interaction.user == self.ctx.author:
            random_word = choice(self.word_bank[self.part_of_speech])
            self.cog.submitted_words[self.index] = random_word

            wait_task = getattr(self.cog, "wait_task", None)
            if wait_task and not wait_task.done():
                wait_task.cancel()

            await interaction.response.send_message(f"Randomly chosen word: {random_word}", ephemeral=True)
        else:
            await interaction.response.send_message("Only the owner of the game can end it!", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.red, label="End Game")
    async def end_button(self, interaction: discord.Interaction, *_) -> None:
        """Button that ends the current game."""
        if interaction.user == self.ctx.author:
            # Cancel the wait task if it's running
            self.cog.end_game = True
            wait_task = getattr(self.cog, "wait_task", None)
            if wait_task and not wait_task.done():
                wait_task.cancel()

            # Disable all buttons in the view
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True

            await interaction.response.send_message("Ended the current game.", ephemeral=True)
            await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
        else:
            await interaction.response.send_message("Only the owner of the game can end it!", ephemeral=True)


async def setup(bot: Bot) -> None:
    """Load the Madlibs cog."""
    await bot.add_cog(Madlibs(bot))
