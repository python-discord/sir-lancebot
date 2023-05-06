import asyncio
import io
import json
import logging
import math
import random
from itertools import product
from pathlib import Path

from PIL import Image
from PIL.ImageDraw import ImageDraw
from discord import File, Member, Reaction, User
from discord.ext.commands import Cog, Context

from bot.constants import MODERATION_ROLES

SNAKE_RESOURCES = Path("bot/resources/fun/snakes").absolute()

h1 = r"""```
   ----
  ------
/--------\
|--------|
|--------|
 \------/
   ----
```"""
h2 = r"""```
   ----
  ------
/---\-/--\
|-----\--|
|--------|
 \------/
   ----
```"""
h3 = r"""```
   ----
  ------
/---\-/--\
|-----\--|
|-----/--|
 \----\-/
   ----
```"""
h4 = r"""```
   -----
  -----  \
/--|  /---\
|--\  -\---|
|--\--/--  /
 \------- /
   ------
```"""
stages = [h1, h2, h3, h4]
snakes = {
    "Baby Python": "https://i.imgur.com/SYOcmSa.png",
    "Baby Rattle Snake": "https://i.imgur.com/i5jYA8f.png",
    "Baby Dragon Snake": "https://i.imgur.com/SuMKM4m.png",
    "Baby Garden Snake": "https://i.imgur.com/5vYx3ah.png",
    "Baby Cobra": "https://i.imgur.com/jk14ryt.png",
    "Baby Anaconda": "https://i.imgur.com/EpdrnNr.png",
}

BOARD_TILE_SIZE = 56         # the size of each board tile
BOARD_PLAYER_SIZE = 20       # the size of each player icon
BOARD_MARGIN = (10, 0)       # margins, in pixels (for player icons)
# The size of the image to download
# Should a power of 2 and higher than BOARD_PLAYER_SIZE
PLAYER_ICON_IMAGE_SIZE = 32
MAX_PLAYERS = 4              # depends on the board size/quality, 4 is for the default board

# board definition (from, to)
BOARD = {
    # ladders
    2: 38,
    7: 14,
    8: 31,
    15: 26,
    21: 42,
    28: 84,
    36: 44,
    51: 67,
    71: 91,
    78: 98,
    87: 94,

    # snakes
    99: 80,
    95: 75,
    92: 88,
    89: 68,
    74: 53,
    64: 60,
    62: 19,
    49: 11,
    46: 25,
    16: 6
}

DEFAULT_SNAKE_COLOR = 0x15c7ea
DEFAULT_BACKGROUND_COLOR = 0
DEFAULT_IMAGE_DIMENSIONS = (200, 200)
DEFAULT_SNAKE_LENGTH = 22
DEFAULT_SNAKE_WIDTH = 8
DEFAULT_SEGMENT_LENGTH_RANGE = (7, 10)
DEFAULT_IMAGE_MARGINS = (50, 50)
DEFAULT_TEXT = "snek\nit\nup"
DEFAULT_TEXT_POSITION = (
    10,
    10
)
DEFAULT_TEXT_COLOR = 0xf2ea15
X = 0
Y = 1
ANGLE_RANGE = math.pi * 2


def get_resource(file: str) -> list[dict]:
    """Load Snake resources JSON."""
    return json.loads((SNAKE_RESOURCES / f"{file}.json").read_text("utf-8"))


def smoothstep(t: float) -> float:
    """Smooth curve with a zero derivative at 0 and 1, making it useful for interpolating."""
    return t * t * (3. - 2. * t)


def lerp(t: float, a: float, b: float) -> float:
    """Linear interpolation between a and b, given a fraction t."""
    return a + t * (b - a)


