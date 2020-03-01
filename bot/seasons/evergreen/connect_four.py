import asyncio
import random
import typing
from functools import partial

import discord
from discord.ext import commands

EMOJIS = [":white_circle:", ":blue_circle:", ":red_circle:"]

NUMBERS = (
    ":one:"
    ":two:"
    ":three:"
    ":four:"
    ":five:"
    ":six:"
    ":seven:"
)

UNICODE_NUMBERS = [
    "\u0031\u20e3", "\u0032\u20e3",
    "\u0033\u20e3", "\u0034\u20e3",
    "\u0035\u20e3", "\u0036\u20e3",
    "\u0037\u20e3"
]

HAND_RAISED_EMOJI = "\U0001f64b"

Coordinate = typing.Tuple[int, int]


class Game():
    """A Connect 4 Game."""

    def __init__(
        self,
        bot: commands.Bot,
        channel: discord.TextChannel,
        player1: discord.Member,
        player2: typing.Optional[discord.abc.User] = None
    ) -> None:

        self.bot = bot
        self.channel = channel
        self.player1 = player1
        self.player2 = player2 or AI(self)

        self.grid = [[0 for _ in range(7)] for _ in range(7)]

        self.message = None

        self.turn = None
        self.next = None

    async def print_grid(self) -> None:
        """Formats and outputs the Connect Four grid to the channel."""
        rows = ["".join(EMOJIS[s] for s in row) for row in self.grid]
        formatted_grid = "\n".join([NUMBERS] + rows)

        if self.message:
            await self.message.edit(content=formatted_grid)
        else:
            self.message = await self.channel.send(formatted_grid)
            for emoji in UNICODE_NUMBERS:
                await self.message.add_reaction(emoji)

    async def start_game(self) -> None:
        """Begins the game."""
        self.turn = self.player1
        self.next = self.player2

        while True:
            await self.print_grid()
            if isinstance(self.turn, AI):
                coords = self.turn.play()
            else:
                coords = await self.player_turn()

            if not coords:
                return

            if self.check_win(coords, 1 if self.turn == self.player1 else 2):
                if isinstance(self.turn, AI):
                    await self.channel.send("YOU LOSE!")
                else:
                    await self.channel.send(f"{self.turn.mention}, YOU WIN!")
                await self.print_grid()
                return

            self.turn, self.next = self.next, self.turn
        await self.print_grid()

    def predicate(self, reaction: discord.Reaction, user: discord.Member) -> bool:
        """The predicate to check for the player's reaction."""
        return (
            reaction.message.id == self.message.id
            and user.id == self.turn.id
            and str(reaction.emoji) in UNICODE_NUMBERS
        )

    async def player_turn(self) -> Coordinate:
        """Initiate the player's turn."""
        message = await self.channel.send(
            f"{self.turn.mention}, it's your turn! React with a column you want to place your token"
        )
        player_num = 1 if self.turn == self.player1 else 2
        while True:
            fullcolumn = False
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=self.predicate, timeout=30.0)
            except asyncio.TimeoutError:
                await self.channel.send(f"{self.turn.mention}, you took too long. Game over!")
                return
            else:
                await message.delete()
                await self.message.remove_reaction(reaction, user)
                column_num = UNICODE_NUMBERS.index(str(reaction.emoji))

                column = [row[column_num] for row in self.grid]

                for row_num, square in reversed(list(enumerate(column))):
                    if not square:
                        self.grid[row_num][column_num] = player_num
                        coords = row_num, column_num
                        break
                else:
                    await self.channel.send(f"Column {column_num+1} is full. Try again")
                    fullcolumn = True
            if not fullcolumn:
                break

        return coords

    def check_win(self, coords: Coordinate, player_num: int) -> bool:
        """Check that placing a counter here would cause the player to win."""
        vertical = [(-1, 0), (1, 0)]
        horizontal = [(0, 1), (0, -1)]
        forward_diag = [(-1, 1), (1, -1)]
        backward_diag = [(-1, -1), (1, 1)]
        axes = [vertical, horizontal, forward_diag, backward_diag]

        for axis in axes:
            in_a_row = 1  # The initial counter that is compared to
            for increment in axis:
                row, column = coords
                row_incr, column_incr = increment
                row += row_incr
                column += column_incr

                while 0 <= row < 7 and 0 <= column < 7:
                    if self.grid[row][column] == player_num:
                        in_a_row += 1
                        row += row_incr
                        column += column_incr
                    else:
                        break
            if in_a_row >= 4:
                return True
        return False


