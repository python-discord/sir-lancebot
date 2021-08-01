import asyncio
import colorsys
import logging
import os
import random
import re
import string
import textwrap
import urllib
from functools import partial
from io import BytesIO
from typing import Any, Dict, List, Optional

import async_timeout
from PIL import Image, ImageDraw, ImageFont
from discord import Colour, Embed, File, Member, Message, Reaction
from discord.errors import HTTPException
from discord.ext.commands import Cog, CommandError, Context, bot_has_permissions, group

from bot.bot import Bot
from bot.constants import ERROR_REPLIES, Tokens
from bot.exts.evergreen.snakes import _utils as utils
from bot.exts.evergreen.snakes._converter import Snake
from bot.utils.decorators import locked
from bot.utils.extensions import invoke_help_command

log = logging.getLogger(__name__)


# region: Constants
# Color
SNAKE_COLOR = 0x399600

# Antidote constants
SYRINGE_EMOJI = "\U0001F489"  # :syringe:
PILL_EMOJI = "\U0001F48A"     # :pill:
HOURGLASS_EMOJI = "\u231B"    # :hourglass:
CROSSBONES_EMOJI = "\u2620"   # :skull_crossbones:
ALEMBIC_EMOJI = "\u2697"      # :alembic:
TICK_EMOJI = "\u2705"         # :white_check_mark: - Correct peg, correct hole
CROSS_EMOJI = "\u274C"        # :x: - Wrong peg, wrong hole
BLANK_EMOJI = "\u26AA"        # :white_circle: - Correct peg, wrong hole
HOLE_EMOJI = "\u2B1C"         # :white_square: - Used in guesses
EMPTY_UNICODE = "\u200b"      # literally just an empty space

ANTIDOTE_EMOJI = (
    SYRINGE_EMOJI,
    PILL_EMOJI,
    HOURGLASS_EMOJI,
    CROSSBONES_EMOJI,
    ALEMBIC_EMOJI,
)

# Quiz constants
ANSWERS_EMOJI = {
    "a": "\U0001F1E6",  # :regional_indicator_a: 🇦
    "b": "\U0001F1E7",  # :regional_indicator_b: 🇧
    "c": "\U0001F1E8",  # :regional_indicator_c: 🇨
    "d": "\U0001F1E9",  # :regional_indicator_d: 🇩
}

ANSWERS_EMOJI_REVERSE = {
    "\U0001F1E6": "A",  # :regional_indicator_a: 🇦
    "\U0001F1E7": "B",  # :regional_indicator_b: 🇧
    "\U0001F1E8": "C",  # :regional_indicator_c: 🇨
    "\U0001F1E9": "D",  # :regional_indicator_d: 🇩
}

# Zzzen of pythhhon constant
ZEN = """
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
"""

# Max messages to train snake_chat on
MSG_MAX = 100

# get_snek constants
URL = "https://en.wikipedia.org/w/api.php?"

# snake guess responses
INCORRECT_GUESS = (
    "Nope, that's not what it is.",
    "Not quite.",
    "Not even close.",
    "Terrible guess.",
    "Nnnno.",
    "Dude. No.",
    "I thought everyone knew this one.",
    "Guess you suck at snakes.",
    "Bet you feel stupid now.",
    "Hahahaha, no.",
    "Did you hit the wrong key?"
)

CORRECT_GUESS = (
    "**WRONG**. Wait, no, actually you're right.",
    "Yeah, you got it!",
    "Yep, that's exactly what it is.",
    "Uh-huh. Yep yep yep.",
    "Yeah that's right.",
    "Yup. How did you know that?",
    "Are you a herpetologist?",
    "Sure, okay, but I bet you can't pronounce it.",
    "Are you cheating?"
)

# snake card consts
CARD = {
    "top": Image.open("bot/resources/snakes/snake_cards/card_top.png"),
    "frame": Image.open("bot/resources/snakes/snake_cards/card_frame.png"),
    "bottom": Image.open("bot/resources/snakes/snake_cards/card_bottom.png"),
    "backs": [
        Image.open(f"bot/resources/snakes/snake_cards/backs/{file}")
        for file in os.listdir("bot/resources/snakes/snake_cards/backs")
    ],
    "font": ImageFont.truetype("bot/resources/snakes/snake_cards/expressway.ttf", 20)
}
# endregion


