import asyncio
import hashlib
import string
import sys
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import discord
import platformdirs
from PIL import Image
from discord.ext import commands
from pydis_core.utils.logging import get_logger
from pydis_core.utils.paste_service import (
    PasteFile,
    PasteTooLongError,
    PasteUploadError,
    send_to_paste_service,
)

from bot.bot import Bot
from bot.constants import Channels, Typst as Config, WHITELISTED_CHANNELS
from bot.utils.archives import archive_retrieve_file
from bot.utils.codeblocks import prepare_input
from bot.utils.decorators import whitelist_override
from bot.utils.images import crop_background
from bot.utils.typst import compile_typst

log = get_logger(__name__)

PASTEBIN_URL = "https://paste.pythondiscord.com"

THIS_DIR = Path(__file__).parent
# The cache directory used for typst. A temporary subdirectory is made for each invocation,
# which should be cleaned up automatically on success.
CACHE_DIRECTORY = THIS_DIR / "_typst_cache"
CACHE_DIRECTORY.mkdir(exist_ok=True)
TEMPLATE = string.Template(Path("bot/resources/fun/typst_template.typ").read_text())
PACKAGES_INSTALL_STRING = Path("bot/resources/fun/typst_packages.typ").read_text()

# the default typst packages directory.
TYPST_PACKAGES_DIR = platformdirs.user_cache_path("typst") / "packages"

# how many pixels to leave on each side when cropping the image to only the contents. Set to None to disable cropping.
CROP_PADDING: int | None = 10
# commands.max_concurrency limit for .typst
MAX_CONCURRENCY: int = 2
# max time in seconds to allow the typst process to run
TYPST_TIMEOUT: float = 1.0
# memory limit (in bytes) to set via RLIMIT_AS for the child process.
TYPST_MEMORY_LIMIT: int = 200 * 1024**2  # 200MB, which is pretty generous
# max size of the typst output image (before cropping) to allow rather than emitting an error
MAX_RAW_SIZE = 2 * 1024**2  # 2MB
# if set, limits the internal parallelism of the typst subprocess (--jobs argument).
WORKER_JOBS: int | None = None


TYPST_ALLOWED_CHANNNELS = WHITELISTED_CHANNELS + (
    Channels.data_science_and_ai,
    Channels.algos_and_data_structs,
    Channels.python_help,
)


class InvalidTypstError(Exception):
    """Represents an error caused by invalid typst source code."""

    def __init__(self, logs: str | None):
        super().__init__(logs)
        self.logs = logs


class TypstTimeoutError(Exception):
    """Represents an error caused by the Typst rendering taking too long."""


class OutputTooBigError(Exception):
    """Represents an error caused by the Typst output image being too big."""


class EmptyImageError(Exception):
    """Represents an error caused by the output image being empty."""


class TypstWorkerCrashedError(Exception):
    """Represents an error caused by Typst rendering process crashing. This can mean the memory limit was exceeded."""