class PerlinNoiseFactory:
    """
    Callable that produces Perlin noise for an arbitrary point in an arbitrary number of dimensions.

    The underlying grid is aligned with the integers.

    There is no limit to the coordinates used; new gradients are generated on the fly as necessary.

    Taken from: https://gist.github.com/eevee/26f547457522755cb1fb8739d0ea89a1
    Licensed under ISC
    """

    def __init__(self, dimension: int, octaves: int = 1, tile: tuple[int, ...] = (), unbias: bool = False):
        """
        Create a new Perlin noise factory in the given number of dimensions.

        dimension should be an integer and at least 1.

        More octaves create a foggier and more-detailed noise pattern.  More than 4 octaves is rather excessive.

        ``tile`` can be used to make a seamlessly tiling pattern.
        For example:
            pnf = PerlinNoiseFactory(2, tile=(0, 3))

        This will produce noise that tiles every 3 units vertically, but never tiles horizontally.

        If ``unbias`` is True, the smoothstep function will be applied to the output before returning
        it, to counteract some of Perlin noise's significant bias towards the center of its output range.
        """
        self.dimension = dimension
        self.octaves = octaves
        self.tile = tile + (0,) * dimension
        self.unbias = unbias

        # For n dimensions, the range of Perlin noise is ±sqrt(n)/2; multiply
        # by this to scale to ±1
        self.scale_factor = 2 * dimension ** -0.5

        self.gradient = {}

    def _generate_gradient(self) -> tuple[float, ...]:
        """
        Generate a random unit vector at each grid point.

        This is the "gradient" vector, in that the grid tile slopes towards it
        """
        # 1 dimension is special, since the only unit vector is trivial;
        # instead, use a slope between -1 and 1
        if self.dimension == 1:
            return (random.uniform(-1, 1),)

        # Generate a random point on the surface of the unit n-hypersphere;
        # this is the same as a random unit vector in n dimensions.  Thanks
        # to: http://mathworld.wolfram.com/SpherePointPicking.html
        # Pick n normal random variables with stddev 1
        random_point = [random.gauss(0, 1) for _ in range(self.dimension)]
        # Then scale the result to a unit vector
        scale = sum(n * n for n in random_point) ** -0.5
        return tuple(coord * scale for coord in random_point)

    def get_plain_noise(self, *point) -> float:
        """Get plain noise for a single point, without taking into account either octaves or tiling."""
        if len(point) != self.dimension:
            raise ValueError(
                f"Expected {self.dimension} values, got {len(point)}"
            )

        # Build a list of the (min, max) bounds in each dimension
        grid_coords = []
        for coord in point:
            min_coord = math.floor(coord)
            max_coord = min_coord + 1
            grid_coords.append((min_coord, max_coord))

        # Compute the dot product of each gradient vector and the point's
        # distance from the corresponding grid point.  This gives you each
        # gradient's "influence" on the chosen point.
        dots = []
        for grid_point in product(*grid_coords):
            if grid_point not in self.gradient:
                self.gradient[grid_point] = self._generate_gradient()
            gradient = self.gradient[grid_point]

            dot = 0
            for i in range(self.dimension):
                dot += gradient[i] * (point[i] - grid_point[i])
            dots.append(dot)

        # Interpolate all those dot products together.  The interpolation is
        # done with smoothstep to smooth out the slope as you pass from one
        # grid cell into the next.
        # Due to the way product() works, dot products are ordered such that
        # the last dimension alternates: (..., min), (..., max), etc.  So we
        # can interpolate adjacent pairs to "collapse" that last dimension.  Then
        # the results will alternate in their second-to-last dimension, and so
        # forth, until we only have a single value left.
        dim = self.dimension
        while len(dots) > 1:
            dim -= 1
            s = smoothstep(point[dim] - grid_coords[dim][0])

            next_dots = []
            while dots:
                next_dots.append(lerp(s, dots.pop(0), dots.pop(0)))

            dots = next_dots

        return dots[0] * self.scale_factor

    def __call__(self, *point) -> float:
        """
        Get the value of this Perlin noise function at the given point.

        The number of values given should match the number of dimensions.
        """
        ret = 0
        for o in range(self.octaves):
            o2 = 1 << o
            new_point = []
            for i, coord in enumerate(point):
                coord *= o2
                if self.tile[i]:
                    coord %= self.tile[i] * o2
                new_point.append(coord)
            ret += self.get_plain_noise(*new_point) / o2

        # Need to scale n back down since adding all those extra octaves has
        # probably expanded it beyond ±1
        # 1 octave: ±1
        # 2 octaves: ±1½
        # 3 octaves: ±1¾
        ret /= 2 - 2 ** (1 - self.octaves)

        if self.unbias:
            # The output of the plain Perlin noise algorithm has a fairly
            # strong bias towards the center due to the central limit theorem
            # -- in fact the top and bottom 1/8 virtually never happen.  That's
            # a quarter of our entire output range!  If only we had a function
            # in [0..1] that could introduce a bias towards the endpoints...
            r = (ret + 1) / 2
            # Doing it this many times is a completely made-up heuristic.
            for _ in range(int(self.octaves / 2 + 0.5)):
                r = smoothstep(r)
            ret = r * 2 - 1

        return ret


