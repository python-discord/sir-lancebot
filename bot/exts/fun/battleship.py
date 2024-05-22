import random
import re
from dataclasses import dataclass
from functools import partial

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Colours, Emojis

log = get_logger(__name__)


@dataclass
class Square:
    """Each square on the battleship grid - if they contain a boat and if they've been aimed at."""

    boat: str | None
    aimed: bool


Grid = list[list[Square]]
EmojiSet = dict[tuple[bool, bool], str]


@dataclass
class Player:
    """Each player in the game - their messages for the boards and their current grid."""

    user: discord.Member | None
    board: discord.Message | None
    opponent_board: discord.Message
    grid: Grid


# The name of the ship and its size
SHIPS = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}


# For these two variables, the first boolean is whether the square is a ship (True) or not (False).
# The second boolean is whether the player has aimed for that square (True) or not (False)

# This is for the player's own board which shows the location of their own ships.
SHIP_EMOJIS = {
    (True, True): ":fire:",
    (True, False): ":ship:",
    (False, True): ":anger:",
    (False, False): ":ocean:",
}

# This is for the opposing player's board which only shows aimed locations.
HIDDEN_EMOJIS = {
    (True, True): ":red_circle:",
    (True, False): ":black_circle:",
    (False, True): ":white_circle:",
    (False, False): ":black_circle:",
}

# For the top row of the board
LETTERS = (
    ":stop_button::regional_indicator_a::regional_indicator_b::regional_indicator_c::regional_indicator_d:"
    ":regional_indicator_e::regional_indicator_f::regional_indicator_g::regional_indicator_h:"
    ":regional_indicator_i::regional_indicator_j:"
)

# For the first column of the board
NUMBERS = [
    ":one:",
    ":two:",
    ":three:",
    ":four:",
    ":five:",
    ":six:",
    ":seven:",
    ":eight:",
    ":nine:",
    ":keycap_ten:",
]

CROSS_EMOJI = "\u274e"


