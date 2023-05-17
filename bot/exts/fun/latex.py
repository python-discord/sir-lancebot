import hashlib
import logging
import os
import re
import string
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import discord
from PIL import Image
from aiohttp import client_exceptions, web
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Channels, WHITELISTED_CHANNELS
from bot.utils.decorators import whitelist_override

log = logging.getLogger(__name__)
FORMATTED_CODE_REGEX = re.compile(
    r"(?P<delim>(?P<block>```)|``?)"        # code delimiter: 1-3 backticks; (?P=block) only matches if it's a block
    r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"    # if we're in a block, match optional language (only letters plus newline)
    r"(?:[ \t]*\n)*"                        # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"                        # extract all code inside the markup
    r"\s*"                                  # any more whitespace before the end of the code markup
    r"(?P=delim)",                          # match the exact same delimiter from the start again
    re.DOTALL | re.IGNORECASE,              # "." also matches newlines, case insensitive
)

LATEX_API_URL = os.getenv("LATEX_API_URL", "https://rtex.probablyaweb.site/api/v2")
PASTEBIN_URL = "https://paste.pythondiscord.com"

THIS_DIR = Path(__file__).parent
CACHE_DIRECTORY = THIS_DIR / "_latex_cache"
CACHE_DIRECTORY.mkdir(exist_ok=True)
TEMPLATE = string.Template(Path("bot/resources/fun/latex_template.txt").read_text())

PAD = 10

LATEX_ALLOWED_CHANNNELS = WHITELISTED_CHANNELS + (
    Channels.data_science_and_ai,
    Channels.algos_and_data_structs,
    Channels.python_help,
)


def _prepare_input(text: str) -> str:
    """Extract latex from a codeblock, if it is in one."""
    if match := FORMATTED_CODE_REGEX.match(text):
        return match.group("code")
    return text


def _process_image(data: bytes, out_file: BinaryIO) -> None:
    """Read `data` as an image file, and paste it on a white background."""
    image = Image.open(BytesIO(data)).convert("RGBA")
    width, height = image.size
    background = Image.new("RGBA", (width + 2 * PAD, height + 2 * PAD), "WHITE")

    # paste the image on the background, using the same image as the mask
    # when an RGBA image is passed as the mask, its alpha band is used.
    # this has the effect of skipping pasting the pixels where the image is transparent.
    background.paste(image, (PAD, PAD), image)
    background.save(out_file)


class InvalidLatexError(Exception):
    """Represents an error caused by invalid latex."""

    def __init__(self, logs: str | None):
        super().__init__(logs)
        self.logs = logs


class LatexServerError(Exception):
    """Represents an error raised from Latex rendering server."""

    def __init__(self, logs: str | None):
        super().__init__(logs)
        self.logs = logs

class Latex(commands.Cog):
    """Renders latex."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def _generate_image(self, query: str, out_file: BinaryIO) -> None:
        """Make an API request and save the generated image to cache."""
        payload = {"code": query, "format": "png"}
        try:
            async with self.bot.http_session.post(LATEX_API_URL, data=payload, raise_for_status=True) as response:
                response_json = await response.json()
        except client_exceptions.ClientResponseError:
            raise LatexServerError(None)
        if response_json["status"] != "success":
            raise InvalidLatexError(logs=response_json.get("log"))
        async with self.bot.http_session.get(
            f"{LATEX_API_URL}/{response_json['filename']}",
            raise_for_status=True
        ) as response:
            _process_image(await response.read(), out_file)

    async def _upload_to_pastebin(self, text: str) -> str | None:
        """Uploads `text` to the paste service, returning the url if successful."""
        try:
            async with self.bot.http_session.post(
                PASTEBIN_URL + "/documents",
                data=text,
                raise_for_status=True
            ) as response:
                response_json = await response.json()
            if "key" in response_json:
                return f"{PASTEBIN_URL}/{response_json['key']}.txt?noredirect"
        except web.HTTPClientError as e:
            log.info("Error when uploading latex output to pastebin. %s", e)

    async def _prepare_error_embed(self, title: str, err: Exception | None) -> discord.Embed:
        embed = discord.Embed(title=title)
        embed.description = "No logs available."
        if err is not None and err.logs is not None:
            logs_paste_url = await self._upload_to_pastebin(err.logs)
            embed.description = "Couldn't upload logs."
            if logs_paste_url:
                embed.description = f"[View Logs]({logs_paste_url})"
        return embed

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @whitelist_override(channels=LATEX_ALLOWED_CHANNNELS)
    async def latex(self, ctx: commands.Context, *, query: str) -> None:
        """Renders the text in latex and sends the image."""
        query = _prepare_input(query)

        # the hash of the query is used as the filename in the cache.
        query_hash = hashlib.md5(query.encode()).hexdigest()  # noqa: S324
        image_path = CACHE_DIRECTORY / f"{query_hash}.png"
        async with ctx.typing():
            if not image_path.exists():
                try:
                    with open(image_path, "wb") as out_file:
                        await self._generate_image(TEMPLATE.substitute(text=query), out_file)
                except InvalidLatexError as err:
                    embed = await self._prepare_error_embed("Failed to render input.", err)
                    await ctx.send(embed=embed)
                    image_path.unlink()
                    return
                except LatexServerError as err:
                    embed = await self._prepare_error_embed("Server encountered an issue, please retry later.", err)
                    await ctx.send(embed=embed)
                    image_path.unlink()
                    return
            await ctx.send(file=discord.File(image_path, "latex.png"))


async def setup(bot: Bot) -> None:
    """Load the Latex Cog."""
    await bot.add_cog(Latex(bot))
