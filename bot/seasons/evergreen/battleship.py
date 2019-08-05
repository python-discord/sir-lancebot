import asyncio
import random
import re
import typing
from dataclasses import dataclass

import discord
from discord.ext import commands

from bot.constants import Colours


@dataclass
class Square:
    """Each square on the battleship grid - if they contain a boat and if they've been aimed at"""

    boat: typing.Optional[str]
    aimed: bool


ships = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}

ship_emojis = {
    (True, True): ":fire:",
    (True, False): ":ship:",
    (False, True): ":anger:",
    (False, False): ":ocean:",
}
hidden_emojis = {
    (True, True): ":red_circle:",
    (True, False): ":black_circle:",
    (False, True): ":white_circle:",
    (False, False): ":black_circle:",
}

letters = (
    ":stop_button::regional_indicator_a::regional_indicator_b::regional_indicator_c::regional_indicator_d:"
    ":regional_indicator_e::regional_indicator_f::regional_indicator_g::regional_indicator_h:"
    ":regional_indicator_i::regional_indicator_j:"
)

numbers = [
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

grid_typehint = typing.List[typing.List[Square]]


class Game:
    """A Battleship Game."""

    def __init__(
        self,
        bot: commands.Bot,
        channel: discord.TextChannel,
        player1: discord.Member,
        player2: discord.Member
    ) -> None:

        self.bot = bot
        self.public_channel = channel
        self.player1 = player1
        self.player2 = player2

        # Message containing Player 1's Own Board
        self.self_player1: typing.Optional[discord.Message] = None

        # Message containing Player 2's Board Displayed in Player 1's DMs
        self.other_player1: typing.Optional[discord.Message] = None

        # Message containing Player 2's Own Board
        self.self_player2: typing.Optional[discord.Message] = None

        # Message containing Player 1's Board Displayed in Player 2's DMs
        self.other_player2: typing.Optional[discord.Message] = None

        self.grids: typing.Dict[discord.Member, grid_typehint] = {}
        self.grids[self.player1] = [
            [Square(boat=None, aimed=False) for _ in range(10)] for _ in range(10)
        ]
        self.grids[self.player2] = [
            [Square(boat=None, aimed=False) for _ in range(10)] for _ in range(10)
        ]

        self.gameover: bool = False

        self.turn: typing.Optional[discord.Member] = None
        self.next: typing.Optional[discord.Member] = None

        self.match: typing.Optional[typing.Match] = None

        self.setup_grids()

    @staticmethod
    def format_grid(grid: grid_typehint) -> str:
        """Formats the grid as a list into a string to be output to the DM. Also adds the Letter and Number indexes."""
        rows = ["".join([number] + row) for number, row in zip(numbers, grid)]
        return "\n".join([letters] + rows)

    @staticmethod
    def get_square(grid: grid_typehint, square: str) -> Square:
        """Grabs a square from a grid with an inputted key."""
        index = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7, "I": 8, "J": 9}
        letter = square[0]
        number = int(square[1:])

        return grid[number-1][index[letter]]  # -1 since lists are indexed from 0

    async def game_over(
        self,
        *,
        timeout: bool = False,
        winner: typing.Optional[discord.Member] = None,
        loser: typing.Optional[discord.Member] = None
    ) -> None:
        """Removes games from list of current games and announces to public chat."""
        if not timeout:  # If someone won and not the game timed out
            await self.public_channel.send(f"Game Over! {winner.mention} won against {loser.mention}")
            self_grid_1 = self.format_grid([
                [ship_emojis[bool(square.boat), square.aimed] for square in row]
                for row in self.grids[self.player1]
            ])

            self_grid_2 = self.format_grid([
                [ship_emojis[bool(square.boat), square.aimed] for square in row]
                for row in self.grids[self.player2]
            ])

            await self.public_channel.send(f"{self.player1}'s Board:\n{self_grid_1}")
            await self.public_channel.send(f"{self.player2}'s Board:\n{self_grid_2}")

        self.bot.get_cog("Battleship").games.remove(self)

    @staticmethod
    def check_sink(grid: grid_typehint, boat: str) -> bool:
        """Checks if all squares containing a given boat have sunk."""
        return all(square.aimed for row in grid for square in row if square.boat == boat)

    @staticmethod
    def check_gameover(grid: grid_typehint) -> bool:
        """Checks if all boats have been sunk."""
        return all(square.aimed for row in grid for square in row if square.boat)

    def setup_grids(self) -> None:
        """Places the boats on the grids to initialise the game."""
        for player in (self.player1, self.player2):
            for name, size in ships.items():
                while True:  # Repeats if about to overwrite another boat
                    overwrite = False
                    coords = []
                    if random.choice((True, False)):  # Vertical or Horizontal
                        # Vertical
                        x_coord = random.randint(0, 9)
                        y_coord = random.randint(0, 9 - size)
                        for i in range(size):
                            if self.grids[player][x_coord][y_coord + i].boat:  # Check if there's already a boat
                                overwrite = True
                            coords.append((x_coord, y_coord + i))
                    else:
                        # Horizontal
                        x_coord = random.randint(0, 9 - size)
                        y_coord = random.randint(0, 9)
                        for i in range(size):
                            if self.grids[player][x_coord + i][y_coord].boat:  # Check if there's already a boat
                                overwrite = True
                            coords.append((x_coord + i, y_coord))
                    if not overwrite:  # If not overwriting any other boat spaces, break loop
                        break

                for x, y in coords:
                    self.grids[player][x][y].boat = name

    async def print_grids(self) -> None:
        """Prints grids to the DM channels."""
        # Convert squares into Emoji

        # Player 1's Grid
        self_grid_1 = self.format_grid([
            [ship_emojis[bool(square.boat), square.aimed] for square in row]
            for row in self.grids[self.player1]
        ])

        # Player 2's Grid hidden for Player 1
        other_grid_1 = self.format_grid([
            [hidden_emojis[bool(square.boat), square.aimed] for square in row]
            for row in self.grids[self.player2]
        ])

        # Player 2's Grid
        self_grid_2 = self.format_grid([
            [ship_emojis[bool(square.boat), square.aimed] for square in row]
            for row in self.grids[self.player2]
        ])

        # Player 1's Grid hidden for Player 2
        other_grid_2 = self.format_grid([
            [hidden_emojis[bool(square.boat), square.aimed] for square in row]
            for row in self.grids[self.player1]
        ])

        if self.self_player1:  # If messages already exist
            await self.self_player1.edit(content=self_grid_1)
            await self.other_player1.edit(content=other_grid_1)
            await self.self_player2.edit(content=self_grid_2)
            await self.other_player2.edit(content=other_grid_2)
        else:
            self.self_player1 = await self.player1.send(self_grid_1)
            self.other_player1 = await self.player1.send(other_grid_1)
            self.self_player2 = await self.player2.send(self_grid_2)
            self.other_player2 = await self.player2.send(other_grid_2)

    def predicate(self, message: discord.Message) -> bool:
        """Predicate checking the message typed for each turn."""
        if message.author == self.turn and message.channel == self.turn.dm_channel:
            self.match = re.match("([A-J]|[a-j]) ?((10)|[1-9])", message.content.strip())
            if not self.match:
                self.bot.loop.create_task(message.add_reaction("\u274e"))
            return bool(self.match)

    async def start_game(self) -> None:
        """Begins the game."""
        await self.player1.send(f"You're playing battleships with {self.player2}.")
        await self.player2.send(f"You're playing battleships with {self.player1}.")

        alert_messages = []

        self.turn = self.player1
        self.next = self.player2

        while True:
            await self.print_grids()

            turn_message = await self.turn.send(
                "It's your turn! Type the square you want to fire at. Format it like this: A1"
            )
            await self.next.send("Their turn", delete_after=3.0)
            while True:
                try:
                    await self.bot.wait_for("message", check=self.predicate, timeout=60.0)
                except asyncio.TimeoutError:
                    await self.turn.send("You took too long. Game over!")
                    await self.next.send(f"{self.turn} took too long. Game over!")
                    self.gameover = True
                    break
                else:
                    square = self.get_square(self.grids[self.next], self.match.string)
                    if square.aimed:
                        await self.turn.send("You've already aimed at this square!", delete_after=3.0)
                    else:
                        break

            if self.gameover:
                await self.game_over(timeout=True)
                break

            square.aimed = True
            await turn_message.delete()
            for message in alert_messages:
                await message.delete()

            alert_messages = []
            alert_messages.append(await self.next.send(f"{self.turn} aimed at {self.match.string}!"))

            if square.boat:
                await self.turn.send("Hit!", delete_after=3.0)
                alert_messages.append(await self.next.send("Hit!"))
                if self.check_sink(self.grids[self.next], square.boat):
                    await self.turn.send(f"You've sunk their {square.boat} ship!", delete_after=3.0)
                    alert_messages.append(await self.next.send(f"Oh no! Your {square.boat} ship sunk!"))
                    if self.check_gameover(self.grids[self.next]):
                        await self.turn.send("You win!")
                        await self.next.send("You lose!")
                        self.gameover = True
                        await self.game_over(winner=self.turn, loser=self.next)
                        break
            else:
                await self.turn.send("Miss!", delete_after=3.0)
                alert_messages.append(await self.next.send("Miss!"))

            self.turn, self.next = self.next, self.turn


