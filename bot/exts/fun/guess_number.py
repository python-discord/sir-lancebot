import random

from discord import Message
from discord.ext import commands

from bot.bot import Bot


class Difficulty(commands.Converter):
    """Class used to convert the `difficulty` parameter."""

    EASY = ("e", "eas", "easy")
    MEDIUM = ("m", "med", ",medium")
    HARD = ("h", "hard")

    async def convert(self, ctx: commands.Context, diff: str) -> str:
        """Converts the provided `difficulty` into the corresponding string."""
        if diff.lower() in self.EASY:
            return "easy"

        if diff.lower() in self.MEDIUM:
            return "medium"

        if diff.lower() in self.HARD:
            return "hard"

        raise commands.BadArgument(f"{diff!r} is not a valid difficulty.")


class GuessNumber(commands.Cog):
    """Cog for the GuessNumber command."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_games = {}

    @commands.command(name="guessnumber", aliases=("gn", "numbergame"))
    async def guess_number(self, ctx: commands.Context, difficulty: Difficulty = "medium") -> None:
        """Starts a new game of guessing the number with default difficulty set to medium."""
        # Duplicate game check
        if ctx.author.id in self.active_games:
            await ctx.send("You already have an active game. Finish that one before starting a new one.")
            return

        if difficulty == "easy":
            secret_number = random.randint(1, 50)
            await ctx.send("I am thinking of a number between 1 and 50. Try to guess!")
        elif difficulty == "medium":
            secret_number = random.randint(1, 100)
            await ctx.send("I am thinking of a number between 1 and 100. Try to guess!")
        elif difficulty == "hard":
            secret_number = random.randint(1, 200)
            await ctx.send("I am thinking of a number between 1 and 200. Try to guess!")
        else:
            await ctx.send("Invalid difficulty mode.")

        self.active_games[ctx.author.id] = secret_number

        def check(msg: Message) -> bool:
            return msg.author == ctx.author and msg.channel == ctx.channel

        tries = 5
        while tries > 0:
            try:
                user_guess = await self.bot.wait_for(
                    "message",
                    timeout=30.0,
                    check=check
                )
            except TimeoutError:
                self.active_games.pop(ctx.author.id)
                await ctx.send("Timeout!")
                return

            if not user_guess.content.isdigit():
                await ctx.send(f"**Invalid guess**, Please guess a number. Try again, You've {tries} left.")

            elif int(user_guess.content) == self.active_games[ctx.author.id]:
                await ctx.channel.send(
                    f"Congratulations {ctx.author}! You guessed the correct number.")
                self.active_games.pop(ctx.author.id)
                return
            # when 0 tries left for the user
            else:
                tries = tries - 1
                if tries == 0:
                    await ctx.channel.send(
                        f"Incorrect, You lost. I was thinking of number {self.active_games[ctx.author.id]}")
                    self.active_games.pop(ctx.author.id)
                    return

                if int(user_guess.content) < self.active_games[ctx.author.id]:
                    low_high = "lower"
                else:
                    low_high = "higher"
                await ctx.channel.send(f"Incorrect! Number guessed is {low_high} than what I'm thinking. "
                                       f"You have {tries} tries left.")


async def setup(bot: Bot) -> None:
    """Loads the  cog."""
    await bot.add_cog(GuessNumber(bot))
