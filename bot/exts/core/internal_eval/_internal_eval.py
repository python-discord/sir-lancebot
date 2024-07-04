import re
import textwrap

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger
from pydis_core.utils.paste_service import PasteFile, PasteTooLongError, PasteUploadError, send_to_paste_service

from bot.bot import Bot
from bot.constants import Client, Roles
from bot.utils.decorators import with_role

from ._helpers import EvalContext

__all__ = ["InternalEval"]

log = get_logger(__name__)

FORMATTED_CODE_REGEX = re.compile(
    r"(?P<delim>(?P<block>```)|``?)"        # code delimiter: 1-3 backticks; (?P=block) only matches if it's a block
    r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"    # if we're in a block, match optional language (only letters plus newline)
    r"(?:[ \t]*\n)*"                        # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"                        # extract all code inside the markup
    r"\s*"                                  # any more whitespace before the end of the code markup
    r"(?P=delim)",                          # match the exact same delimiter from the start again
    re.DOTALL | re.IGNORECASE               # "." also matches newlines, case insensitive
)

RAW_CODE_REGEX = re.compile(
    r"^(?:[ \t]*\n)*"                       # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"                        # extract all the rest as code
    r"\s*$",                                # any trailing whitespace until the end of the string
    re.DOTALL                               # "." also matches newlines
)

MAX_LENGTH = 99980


class InternalEval(commands.Cog):
    """Top secret code evaluation for admins and owners."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.locals = {}

        if Client.debug:
            self.internal_group.add_check(commands.is_owner().predicate)

    @staticmethod
    def shorten_output(
            output: str,
            max_length: int = 1900,
            placeholder: str = "\n[output truncated]"
    ) -> str:
        """
        Shorten the `output` so it's shorter than `max_length`.

        There are three tactics for this, tried in the following order:
        - Shorten the output on a line-by-line basis
        - Shorten the output on any whitespace character
        - Shorten the output solely on character count
        """
        max_length = max_length - len(placeholder)

        shortened_output = []
        char_count = 0
        for line in output.split("\n"):
            if char_count + len(line) > max_length:
                break
            shortened_output.append(line)
            char_count += len(line) + 1  # account for (possible) line ending

        if shortened_output:
            shortened_output.append(placeholder)
            return "\n".join(shortened_output)

        shortened_output = textwrap.shorten(output, width=max_length, placeholder=placeholder)

        if shortened_output.strip() == placeholder.strip():
            # `textwrap` was unable to find whitespace to shorten on, so it has
            # reduced the output to just the placeholder. Let's shorten based on
            # characters instead.
            shortened_output = output[:max_length] + placeholder

        return shortened_output

    async def _upload_output(self, output: str) -> str | None:
        """Upload `internal eval` output to our pastebin and return the url."""
        data = self.shorten_output(output, max_length=MAX_LENGTH)
        file = PasteFile(content=data, lexer="text")
        try:
            resp = await send_to_paste_service(
                files=[file],
                http_session=self.bot.http_session,
            )
            return resp.link
        except (PasteTooLongError, PasteUploadError):
            log.exception("Failed to upload `internal eval` output to paste service!")
            return None

    async def _send_output(self, ctx: commands.Context, output: str) -> None:
        """Send the `internal eval` output to the command invocation context."""
        upload_message = ""
        if len(output) >= 1980:
            # The output is too long, let's truncate it for in-channel output and
            # upload the complete output to the paste service.
            url = await self._upload_output(output)

            if url:
                upload_message = f"\nFull output here: {url}"
            else:
                upload_message = "\n:warning: Failed to upload full output!"

            output = self.shorten_output(output)

        await ctx.send(f"```py\n{output}\n```{upload_message}")

    async def _eval(self, ctx: commands.Context, code: str) -> None:
        """Evaluate the `code` in the current evaluation context."""
        context_vars = {
            "message": ctx.message,
            "author": ctx.author,
            "channel": ctx.channel,
            "guild": ctx.guild,
            "ctx": ctx,
            "self": self,
            "bot": self.bot,
            "discord": discord,
        }

        eval_context = EvalContext(context_vars, self.locals)

        log.trace("Preparing the evaluation by parsing the AST of the code")
        error = eval_context.prepare_eval(code)

        if error:
            log.trace("The code can't be evaluated due to an error")
            await ctx.send(f"```py\n{error}\n```")
            return

        log.trace("Evaluate the AST we've generated for the evaluation")
        new_locals = await eval_context.run_eval()

        log.trace("Updating locals with those set during evaluation")
        self.locals.update(new_locals)

        log.trace("Sending the formatted output back to the context")
        await self._send_output(ctx, eval_context.format_output())

    @commands.group(name="internal", aliases=("int",))
    @with_role(Roles.admins)
    async def internal_group(self, ctx: commands.Context) -> None:
        """Internal commands. Top secret!"""
        if not ctx.invoked_subcommand:
            await self.bot.invoke_help_command(ctx)

    @internal_group.command(name="eval", aliases=("e",))
    @with_role(Roles.admins)
    async def eval(self, ctx: commands.Context, *, code: str) -> None:
        """Run eval in a REPL-like format."""
        if match := list(FORMATTED_CODE_REGEX.finditer(code)):
            blocks = [block for block in match if block.group("block")]

            if len(blocks) > 1:
                code = "\n".join(block.group("code") for block in blocks)
            else:
                match = match[0] if len(blocks) == 0 else blocks[0]
                code, _, _, _ = match.group("code", "block", "lang", "delim")

        else:
            code = RAW_CODE_REGEX.fullmatch(code).group("code")

        code = textwrap.dedent(code)
        await self._eval(ctx, code)

    @internal_group.command(name="reset", aliases=("clear", "exit", "r", "c"))
    @with_role(Roles.admins)
    async def reset(self, ctx: commands.Context) -> None:
        """Reset the context and locals of the eval session."""
        self.locals = {}
        await ctx.send("The evaluation context was reset.")