class Battleship(commands.Cog):
    """Play the classic game Battleships!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.games: typing.List[Game] = []
        self.waiting: typing.List[discord.Member] = []

    def already_playing(self, player: discord.Member) -> bool:
        """Check if someone is already in a game."""
        return player in [getattr(game, x) for game in self.games for x in ("player1", "player2")]

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def battleship(self, ctx: commands.Context) -> None:
        """
        Play a game of Battleships with someone else!

        This will set up a message waiting for someone else to react and play along.
        The game takes place entirely in DMs.
        Make sure you have your DMs open so that the bot can message you.
        """
        if self.already_playing(ctx.author):
            return await ctx.send("You're already playing a game!")

        if ctx.author in self.waiting:
            return await ctx.send("You've already sent out a request for a player 2")

        announcement = await ctx.send(
            "**Battleships**: A new game is about to start!\n"
            f"Press :raising_hand: to play against {ctx.author.mention}!"
        )
        self.waiting.append(ctx.author)
        await announcement.add_reaction("\U0001f64b")

        def predicate(reaction: discord.Reaction, user: discord.Member):
            if self.already_playing(ctx.author):  # If they've joined a game since requesting a player 2
                raise asyncio.TimeoutError
            if (
                user.id not in [ctx.me.id, ctx.author.id]
                and str(reaction.emoji) == "\U0001f64b"
                and reaction.message.id == announcement.id
            ):
                if self.already_playing(user):
                    self.bot.loop.create_task(ctx.send(f"{user.mention} You're already playing a game!"))
                    return False
                return True
            return False

        try:
            _reaction, user = await self.bot.wait_for("reaction_add", check=predicate, timeout=60.0)
        except asyncio.TimeoutError:
            self.waiting.remove(ctx.author)
            await announcement.delete()
            if self.already_playing(ctx.author):
                return
            return await ctx.send(f"{ctx.author.mention} Seems like there's noone here to play...")
        else:
            await announcement.delete()
            self.waiting.remove(ctx.author)
            try:
                if self.already_playing(ctx.author):
                    return
                game = Game(self.bot, ctx.channel, ctx.author, user)
                self.games.append(game)
                await game.start_game()
            except discord.Forbidden:
                await ctx.send(
                    f"{ctx.author.mention} {user.mention}"
                    "Game failed. This is likely due to you not having your DMs open. Check and try again."
                )
                self.games.remove(game)
            except Exception:
                # Unforseen error so the players aren't stuck in a game
                await ctx.send(f"{ctx.author.mention} {user.mention} An error occured. Game failed")
                self.games.remove(game)
                raise

    @battleship.command(name="ships", aliases=["boats"])
    async def battleship_ships(self, ctx: commands.Context) -> None:
        """This lists the ships that are found on the battleship grid."""
        embed = discord.Embed(colour=Colours.blue)
        embed.add_field(name="Name", value="Carrier\nBattleship\nCruiser\nSubmarine\nDestroyer")
        embed.add_field(name="Size", value="5\n4\n3\n3\n2")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    """Cog load."""
    bot.add_cog(Battleship(bot))
