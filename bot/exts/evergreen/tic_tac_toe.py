import asyncio
import random
import typing as t

import discord
from discord.ext.commands import Cog, Context, check, group, guild_only

from bot.bot import SeasonalBot
from bot.constants import Emojis
from bot.utils.pagination import LinePaginator

CONFIRMATION_MESSAGE = (
    "{opponent}, {requester} want to play Tic-Tac-Toe against you. React to this message with "
    f"{Emojis.confirmation} to accept or with {Emojis.decline} to decline."
)


class Player:
    """Class that contains information about player and functions that interact with player."""

    def __init__(self, user: discord.User, ctx: Context, symbol: str):
        self.user = user
        self.ctx = ctx
        self.symbol = symbol

    async def get_move(self, board: t.Dict[int, str], msg: discord.Message) -> t.Tuple[bool, t.Optional[int]]:
        """
        Get move from user.

        Return is timeout reached and position of field what user will fill when timeout don't reach.
        """
        def check_for_move(r: discord.Reaction, u: discord.User) -> bool:
            return (
                u.id == self.user.id
                and msg.id == r.message.id
                and r.emoji in board.values()
                and r.emoji in Emojis.number_emojis.values()
            )

        try:
            react, _ = await self.ctx.bot.wait_for('reaction_add', timeout=120.0, check=check_for_move)
        except asyncio.TimeoutError:
            return True, None
        else:
            return False, list(Emojis.number_emojis.keys())[list(Emojis.number_emojis.values()).index(react.emoji)]

    async def display(self) -> str:
        """Return mention of user."""
        return self.user.mention


class AI:
    """Tic Tac Toe AI class for against computer gaming."""

    def __init__(self, symbol: str):
        self.symbol = symbol

    async def check_win(self, board: t.Dict[int, str]) -> bool:
        """Check does this move will result game end."""
        if (
            # Horizontal
            board[1] == board[2] == board[3]
            or board[4] == board[5] == board[6]
            or board[7] == board[8] == board[9]
            # Vertical
            or board[1] == board[4] == board[7]
            or board[2] == board[5] == board[8]
            or board[3] == board[6] == board[9]
            # Diagonal
            or board[1] == board[5] == board[9]
            or board[3] == board[5] == board[7]
        ):
            return True
        return False

    async def get_move(self, board: t.Dict[int, str], _: discord.Message) -> t.Tuple[bool, int]:
        """Get move from AI. AI use Minimax strategy."""
        possible_moves = [i for i, emoji in board.items() if emoji in list(Emojis.number_emojis.values())]

        for symbol in (Emojis.o, Emojis.x):
            for move in possible_moves:
                board_copy = board.copy()
                board_copy[move] = symbol
                if await self.check_win(board_copy):
                    return False, move

        open_corners = [i for i in possible_moves if i in (1, 3, 7, 9)]
        if len(open_corners) > 0:
            return False, random.choice(open_corners)

        if 5 in possible_moves:
            return False, 5

        open_edges = [i for i in possible_moves if i in (2, 4, 6, 8)]
        return False, random.choice(open_edges)

    def display(self) -> str:
        """Return `AI` as user name."""
        return "AI"


