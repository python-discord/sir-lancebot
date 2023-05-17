import asyncio
import random
from collections.abc import Callable

import discord
from discord.ext.commands import Cog, Context, check, group

from bot.bot import Bot
from bot.constants import Emojis
from bot.utils.pagination import LinePaginator

CONFIRMATION_MESSAGE = (
    "{opponent}, {requester} wants to play Tic-Tac-Toe against you."
    f"\nReact to this message with {Emojis.confirmation} to accept or with {Emojis.decline} to decline."
)


def check_win(board: dict[int, str]) -> bool:
    """Check from board, is any player won game."""
    return any(
        (
            # Horizontal
            board[1] == board[2] == board[3],
            board[4] == board[5] == board[6],
            board[7] == board[8] == board[9],
            # Vertical
            board[1] == board[4] == board[7],
            board[2] == board[5] == board[8],
            board[3] == board[6] == board[9],
            # Diagonal
            board[1] == board[5] == board[9],
            board[3] == board[5] == board[7],
        )
    )


class Player:
    """Class that contains information about player and functions that interact with player."""

    def __init__(self, user: discord.User, ctx: Context, symbol: str):
        self.user = user
        self.ctx = ctx
        self.symbol = symbol

    async def get_move(self, board: dict[int, str], msg: discord.Message) -> tuple[bool, int | None]:
        """
        Get move from user.

        Return is timeout reached and position of field what user will fill when timeout don't reach.
        """
        def check_for_move(r: discord.Reaction, u: discord.User) -> bool:
            """Check does user who reacted is user who we want, message is board and emoji is in board values."""
            return (
                u.id == self.user.id
                and msg.id == r.message.id
                and r.emoji in board.values()
                and r.emoji in Emojis.number_emojis.values()
            )

        try:
            react, _ = await self.ctx.bot.wait_for("reaction_add", timeout=30.0, check=check_for_move)
        except asyncio.TimeoutError:
            return True, None
        else:
            return False, list(Emojis.number_emojis.keys())[list(Emojis.number_emojis.values()).index(react.emoji)]

    def __str__(self) -> str:
        """Return mention of user."""
        return self.user.mention


class AI:
    """Tic Tac Toe AI class for against computer gaming."""

    def __init__(self, bot_user: discord.Member, symbol: str):
        self.user = bot_user
        self.symbol = symbol

    @staticmethod
    async def get_move(board: dict[int, str], _: discord.Message) -> tuple[bool, int]:
        """Get move from AI. AI use Minimax strategy."""
        possible_moves = [i for i, emoji in board.items() if emoji in list(Emojis.number_emojis.values())]

        for symbol in (Emojis.o_square, Emojis.x_square):
            for move in possible_moves:
                board_copy = board.copy()
                board_copy[move] = symbol
                if check_win(board_copy):
                    return False, move

        open_corners = [i for i in possible_moves if i in (1, 3, 7, 9)]
        if len(open_corners) > 0:
            return False, random.choice(open_corners)

        if 5 in possible_moves:
            return False, 5

        open_edges = [i for i in possible_moves if i in (2, 4, 6, 8)]
        return False, random.choice(open_edges)

    def __str__(self) -> str:
        """Return mention of @Sir Lancebot."""
        return self.user.mention


class Game:
    """Class that contains information and functions about Tic Tac Toe game."""

    def __init__(self, players: list[Player | AI], ctx: Context):
        self.players = players
        self.ctx = ctx
        self.channel = ctx.channel
        self.board = {
            1: Emojis.number_emojis[1],
            2: Emojis.number_emojis[2],
            3: Emojis.number_emojis[3],
            4: Emojis.number_emojis[4],
            5: Emojis.number_emojis[5],
            6: Emojis.number_emojis[6],
            7: Emojis.number_emojis[7],
            8: Emojis.number_emojis[8],
            9: Emojis.number_emojis[9]
        }

        self.current = self.players[0]
        self.next = self.players[1]

        self.winner: Player | AI | None = None
        self.loser: Player | AI | None = None
        self.over = False
        self.canceled = False
        self.draw = False

    async def get_confirmation(self) -> tuple[bool, str | None]:
        """
        Ask does user want to play TicTacToe against requester. First player is always requester.

        This return tuple that have:
        - first element boolean (is game accepted?)
        - (optional, only when first element is False, otherwise None) reason for declining.
        """
        confirm_message = await self.ctx.send(
            CONFIRMATION_MESSAGE.format(
                opponent=self.players[1].user.mention,
                requester=self.players[0].user.mention
            )
        )
        await confirm_message.add_reaction(Emojis.confirmation)
        await confirm_message.add_reaction(Emojis.decline)

        def confirm_check(reaction: discord.Reaction, user: discord.User) -> bool:
            """Check is user who reacted from who this was requested, message is confirmation and emoji is valid."""
            return (
                reaction.emoji in (Emojis.confirmation, Emojis.decline)
                and reaction.message.id == confirm_message.id
                and user == self.players[1].user
            )

        try:
            reaction, user = await self.ctx.bot.wait_for(
                "reaction_add",
                timeout=60.0,
                check=confirm_check
            )
        except asyncio.TimeoutError:
            self.over = True
            self.canceled = True
            await confirm_message.delete()
            return False, "Running out of time... Cancelled game."

        await confirm_message.delete()
        if reaction.emoji == Emojis.confirmation:
            return True, None

        self.over = True
        self.canceled = True
        return False, "User declined"

    @staticmethod
    async def add_reactions(msg: discord.Message) -> None:
        """Add number emojis to message."""
        for nr in Emojis.number_emojis.values():
            await msg.add_reaction(nr)

    def format_board(self) -> str:
        """Get formatted tic-tac-toe board for message."""
        board = list(self.board.values())
        return "\n".join(
            f"{board[line]} {board[line + 1]} {board[line + 2]}"
            for line in range(0, len(board), 3)
        )

    async def play(self) -> None:
        """Start and handle game."""
        await self.ctx.send("It's time for the game! Let's begin.")
        board = await self.ctx.send(
            embed=discord.Embed(description=self.format_board())
        )
        await self.add_reactions(board)

        for _ in range(9):
            if isinstance(self.current, Player):
                announce = await self.ctx.send(
                    f"{self.current.user.mention}, it's your turn! "
                    "React with an emoji to take your go."
                )
            timeout, pos = await self.current.get_move(self.board, board)
            if isinstance(self.current, Player):
                await announce.delete()
            if timeout:
                await self.ctx.send(f"{self.current.user.mention} ran out of time. Canceling game.")
                self.over = True
                self.canceled = True
                return
            self.board[pos] = self.current.symbol
            await board.edit(
                embed=discord.Embed(description=self.format_board())
            )
            await board.clear_reaction(Emojis.number_emojis[pos])
            if check_win(self.board):
                self.winner = self.current
                self.loser = self.next
                await self.ctx.send(
                    f":tada: {self.current} won this game! :tada:"
                )
                await board.clear_reactions()
                break
            self.current, self.next = self.next, self.current
        if not self.winner:
            self.draw = True
            await self.ctx.send("It's a DRAW!")
        self.over = True


