import asyncio
import random
import re
from collections import defaultdict
from io import BytesIO
from itertools import product
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from bot.bot import Bot
from bot.constants import MODERATION_ROLES
from bot.utils.decorators import with_role

DECK = list(product(*[(0, 1, 2)]*4))

GAME_DURATION = 180

# Scoring
CORRECT_SOLN = 1
INCORRECT_SOLN = -1
CORRECT_GOOSE = 2
INCORRECT_GOOSE = -1

# Distribution of minimum acceptable solutions at board generation.
# This is for gameplay reasons, to shift the number of solutions per board up,
# while still making the end of the game unpredictable.
# Note: this is *not* the same as the distribution of number of solutions.

SOLN_DISTR = 0, 0.05, 0.05, 0.1, 0.15, 0.25, 0.2, 0.15, .05

IMAGE_PATH = Path("bot", "resources", "fun", "all_cards.png")
FONT_PATH = Path("bot", "resources", "fun", "LuckiestGuy-Regular.ttf")
HELP_IMAGE_PATH = Path("bot", "resources", "fun", "ducks_help_ex.png")

ALL_CARDS = Image.open(IMAGE_PATH)
LABEL_FONT = ImageFont.truetype(str(FONT_PATH), size=16)
CARD_WIDTH = 155
CARD_HEIGHT = 97

EMOJI_WRONG = "\u274C"

ANSWER_REGEX = re.compile(r'^\D*(\d+)\D+(\d+)\D+(\d+)\D*$')

HELP_TEXT = """
**Each card has 4 features**
Color, Number, Hat, and Accessory

**A valid flight**
3 cards where each feature is either all the same or all different

**Call "GOOSE"**
if you think there are no more flights

**+1** for each valid flight
**+2** for a correct "GOOSE" call
**-1** for any wrong answer

The first flight below is invalid: the first card has swords while the other two have no accessory.\
 It would be valid if the first card was empty-handed, or one of the other two had paintbrushes.

The second flight is valid because there are no 2:1 splits; each feature is either all the same or all different.
"""


def assemble_board_image(board: list[tuple[int]], rows: int, columns: int) -> Image:
    """Cut and paste images representing the given cards into an image representing the board."""
    new_im = Image.new("RGBA", (CARD_WIDTH*columns, CARD_HEIGHT*rows))
    draw = ImageDraw.Draw(new_im)
    for idx, card in enumerate(board):
        card_image = get_card_image(card)
        row, col = divmod(idx, columns)
        top, left = row * CARD_HEIGHT, col * CARD_WIDTH
        new_im.paste(card_image, (left, top))
        draw.text(
            xy=(left+5, top+5),  # magic numbers are buffers for the card labels
            text=str(idx),
            fill=(0, 0, 0),
            font=LABEL_FONT,
        )
    return new_im


def get_card_image(card: tuple[int]) -> Image:
    """Slice the image containing all the cards to get just this card."""
    # The master card image file should have 9x9 cards,
    # arranged such that their features can be interpreted as ordered trinary.
    row, col = divmod(as_trinary(card), 9)
    x1 = col * CARD_WIDTH
    x2 = x1 + CARD_WIDTH
    y1 = row * CARD_HEIGHT
    y2 = y1 + CARD_HEIGHT
    return ALL_CARDS.crop((x1, y1, x2, y2))


def as_trinary(card: tuple[int]) -> int:
    """Find the card's unique index by interpreting its features as trinary."""
    return int(''.join(str(x) for x in card), base=3)


