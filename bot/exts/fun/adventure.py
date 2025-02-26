# Adventure command from Python bot. 
import asyncio
from contextlib import suppress
import json
from pathlib import Path
from typing import Literal, NamedTuple, TypedDict, Union

from discord import Embed, HTTPException, Message, Reaction, User
from discord.ext import commands
from discord.ext.commands import Cog as DiscordCog, Command, Context
from pydis_core.utils.logging import get_logger

from bot import constants
from bot.bot import Bot


class Cog(NamedTuple):
    """Show information about a Cog's name, description and commands."""

    name: str
    description: str
    commands: list[Command]


log = get_logger(__name__)


class GameInfo(TypedDict):
    """
    A dictionary containing the game information. Used in `available_games.json`.
    """

    id: str
    name: str
    description: str


BASE_PATH = "bot/resources/fun/adventures"

AVAILABLE_GAMES: list[GameInfo] = json.loads(
    Path(f"{BASE_PATH}/available_games.json").read_text("utf8")
)

AVAILABLE_GAMES_DICT = {game["id"]: game for game in AVAILABLE_GAMES}


class OptionData(TypedDict):
    """A dictionary containing the options data of the game. Part of the RoomData dictionary."""

    text: str
    leads_to: str
    emoji: str


class RoomData(TypedDict):
    """A dictionary containing the room data of the game. Part of the AdventureData dictionary."""

    text: str
    options: list[OptionData]


class EndRoomData(TypedDict):
    """
    A dictionary containing the ending room data of the game.

    Variant of the RoomData dictionary, also part of the AdventureData dictionary.
    """

    text: str
    type: Literal["end"]
    emoji: str


class AdventureData(TypedDict):
    """
    A dictionary containing the game data, serialized from a JSON file in `resources/fun/adventures`.

    The keys are the room names, and the values are dictionaries containing the room data, which can be either a RoomData or an EndRoomData.

    There must exist only one "start" key in the dictionary. However, there can be multiple endings, i.e., EndRoomData.
    """

    start: RoomData
    __annotations__: dict[str, Union[RoomData, EndRoomData]]


class GameCodeNotFoundError(ValueError):
    """
    Raised when a GameSession code doesn't exist.
    """

    def __init__(
        self,
        arg: str,
    ) -> None:
        super().__init__(arg)