class Game:
    """A Battleship Game."""

    def __init__(
        self,
        bot: Bot,
        channel: discord.TextChannel,
        player1: discord.Member,
        player2: discord.Member
    ):

        self.bot = bot
        self.public_channel = channel

        self.p1 = Player(player1, None, None, self.generate_grid())
        self.p2 = Player(player2, None, None, self.generate_grid())

        self.gameover: bool = False

        self.turn: Player | None = None
        self.next: Player | None = None

        self.match: re.Match | None = None
        self.surrender: bool = False

        self.setup_grids()

    @staticmethod
    def generate_grid() -> Grid:
        """Generates a grid by instantiating the Squares."""
        return [[Square(None, False) for _ in range(10)] for _ in range(10)]

    @staticmethod
    def format_grid(player: Player, emojiset: EmojiSet) -> str:
        """
        Gets and formats the grid as a list into a string to be output to the DM.

        Also adds the Letter and Number indexes.
        """
        grid = [
            [emojiset[bool(square.boat), square.aimed] for square in row]
            for row in player.grid
        ]

        rows = ["".join([number] + row) for number, row in zip(NUMBERS, grid, strict=True)]
        return "\n".join([LETTERS] + rows)

    @staticmethod
    def get_square(grid: Grid, square: str) -> Square:
        """Grabs a square from a grid with an inputted key."""
        index = ord(square[0].upper()) - ord("A")
        number = int(square[1:])

        return grid[number-1][index]  # -1 since lists are indexed from 0

    async def game_over(
        self,
        *,
        winner: discord.Member,
        loser: discord.Member
    ) -> None:
        """Removes games from list of current games and announces to public chat."""
        await self.public_channel.send(f"Game Over! {winner.mention} won against {loser.mention}")

        for player in (self.p1, self.p2):
            grid = self.format_grid(player, SHIP_EMOJIS)
            await self.public_channel.send(f"{player.user}'s Board:\n{grid}")

    @staticmethod
    def check_sink(grid: Grid, boat: str) -> bool:
        """Checks if all squares containing a given boat have sunk."""
        return all(square.aimed for row in grid for square in row if square.boat == boat)

    @staticmethod
    def check_gameover(grid: Grid) -> bool:
        """Checks if all boats have been sunk."""
        return all(square.aimed for row in grid for square in row if square.boat)

    def setup_grids(self) -> None:
        """Places the boats on the grids to initialise the game."""
        for player in (self.p1, self.p2):
            for name, size in SHIPS.items():
                while True:  # Repeats if about to overwrite another boat
                    ship_collision = False
                    coords = []

                    coord1 = random.randint(0, 9)
                    coord2 = random.randint(0, 10 - size)

                    if random.choice((True, False)):  # Vertical or Horizontal
                        x, y = coord1, coord2
                        xincr, yincr = 0, 1
                    else:
                        x, y = coord2, coord1
                        xincr, yincr = 1, 0

                    for i in range(size):
                        new_x = x + (xincr * i)
                        new_y = y + (yincr * i)
                        if player.grid[new_x][new_y].boat:  # Check if there's already a boat
                            ship_collision = True
                            break
                        coords.append((new_x, new_y))
                    if not ship_collision:  # If not overwriting any other boat spaces, break loop
                        break

                for x, y in coords:
                    player.grid[x][y].boat = name

    async def print_grids(self) -> None:
        """Prints grids to the DM channels."""
        # Convert squares into Emoji

        boards = [
            self.format_grid(player, emojiset)
            for emojiset in (HIDDEN_EMOJIS, SHIP_EMOJIS)
            for player in (self.p1, self.p2)
        ]

        locations = (
            (self.p2, "opponent_board"), (self.p1, "opponent_board"),
            (self.p1, "board"), (self.p2, "board")
        )

        for board, location in zip(boards, locations, strict=True):
            player, attr = location
            if getattr(player, attr):
                await getattr(player, attr).edit(content=board)
            else:
                setattr(player, attr, await player.user.send(board))

    def predicate(self, message: discord.Message) -> bool:
        """Predicate checking the message typed for each turn."""
        if message.author == self.turn.user and message.channel == self.turn.user.dm_channel:
            if message.content.lower() == "surrender":
                self.surrender = True
                return True
            self.match = re.fullmatch("([A-J]|[a-j]) ?((10)|[1-9])", message.content.strip())
            if not self.match:
                self.bot.loop.create_task(message.add_reaction(CROSS_EMOJI))
            return bool(self.match)
        return None

    async def take_turn(self) -> Square | None:
        """Lets the player who's turn it is choose a square."""
        square = None
        turn_message = await self.turn.user.send(
            "It's your turn! Type the square you want to fire at. Format it like this: A1\n"
            "Type `surrender` to give up."
        )
        await self.next.user.send("Their turn", delete_after=3.0)
        while True:
            try:
                await self.bot.wait_for("message", check=self.predicate, timeout=60.0)
            except TimeoutError:
                await self.turn.user.send("You took too long. Game over!")
                await self.next.user.send(f"{self.turn.user} took too long. Game over!")
                await self.public_channel.send(
                    f"Game over! {self.turn.user.mention} timed out so {self.next.user.mention} wins!"
                )
                self.gameover = True
                break
            else:
                if self.surrender:
                    await self.next.user.send(f"{self.turn.user} surrendered. Game over!")
                    await self.public_channel.send(
                        f"Game over! {self.turn.user.mention} surrendered to {self.next.user.mention}!"
                    )
                    self.gameover = True
                    break
                square = self.get_square(self.next.grid, self.match.string)
                if square.aimed:
                    await self.turn.user.send("You've already aimed at this square!", delete_after=3.0)
                else:
                    break
        await turn_message.delete()
        return square

    async def hit(self, square: Square, alert_messages: list[discord.Message]) -> None:
        """Occurs when a player successfully aims for a ship."""
        await self.turn.user.send("Hit!", delete_after=3.0)
        alert_messages.append(await self.next.user.send("Hit!"))
        if self.check_sink(self.next.grid, square.boat):
            await self.turn.user.send(f"You've sunk their {square.boat} ship!", delete_after=3.0)
            alert_messages.append(await self.next.user.send(f"Oh no! Your {square.boat} ship sunk!"))
            if self.check_gameover(self.next.grid):
                await self.turn.user.send("You win!")
                await self.next.user.send("You lose!")
                self.gameover = True
                await self.game_over(winner=self.turn.user, loser=self.next.user)

    async def start_game(self) -> None:
        """Begins the game."""
        await self.p1.user.send(f"You're playing battleship with {self.p2.user}.")
        await self.p2.user.send(f"You're playing battleship with {self.p1.user}.")

        alert_messages = []

        self.turn = self.p1
        self.next = self.p2

        while True:
            await self.print_grids()

            if self.gameover:
                return

            square = await self.take_turn()
            if not square:
                return
            square.aimed = True

            for message in alert_messages:
                await message.delete()

            alert_messages = []
            alert_messages.append(await self.next.user.send(f"{self.turn.user} aimed at {self.match.string}!"))

            if square.boat:
                await self.hit(square, alert_messages)
                if self.gameover:
                    return
            else:
                await self.turn.user.send("Miss!", delete_after=3.0)
                alert_messages.append(await self.next.user.send("Miss!"))

            self.turn, self.next = self.next, self.turn