class DuckGame:
    """A class for a single game."""

    def __init__(
        self,
        rows: int = 4,
        columns: int = 3,
        minimum_solutions: int = 1,
    ):
        """
        Take samples from the deck to generate a board.

        Args:
            rows (int, optional): Rows in the game board. Defaults to 4.
            columns (int, optional): Columns in the game board. Defaults to 3.
            minimum_solutions (int, optional): Minimum acceptable number of solutions in the board. Defaults to 1.
        """
        self.rows = rows
        self.columns = columns
        size = rows * columns

        self._solutions = None
        self.claimed_answers = {}
        self.scores = defaultdict(int)
        self.editing_embed = asyncio.Lock()

        self.board = random.sample(DECK, size)
        while len(self.solutions) < minimum_solutions:
            self.board = random.sample(DECK, size)

        self.board_msg = None
        self.found_msg = None

    @property
    def board(self) -> list[tuple[int]]:
        """Accesses board property."""
        return self._board

    @board.setter
    def board(self, val: list[tuple[int]]) -> None:
        """Erases calculated solutions if the board changes."""
        self._solutions = None
        self._board = val

    @property
    def solutions(self) -> None:
        """Calculate valid solutions and cache to avoid redoing work."""
        if self._solutions is None:
            self._solutions = set()
            for idx_a, card_a in enumerate(self.board):
                for idx_b, card_b in enumerate(self.board[idx_a+1:], start=idx_a+1):
                    # Two points determine a line, and there are exactly 3 points per line in {0,1,2}^4.
                    # The completion of a line will only be a duplicate point if the other two points are the same,
                    # which is prevented by the triangle iteration.
                    completion = tuple(
                        feat_a if feat_a == feat_b else 3-feat_a-feat_b
                        for feat_a, feat_b in zip(card_a, card_b)
                    )
                    try:
                        idx_c = self.board.index(completion)
                    except ValueError:
                        continue

                    # Indices within the solution are sorted to detect duplicate solutions modulo order.
                    solution = tuple(sorted((idx_a, idx_b, idx_c)))
                    self._solutions.add(solution)

        return self._solutions