class Typst(commands.Cog):
    """Renders typst."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def _setup_typst(self) -> None:
        await self._ensure_typst_executable()
        await self._setup_packages()

    async def _ensure_typst_executable(self) -> None:
        path = Path(Config.typst_path).resolve()
        if path.exists():
            if not path.is_file():
                raise ValueError("Typst path exists but doesn't point to a file:", path)
        else:
            log.info("Typst executable not found at '%s', downloading", path)
            await self._download_typst_executable()
        proc = await asyncio.subprocess.create_subprocess_exec(
            path,
            "--version",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        log.info(f"Typst executable reports itself as {stdout.decode('utf-8').strip()!r}.")

    async def _download_typst_executable(self) -> None:
        if not Config.typst_archive_url:
            raise ValueError("Trying to download Typst but the archive URL isn't set")
        async with self.bot.http_session.get(
            Config.typst_archive_url, raise_for_status=True
        ) as response:
            arc_data = await response.read()
        log.info("Retrieved Typst archive, unpacking")
        typst_executable = archive_retrieve_file(
            arc_data,
            filename="typst.exe" if sys.platform == "win32" else "typst",
        )
        log.info("Storing the typst executable on disk")
        exe_path = Path(Config.typst_path)
        exe_path.parent.mkdir(exist_ok=True)
        exe_path.write_bytes(typst_executable)
        exe_path.chmod(0o555)  # read, execute, not write

    async def _setup_packages(self) -> None:
        if TYPST_PACKAGES_DIR.exists():
            return
        log.info(
            f"The Typst package directory '{TYPST_PACKAGES_DIR}' doesn't currently exist; populating allowed packages."
        )
        with TemporaryDirectory(
            prefix="packageinstall", dir=CACHE_DIRECTORY
        ) as tempdir:
            await compile_typst(PACKAGES_INSTALL_STRING, root_path=Path(tempdir))

        if not TYPST_PACKAGES_DIR.exists():
            raise ValueError(
                f"'{TYPST_PACKAGES_DIR}' still doesn't exist after installing packages - "
                "this suggests the packages path is incorrect or no packages were installed."
            )
        num_packages = 0
        for universe in TYPST_PACKAGES_DIR.iterdir():
            num_packages += sum(1 for _ in universe.iterdir())
        log.info(
            f"Installed {num_packages} packages. Locking the packages directory against writes."
        )
        # for security, remove the write permissions from typst packages
        mode = 0o555  # read, execute, not write
        for (
            dirpath,
            dirnames,
            filenames,
        ) in TYPST_PACKAGES_DIR.walk():
            for d in dirnames + filenames:
                (dirpath / d).chmod(mode)
        TYPST_PACKAGES_DIR.chmod(mode)

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
                    image_path.unlink(missing_ok=True)
                    return
                except EmptyImageError:
                    await ctx.send("The output image was empty.")
                    return
                except TypstTimeoutError:
                    await ctx.send(
                        f"Typst rendering took too long (current timeout is {TYPST_TIMEOUT}s)."
                    )
                    image_path.unlink(missing_ok=True)
                    return
                except OutputTooBigError:
                    await ctx.send(
                        f"Typst output was too big (current limit is {MAX_RAW_SIZE/1024**2:.1f}MB.)"
                    )
                    return
                except TypstWorkerCrashedError:
                    log.exception("typst worker crashed")
                    await ctx.send(
                        "Worker process crashed. "
                        f"Perhaps the memory limit of {TYPST_MEMORY_LIMIT/1024**2:.1f}MB was exceeded?"
                    )
                    return
            await ctx.send(file=discord.File(image_path, "typst.png"))

    async def render_typst(
        self, query: str, tempdir_name: str, image_path: Path
    ) -> None:
        """
        Renders the query as Typst to PNG.

        If successful, the processed output is stored in `image_path`.
        `tempdir_name` under cache will be the temporary root directory to be used.
        """
        source = TEMPLATE.substitute(text=query)
        with TemporaryDirectory(prefix=tempdir_name, dir=CACHE_DIRECTORY) as tempdir:
            try:
                async with asyncio.timeout(TYPST_TIMEOUT):
                    res = await compile_typst(
                        source,
                        root_path=Path(tempdir),
                        format="png",
                        mem_rlimit=TYPST_MEMORY_LIMIT,
                        jobs=WORKER_JOBS,
                    )
            except RuntimeError as e:
                raise InvalidTypstError(
                    e.args[0] if e.args else "<no error message emitted>"
                )
            except TimeoutError:
                raise TypstTimeoutError

        raw_img = res.output
        if len(raw_img) > MAX_RAW_SIZE:
            log.debug(
                "Raw image rejected for having size %.1f MB", len(raw_img) / 1024**2
            )
            raise OutputTooBigError

        if CROP_PADDING is None:
            image_path.write_bytes(raw_img)
        else:
            res = crop_background(
                Image.open(BytesIO(raw_img)).convert("RGB"),
                (255, 255, 255),
                pad=CROP_PADDING,
            )
            if res is None:
                raise EmptyImageError
            res.save(image_path)

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
    cog = Typst(bot)
    await cog._setup_typst()
    await bot.add_cog(cog)