def create_snek_frame(
        perlin_factory: PerlinNoiseFactory, perlin_lookup_vertical_shift: float = 0,
        image_dimensions: tuple[int, int] = DEFAULT_IMAGE_DIMENSIONS,
        image_margins: tuple[int, int] = DEFAULT_IMAGE_MARGINS,
        snake_length: int = DEFAULT_SNAKE_LENGTH,
        snake_color: int = DEFAULT_SNAKE_COLOR, bg_color: int = DEFAULT_BACKGROUND_COLOR,
        segment_length_range: tuple[int, int] = DEFAULT_SEGMENT_LENGTH_RANGE, snake_width: int = DEFAULT_SNAKE_WIDTH,
        text: str = DEFAULT_TEXT, text_position: tuple[float, float] = DEFAULT_TEXT_POSITION,
        text_color: int = DEFAULT_TEXT_COLOR
) -> Image.Image:
    """
    Creates a single random snek frame using Perlin noise.

    `perlin_lookup_vertical_shift` represents the Perlin noise shift in the Y-dimension for this frame.
    If `text` is given, display the given text with the snek.
    """
    start_x = random.randint(image_margins[X], image_dimensions[X] - image_margins[X])
    start_y = random.randint(image_margins[Y], image_dimensions[Y] - image_margins[Y])
    points: list[tuple[float, float]] = [(start_x, start_y)]

    for index in range(0, snake_length):
        angle = perlin_factory.get_plain_noise(
            ((1 / (snake_length + 1)) * (index + 1)) + perlin_lookup_vertical_shift
        ) * ANGLE_RANGE
        current_point = points[index]
        segment_length = random.randint(segment_length_range[0], segment_length_range[1])
        points.append((
            current_point[X] + segment_length * math.cos(angle),
            current_point[Y] + segment_length * math.sin(angle)
        ))

    # normalize bounds
    min_dimensions: list[float] = [start_x, start_y]
    max_dimensions: list[float] = [start_x, start_y]
    for point in points:
        min_dimensions[X] = min(point[X], min_dimensions[X])
        min_dimensions[Y] = min(point[Y], min_dimensions[Y])
        max_dimensions[X] = max(point[X], max_dimensions[X])
        max_dimensions[Y] = max(point[Y], max_dimensions[Y])

    # shift towards middle
    dimension_range = (max_dimensions[X] - min_dimensions[X], max_dimensions[Y] - min_dimensions[Y])
    shift = (
        image_dimensions[X] / 2 - (dimension_range[X] / 2 + min_dimensions[X]),
        image_dimensions[Y] / 2 - (dimension_range[Y] / 2 + min_dimensions[Y])
    )

    image = Image.new(mode="RGB", size=image_dimensions, color=bg_color)
    draw = ImageDraw(image)
    for index in range(1, len(points)):
        point = points[index]
        previous = points[index - 1]
        draw.line(
            (
                shift[X] + previous[X],
                shift[Y] + previous[Y],
                shift[X] + point[X],
                shift[Y] + point[Y]
            ),
            width=snake_width,
            fill=snake_color
        )
    if text is not None:
        draw.multiline_text(text_position, text, fill=text_color)
    del draw
    return image


def frame_to_png_bytes(image: Image) -> io.BytesIO:
    """Convert image to byte stream."""
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    return stream