class Snakes(Cog):
    """
    Commands related to snakes, created by our community during the first code jam.

    More information can be found in the code-jam-1 repo.

    https://github.com/python-discord/code-jam-1
    """

    wiki_brief = re.compile(r"(.*?)(=+ (.*?) =+)", flags=re.DOTALL)
    valid_image_extensions = ("gif", "png", "jpeg", "jpg", "webp")

    def __init__(self, bot: Bot):
        self.active_sal = {}
        self.bot = bot
        self.snake_names = utils.get_resource("snake_names")
        self.snake_idioms = utils.get_resource("snake_idioms")
        self.snake_quizzes = utils.get_resource("snake_quiz")
        self.snake_facts = utils.get_resource("snake_facts")
        self.num_movie_pages = None

    # region: Helper methods
    @staticmethod
    def _beautiful_pastel(hue: float) -> int:
        """Returns random bright pastels."""
        light = random.uniform(0.7, 0.85)
        saturation = 1

        rgb = colorsys.hls_to_rgb(hue, light, saturation)
        hex_rgb = ""

        for part in rgb:
            value = int(part * 0xFF)
            hex_rgb += f"{value:02x}"

        return int(hex_rgb, 16)

    @staticmethod
    def _generate_card(buffer: BytesIO, content: dict) -> BytesIO:
        """
        Generate a card from snake information.

        Written by juan and Someone during the first code jam.
        """
        snake = Image.open(buffer)

        # Get the size of the snake icon, configure the height of the image box (yes, it changes)
        icon_width = 347  # Hardcoded, not much i can do about that
        icon_height = int((icon_width / snake.width) * snake.height)
        frame_copies = icon_height // CARD["frame"].height + 1
        snake.thumbnail((icon_width, icon_height))

        # Get the dimensions of the final image
        main_height = icon_height + CARD["top"].height + CARD["bottom"].height
        main_width = CARD["frame"].width

        # Start creating the foreground
        foreground = Image.new("RGBA", (main_width, main_height), (0, 0, 0, 0))
        foreground.paste(CARD["top"], (0, 0))

        # Generate the frame borders to the correct height
        for offset in range(frame_copies):
            position = (0, CARD["top"].height + offset * CARD["frame"].height)
            foreground.paste(CARD["frame"], position)

        # Add the image and bottom part of the image
        foreground.paste(snake, (36, CARD["top"].height))  # Also hardcoded :(
        foreground.paste(CARD["bottom"], (0, CARD["top"].height + icon_height))

        # Setup the background
        back = random.choice(CARD["backs"])
        back_copies = main_height // back.height + 1
        full_image = Image.new("RGBA", (main_width, main_height), (0, 0, 0, 0))

        # Generate the tiled background
        for offset in range(back_copies):
            full_image.paste(back, (16, 16 + offset * back.height))

        # Place the foreground onto the final image
        full_image.paste(foreground, (0, 0), foreground)

        # Get the first two sentences of the info
        description = ".".join(content["info"].split(".")[:2]) + "."

        # Setup positioning variables
        margin = 36
        offset = CARD["top"].height + icon_height + margin

        # Create blank rectangle image which will be behind the text
        rectangle = Image.new(
            "RGBA",
            (main_width, main_height),
            (0, 0, 0, 0)
        )

        # Draw a semi-transparent rectangle on it
        rect = ImageDraw.Draw(rectangle)
        rect.rectangle(
            (margin, offset, main_width - margin, main_height - margin),
            fill=(63, 63, 63, 128)
        )

        # Paste it onto the final image
        full_image.paste(rectangle, (0, 0), mask=rectangle)

        # Draw the text onto the final image
        draw = ImageDraw.Draw(full_image)
        for line in textwrap.wrap(description, 36):
            draw.text([margin + 4, offset], line, font=CARD["font"])
            offset += CARD["font"].getsize(line)[1]

        # Get the image contents as a BufferIO object
        buffer = BytesIO()
        full_image.save(buffer, "PNG")
        buffer.seek(0)

        return buffer

    @staticmethod
    def _snakify(message: str) -> str:
        """Sssnakifffiesss a sstring."""
        # Replace fricatives with exaggerated snake fricatives.
        simple_fricatives = [
            "f", "s", "z", "h",
            "F", "S", "Z", "H",
        ]
        complex_fricatives = [
            "th", "sh", "Th", "Sh"
        ]

        for letter in simple_fricatives:
            if letter.islower():
                message = message.replace(letter, letter * random.randint(2, 4))
            else:
                message = message.replace(letter, (letter * random.randint(2, 4)).title())

        for fricative in complex_fricatives:
            message = message.replace(fricative, fricative[0] + fricative[1] * random.randint(2, 4))

        return message

    async def _fetch(self, url: str, params: Optional[dict] = None) -> dict:
        """Asynchronous web request helper method."""
        if params is None:
            params = {}

        async with async_timeout.timeout(10):
            async with self.bot.http_session.get(url, params=params) as response:
                return await response.json()

    def _get_random_long_message(self, messages: List[str], retries: int = 10) -> str:
        """
        Fetch a message that's at least 3 words long, if possible to do so in retries attempts.

        Else, just return whatever the last message is.
        """
        long_message = random.choice(messages)
        if len(long_message.split()) < 3 and retries > 0:
            return self._get_random_long_message(
                messages,
                retries=retries - 1
            )

        return long_message

    async def _get_snek(self, name: str) -> Dict[str, Any]:
        """
        Fetches all the data from a wikipedia article about a snake.

        Builds a dict that the .get() method can use.

        Created by Ava and eivl.
        """
        snake_info = {}

        params = {
            "format": "json",
            "action": "query",
            "list": "search",
            "srsearch": name,
            "utf8": "",
            "srlimit": "1",
        }

        json = await self._fetch(URL, params=params)

        # Wikipedia does have a error page
        try:
            pageid = json["query"]["search"][0]["pageid"]
        except KeyError:
            # Wikipedia error page ID(?)
            pageid = 41118
        except IndexError:
            return None

        params = {
            "format": "json",
            "action": "query",
            "prop": "extracts|images|info",
            "exlimit": "max",
            "explaintext": "",
            "inprop": "url",
            "pageids": pageid
        }

        json = await self._fetch(URL, params=params)

        # Constructing dict - handle exceptions later
        try:
            snake_info["title"] = json["query"]["pages"][f"{pageid}"]["title"]
            snake_info["extract"] = json["query"]["pages"][f"{pageid}"]["extract"]
            snake_info["images"] = json["query"]["pages"][f"{pageid}"]["images"]
            snake_info["fullurl"] = json["query"]["pages"][f"{pageid}"]["fullurl"]
            snake_info["pageid"] = json["query"]["pages"][f"{pageid}"]["pageid"]
        except KeyError:
            snake_info["error"] = True

        if snake_info["images"]:
            i_url = "https://commons.wikimedia.org/wiki/Special:FilePath/"
            image_list = []
            map_list = []
            thumb_list = []

            # Wikipedia has arbitrary images that are not snakes
            banned = [
                "Commons-logo.svg",
                "Red%20Pencil%20Icon.png",
                "distribution",
                "The%20Death%20of%20Cleopatra%20arthur.jpg",
                "Head%20of%20holotype",
                "locator",
                "Woma.png",
                "-map.",
                ".svg",
                "ange.",
                "Adder%20(PSF).png"
            ]

            for image in snake_info["images"]:
                # Images come in the format of `File:filename.extension`
                file, sep, filename = image["title"].partition(":")
                filename = filename.replace(" ", "%20")  # Wikipedia returns good data!

                if not filename.startswith("Map"):
                    if any(ban in filename for ban in banned):
                        pass
                    else:
                        image_list.append(f"{i_url}{filename}")
                        thumb_list.append(f"{i_url}{filename}?width=100")
                else:
                    map_list.append(f"{i_url}{filename}")

        snake_info["image_list"] = image_list
        snake_info["map_list"] = map_list
        snake_info["thumb_list"] = thumb_list
        snake_info["name"] = name

        match = self.wiki_brief.match(snake_info["extract"])
        info = match.group(1) if match else None

        if info:
            info = info.replace("\n", "\n\n")  # Give us some proper paragraphs.

        snake_info["info"] = info

        return snake_info

    async def _get_snake_name(self) -> Dict[str, str]:
        """Gets a random snake name."""
        return random.choice(self.snake_names)

    async def _validate_answer(self, ctx: Context, message: Message, answer: str, options: list) -> None:
        """Validate the answer using a reaction event loop."""
        def predicate(reaction: Reaction, user: Member) -> bool:
            """Test if the the answer is valid and can be evaluated."""
            return (
                reaction.message.id == message.id                  # The reaction is attached to the question we asked.
                and user == ctx.author                             # It's the user who triggered the quiz.
                and str(reaction.emoji) in ANSWERS_EMOJI.values()  # The reaction is one of the options.
            )

        for emoji in ANSWERS_EMOJI.values():
            await message.add_reaction(emoji)

        # Validate the answer
        try:
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=45.0, check=predicate)
        except asyncio.TimeoutError:
            await ctx.send(f"You took too long. The correct answer was **{options[answer]}**.")
            await message.clear_reactions()
            return

        if str(reaction.emoji) == ANSWERS_EMOJI[answer]:
            await ctx.send(f"{random.choice(CORRECT_GUESS)} The correct answer was **{options[answer]}**.")
        else:
            await ctx.send(
                f"{random.choice(INCORRECT_GUESS)} The correct answer was **{options[answer]}**."
            )

        await message.clear_reactions()
    # endregion

    # region: Commands
    @group(name="snakes", aliases=("snake",), invoke_without_command=True)
    async def snakes_group(self, ctx: Context) -> None:
        """Commands from our first code jam."""
        await invoke_help_command(ctx)

    @bot_has_permissions(manage_messages=True)
    @snakes_group.command(name="antidote")
    @locked()
    async def antidote_command(self, ctx: Context) -> None:
        """
        Antidote! Can you create the antivenom before the patient dies?

        Rules:  You have 4 ingredients for each antidote, you only have 10 attempts
                Once you synthesize the antidote, you will be presented with 4 markers
                Tick: This means you have a CORRECT ingredient in the CORRECT position
                Circle: This means you have a CORRECT ingredient in the WRONG position
                Cross: This means you have a WRONG ingredient in the WRONG position

        Info:   The game automatically ends after 5 minutes inactivity.
                You should only use each ingredient once.

        This game was created by Lord Bisk and Runew0lf.
        """
        def predicate(reaction_: Reaction, user_: Member) -> bool:
            """Make sure that this reaction is what we want to operate on."""
            return (
                all((
                    # Reaction is on this message
                    reaction_.message.id == board_id.id,
                    # Reaction is one of the pagination emotes
                    reaction_.emoji in ANTIDOTE_EMOJI,
                    # Reaction was not made by the Bot
                    user_.id != self.bot.user.id,
                    # Reaction was made by author
                    user_.id == ctx.author.id
                ))
            )

        # Initialize variables
        antidote_tries = 0
        antidote_guess_count = 0
        antidote_guess_list = []
        guess_result = []
        board = []
        page_guess_list = []
        page_result_list = []
        win = False

        antidote_embed = Embed(color=SNAKE_COLOR, title="Antidote")
        antidote_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        # Generate answer
        antidote_answer = list(ANTIDOTE_EMOJI)  # Duplicate list, not reference it
        random.shuffle(antidote_answer)
        antidote_answer.pop()

        # Begin initial board building
        for i in range(0, 10):
            page_guess_list.append(f"{HOLE_EMOJI} {HOLE_EMOJI} {HOLE_EMOJI} {HOLE_EMOJI}")
            page_result_list.append(f"{CROSS_EMOJI} {CROSS_EMOJI} {CROSS_EMOJI} {CROSS_EMOJI}")
            board.append(
                f"`{i+1:02d}` "
                f"{page_guess_list[i]} - "
                f"{page_result_list[i]}"
            )
            board.append(EMPTY_UNICODE)
        antidote_embed.add_field(name="10 guesses remaining", value="\n".join(board))
        board_id = await ctx.send(embed=antidote_embed)  # Display board

        # Add our player reactions
        for emoji in ANTIDOTE_EMOJI:
            await board_id.add_reaction(emoji)

        # Begin main game loop
        while not win and antidote_tries < 10:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add", timeout=300, check=predicate)
            except asyncio.TimeoutError:
                log.debug("Antidote timed out waiting for a reaction")
                break  # We're done, no reactions for the last 5 minutes

            if antidote_tries < 10:
                if antidote_guess_count < 4:
                    if reaction.emoji in ANTIDOTE_EMOJI:
                        antidote_guess_list.append(reaction.emoji)
                        antidote_guess_count += 1

                    if antidote_guess_count == 4:  # Guesses complete
                        antidote_guess_count = 0
                        page_guess_list[antidote_tries] = " ".join(antidote_guess_list)

                        # Now check guess
                        for i in range(0, len(antidote_answer)):
                            if antidote_guess_list[i] == antidote_answer[i]:
                                guess_result.append(TICK_EMOJI)
                            elif antidote_guess_list[i] in antidote_answer:
                                guess_result.append(BLANK_EMOJI)
                            else:
                                guess_result.append(CROSS_EMOJI)
                        guess_result.sort()
                        page_result_list[antidote_tries] = " ".join(guess_result)

                        # Rebuild the board
                        board = []
                        for i in range(0, 10):
                            board.append(f"`{i+1:02d}` "
                                         f"{page_guess_list[i]} - "
                                         f"{page_result_list[i]}")
                            board.append(EMPTY_UNICODE)

                        # Remove Reactions
                        for emoji in antidote_guess_list:
                            await board_id.remove_reaction(emoji, user)

                        if antidote_guess_list == antidote_answer:
                            win = True

                        antidote_tries += 1
                        guess_result = []
                        antidote_guess_list = []

                        antidote_embed.clear_fields()
                        antidote_embed.add_field(name=f"{10 - antidote_tries} "
                                                      f"guesses remaining",
                                                 value="\n".join(board))
                        # Redisplay the board
                        await board_id.edit(embed=antidote_embed)

        # Winning / Ending Screen
        if win is True:
            antidote_embed = Embed(color=SNAKE_COLOR, title="Antidote")
            antidote_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            antidote_embed.set_image(url="https://i.makeagif.com/media/7-12-2015/Cj1pts.gif")
            antidote_embed.add_field(name="You have created the snake antidote!",
                                     value=f"The solution was: {' '.join(antidote_answer)}\n"
                                           f"You had {10 - antidote_tries} tries remaining.")
            await board_id.edit(embed=antidote_embed)
        else:
            antidote_embed = Embed(color=SNAKE_COLOR, title="Antidote")
            antidote_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            antidote_embed.set_image(url="https://media.giphy.com/media/ceeN6U57leAhi/giphy.gif")
            antidote_embed.add_field(
                name=EMPTY_UNICODE,
                value=(
                    f"Sorry you didnt make the antidote in time.\n"
                    f"The formula was {' '.join(antidote_answer)}"
                )
            )
            await board_id.edit(embed=antidote_embed)

        log.debug("Ending pagination and removing all reactions...")
        await board_id.clear_reactions()

    @snakes_group.command(name="draw")
    async def draw_command(self, ctx: Context) -> None:
        """
        Draws a random snek using Perlin noise.

        Written by Momo and kel.
        Modified by juan and lemon.
        """
        with ctx.typing():

            # Generate random snake attributes
            width = random.randint(6, 10)
            length = random.randint(15, 22)
            random_hue = random.random()
            snek_color = self._beautiful_pastel(random_hue)
            text_color = self._beautiful_pastel((random_hue + 0.5) % 1)
            bg_color = (
                random.randint(32, 50),
                random.randint(32, 50),
                random.randint(50, 70),
            )

            # Build and send the snek
            text = random.choice(self.snake_idioms)["idiom"]
            factory = utils.PerlinNoiseFactory(dimension=1, octaves=2)
            image_frame = utils.create_snek_frame(
                factory,
                snake_width=width,
                snake_length=length,
                snake_color=snek_color,
                text=text,
                text_color=text_color,
                bg_color=bg_color
            )
            png_bytes = utils.frame_to_png_bytes(image_frame)
            file = File(png_bytes, filename="snek.png")
            await ctx.send(file=file)

    @snakes_group.command(name="get")
    @bot_has_permissions(manage_messages=True)
    @locked()
    async def get_command(self, ctx: Context, *, name: Snake = None) -> None:
        """
        Fetches information about a snake from Wikipedia.

        Created by Ava and eivl.
        """
        with ctx.typing():
            if name is None:
                name = await Snake.random()

            if isinstance(name, dict):
                data = name
            else:
                data = await self._get_snek(name)

            if data.get("error"):
                await ctx.send("Could not fetch data from Wikipedia.")
                return

            description = data["info"]

            # Shorten the description if needed
            if len(description) > 1000:
                description = description[:1000]
                last_newline = description.rfind("\n")
                if last_newline > 0:
                    description = description[:last_newline]

            # Strip and add the Wiki link.
            if "fullurl" in data:
                description = description.strip("\n")
                description += f"\n\nRead more on [Wikipedia]({data['fullurl']})"

            # Build and send the embed.
            embed = Embed(
                title=data.get("title", data.get("name")),
                description=description,
                colour=0x59982F,
            )

            emoji = "https://emojipedia-us.s3.amazonaws.com/thumbs/60/google/3/snake_1f40d.png"

            _iter = (
                url
                for url in data["image_list"]
                if url.endswith(self.valid_image_extensions)
            )
            image = next(_iter, emoji)

            embed.set_image(url=image)

            await ctx.send(embed=embed)

    @snakes_group.command(name="guess", aliases=("identify",))
    @locked()
    async def guess_command(self, ctx: Context) -> None:
        """
        Snake identifying game.

        Made by Ava and eivl.
        Modified by lemon.
        """
        with ctx.typing():

            image = None

            while image is None:
                snakes = [await Snake.random() for _ in range(4)]
                snake = random.choice(snakes)
                answer = "abcd"[snakes.index(snake)]

                data = await self._get_snek(snake)

                _iter = (
                    url
                    for url in data["image_list"]
                    if url.endswith(self.valid_image_extensions)
                )
                image = next(_iter, None)

            embed = Embed(
                title="Which of the following is the snake in the image?",
                description="\n".join(
                    f"{'ABCD'[snakes.index(snake)]}: {snake}" for snake in snakes),
                colour=SNAKE_COLOR
            )
            embed.set_image(url=image)

        guess = await ctx.send(embed=embed)
        options = {f"{'abcd'[snakes.index(snake)]}": snake for snake in snakes}
        await self._validate_answer(ctx, guess, answer, options)

    @snakes_group.command(name="hatch")
    async def hatch_command(self, ctx: Context) -> None:
        """
        Hatches your personal snake.

        Written by Momo and kel.
        """
        # Pick a random snake to hatch.
        snake_name = random.choice(list(utils.snakes.keys()))
        snake_image = utils.snakes[snake_name]

        # Hatch the snake
        message = await ctx.send(embed=Embed(description="Hatching your snake :snake:..."))
        await asyncio.sleep(1)

        for stage in utils.stages:
            hatch_embed = Embed(description=stage)
            await message.edit(embed=hatch_embed)
            await asyncio.sleep(1)
        await asyncio.sleep(1)
        await message.delete()

        # Build and send the embed.
        my_snake_embed = Embed(description=":tada: Congrats! You hatched: **{0}**".format(snake_name))
        my_snake_embed.set_thumbnail(url=snake_image)
        my_snake_embed.set_footer(
            text=" Owner: {0}#{1}".format(ctx.author.name, ctx.author.discriminator)
        )

        await ctx.send(embed=my_snake_embed)

    @snakes_group.command(name="movie")
    async def movie_command(self, ctx: Context) -> None:
        """
        Gets a random snake-related movie from TMDB.

        Written by Samuel.
        Modified by gdude.
        Modified by Will Da Silva.
        """
        # Initially 8 pages are fetched. The actual number of pages is set after the first request.
        page = random.randint(1, self.num_movie_pages or 8)

        async with ctx.typing():
            response = await self.bot.http_session.get(
                "https://api.themoviedb.org/3/search/movie",
                params={
                    "query": "snake",
                    "page": page,
                    "language": "en-US",
                    "api_key": Tokens.tmdb,
                }
            )
            data = await response.json()
            if self.num_movie_pages is None:
                self.num_movie_pages = data["total_pages"]
            movie = random.choice(data["results"])["id"]

            response = await self.bot.http_session.get(
                f"https://api.themoviedb.org/3/movie/{movie}",
                params={
                    "language": "en-US",
                    "api_key": Tokens.tmdb,
                }
            )
            data = await response.json()

        embed = Embed(title=data["title"], color=SNAKE_COLOR)

        if data["poster_path"] is not None:
            embed.set_image(url=f"https://images.tmdb.org/t/p/original{data['poster_path']}")

        if data["overview"]:
            embed.add_field(name="Overview", value=data["overview"])

        if data["release_date"]:
            embed.add_field(name="Release Date", value=data["release_date"])

        if data["genres"]:
            embed.add_field(name="Genres", value=", ".join([x["name"] for x in data["genres"]]))

        if data["vote_count"]:
            embed.add_field(name="Rating", value=f"{data['vote_average']}/10 ({data['vote_count']} votes)", inline=True)

        if data["budget"] and data["revenue"]:
            embed.add_field(name="Budget", value=data["budget"], inline=True)
            embed.add_field(name="Revenue", value=data["revenue"], inline=True)

        embed.set_footer(text="This product uses the TMDb API but is not endorsed or certified by TMDb.")
        embed.set_thumbnail(url="https://i.imgur.com/LtFtC8H.png")

        try:
            await ctx.send(embed=embed)
        except HTTPException as err:
            await ctx.send("An error occurred while fetching a snake-related movie!")
            raise err from None

    @snakes_group.command(name="quiz")
    @locked()
    async def quiz_command(self, ctx: Context) -> None:
        """
        Asks a snake-related question in the chat and validates the user's guess.

        This was created by Mushy and Cardium,
        and modified by Urthas and lemon.
        """
        # Prepare a question.
        question = random.choice(self.snake_quizzes)
        answer = question["answerkey"]
        options = {key: question["options"][key] for key in ANSWERS_EMOJI.keys()}

        # Build and send the embed.
        embed = Embed(
            color=SNAKE_COLOR,
            title=question["question"],
            description="\n".join(
                [f"**{key.upper()}**: {answer}" for key, answer in options.items()]
            )
        )

        quiz = await ctx.send(embed=embed)
        await self._validate_answer(ctx, quiz, answer, options)

    @snakes_group.command(name="name", aliases=("name_gen",))
    async def name_command(self, ctx: Context, *, name: str = None) -> None:
        """
        Snakifies a username.

        Slices the users name at the last vowel (or second last if the name
        ends with a vowel), and then combines it with a random snake name,
        which is sliced at the first vowel (or second if the name starts with
        a vowel).

        If the name contains no vowels, it just appends the snakename
        to the end of the name.

        Examples:
            lemon + anaconda = lemoconda
            krzsn + anaconda = krzsnconda
            gdude + anaconda = gduconda
            aperture + anaconda = apertuconda
            lucy + python = luthon
            joseph + taipan = joseipan

        This was written by Iceman, and modified for inclusion into the bot by lemon.
        """
        snake_name = await self._get_snake_name()
        snake_name = snake_name["name"]
        snake_prefix = ""

        # Set aside every word in the snake name except the last.
        if " " in snake_name:
            snake_prefix = " ".join(snake_name.split()[:-1])
            snake_name = snake_name.split()[-1]

        # If no name is provided, use whoever called the command.
        if name:
            user_name = name
        else:
            user_name = ctx.author.display_name

        # Get the index of the vowel to slice the username at
        user_slice_index = len(user_name)
        for index, char in enumerate(reversed(user_name)):
            if index == 0:
                continue
            if char.lower() in "aeiouy":
                user_slice_index -= index
                break

        # Now, get the index of the vowel to slice the snake_name at
        snake_slice_index = 0
        for index, char in enumerate(snake_name):
            if index == 0:
                continue
            if char.lower() in "aeiouy":
                snake_slice_index = index + 1
                break

        # Combine!
        snake_name = snake_name[snake_slice_index:]
        user_name = user_name[:user_slice_index]
        result = f"{snake_prefix} {user_name}{snake_name}"
        result = string.capwords(result)

        # Embed and send
        embed = Embed(
            title="Snake name",
            description=f"Your snake-name is **{result}**",
            color=SNAKE_COLOR
        )

        await ctx.send(embed=embed)
        return

    @snakes_group.command(name="sal")
    @locked()
    async def sal_command(self, ctx: Context) -> None:
        """
        Play a game of Snakes and Ladders.

        Written by Momo and kel.
        Modified by lemon.
        """
        # Check if there is already a game in this channel
        if ctx.channel in self.active_sal:
            await ctx.send(f"{ctx.author.mention} A game is already in progress in this channel.")
            return

        game = utils.SnakeAndLaddersGame(snakes=self, context=ctx)
        self.active_sal[ctx.channel] = game

        await game.open_game()

    @snakes_group.command(name="about")
    async def about_command(self, ctx: Context) -> None:
        """Show an embed with information about the event, its participants, and its winners."""
        contributors = [
            "<@!245270749919576066>",
            "<@!396290259907903491>",
            "<@!172395097705414656>",
            "<@!361708843425726474>",
            "<@!300302216663793665>",
            "<@!210248051430916096>",
            "<@!174588005745557505>",
            "<@!87793066227822592>",
            "<@!211619754039967744>",
            "<@!97347867923976192>",
            "<@!136081839474343936>",
            "<@!263560579770220554>",
            "<@!104749643715387392>",
            "<@!303940835005825024>",
        ]

        embed = Embed(
            title="About the snake cog",
            description=(
                "The features in this cog were created by members of the community "
                "during our first ever "
                "[code jam event](https://pythondiscord.com/pages/code-jams/code-jam-1-snakes-bot/). \n\n"
                "The event saw over 50 participants, who competed to write a discord bot cog with a snake theme over "
                "48 hours. The staff then selected the best features from all the best teams, and made modifications "
                "to ensure they would all work together before integrating them into the community bot.\n\n"
                "It was a tight race, but in the end, <@!104749643715387392> and <@!303940835005825024> "
                f"walked away as grand champions. Make sure you check out `{ctx.prefix}snakes sal`,"
                f"`{ctx.prefix}snakes draw` and `{ctx.prefix}snakes hatch` "
                "to see what they came up with."
            )
        )

        embed.add_field(
            name="Contributors",
            value=(
                ", ".join(contributors)
            )
        )

        await ctx.send(embed=embed)

    @snakes_group.command(name="card")
    async def card_command(self, ctx: Context, *, name: Snake = None) -> None:
        """
        Create an interesting little card from a snake.

        Created by juan and Someone during the first code jam.
        """
        # Get the snake data we need
        if not name:
            name_obj = await self._get_snake_name()
            name = name_obj["scientific"]
            content = await self._get_snek(name)

        elif isinstance(name, dict):
            content = name

        else:
            content = await self._get_snek(name)

        # Make the card
        async with ctx.typing():

            stream = BytesIO()
            async with async_timeout.timeout(10):
                async with self.bot.http_session.get(content["image_list"][0]) as response:
                    stream.write(await response.read())

            stream.seek(0)

            func = partial(self._generate_card, stream, content)
            final_buffer = await self.bot.loop.run_in_executor(None, func)

        # Send it!
        await ctx.send(
            f"A wild {content['name'].title()} appears!",
            file=File(final_buffer, filename=content["name"].replace(" ", "") + ".png")
        )

    @snakes_group.command(name="fact")
    async def fact_command(self, ctx: Context) -> None:
        """
        Gets a snake-related fact.

        Written by Andrew and Prithaj.
        Modified by lemon.
        """
        question = random.choice(self.snake_facts)["fact"]
        embed = Embed(
            title="Snake fact",
            color=SNAKE_COLOR,
            description=question
        )
        await ctx.send(embed=embed)

    @snakes_group.command(name="snakify")
    async def snakify_command(self, ctx: Context, *, message: str = None) -> None:
        """
        How would I talk if I were a snake?

        If `message` is passed, the bot will snakify the message.
        Otherwise, a random message from the user's history is snakified.

        Written by Momo and kel.
        Modified by lemon.
        """
        with ctx.typing():
            embed = Embed()
            user = ctx.author

            if not message:

                # Get a random message from the users history
                messages = []
                async for message in ctx.history(limit=500).filter(
                        lambda msg: msg.author == ctx.author  # Message was sent by author.
                ):
                    messages.append(message.content)

                message = self._get_random_long_message(messages)

            # Set the avatar
            if user.avatar is not None:
                avatar = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}"
            else:
                avatar = ctx.author.default_avatar_url

            # Build and send the embed
            embed.set_author(
                name=f"{user.name}#{user.discriminator}",
                icon_url=avatar,
            )
            embed.description = f"*{self._snakify(message)}*"

            await ctx.send(embed=embed)

    @snakes_group.command(name="video", aliases=("get_video",))
    async def video_command(self, ctx: Context, *, search: str = None) -> None:
        """
        Gets a YouTube video about snakes.

        If `search` is given, a snake with that name will be searched on Youtube.

        Written by Andrew and Prithaj.
        """
        # Are we searching for anything specific?
        if search:
            query = search + " snake"
        else:
            snake = await self._get_snake_name()
            query = snake["name"]

        # Build the URL and make the request
        url = "https://www.googleapis.com/youtube/v3/search"
        response = await self.bot.http_session.get(
            url,
            params={
                "part": "snippet",
                "q": urllib.parse.quote_plus(query),
                "type": "video",
                "key": Tokens.youtube
            }
        )
        response = await response.json()
        data = response.get("items", [])

        # Send the user a video
        if len(data) > 0:
            num = random.randint(0, len(data) - 1)
            youtube_base_url = "https://www.youtube.com/watch?v="
            await ctx.send(
                content=f"{youtube_base_url}{data[num]['id']['videoId']}"
            )
        else:
            log.warning(f"YouTube API error. Full response looks like {response}")

    @snakes_group.command(name="zen")
    async def zen_command(self, ctx: Context) -> None:
        """
        Gets a random quote from the Zen of Python, except as if spoken by a snake.

        Written by Prithaj and Andrew.
        Modified by lemon.
        """
        embed = Embed(
            title="Zzzen of Pythhon",
            color=SNAKE_COLOR
        )

        # Get the zen quote and snakify it
        zen_quote = random.choice(ZEN.splitlines())
        zen_quote = self._snakify(zen_quote)

        # Embed and send
        embed.description = zen_quote
        await ctx.send(
            embed=embed
        )
    # endregion

    # region: Error handlers
    @card_command.error
    async def command_error(self, ctx: Context, error: CommandError) -> None:
        """Local error handler for the Snake Cog."""
        original_error = getattr(error, "original", None)
        if isinstance(original_error, OSError):
            error.handled = True
            embed = Embed()
            embed.colour = Colour.red()
            log.error(f"snake_card encountered an OSError: {error} ({original_error})")
            embed.description = "Could not generate the snake card! Please try again."
            embed.title = random.choice(ERROR_REPLIES)
            await ctx.send(embed=embed)
