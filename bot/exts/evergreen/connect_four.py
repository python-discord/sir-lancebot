import asyncio
import random
import typing
from functools import partial

import discord
from discord.ext import commands

EMOJIS = [":white_circle:", ":blue_circle:", ":red_circle:"]
NUMBERS = [
    ":one:",
    ":two:",
    ":three:",
    ":four:",
    ":five:",
    ":six:",
    ":seven:",
    ":eight:",
    ":nine:"
]
UNICODE_NUMBERS = [
    "\u0031\u20e3",
    "\u0032\u20e3",
    "\u0033\u20e3",
    "\u0034\u20e3",
    "\u0035\u20e3",
    "\u0036\u20e3",
    "\u0037\u20e3",
    "\u0038\u20e3",
    "\u0039\u20e3",
]
CROSS_EMOJI = "\u274e"
HAND_RAISED_EMOJI = "\U0001f64b"
Coordinate = typing.Optional[typing.Tuple[int, int]]


class Game:
    """A Connect 4 Game."""

    def __init__(
            self,
            bot: commands.Bot,
            channel: discord.TextChannel,
            player1: discord.Member,
            player2: typing.Optional[discord.Member],
            size: int = 7,
    ) -> None:

        self.bot = bot
        self.channel = channel
        self.player1 = player1
        self.player2 = player2 or AI(self.bot, game=self)

        self.grid = self.generate_board(size)
        self.grid_size = size

        self.unicode_numbers = UNICODE_NUMBERS[:self.grid_size]

        self.message = None

        self.player_active = None
        self.player_inactive = None

    @staticmethod
    def generate_board(size: int) -> typing.List[typing.List[int]]:
        """Generate the connect 4 board."""
        return [[0 for _ in range(size)] for _ in range(size)]

    async def print_grid(self) -> None:
        """Formats and outputs the Connect Four grid to the channel."""
        rows = [" ".join(EMOJIS[s] for s in row) for row in self.grid]
        first_row = " ".join(x for x in NUMBERS[:self.grid_size])
        formatted_grid = "\n".join([first_row] + rows)
        embed = discord.Embed(title="Connect Four Board", description=formatted_grid)

        if self.message:
            await self.message.edit(embed=embed)
        else:
            self.message = await self.channel.send(embed=embed)
            for emoji in self.unicode_numbers:
                await self.message.add_reaction(emoji)
            await self.message.add_reaction(CROSS_EMOJI)

    async def start_game(self) -> None:
        """Begins the game."""
        self.player_active, self.player_inactive = self.player1, self.player2

        while True:
            await self.print_grid()
            if isinstance(self.player_active, AI):
                coords = self.player_active.play()
            else:
                coords = await self.player_turn()

            if not coords:
                return

            if self.check_win(coords, 1 if self.player_active == self.player1 else 2):
                if isinstance(self.player_active, AI):
                    await self.channel.send(f"Game Over! {self.player_inactive.mention} lost against"
                                            f" {self.bot.user.mention}")
                else:
                    if isinstance(self.player_inactive, AI):
                        await self.channel.send(f"Game Over! {self.player_active.mention} won against"
                                                f" {self.bot.user.mention}")
                    else:
                        await self.channel.send(
                            f"Game Over! {self.player_active.mention} won against {self.player_inactive.mention}"
                        )
                await self.print_grid()
                return

            self.player_active, self.player_inactive = self.player_inactive, self.player_active

    def predicate(self, reaction: discord.Reaction, user: discord.Member) -> bool:
        """The predicate to check for the player's reaction."""
        return (
            reaction.message.id == self.message.id
            and user.id == self.player_active.id
            and str(reaction.emoji) in (*self.unicode_numbers, CROSS_EMOJI)
        )

    async def player_turn(self) -> Coordinate:
        """Initiate the player's turn."""
        message = await self.channel.send(
            f"{self.player_active.mention}, it's your turn! React with the column you want to place your token in."
        )
        player_num = 1 if self.player_active == self.player1 else 2
        while True:
            full_column = False
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=self.predicate, timeout=30.0)
            except asyncio.TimeoutError:
                await self.channel.send(f"{self.player_active.mention}, you took too long. Game over!")
                return
            else:
                if str(reaction.emoji) == CROSS_EMOJI:
                    await message.delete()
                    await self.channel.send(
                        f"{user.mention} has abandoned the game :("
                    )
                    return

                await message.delete()
                await self.message.remove_reaction(reaction, user)
                column_num = self.unicode_numbers.index(str(reaction.emoji))

                column = [row[column_num] for row in self.grid]

                for row_num, square in reversed(list(enumerate(column))):
                    if not square:
                        self.grid[row_num][column_num] = player_num
                        coords = row_num, column_num
                        break
                else:
                    await self.channel.send(f"Column {column_num + 1} is full. Try again")
                    full_column = True
            if not full_column:
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
            counters_in_a_row = 1  # The initial counter that is compared to
            for (row_incr, column_incr) in axis:
                row, column = coords
                row += row_incr
                column += column_incr

                while 0 <= row < self.grid_size and 0 <= column < self.grid_size:
                    if self.grid[row][column] == player_num:
                        counters_in_a_row += 1
                        row += row_incr
                        column += column_incr
                    else:
                        break
            if counters_in_a_row >= 4:
                return True
        return False


