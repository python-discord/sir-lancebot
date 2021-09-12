from asyncio import TimeoutError
from pathlib import Path
from random import choice
from typing import Literal

from discord import Embed, Message
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

# defining all words in the list of words as a global variable
with Path("bot/resources/fun/hangman_words.txt").resolve().open(mode="r", encoding="utf-8") as f:
    ALL_WORDS = [line.strip('\n') for line in f.readlines()]

# defining a list of images that will be used for the game to represent the hangman person
IMAGES = {
    6: "https://cdn.discordapp.com/attachments/859123972884922418/883472355056295946/hangman0.png",
    5: "https://cdn.discordapp.com/attachments/859123972884922418/883472756744814613/hangman1.png",
    4: "https://cdn.discordapp.com/attachments/859123972884922418/883472808699629578/hangman2.png",
    3: "https://cdn.discordapp.com/attachments/859123972884922418/883472862441267230/hangman3.png",
    2: "https://cdn.discordapp.com/attachments/859123972884922418/883472950991396864/hangman4.png",
    1: "https://cdn.discordapp.com/attachments/859123972884922418/883472999431430204/hangman5.png",
    0: "https://cdn.discordapp.com/attachments/859123972884922418/883473051277226015/hangman6.png",
}


class Hangman(commands.Cog):
    """
    Cog for the Hangman game.

    Hangman is a classic game where the user tries to guess a word, with a limited amount of tries.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def hangman(
            self,
            ctx: commands.Context,
            min_length: int = 0,
            max_length: int = 25,
            min_unique_letters: int = 0,
            max_unique_letters: int = 25,
            singleplayer: Literal["s", "m"] = "s",
    ) -> None:
        """
        Play hangman against the bot, where you have to guess the word it has provided!

        The arguments for this command mean:
        - min_length: the minimum length you want the word to be (i.e. 2)
        - max_length: the maximum length you want the word to be (i.e. 5)
        - min_unique_letters: the minimum unique letters you want the word to have (i.e. 4)
        - max_unique_letters: the maximum unique letters you want the word to have (i.e. 7)
        - singleplayer: writing 's' means you want to play by yourself, and only you can suggest letters,
            - writing 'm' means you want multiple players to join in and guess the word.
        """
        # filtering the list of all words depending on the configuration
        filtered_words = [
            word for word in ALL_WORDS
            if min_length < len(word) < max_length
            and min_unique_letters < len(set(word)) < max_unique_letters
        ]

        if not filtered_words:
            filter_not_found_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="No words could be found that fit all the filters specified.",
                color=Colours.soft_red,
            )
            await ctx.send(embed=filter_not_found_embed)
            return

        word = choice(filtered_words)

        user_guess = "_" * len(word)
        tries = 6

        # check if the game is singleplayer or multiplayer
        def check(msg: Message) -> bool:
            if singleplayer == 's':
                return msg.author == ctx.author
            elif singleplayer == 'm':
                return msg.author != self.bot
            else:
                raise commands.BadArgument("`singleplayer` must be either `s` or `m`")

        hangman_embed = Embed(
            title="Hangman",
            color=Colours.python_blue,
        )
        hangman_embed.set_image(url=IMAGES[tries])
        hangman_embed.add_field(
            name=f"You've guessed `{user_guess}` so far.",
            value="Guess the word by sending a message with the letter!",
            inline=False,
        )
        hangman_embed.set_footer(text=f"Tries: {tries}")
        original_message = await ctx.send(embed=hangman_embed)

        while user_guess != word:
            try:
                message = await self.bot.wait_for(
                    event="message",
                    timeout=30.0,
                    check=check
                )
            except TimeoutError:
                timeout_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="Looks like the bot timed out! You must send a letter within 60 seconds.",
                    color=Colours.soft_red,
                )
                await original_message.edit(embed=timeout_embed)
                return

            message.content = message.content.lower()
            if len(message.content) > 1:
                letter_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="You can only send a letter for the hangman game!",
                    color=Colours.soft_red,
                )
                await original_message.edit(embed=letter_embed)
                continue

            elif message.content in word:
                positions = {idx for idx, letter in enumerate(word) if letter == message.content}
                user_guess = "".join(
                    [message.content if index in positions else dash for index, dash in enumerate(user_guess)]
                )

            else:
                tries -= 1

                if tries <= 0:
                    losing_embed = Embed(
                        title="You lost.",
                        description=f"The word was `{word}`.",
                        color=Colours.soft_red,
                    )
                    await original_message.edit(embed=losing_embed)
                    return

            hangman_embed.clear_fields()
            hangman_embed.set_image(url=IMAGES[tries])
            hangman_embed.add_field(
                name=f"You've guessed `{user_guess}` so far.",
                value="Guess the word by sending a message with the letter!",
                inline=False,
            )
            hangman_embed.set_footer(text=f"Tries: {tries}")
            await original_message.edit(embed=hangman_embed)

        win_embed = Embed(
            title="You won!",
            color=Colours.grass_green,
        )
        await ctx.send(embed=win_embed)


def setup(bot: Bot) -> None:
    """Load the Hangman cog."""
    bot.add_cog(Hangman(bot))