class GameSession:
    """
    An interactive session for the Adventure RPG game.
    """

    def __init__(
        self,
        ctx: Context,
        game_code: str | None = None,
    ):
        """Creates an instance of the GameSession class."""
        self._ctx = ctx
        self._bot = ctx.bot

        # set the game details/ game codes required for the session
        self.game_code = game_code
        self.game_data = None
        if game_code:
            self.game_data = self._get_game_data(game_code)

        # store relevant discord info
        self.author = ctx.author
        self.destination = ctx.channel
        self.message = None

        # init session states
        self._current_room = "start"
        self._path = [self._current_room]

        # session settings
        self.timeout_message = (
            "Time is running out! You must make a choice within 60 seconds. ⏳"
        )
        self._timeout_task = None
        self.reset_timeout()

    def _get_game_data(self, game_code: str) -> AdventureData | None:
        """Returns the game data for the given game code."""
        try:
            # sanitize the game code to prevent directory traversal attacks.
            game_code = Path(game_code).name
            game_data = json.loads(
                Path(f"{BASE_PATH}/{game_code}.json").read_text("utf8")
            )
            return game_data
        except FileNotFoundError:
            raise GameCodeNotFoundError(f'Game code "{game_code}" not found.')

    async def notify_timeout(self) -> None:
        """Notifies the user that the session has timed out."""
        await self.message.edit(content="⏰ You took too long to make a choice! The game has ended. :(")

    async def timeout(self, seconds: int = 60) -> None:
        """Waits for a set number of seconds, then stops the game session."""
        await asyncio.sleep(seconds)
        await self.notify_timeout()
        await self.stop()

    def cancel_timeout(self) -> None:
        """Cancels the timeout task."""
        if self._timeout_task and not self._timeout_task.cancelled():
            self._timeout_task.cancel()

    def reset_timeout(self) -> None:
        """Cancels the original timeout task and sets it again from the start."""
        self.cancel_timeout()
        
        # recreate the timeout task
        self._timeout_task = self._bot.loop.create_task(self.timeout())

    async def send_available_game_codes(self) -> None:
        """Sends a list of all available game codes."""
        available_game_codes = "\n".join(
            f"{game['id']} - {game['name']}" for game in AVAILABLE_GAMES
        )

        embed = Embed(
            title="Available games",
            description=available_game_codes,
            colour=constants.Colours.soft_red,
        )

        await self.destination.send(embed=embed)
        
    async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
        """Event handler for when reactions are added on the game message."""
        # ensure it was the relevant session message
        if reaction.message.id != self.message.id:
            return

        # ensure it was the session author who reacted
        if user.id != self.author.id:
            return

        emoji = str(reaction.emoji)

        # check if valid action
        current_room = self._current_room
        available_options = self.game_data[current_room]["options"]
        acceptable_emojis = [option["emoji"] for option in available_options]
        if emoji not in acceptable_emojis:
            return

        self.reset_timeout()

        # remove all the reactions to prep for re-use
        with suppress(HTTPException):
            await self.message.clear_reactions()

        # Run relevant action method
        await self.pick_option(acceptable_emojis.index(emoji))


    async def on_message_delete(self, message: Message) -> None:
        """Closes the game session when the game message is deleted."""
        if message.id == self.message.id:
            await self.stop()

    async def prepare(self) -> None:
        """Sets up the game events, message and reactions."""
        if self.game_data:
            await self.update_message("start")
            self._bot.add_listener(self.on_reaction_add)
            self._bot.add_listener(self.on_message_delete)
        else:
            await self.send_available_game_codes()
            

    def add_reactions(self) -> None:
        """Adds the relevant reactions to the message based on if options are available in the current room."""
        if self.is_in_ending_room:
            return
        
        current_room = self._current_room
        available_options = self.game_data[current_room]["options"]
        reactions = [option["emoji"] for option in available_options]

        for reaction in reactions:
            self._bot.loop.create_task(self.message.add_reaction(reaction))

    def _format_room_data(self, room_data: RoomData) -> str:
        """Formats the room data into a string for the embed description."""
        text = room_data["text"]
        options = room_data["options"]

        formatted_options = "\n".join(
            f"{option["emoji"]} {option["text"]}" for option in options
        )

        return f"{text}\n\n{formatted_options}"
    
    def embed_message(self, room_data: RoomData | EndRoomData) -> Embed:
        """Returns an Embed with the requested room data formatted within."""
        embed = Embed()

        current_game_name = AVAILABLE_GAMES_DICT[self.game_code]["name"]

        if self.is_in_ending_room:
            embed.description = room_data["text"]
            emoji = room_data["emoji"]
            embed.set_author(name=f"Game over! {emoji}")
            embed.set_footer(text=f"Thanks for playing - {current_game_name}")
        else:
            embed.description = self._format_room_data(room_data)
            embed.set_author(name=current_game_name)
            embed.set_footer(text=self.timeout_message)

        return embed

    async def update_message(self, room_id: str) -> None:
        """Sends the initial message, or changes the existing one to the given room ID."""
        target_room_data = self.game_data[room_id]
        embed_message = self.embed_message(target_room_data)

        if not self.message:
            self.message = await self.destination.send(embed=embed_message)
        else:
            await self.message.edit(embed=embed_message)

        if self.is_in_ending_room:
            await self.stop()
        else:
            self.add_reactions()

    @classmethod
    async def start(cls, ctx: Context, game_code: str | None = None) -> "GameSession":
        """
        Create and begin a game session based on the given game code.
        """
        session = cls(ctx, game_code)
        await session.prepare()

        return session

    async def stop(self) -> None:
        """Stops the game session, clean up by removing event listeners."""
        self.cancel_timeout()
        self._bot.remove_listener(self.on_reaction_add)
        self._bot.remove_listener(self.on_message_delete)

    @property
    def is_in_ending_room(self) -> bool:
        """Check if the game has ended."""
        current_room = self._current_room

        return self.game_data[current_room].get("type") == "end"

    async def pick_option(self, index: int) -> None:
        """Event that is called when the user picks an option."""
        current_room = self._current_room
        next_room = self.game_data[current_room]["options"][index]["leads_to"]

        # update the path and current room
        self._path.append(next_room)
        self._current_room = next_room

        # update the message with the new room
        await self.update_message(next_room)


class Adventure(DiscordCog):
    """Custom Embed for Adventure RPG games."""

    @commands.command(name="adventure")
    async def new_adventure(self, ctx: Context, game_code: str | None = None) -> None:
        """Wanted to slay a dragon? Embark on an exciting journey through text-based RPG adventure."""
        try:
            await GameSession.start(ctx, game_code)
        except GameCodeNotFoundError as error:
            await ctx.send(str(error))
            return


async def setup(bot: Bot) -> None:
    await bot.add_cog(Adventure(bot))