class AI:
    """The Computer Player for Single-Player games."""

    def __init__(self, bot: commands.Bot, game: Game) -> None:
        self.game = game
        self.mention = bot.user.mention

    def get_possible_places(self) -> typing.List[Coordinate]:
        """Gets all the coordinates where the AI could possibly place a counter."""
        possible_coords = []
        for column_num in range(self.game.grid_size):
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

    @staticmethod
    def random_coords(coord_list: typing.List[Coordinate]) -> Coordinate:
        """Picks a random coordinate from the possible ones."""
        return random.choice(coord_list)

    def play(self) -> Coordinate:
        """
        Plays for the AI.

        Gets all possible coords, and determins the move:
        1. coords where it can win.
        2. coords where the player can win.
        3. Random coord
        The first possible value is choosen.
        """
        possible_coords = self.get_possible_places()

        coords = (
            self.check_ai_win(possible_coords)
            or self.check_player_win(possible_coords)
            or self.random_coords(possible_coords)
        )

        row, column = coords
        self.game.grid[row][column] = 2
        return coords


class ConnectFour(commands.Cog):
    """Connect Four. The Classic Vertical Four-in-a-row Game!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.games: typing.List[Game] = []
        self.waiting: typing.List[discord.Member] = []

        self.max_board_size = 9
        self.min_board_size = 5

    async def check_author(self, ctx: commands.Context, board_size: int) -> bool:
        """Check if the requester is free and the board size is correct."""
        if self.already_playing(ctx.author):
            await ctx.send("You're already playing a game!")
            return False

        if ctx.author in self.waiting:
            await ctx.send("You've already sent out a request for a player 2")
            return False

        if not self.min_board_size <= board_size <= self.max_board_size:
            await ctx.send(f"{board_size} is not a valid board size. A valid board size is "
                           f"between `{self.min_board_size}` and `{self.max_board_size}`.")
            return False

        return True

    def get_player(
            self,
            ctx: commands.Context,
            announcement: discord.Message,
            reaction: discord.Reaction,
            user: discord.Member
    ) -> bool:
        """Predicate checking the criteria for the announcement message."""
        if self.already_playing(ctx.author):  # If they've joined a game since requesting a player 2
            return True  # Is dealt with later on
        if (
                user.id not in (ctx.me.id, ctx.author.id)
                and str(reaction.emoji) == HAND_RAISED_EMOJI
                and reaction.message.id == announcement.id
        ):
            if self.already_playing(user):
                self.bot.loop.create_task(ctx.send(f"{user.mention} You're already playing a game!"))
                self.bot.loop.create_task(announcement.remove_reaction(reaction, user))
                return False

            if user in self.waiting:
                self.bot.loop.create_task(ctx.send(
                    f"{user.mention} Please cancel your game first before joining another one."
                ))
                self.bot.loop.create_task(announcement.remove_reaction(reaction, user))
                return False

            return True

        if (
                user.id == ctx.author.id
                and str(reaction.emoji) == CROSS_EMOJI
                and reaction.message.id == announcement.id
        ):
            return True
        return False

    def already_playing(self, player: discord.Member) -> bool:
        """Check if someone is already in a game."""
        return any(player in (game.player1, game.player2) for game in self.games)

    async def _play_game(self, ctx: commands.Context, user: typing.Optional[discord.Member], board_size: int) -> None:
        """Helper for playing a game of connect four."""
        try:
            game = Game(self.bot, ctx.channel, ctx.author, user, size=board_size)
            self.games.append(game)
            await game.start_game()
            self.games.remove(game)
        except Exception:
            # End the game in the event of an unforeseen error so the players aren't stuck in a game
            await ctx.send(f"{ctx.author.mention} {user.mention if user else ''} An error occurred. Game failed")
            self.games.remove(game)
            raise

    @commands.group(
        invoke_without_command=True,
        aliases=["4inarow", "connect4", "connectfour", "c4"]
    )
    async def connect_four(self, ctx: commands.Context, board_size: int = 7) -> None:
        """
        Play the classic game of Connect Four with someone!

        Sets up a message waiting for someone else to react and play along.
        The game will start once someone has reacted.
        All inputs will be through reactions.
        """
        check_author_result = await self.check_author(ctx, board_size)
        if not check_author_result:
            return

        announcement = await ctx.send(
            "**Connect Four**: A new game is about to start!\n"
            f"Press {HAND_RAISED_EMOJI} to play against {ctx.author.mention}!\n"
            f"(Cancel the game with {CROSS_EMOJI}.)"
        )
        self.waiting.append(ctx.author)
        await announcement.add_reaction(HAND_RAISED_EMOJI)
        await announcement.add_reaction(CROSS_EMOJI)

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=partial(self.get_player, ctx, announcement),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            self.waiting.remove(ctx.author)
            await announcement.delete()
            await ctx.send(
                f"{ctx.author.mention} Seems like there's no one here to play. "
                f"Use `{ctx.prefix}{ctx.invoked_with} ai` to play against a computer."
            )
            return

        if str(reaction.emoji) == CROSS_EMOJI:
            self.waiting.remove(ctx.author)
            await announcement.delete()
            await ctx.send(f"{ctx.author.mention} Game cancelled.")
            return

        await announcement.delete()
        self.waiting.remove(ctx.author)
        if self.already_playing(ctx.author):
            return

        await self._play_game(ctx, user, board_size)

    @connect_four.command(aliases=["bot", "computer", "cpu"])
    async def ai(self, ctx: commands.Context, board_size: int = 7) -> None:
        """Play Connect Four against a computer player."""
        check_author_result = await self.check_author(ctx, board_size)
        if not check_author_result:
            return

        await self._play_game(ctx, user=None, board_size=board_size)


def setup(bot: commands.Bot) -> None:
    """Load ConnectFour Cog."""
    bot.add_cog(ConnectFour(bot))
