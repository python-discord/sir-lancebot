import asyncio
import hashlib
import sys
from pathlib import Path
import re

import discord
from discord.ext import commands


FORMATTED_CODE_REGEX = re.compile(
    r"(?P<delim>(?P<block>```)|``?)"        # code delimiter: 1-3 backticks; (?P=block) only matches if it's a block
    r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"    # if we're in a block, match optional language (only letters plus newline)
    r"(?:[ \t]*\n)*"                        # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"                        # extract all code inside the markup
    r"\s*"                                  # any more whitespace before the end of the code markup
    r"(?P=delim)",                          # match the exact same delimiter from the start again
    re.DOTALL | re.IGNORECASE,              # "." also matches newlines, case insensitive
)

THIS_DIR = Path(__file__).parent
CACHE_DIRECTORY = THIS_DIR / "cache"
CACHE_DIRECTORY.mkdir(exist_ok=True)


def _prepare_input(text: str) -> str:
    text = text.replace(r"\\", "$\n$")  # matplotlib uses \n for newlines, not \\

    if match := FORMATTED_CODE_REGEX.match(text):
        return match.group("code")
    else:
        return text


class Latex(commands.Cog):
    """Renders latex."""
    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    async def latex(self, ctx: commands.Context, *, query: str) -> None:
        """Renders the text in latex and sends the image."""
        query = _prepare_input(query)
        query_hash = hashlib.md5(query.encode()).hexdigest()
        image_path = CACHE_DIRECTORY / f"{query_hash}.png"
        async with ctx.typing():
            if not image_path.exists():
                proc = await asyncio.subprocess.create_subprocess_exec(
                    sys.executable,
                    "_renderer.py",
                    query,
                    image_path.relative_to(THIS_DIR),
                    cwd=THIS_DIR,
                    stderr=asyncio.subprocess.PIPE
                )
                return_code = await proc.wait()
                if return_code != 0:
                    image_path.unlink()
                    err = (await proc.stderr.read()).decode()
                    raise commands.BadArgument(err)

            await ctx.send(file=discord.File(image_path, "latex.png"))