class Game:
    """Class that contains information and functions about Tic Tac Toe game."""

    def __init__(self, players: t.List[t.Union[Player, AI]], ctx: Context):
        self.players = players
        self.ctx = ctx
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

        self.winner: t.Optional[t.Union[Player, AI]] = None
        self.loser: t.Optional[t.Union[Player, AI]] = None
        self.over = False
        self.canceled = False
        self.draw = False

    async def get_confirmation(self) -> t.Tuple[bool, t.Optional[str]]:
        """Ask does user want to play TicTacToe against requester. First player is always requester."""
        confirm_message = await self.ctx.send(
            CONFIRMATION_MESSAGE.format(
                opponent=self.players[1].user.mention,
                requester=self.players[0].user.mention
            )
        )
        await confirm_message.add_reaction(Emojis.confirmation)
        await confirm_message.add_reaction(Emojis.decline)

        def confirm_check(reaction: discord.Reaction, user: discord.User) -> bool:
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
        else:
            self.over = True
            self.canceled = True
            return False, "User declined"

    async def add_reactions(self, msg: discord.Message) -> None:
        """Add number emojis to message."""
        for nr in Emojis.number_emojis.values():
            await msg.add_reaction(nr)

    async def send_board(self, channel: t.Optional[discord.TextChannel] = None) -> discord.Message:
        """Send board and return it's message."""
        msg = ""
        c = 0
        for line in self.board.values():
            msg += f"{line} "
            c += 1
            if c == 3:
                msg += "\n"
                c = 0
        if channel:
            return await channel.send(msg)
        return await self.ctx.send(msg)

    async def edit_board(self, message: discord.Message) -> None:
        """Edit Tic Tac Toe game board in message."""
        msg = ""
        c = 0
        for line in self.board.values():
            msg += f"{line} "
            c += 1
            if c == 3:
                msg += "\n"
                c = 0
        await message.edit(content=msg)

    async def check_for_win(self) -> bool:
        """Check from board, is any player won game."""
        if (
            # Horizontal
            self.board[1] == self.board[2] == self.board[3]
            or self.board[4] == self.board[5] == self.board[6]
            or self.board[7] == self.board[8] == self.board[9]
            # Vertical
            or self.board[1] == self.board[4] == self.board[7]
            or self.board[2] == self.board[5] == self.board[8]
            or self.board[3] == self.board[6] == self.board[9]
            # Diagonal
            or self.board[1] == self.board[5] == self.board[9]
            or self.board[3] == self.board[5] == self.board[7]
        ):
            return True
        return False

    async def play(self) -> None:
        """Start and handle game."""
        await self.ctx.send("It's time for game! Let's begin.")
        board = await self.send_board()
        await self.add_reactions(board)

        for _ in range(9):
            if isinstance(self.current, Player):
                announce = await self.ctx.send(f"{self.current.user.mention}, your turn! React to emoji to mark field.")
            timeout, pos = await self.current.get_move(self.board, board)
            if isinstance(self.current, Player):
                await announce.delete()
            if timeout:
                await self.ctx.send(f"{self.current.user.mention} ran out of time. Canceling game.")
                self.over = True
                self.canceled = True
                return
            self.board[pos] = self.current.symbol
            await self.edit_board(board)
            await board.clear_reaction(Emojis.number_emojis[pos])
            if await self.check_for_win():
                self.winner = self.current
                self.loser = self.next
                await self.ctx.send(
                    f":tada: {self.current.user.mention if isinstance(self.current, Player) else 'AI'} "
                    f"is won this game! :tada:"
                )
                await board.clear_reactions()
                break
            self.current, self.next = self.next, self.current
        if not self.winner:
            self.draw = True
            await self.ctx.send("It's DRAW!")
        self.over = True


def is_channel_free() -> t.Callable:
    """Check is channel where command will be invoked free."""
    async def predicate(ctx: Context) -> bool:
        return all(game.channel != ctx.channel for game in ctx.cog.games if not game.over)
    return check(predicate)


def is_requester_free() -> t.Callable:
    """Check is requester not already in any game."""
    async def predicate(ctx: Context) -> bool:
        return all(
            ctx.author not in (player.user for player in game.players) for game in ctx.cog.games if not game.over
        )
    return check(predicate)


class TicTacToe(Cog):
    """TicTacToe cog contains tic-tac-toe game commands."""

    def __init__(self, bot: SeasonalBot):
        self.bot = bot
        self.games: t.List[Game] = []

    @guild_only()
    @is_channel_free()
    @is_requester_free()
    @group(name="tictactoe", aliases=("ttt",), invoke_without_command=True)
    async def tic_tac_toe(self, ctx: Context, opponent: t.Optional[discord.User]) -> None:
        """Tic Tac Toe game. Play agains friends or AI. Use reactions to add your mark to field."""
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
                [Player(ctx.author, ctx, Emojis.x), AI(Emojis.o)],
                ctx
            )
        else:
            game = Game(
                [Player(ctx.author, ctx, Emojis.x), Player(opponent, ctx, Emojis.o)],
                ctx
            )
        self.games.append(game)
        if opponent is not None:
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
                        f"**#{i+1}**: {game.players[0].user.mention} vs "
                        f"{game.players[1].user.mention if isinstance(game.players[1], Player) else 'AI'} (draw)"
                    )
                else:
                    log_games.append(
                        f"**#{i+1}**: {game.winner.user.mention if isinstance(game.winner, Player) else 'AI'} :trophy: "
                        f"vs {game.loser.user.mention if isinstance(game.loser, Player) else 'AI'}"
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
        await ctx.send(
            f"{game.winner.user if isinstance(game.winner, Player) else 'AI'} "
            f":trophy: vs {game.loser.user if isinstance(game.winner, Player) else 'AI'}"
        )
        await game.send_board(ctx.channel)


def setup(bot: SeasonalBot) -> None:
    """Load TicTacToe Cog."""
    bot.add_cog(TicTacToe(bot))