class DuckGamesDirector(commands.Cog):
    """A cog for running Duck Duck Duck Goose games."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.current_games = {}

    @commands.group(
        name='duckduckduckgoose',
        aliases=['dddg', 'ddg', 'duckduckgoose', 'duckgoose'],
        invoke_without_command=True
    )
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.channel)
    async def start_game(self, ctx: commands.Context) -> None:
        """Start a new Duck Duck Duck Goose game."""
        if ctx.channel.id in self.current_games:
            await ctx.send("There's already a game running!")
            return

        minimum_solutions, = random.choices(range(len(SOLN_DISTR)), weights=SOLN_DISTR)
        game = DuckGame(minimum_solutions=minimum_solutions)
        game.running = True
        self.current_games[ctx.channel.id] = game

        game.board_msg = await self.send_board_embed(ctx, game)
        game.found_msg = await self.send_found_embed(ctx)
        await asyncio.sleep(GAME_DURATION)

        # Checking for the channel ID in the currently running games is not sufficient.
        # The game could have been ended by a player, and a new game already started in the same channel.
        if game.running:
            try:
                del self.current_games[ctx.channel.id]
                await self.end_game(ctx.channel, game, end_message="Time's up!")
            except KeyError:
                pass

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        """Listen for messages and process them as answers if appropriate."""
        if msg.author.bot:
            return

        channel = msg.channel
        if channel.id not in self.current_games:
            return

        game = self.current_games[channel.id]
        if msg.content.strip().lower() == 'goose':
            # If all of the solutions have been claimed, i.e. the "goose" call is correct.
            if len(game.solutions) == len(game.claimed_answers):
                try:
                    del self.current_games[channel.id]
                    game.scores[msg.author] += CORRECT_GOOSE
                    await self.end_game(channel, game, end_message=f"{msg.author.display_name} GOOSED!")
                except KeyError:
                    pass
            else:
                await msg.add_reaction(EMOJI_WRONG)
                game.scores[msg.author] += INCORRECT_GOOSE
            return

        # Valid answers contain 3 numbers.
        if not (match := re.match(ANSWER_REGEX, msg.content)):
            return
        answer = tuple(sorted(int(m) for m in match.groups()))

        # Be forgiving for answers that use indices not on the board.
        if not all(0 <= n < len(game.board) for n in answer):
            return

        # Also be forgiving for answers that have already been claimed (and avoid penalizing for racing conditions).
        if answer in game.claimed_answers:
            return

        if answer in game.solutions:
            game.claimed_answers[answer] = msg.author
            game.scores[msg.author] += CORRECT_SOLN
            await self.append_to_found_embed(game, f"{str(answer):12s}  -  {msg.author.display_name}")
        else:
            await msg.add_reaction(EMOJI_WRONG)
            game.scores[msg.author] += INCORRECT_SOLN

    async def send_board_embed(self, ctx: commands.Context, game: DuckGame) -> discord.Message:
        """Create and send an embed to display the board."""
        image = assemble_board_image(game.board, game.rows, game.columns)
        with BytesIO() as image_stream:
            image.save(image_stream, format="png")
            image_stream.seek(0)
            file = discord.File(fp=image_stream, filename="board.png")
        embed = discord.Embed(
            title="Duck Duck Duck Goose!",
            color=discord.Color.dark_purple(),
        )
        embed.set_image(url="attachment://board.png")
        return await ctx.send(embed=embed, file=file)

    async def send_found_embed(self, ctx: commands.Context) -> discord.Message:
        """Create and send an embed to display claimed answers. This will be edited as the game goes on."""
        # Can't be part of the board embed because of discord.py limitations with editing an embed with an image.
        embed = discord.Embed(
            title="Flights Found",
            color=discord.Color.dark_purple(),
        )
        return await ctx.send(embed=embed)

    async def append_to_found_embed(self, game: DuckGame, text: str) -> None:
        """Append text to the claimed answers embed."""
        async with game.editing_embed:
            found_embed, = game.found_msg.embeds
            old_desc = found_embed.description or ""
            found_embed.description = f"{old_desc.rstrip()}\n{text}"
            await game.found_msg.edit(embed=found_embed)

    async def end_game(self, channel: discord.TextChannel, game: DuckGame, end_message: str) -> None:
        """Edit the game embed to reflect the end of the game and mark the game as not running."""
        game.running = False

        scoreboard_embed = discord.Embed(
            title=end_message,
            color=discord.Color.dark_purple(),
        )
        scores = sorted(
            game.scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        scoreboard = "Final scores:\n\n"
        scoreboard += "\n".join(f"{member.display_name}: {score}" for member, score in scores)
        scoreboard_embed.description = scoreboard
        await channel.send(embed=scoreboard_embed)

        missed = [ans for ans in game.solutions if ans not in game.claimed_answers]
        if missed:
            missed_text = "Flights everyone missed:\n" + "\n".join(f"{ans}" for ans in missed)
        else:
            missed_text = "All the flights were found!"
        await self.append_to_found_embed(game, f"\n{missed_text}")

    @start_game.command(name="help")
    async def show_rules(self, ctx: commands.Context) -> None:
        """Explain the rules of the game."""
        await self.send_help_embed(ctx)

    @start_game.command(name="stop")
    @with_role(*MODERATION_ROLES)
    async def stop_game(self, ctx: commands.Context) -> None:
        """Stop a currently running game. Only available to mods."""
        try:
            game = self.current_games.pop(ctx.channel.id)
        except KeyError:
            await ctx.send("No game currently running in this channel")
            return
        await self.end_game(ctx.channel, game, end_message="Game canceled.")

    @staticmethod
    async def send_help_embed(ctx: commands.Context) -> discord.Message:
        """Send rules embed."""
        embed = discord.Embed(
            title="Compete against other players to find valid flights!",
            color=discord.Color.dark_purple(),
        )
        embed.description = HELP_TEXT
        file = discord.File(HELP_IMAGE_PATH, filename="help.png")
        embed.set_image(url="attachment://help.png")
        embed.set_footer(
            text="Tip: using Discord's compact message display mode can help keep the board on the screen"
        )
        return await ctx.send(file=file, embed=embed)


async def setup(bot: Bot) -> None:
    """Load the DuckGamesDirector cog."""
    await bot.add_cog(DuckGamesDirector(bot))