def is_channel_free() -> Callable:
    """Check is channel where command will be invoked free."""
    async def predicate(ctx: Context) -> bool:
        return all(game.channel != ctx.channel for game in ctx.cog.games if not game.over)
    return check(predicate)


def is_requester_free() -> Callable:
    """Check is requester not already in any game."""
    async def predicate(ctx: Context) -> bool:
        return all(
            ctx.author not in (player.user for player in game.players) for game in ctx.cog.games if not game.over
        )
    return check(predicate)


class TicTacToe(Cog):
    """TicTacToe cog contains tic-tac-toe game commands."""

    def __init__(self):
        self.games: list[Game] = []

    @is_channel_free()
    @is_requester_free()
    @group(name="tictactoe", aliases=("ttt", "tic"), invoke_without_command=True)
    async def tic_tac_toe(self, ctx: Context, opponent: discord.User | None) -> None:
        """Tic Tac Toe game. Play against friends or AI. Use reactions to add your mark to field."""
        if opponent == ctx.author:
            await ctx.send("You can't play against yourself.")
            return
        if opponent is not None and not all(
            opponent not in (player.user for player in g.players) for g in ctx.cog.games if not g.over
        ):
            await ctx.send("Opponent is already in game.")
            return
        if opponent is None:
            game = Game(
                [Player(ctx.author, ctx, Emojis.x_square), AI(ctx.me, Emojis.o_square)],
                ctx
            )
        else:
            game = Game(
                [Player(ctx.author, ctx, Emojis.x_square), Player(opponent, ctx, Emojis.o_square)],
                ctx
            )
        self.games.append(game)
        if opponent is not None:
            if opponent.bot:  # check whether the opponent is a bot or not
                await ctx.send("You can't play Tic-Tac-Toe with bots!")
                return

            confirmed, msg = await game.get_confirmation()

            if not confirmed:
                if msg:
                    await ctx.send(msg)
                return
        await game.play()

    @tic_tac_toe.group(name="history", aliases=("log",), invoke_without_command=True)
    async def tic_tac_toe_logs(self, ctx: Context) -> None:
        """Show most recent tic-tac-toe games."""
        if len(self.games) < 1:
            await ctx.send("No recent games.")
            return
        log_games = []
        for i, game in enumerate(self.games):
            if game.over and not game.canceled:
                if game.draw:
                    log_games.append(
                        f"**#{i+1}**: {game.players[0]} vs {game.players[1]} (draw)"
                    )
                else:
                    log_games.append(
                        f"**#{i+1}**: {game.winner} :trophy: vs {game.loser}"
                    )
        await LinePaginator.paginate(
            log_games,
            ctx,
            discord.Embed(title="Most recent Tic Tac Toe games")
        )

    @tic_tac_toe_logs.command(name="show", aliases=("s",))
    async def show_tic_tac_toe_board(self, ctx: Context, game_id: int) -> None:
        """View game board by ID (ID is possible to get by `.tictactoe history`)."""
        if len(self.games) < game_id:
            await ctx.send("Game don't exist.")
            return
        game = self.games[game_id - 1]

        if game.draw:
            description = f"{game.players[0]} vs {game.players[1]} (draw)\n\n{game.format_board()}"
        else:
            description = f"{game.winner} :trophy: vs {game.loser}\n\n{game.format_board()}"

        embed = discord.Embed(
            title=f"Match #{game_id} Game Board",
            description=description,
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the TicTacToe cog."""
    await bot.add_cog(TicTacToe())