class Battleship(commands.Cog):
    """Play the classic game Battleship!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.games: list[Game] = []
        self.waiting: list[discord.Member] = []

    def predicate(
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
            and str(reaction.emoji) == Emojis.hand_raised
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

        return bool(
            user.id == ctx.author.id
            and str(reaction.emoji) == CROSS_EMOJI
            and reaction.message.id == announcement.id
        )

    def already_playing(self, player: discord.Member) -> bool:
        """Check if someone is already in a game."""
        return any(player in (game.p1.user, game.p2.user) for game in self.games)

    @commands.group(invoke_without_command=True)
    async def battleship(self, ctx: commands.Context) -> None:
        """
        Play a game of Battleship with someone else!

        This will set up a message waiting for someone else to react and play along.
        The game takes place entirely in DMs.
        Make sure you have your DMs open so that the bot can message you.
        """
        if self.already_playing(ctx.author):
            await ctx.send("You're already playing a game!")
            return

        if ctx.author in self.waiting:
            await ctx.send("You've already sent out a request for a player 2.")
            return

        announcement = await ctx.send(
            "**Battleship**: A new game is about to start!\n"
            f"Press {Emojis.hand_raised} to play against {ctx.author.mention}!\n"
            f"(Cancel the game with {CROSS_EMOJI}.)"
        )
        self.waiting.append(ctx.author)
        await announcement.add_reaction(Emojis.hand_raised)
        await announcement.add_reaction(CROSS_EMOJI)

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=partial(self.predicate, ctx, announcement),
                timeout=60.0
            )
        except TimeoutError:
            self.waiting.remove(ctx.author)
            await announcement.delete()
            await ctx.send(f"{ctx.author.mention} Seems like there's no one here to play...")
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
        game = Game(self.bot, ctx.channel, ctx.author, user)
        self.games.append(game)
        try:
            await game.start_game()
            self.games.remove(game)
        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} {user.mention} "
                "Game failed. This is likely due to you not having your DMs open. Check and try again."
            )
            self.games.remove(game)
        except Exception:
            # End the game in the event of an unforseen error so the players aren't stuck in a game
            await ctx.send(f"{ctx.author.mention} {user.mention} An error occurred. Game failed.")
            self.games.remove(game)
            raise

    @battleship.command(name="ships", aliases=("boats",))
    async def battleship_ships(self, ctx: commands.Context) -> None:
        """Lists the ships that are found on the battleship grid."""
        embed = discord.Embed(colour=Colours.blue)
        embed.add_field(name="Name", value="\n".join(SHIPS))
        embed.add_field(name="Size", value="\n".join(str(size) for size in SHIPS.values()))
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Battleship Cog."""
    await bot.add_cog(Battleship(bot))