class AI():
    """The Computer Player for Single-Player games."""

    def __init__(
        self,
        game: Game
    ) -> None:
        self.game = game

    def get_possible_places(self) -> typing.List[Coordinate]:
        """Gets all the coordinates where the AI could possibly place a counter."""
        possible_coords = []
        for column_num in range(7):
            column = [row[column_num] for row in self.game.grid]
            for row_num, square in reversed(list(enumerate(column))):
                if not square:
                    possible_coords.append((row_num, column_num))
                    break
        return possible_coords

    def check_ai_win(self, coord_list: typing.List[Coordinate]) -> typing.Optional[Coordinate]:
        """Check if placing a counter in any possible coordinate would cause the AI to win."""
        if random.randint(1, 10) == 1:  # 10% chance of not winning
            return
        for coords in coord_list:
            if self.game.check_win(coords, 2):
                return coords

    def check_player_win(self, coord_list: typing.List[Coordinate]) -> typing.Optional[Coordinate]:
        """Check if placing a counter in any possible coordinate would stop the player from winning."""
        if random.randint(1, 4) == 1:  # 25% chance of not blocking the player
            return
        for coords in coord_list:
            if self.game.check_win(coords, 1):
                return coords

    def random_coords(self, coord_list: typing.List[Coordinate]) -> Coordinate:
        """Picks a random coordinate from the possible ones."""
        return random.choice(coord_list)

    def play(self) -> Coordinate:
        """The AI's turn."""
        possible_coords = self.get_possible_places()

        coords = self.check_ai_win(possible_coords)  # Win
        if not coords:
            coords = self.check_player_win(possible_coords)  # Try to stop P1 from winning
        if not coords:
            coords = self.random_coords(possible_coords)

        row, column = coords
        self.game.grid[row][column] = 2
        return coords


class ConnectFour(commands.Cog):
    """Connect Four. The Classic Vertical Four-in-a-row Game!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.games = []
        self.waiting = []

    def predicate(
        self,
        ctx: commands.Context,
        announcement: discord.Message,
        reaction: discord.Reaction,
        user: discord.Member
    ) -> bool:
        """Predicate checking the criteria for the announcement message."""
        return (
            user.id not in (ctx.me.id, ctx.author.id)
            and reaction.message.id == announcement.id
            and str(reaction.emoji) == HAND_RAISED_EMOJI
        )

    @commands.group(invoke_without_command=True, aliases=[
        "4inarow", "4-in-a-row", "4_in_a_row", "connect4", "connect-four", "connect_four"
    ])
    async def connectfour(self, ctx: commands.Context) -> None:
        """
        Play the classic game of Connect Four with someone!

        Sets up a message waiting for someone else to react and play along.
        The game will start once someone has reacted.
        All inputs will be through reactions.
        """
        if ctx.channel in (game.channel for game in self.games):
            return await ctx.send("There's already a game going on in this channel!")

        if ctx.channel in self.waiting:
            return await ctx.send("There's already a pending request in this channel - Maybe join them?")

        announcement = await ctx.send(
            "**Connect Four**: A new game is about to start!\n"
            f"Press :raising_hand: to play against {ctx.author.mention}!"
        )
        self.waiting.append(ctx.channel)
        await announcement.add_reaction(HAND_RAISED_EMOJI)

        try:
            _reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=partial(self.predicate, ctx, announcement),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            self.waiting.remove(ctx.channel)
            await announcement.delete()
            return await ctx.send(
                f"{ctx.author.mention} There's no one here to play. "
                f"Use `{ctx.prefix}{ctx.invoked_with} ai` to play against a computer."
            )
        self.waiting.remove(ctx.channel)
        await announcement.delete()
        try:
            game = Game(self.bot, ctx.channel, ctx.author, user)
            self.games.append(game)
            await game.start_game()
            self.games.remove(game)
        except Exception:
            # End the game in the event of an unforseen error so the channel isn't stuck in a game
            await ctx.send(f"{ctx.author.mention} {user.mention} An unforseen error occurred.")
            self.games.remove(game)
            raise

    @connectfour.command(aliases=["AI", "CPU", "computer", "cpu", "Computer"])
    async def ai(self, ctx: commands.Context) -> None:
        """Play Connect Four against a computer player."""
        if ctx.channel in (game.channel for game in self.games):
            return await ctx.send("There's already a game going on in this channel!")

        if ctx.channel in self.waiting:
            return await ctx.send("There's already a pending request in this channel.")

        try:
            game = Game(self.bot, ctx.channel, ctx.author)
            self.games.append(game)
            await game.start_game()
            self.games.remove(game)
        except Exception:
            # End the game in the event of an unforseen error so the channel isn't stuck in a game
            await ctx.send(f"{ctx.author.mention} An unforseen error occurred.")
            self.games.remove(game)
            raise


def setup(bot: commands.Bot) -> None:
    """Cog load."""
    bot.add_cog(ConnectFour(bot))