log = logging.getLogger(__name__)
START_EMOJI = "\u2611"     # :ballot_box_with_check: - Start the game
CANCEL_EMOJI = "\u274C"    # :x: - Cancel or leave the game
ROLL_EMOJI = "\U0001F3B2"  # :game_die: - Roll the die!
JOIN_EMOJI = "\U0001F64B"  # :raising_hand: - Join the game.
STARTUP_SCREEN_EMOJI = [
    JOIN_EMOJI,
    START_EMOJI,
    CANCEL_EMOJI
]
GAME_SCREEN_EMOJI = [
    ROLL_EMOJI,
    CANCEL_EMOJI
]


class SnakeAndLaddersGame:
    """Snakes and Ladders game Cog."""

    def __init__(self, snakes: Cog, context: Context):
        self.snakes = snakes
        self.ctx = context
        self.channel = self.ctx.channel
        self.state = "booting"
        self.started = False
        self.author = self.ctx.author
        self.players = []
        self.player_tiles = {}
        self.round_has_rolled = {}
        self.avatar_images = {}
        self.board = None
        self.positions = None
        self.rolls = []

    async def open_game(self) -> None:
        """
        Create a new Snakes and Ladders game.

        Listen for reactions until players have joined, and the game has been started.
        """
        def startup_event_check(reaction_: Reaction, user_: User | Member) -> bool:
            """Make sure that this reaction is what we want to operate on."""
            return (
                all((
                    reaction_.message.id == startup.id,       # Reaction is on startup message
                    reaction_.emoji in STARTUP_SCREEN_EMOJI,  # Reaction is one of the startup emotes
                    user_.id != self.ctx.bot.user.id,         # Reaction was not made by the bot
                ))
            )

        # Check to see if the bot can remove reactions
        if not self.channel.permissions_for(self.ctx.guild.me).manage_messages:
            log.warning(
                "Unable to start Snakes and Ladders - "
                f"Missing manage_messages permissions in {self.channel}"
            )
            return

        await self._add_player(self.author)
        await self.channel.send(
            "**Snakes and Ladders**: A new game is about to start!",
            file=File(
                str(SNAKE_RESOURCES / "snakes_and_ladders" / "banner.jpg"),
                filename="Snakes and Ladders.jpg"
            )
        )
        startup = await self.channel.send(
            f"Press {JOIN_EMOJI} to participate, and press "
            f"{START_EMOJI} to start the game"
        )
        for emoji in STARTUP_SCREEN_EMOJI:
            await startup.add_reaction(emoji)

        self.state = "waiting"

        while not self.started:
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    "reaction_add",
                    timeout=300,
                    check=startup_event_check
                )
                if reaction.emoji == JOIN_EMOJI:
                    await self.player_join(user)
                elif reaction.emoji == CANCEL_EMOJI:
                    if user == self.author or (self._is_moderator(user) and user not in self.players):
                        # Allow game author or non-playing moderation staff to cancel a waiting game
                        await self.cancel_game()
                        return
                    await self.player_leave(user)
                elif reaction.emoji == START_EMOJI and self.ctx.author == user:
                    self.started = True
                    await self.start_game(user)
                    await startup.delete()
                    break

                await startup.remove_reaction(reaction.emoji, user)

            except asyncio.TimeoutError:
                log.debug("Snakes and Ladders timed out waiting for a reaction")
                await self.cancel_game()
                return  # We're done, no reactions for the last 5 minutes

    async def _add_player(self, user: User | Member) -> None:
        """Add player to game."""
        self.players.append(user)
        self.player_tiles[user.id] = 1

        avatar_bytes = await user.display_avatar.replace(size=PLAYER_ICON_IMAGE_SIZE).read()
        im = Image.open(io.BytesIO(avatar_bytes)).resize((BOARD_PLAYER_SIZE, BOARD_PLAYER_SIZE))
        self.avatar_images[user.id] = im

    async def player_join(self, user: User | Member) -> None:
        """
        Handle players joining the game.

        Prevent player joining if they have already joined, if the game is full, or if the game is
        in a waiting state.
        """
        for p in self.players:
            if user == p:
                await self.channel.send(user.mention + " You are already in the game.", delete_after=10)
                return
        if self.state != "waiting":
            await self.channel.send(user.mention + " You cannot join at this time.", delete_after=10)
            return
        if len(self.players) is MAX_PLAYERS:
            await self.channel.send(user.mention + " The game is full!", delete_after=10)
            return

        await self._add_player(user)

        await self.channel.send(
            f"**Snakes and Ladders**: {user.mention} has joined the game.\n"
            f"There are now {str(len(self.players))} players in the game.",
            delete_after=10
        )

    async def player_leave(self, user: User | Member) -> bool:
        """
        Handle players leaving the game.

        Leaving is prevented if the user wasn't part of the game.

        If the number of players reaches 0, the game is terminated. In this case, a sentinel boolean
        is returned True to prevent a game from continuing after it's destroyed.
        """
        is_surrendered = False  # Sentinel value to assist with stopping a surrendered game
        for p in self.players:
            if user == p:
                self.players.remove(p)
                self.player_tiles.pop(p.id, None)
                self.round_has_rolled.pop(p.id, None)
                await self.channel.send(
                    "**Snakes and Ladders**: " + user.mention + " has left the game.",
                    delete_after=10
                )

                if self.state != "waiting" and len(self.players) == 0:
                    await self.channel.send("**Snakes and Ladders**: The game has been surrendered!")
                    is_surrendered = True
                    self._destruct()

                return is_surrendered
        else:
            await self.channel.send(user.mention + " You are not in the match.", delete_after=10)
            return is_surrendered

    async def cancel_game(self) -> None:
        """Cancel the running game."""
        await self.channel.send("**Snakes and Ladders**: Game has been canceled.")
        self._destruct()

    async def start_game(self, user: User | Member) -> None:
        """
        Allow the game author to begin the game.

        The game cannot be started if the game is in a waiting state.
        """
        if user != self.author:
            await self.channel.send(user.mention + " Only the author of the game can start it.", delete_after=10)
            return

        if self.state != "waiting":
            await self.channel.send(user.mention + " The game cannot be started at this time.", delete_after=10)
            return

        self.state = "starting"
        player_list = ", ".join(user.mention for user in self.players)
        await self.channel.send("**Snakes and Ladders**: The game is starting!\nPlayers: " + player_list)
        await self.start_round()

    async def start_round(self) -> None:
        """Begin the round."""
        def game_event_check(reaction_: Reaction, user_: User | Member) -> bool:
            """Make sure that this reaction is what we want to operate on."""
            return (
                all((
                    reaction_.message.id == self.positions.id,  # Reaction is on positions message
                    reaction_.emoji in GAME_SCREEN_EMOJI,       # Reaction is one of the game emotes
                    user_.id != self.ctx.bot.user.id,           # Reaction was not made by the bot
                ))
            )

        self.state = "roll"
        for user in self.players:
            self.round_has_rolled[user.id] = False
        board_img = Image.open(SNAKE_RESOURCES / "snakes_and_ladders" / "board.jpg")
        player_row_size = math.ceil(MAX_PLAYERS / 2)

        for i, player in enumerate(self.players):
            tile = self.player_tiles[player.id]
            tile_coordinates = self._board_coordinate_from_index(tile)
            x_offset = BOARD_MARGIN[0] + tile_coordinates[0] * BOARD_TILE_SIZE
            y_offset = \
                BOARD_MARGIN[1] + (
                    (10 * BOARD_TILE_SIZE) - (9 - tile_coordinates[1]) * BOARD_TILE_SIZE - BOARD_PLAYER_SIZE)
            x_offset += BOARD_PLAYER_SIZE * (i % player_row_size)
            y_offset -= BOARD_PLAYER_SIZE * math.floor(i / player_row_size)
            board_img.paste(self.avatar_images[player.id],
                            box=(x_offset, y_offset))

        board_file = File(frame_to_png_bytes(board_img), filename="Board.jpg")
        player_list = "\n".join((user.mention + ": Tile " + str(self.player_tiles[user.id])) for user in self.players)

        # Store and send new messages
        temp_board = await self.channel.send(
            "**Snakes and Ladders**: A new round has started! Current board:",
            file=board_file
        )
        temp_positions = await self.channel.send(
            f"**Current positions**:\n{player_list}\n\nUse {ROLL_EMOJI} to roll the dice!"
        )

        # Delete the previous messages
        if self.board and self.positions:
            await self.board.delete()
            await self.positions.delete()

        # remove the roll messages
        for roll in self.rolls:
            await roll.delete()
        self.rolls = []

        # Save new messages
        self.board = temp_board
        self.positions = temp_positions

        # Wait for rolls
        for emoji in GAME_SCREEN_EMOJI:
            await self.positions.add_reaction(emoji)

        is_surrendered = False
        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    "reaction_add",
                    timeout=300,
                    check=game_event_check
                )

                if reaction.emoji == ROLL_EMOJI:
                    await self.player_roll(user)
                elif reaction.emoji == CANCEL_EMOJI:
                    if self._is_moderator(user) and user not in self.players:
                        # Only allow non-playing moderation staff to cancel a running game
                        await self.cancel_game()
                        return
                    is_surrendered = await self.player_leave(user)

                await self.positions.remove_reaction(reaction.emoji, user)

                if self._check_all_rolled():
                    break

            except asyncio.TimeoutError:
                log.debug("Snakes and Ladders timed out waiting for a reaction")
                await self.cancel_game()
                return  # We're done, no reactions for the last 5 minutes

        # Round completed
        # Check to see if the game was surrendered before completing the round, without this
        # sentinel, the game object would be deleted but the next round still posted into purgatory
        if not is_surrendered:
            await self._complete_round()

    async def player_roll(self, user: User | Member) -> None:
        """Handle the player's roll."""
        if user.id not in self.player_tiles:
            await self.channel.send(user.mention + " You are not in the match.", delete_after=10)
            return
        if self.state != "roll":
            await self.channel.send(user.mention + " You may not roll at this time.", delete_after=10)
            return
        if self.round_has_rolled[user.id]:
            return
        roll = random.randint(1, 6)
        self.rolls.append(await self.channel.send(f"{user.mention} rolled a **{roll}**!"))
        next_tile = self.player_tiles[user.id] + roll

        # apply snakes and ladders
        if next_tile in BOARD:
            target = BOARD[next_tile]
            if target < next_tile:
                await self.channel.send(
                    f"{user.mention} slips on a snake and falls back to **{target}**",
                    delete_after=15
                )
            else:
                await self.channel.send(
                    f"{user.mention} climbs a ladder to **{target}**",
                    delete_after=15
                )
            next_tile = target

        self.player_tiles[user.id] = min(100, next_tile)
        self.round_has_rolled[user.id] = True

    async def _complete_round(self) -> None:
        """At the conclusion of a round check to see if there's been a winner."""
        self.state = "post_round"

        # check for winner
        winner = self._check_winner()
        if winner is None:
            # there is no winner, start the next round
            await self.start_round()
            return

        # announce winner and exit
        await self.channel.send("**Snakes and Ladders**: " + winner.mention + " has won the game! :tada:")
        self._destruct()

    def _check_winner(self) -> User | Member:
        """Return a winning member if we're in the post-round state and there's a winner."""
        if self.state != "post_round":
            return None
        return next((player for player in self.players if self.player_tiles[player.id] == 100),
                    None)

    def _check_all_rolled(self) -> bool:
        """Check if all members have made their roll."""
        return all(rolled for rolled in self.round_has_rolled.values())

    def _destruct(self) -> None:
        """Clean up the finished game object."""
        del self.snakes.active_sal[self.channel]

    def _board_coordinate_from_index(self, index: int) -> tuple[int, int]:
        """Convert the tile number to the x/y coordinates for graphical purposes."""
        y_level = 9 - math.floor((index - 1) / 10)
        is_reversed = math.floor((index - 1) / 10) % 2 != 0
        x_level = (index - 1) % 10
        if is_reversed:
            x_level = 9 - x_level
        return x_level, y_level

    @staticmethod
    def _is_moderator(user: User | Member) -> bool:
        """Return True if the user is a Moderator."""
        return any(role.id in MODERATION_ROLES for role in getattr(user, "roles", []))
