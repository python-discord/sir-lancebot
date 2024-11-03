import asyncio
import hashlib
import string
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger
from pydis_core.utils.paste_service import PasteFile, PasteTooLongError, PasteUploadError, send_to_paste_service

from bot.bot import Bot
from bot.constants import Channels, WHITELISTED_CHANNELS
from bot.utils.codeblocks import prepare_input
from bot.utils.decorators import whitelist_override
from bot.utils.typst import render_typst_worker

log = get_logger(__name__)

PASTEBIN_URL = "https://paste.pythondiscord.com"

THIS_DIR = Path(__file__).parent
# The cache directory used for typst. A temporary subdirectory is made for each invocation,
# which should be cleaned up automatically on success.
CACHE_DIRECTORY = THIS_DIR / "_typst_cache"
CACHE_DIRECTORY.mkdir(exist_ok=True)
TEMPLATE = string.Template(Path("bot/resources/fun/typst_template.typ").read_text())

MAX_CONCURRENCY = 2

TYPST_ALLOWED_CHANNNELS = WHITELISTED_CHANNELS + (
    Channels.data_science_and_ai,
    Channels.algos_and_data_structs,
    Channels.python_help,
)

_EXECUTOR = ProcessPoolExecutor(MAX_CONCURRENCY)


class InvalidTypstError(Exception):
    """Represents an error caused by invalid typst source code."""

    def __init__(self, logs: str | None):
        super().__init__(logs)
        self.logs = logs


class Typst(commands.Cog):
    """Renders typst."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    @commands.max_concurrency(MAX_CONCURRENCY, commands.BucketType.guild, wait=True)
    @whitelist_override(channels=TYPST_ALLOWED_CHANNNELS)
    async def typst(self, ctx: commands.Context, *, query: str) -> None:
        """Renders the text in typst and sends the image."""
        query = prepare_input(query)

        # the hash of the query is used as the tempdir name in the cache,
        # as well as the name for the rendered file.
        query_hash = hashlib.md5(query.encode()).hexdigest()  # noqa: S324
        image_path = CACHE_DIRECTORY / f"{query_hash}.png"
        async with ctx.typing():
            if not image_path.exists():
                try:
                    await self.render_typst(query, query_hash, image_path)
                except InvalidTypstError as err:
                    embed = await self._prepare_error_embed(err)
                    await ctx.send(embed=embed)
                    image_path.unlink()
                    return
            await ctx.send(file=discord.File(image_path, "typst.png"))

    async def render_typst(self, query: str, tempdir_name: str, image_path: Path) -> None:
        """
        Renders the query as Typst.

        Does so by writing it into a file in a temporary directory, storing the output in image_path.
        image_path shouldn't be in that directory or else it will be immediately deleted.
        """
        with TemporaryDirectory(prefix=tempdir_name, dir=CACHE_DIRECTORY) as tempdir:
            source_path = Path(tempdir) / "inp.typ"
            source_path.write_text(TEMPLATE.substitute(text=query), encoding="utf-8")
            try:
                await asyncio.get_event_loop().run_in_executor(
                    _EXECUTOR, render_typst_worker, source_path, image_path
                )
            except RuntimeError as e:
                raise InvalidTypstError(e.args[0] if e.args else "<no error message emitted>")

    async def _prepare_error_embed(
        self, err: InvalidTypstError | None
    ) -> discord.Embed:
        title = "There was some issue rendering your Typst, please retry later."
        if isinstance(err, InvalidTypstError):
            title = "Failed to render input as Typst."

        embed = discord.Embed(title=title)
        embed.description = "No logs available."
        logs = getattr(err, "logs", None)
        if logs:
            logs_paste_url = await self._upload_to_pastebin(logs)
            embed.description = "Couldn't upload logs."
            if logs_paste_url:
                embed.description = f"[View Logs]({logs_paste_url})"
        return embed

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
            log.info("Error when uploading typst output to pastebin. %s", e)
            return None


async def setup(bot: Bot) -> None:
    """Load the Typst Cog."""
    await bot.add_cog(Typst(bot))
