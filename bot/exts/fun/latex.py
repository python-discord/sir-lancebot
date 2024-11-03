import hashlib
import os
import string
from pathlib import Path
from typing import BinaryIO

import discord
from aiohttp import client_exceptions
from discord.ext import commands
from pydis_core.utils.logging import get_logger
from pydis_core.utils.paste_service import PasteFile, PasteTooLongError, PasteUploadError, send_to_paste_service

from bot.bot import Bot
from bot.constants import Channels, WHITELISTED_CHANNELS
from bot.utils.codeblocks import prepare_input
from bot.utils.decorators import whitelist_override
from bot.utils.images import process_image

log = get_logger(__name__)


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


class InvalidLatexError(Exception):
    """Represents an error caused by invalid latex."""

    def __init__(self, logs: str | None):
        super().__init__(logs)
        self.logs = logs


class LatexServerError(Exception):
    """Represents an error raised from Latex rendering server."""


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
            raise LatexServerError
        if response_json["status"] != "success":
            raise InvalidLatexError(logs=response_json.get("log"))
        async with self.bot.http_session.get(
            f"{LATEX_API_URL}/{response_json['filename']}",
            raise_for_status=True
        ) as response:
            process_image(await response.read(), out_file, PAD)

    async def _upload_to_pastebin(self, text: str) -> str | None:
        """Uploads `text` to the paste service, returning the url if successful."""
        file = PasteFile(content=text, lexer="text")
        try:
            resp = await send_to_paste_service(
                files=[file],
                http_session=self.bot.http_session,
            )
            return resp.link
        except (PasteTooLongError, PasteUploadError) as e:
            log.info("Error when uploading latex output to pastebin. %s", e)
            return None

    async def _prepare_error_embed(self, err: InvalidLatexError | LatexServerError | None) -> discord.Embed:
        title = "Server encountered an issue, please retry later."
        if isinstance(err, InvalidLatexError):
            title = "Failed to render input."

        embed = discord.Embed(title=title)
        embed.description = "No logs available."
        logs = getattr(err, "logs", None)
        if logs:
            logs_paste_url = await self._upload_to_pastebin(logs)
            embed.description = "Couldn't upload logs."
            if logs_paste_url:
                embed.description = f"[View Logs]({logs_paste_url})"
        return embed

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @whitelist_override(channels=LATEX_ALLOWED_CHANNNELS)
    async def latex(self, ctx: commands.Context, *, query: str) -> None:
        """Renders the text in latex and sends the image."""
        query = prepare_input(query)

        # the hash of the query is used as the filename in the cache.
        query_hash = hashlib.md5(query.encode()).hexdigest()  # noqa: S324
        image_path = CACHE_DIRECTORY / f"{query_hash}.png"
        async with ctx.typing():
            if not image_path.exists():
                try:
                    with open(image_path, "wb") as out_file:
                        await self._generate_image(TEMPLATE.substitute(text=query), out_file)
                except (InvalidLatexError, LatexServerError) as err:
                    embed = await self._prepare_error_embed(err)
                    await ctx.send(embed=embed)
                    image_path.unlink()
                    return
            await ctx.send(file=discord.File(image_path, "latex.png"))


async def setup(bot: Bot) -> None:
    """Load the Latex Cog."""
    await bot.add_cog(Latex(bot))
