from asyncio import TimeoutError
from pathlib import Path
from random import choice

from discord import Color, Embed
from discord.ext import commands

from bot.bot import Bot


class Hangman(commands.Cog):
    """
    Cog for the Hangman game.

    Hangman is a classic game where the user tries to guess a word, with a limited amount of tries.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        with Path("bot/resources/fun/top_1000_used_words.txt").resolve().open(mode="r", encoding="utf-8") as file:
            self.all_words = list(map(lambda line: line.strip('\n'), file.readlines()))

    @commands.command()
    async def hangman(self, ctx: commands.Context, min_length: str = '0', max_length: str = '25',
                      min_unique_letters: str = '0', max_unique_letters: str = '25') -> None:
        """
        Play against the bot, where you have to guess the word it has provided!

        You have 7 tries, and you have to guess the letters that are in the word, or you lose!
        """
        # filtering the list of all words depending on the configuration
        filtered_words = list(filter(lambda x: int(min_length) < len(x) < int(max_length)
                                     and int(min_unique_letters) < len(set(x)) < int(max_unique_letters),
                                     self.all_words))
        if not filtered_words:
            filter_not_found_embed = Embed(title="With the filters you provided, I could not find any words "
                                                 "that fit all the filters specified..", color=Color.red())
            await ctx.send(embed=filter_not_found_embed)
            return

        # defining a list of images that will be used for the game to represent the hangman person
        images = ['https://cdn.discordapp.com/attachments/859123972884922418/883472355056295946/hangman0.png',
                  'https://cdn.discordapp.com/attachments/859123972884922418/883472756744814613/hangman1.png',
                  'https://cdn.discordapp.com/attachments/859123972884922418/883472808699629578/hangman2.png',
                  'https://cdn.discordapp.com/attachments/859123972884922418/883472862441267230/hangman3.png',
                  'https://cdn.discordapp.com/attachments/859123972884922418/883472950991396864/hangman4.png',
                  'https://cdn.discordapp.com/attachments/859123972884922418/883472999431430204/hangman5.png',
                  'https://cdn.discordapp.com/attachments/859123972884922418/883473051277226015/hangman6.png']

        # a dictionary mapping the images of the 'hung man' to the number of tries it corresponds to
        mapping_of_images = {tries_key: image_name for image_name, tries_key in zip(images, range(6, -1, -1))}

        word = choice(filtered_words)
        user_guess = '_' * len(word)
        tries = 6
        hangman_embed = Embed(title="Hangman", color=Color.blurple())
        hangman_embed.set_image(url=mapping_of_images[tries])
        hangman_embed.add_field(name=f"The word is `{user_guess}`", value="Guess the word by sending a "
                                                                          "message with the letter!", inline=False)
        original_message = await ctx.send(embed=hangman_embed)

        while user_guess != word:
            try:
                message = await self.bot.wait_for(event="message", timeout=30.0,
                                                  check=lambda msg: msg.author != self.bot)

                if len(message.content) > 1:
                    continue

                elif message.content in word:
                    positions = [idx for idx, letter in enumerate(word) if letter == message.content]
                    user_guess = ''.join([message.content if index in positions else dash
                                          for index, dash in enumerate(user_guess)])

                elif tries - 1 <= 0:
                    losing_embed = Embed(title="You lost.", description=f"The word was `{word}`.", color=Color.red())
                    await original_message.edit(embed=losing_embed)
                    return

                else:
                    tries -= 1

                hangman_embed.clear_fields()
                hangman_embed.set_image(url=mapping_of_images[tries])
                hangman_embed.add_field(name=f"The word is `{user_guess}`", value="Guess the word by sending a "
                                                                                  "message with the letter!",
                                        inline=False)
                await original_message.edit(embed=hangman_embed)
            except TimeoutError:
                return
        else:
            win_embed = Embed(title="You won!", color=Color.green())
            await ctx.send(embed=win_embed)


def setup(bot: Bot) -> None:
    """Setting up the Hangman cog."""
    bot.add_cog(Hangman(bot))
