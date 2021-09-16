from asyncio import TimeoutError
from random import choice
from typing import Literal

from discord import Embed, Message
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

# Defining all words in the list of words as a global variable
with open("bot/resources/fun/hangman_words.txt", encoding="utf-8") as f:
    ALL_WORDS = [line.strip('\n') for line in f.readlines()]

# Defining a list of images that will be used for the game to represent the hangman person
IMAGES = {
    6: "https://cdn.discordapp.com/attachments/859123972884922418/888133201497837598/hangman0.png",
    5: "https://cdn.discordapp.com/attachments/859123972884922418/888133595259084800/hangman1.png",
    4: "https://cdn.discordapp.com/attachments/859123972884922418/888134194474139688/hangman2.png",
    3: "https://cdn.discordapp.com/attachments/859123972884922418/888133758069395466/hangman3.png",
    2: "https://cdn.discordapp.com/attachments/859123972884922418/888133786724859924/hangman4.png",
    1: "https://cdn.discordapp.com/attachments/859123972884922418/888133828831477791/hangman5.png",
    0: "https://cdn.discordapp.com/attachments/859123972884922418/888133845449338910/hangman6.png",
}


class Hangman(commands.Cog):
    """
    Cog for the Hangman game.

    Hangman is a classic game where the user tries to guess a word, with a limited amount of tries.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def create_embed(tries: int, user_guess: str) -> Embed:
        """
        Helper method that creates the embed where the game information is shown.

        This includes how many letters the user has guessed so far, and the hangman photo itself.
        """
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
        return hangman_embed

    @commands.command()
    async def hangman(
            self,
            ctx: commands.Context,
            min_length: int = 0,
            max_length: int = 25,
            min_unique_letters: int = 0,
            max_unique_letters: int = 25,
            singleplayer: Literal["s", "m", "S", "M"] = "s",
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
        # Changing singleplayer to a boolean
        singleplayer = True if singleplayer.lower() == 's' else False

        # Filtering the list of all words depending on the configuration
        filtered_words = [
            word for word in ALL_WORDS
            if min_length < len(word) < max_length
            and min_unique_letters < len(set(word)) < max_unique_letters
        ]

        if not filtered_words:
            filter_not_found_embed = Embed(
                title=choice(NEGATIVE_REPLIES),
                description="No words could be found that fit all filters specified.",
                color=Colours.soft_red,
            )
            await ctx.send(embed=filter_not_found_embed)
            return

        word = choice(filtered_words)
        # `pretty_word` is used for comparing the indices where the guess of the user is similar to the word
        # The `user_guess` variable is prettified by adding spaces between every dash, and so is the `pretty_word`
        pretty_word = ''.join([f"{letter} " for letter in word])[:-1]
        user_guess = ("_ " * len(word))[:-1]
        tries = 6
        guessed_letters = set()

        # Checking if the game is singleplayer
        def check(msg: Message) -> bool:
            if singleplayer:
                return msg.author == ctx.author
            else:
                # Multiplayer mode
                return msg.author != self.bot

        original_message = await ctx.send(embed=Embed(
            title="Hangman",
            description="Loading game...",
            color=Colours.soft_green
        ))

        # Game loop
        while user_guess.replace(' ', '') != word:
            # Start of the game
            await original_message.edit(embed=self.create_embed(tries, user_guess))

            # Sends a message if the user does not send a message within 60 seconds
            try:
                message = await self.bot.wait_for(
                    event="message",
                    timeout=60.0,
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

            # Automatically convert uppercase to lowercase letters
            message.content = message.content.lower()

            # Sends a message if the user enters more than one letter per guess
            if len(message.content) > 1:
                letter_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="You can only send one letter at a time, try again!",
                    color=Colours.dark_green,
                )
                to_delete = await ctx.send(embed=letter_embed)
                await to_delete.delete(delay=4)
                continue

            # Check for repeated guesses
            elif message.content in guessed_letters:
                already_guessed_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description=f"You have already guessed `{message.content}`, try again!",
                    color=Colours.dark_green,
                )
                to_delete = await ctx.send(embed=already_guessed_embed)
                await to_delete.delete(delay=4)
                continue

            # Check for the correct guess from the user
            elif message.content in word:
                positions = {idx for idx, letter in enumerate(pretty_word) if letter == message.content}
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
                    await original_message.edit(embed=self.create_embed(tries, user_guess))
                    await ctx.send(embed=losing_embed)
                    return

            guessed_letters.add(message.content)

        # Send the message saying that you won and update the game board
        await original_message.edit(embed=self.create_embed(tries, user_guess))
        win_embed = Embed(
            title="You won!",
            description=f"The word was `{word}`.",
            color=Colours.grass_green
        )
        await ctx.send(embed=win_embed)


def setup(bot: Bot) -> None:
    """Load the Hangman cog."""
    bot.add_cog(Hangman(bot))
