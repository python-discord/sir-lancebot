import functools
from collections.abc import Mapping
from enum import Enum

from discord import Colour, Embed
from discord.ext import commands
from discord.ext.commands import Context, group
from pydis_core.utils._extensions import unqualify
from pydis_core.utils.logging import get_logger

from bot import exts
from bot.bot import Bot
from bot.constants import Client, Emojis, MODERATION_ROLES, Roles
from bot.utils.checks import with_role_check
from bot.utils.pagination import LinePaginator

log = get_logger(__name__)


UNLOAD_BLACKLIST = {f"{exts.__name__}.core.extensions"}
BASE_PATH_LEN = len(exts.__name__.split("."))


class Action(Enum):
    """Represents an action to perform on an extension."""

    # Need to be partial otherwise they are considered to be function definitions.
    LOAD = functools.partial(Bot.load_extension)
    UNLOAD = functools.partial(Bot.unload_extension)
    RELOAD = functools.partial(Bot.reload_extension)


class Extension(commands.Converter):
    """
    Fully qualify the name of an extension and ensure it exists.

    The * and ** values bypass this when used with the reload command.
    """

    async def convert(self, ctx: Context, argument: str) -> str:
        """Fully qualify the name of an extension and ensure it exists."""
        # Special values to reload all extensions
        if argument == "*" or argument == "**":
            return argument

        argument = argument.lower()

        if argument in ctx.bot.all_extensions:
            return argument
        if (qualified_arg := f"{exts.__name__}.{argument}") in ctx.bot.all_extensions:
            return qualified_arg

        matches = []
        for ext in ctx.bot.all_extensions:
            if argument == unqualify(ext):
                matches.append(ext)

        if len(matches) > 1:
            matches.sort()
            names = "\n".join(matches)
            raise commands.BadArgument(
                f":x: `{argument}` is an ambiguous extension name. "
                f"Please use one of the following fully-qualified names.```\n{names}\n```"
            )
        if matches:
            return matches[0]
        raise commands.BadArgument(f":x: Could not find the extension `{argument}`.")


class Extensions(commands.Cog):
    """Extension management commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name="extensions", aliases=("ext", "exts", "c", "cogs"), invoke_without_command=True)
    async def extensions_group(self, ctx: Context) -> None:
        """Load, unload, reload, and list loaded extensions."""
        await self.bot.invoke_help_command(ctx)

    @extensions_group.command(name="load", aliases=("l",))
    async def load_command(self, ctx: Context, *extensions: Extension) -> None:
        r"""
        Load extensions given their fully qualified or unqualified names.

        If '\*' or '\*\*' is given as the name, all unloaded extensions will be loaded.
        """
        if not extensions:
            await self.bot.invoke_help_command(ctx)
            return

        if "*" in extensions or "**" in extensions:
            extensions = set(self.bot.all_extensions) - set(self.bot.extensions.keys())

        msg = await self.batch_manage(Action.LOAD, *extensions)
        await ctx.send(msg)

    @extensions_group.command(name="unload", aliases=("ul",))
    async def unload_command(self, ctx: Context, *extensions: Extension) -> None:
        r"""
        Unload currently loaded extensions given their fully qualified or unqualified names.

        If '\*' or '\*\*' is given as the name, all loaded extensions will be unloaded.
        """
        if not extensions:
            await self.bot.invoke_help_command(ctx)
            return

        blacklisted = "\n".join(UNLOAD_BLACKLIST & set(extensions))

        if blacklisted:
            msg = f":x: The following extension(s) may not be unloaded:```\n{blacklisted}\n```"
        else:
            if "*" in extensions or "**" in extensions:
                extensions = set(self.bot.extensions.keys()) - UNLOAD_BLACKLIST

            msg = await self.batch_manage(Action.UNLOAD, *extensions)

        await ctx.send(msg)

    @extensions_group.command(name="reload", aliases=("r",), root_aliases=("reload",))
    async def reload_command(self, ctx: Context, *extensions: Extension) -> None:
        r"""
        Reload extensions given their fully qualified or unqualified names.

        If an extension fails to be reloaded, it will be rolled-back to the prior working state.

        If '\*' is given as the name, all currently loaded extensions will be reloaded.
        If '\*\*' is given as the name, all extensions, including unloaded ones, will be reloaded.
        """
        if not extensions:
            await self.bot.invoke_help_command(ctx)
            return

        if "**" in extensions:
            extensions = self.bot.all_extensions
        elif "*" in extensions:
            extensions = set(self.bot.extensions.keys()) | set(extensions)
            extensions.remove("*")

        msg = await self.batch_manage(Action.RELOAD, *extensions)

        await ctx.send(msg)

    @extensions_group.command(name="list", aliases=("all",))
    async def list_command(self, ctx: Context) -> None:
        """
        Get a list of all extensions, including their loaded status.

        Grey indicates that the extension is unloaded.
        Green indicates that the extension is currently loaded.
        """
        embed = Embed(colour=Colour.og_blurple())
        embed.set_author(
            name="Extensions List",
            url=Client.github_repo,
            icon_url=str(self.bot.user.display_avatar.url)
        )

        lines = []
        categories = self.group_extension_statuses()
        for category, extensions in sorted(categories.items()):
            # Treat each category as a single line by concatenating everything.
            # This ensures the paginator will not cut off a page in the middle of a category.
            category = category.replace("_", " ").title()
            extensions = "\n".join(sorted(extensions))
            lines.append(f"**{category}**\n{extensions}\n")

        log.debug(f"{ctx.author} requested a list of all cogs. Returning a paginated list.")
        await LinePaginator.paginate(lines, ctx, embed, max_size=1200, empty=False)

    def group_extension_statuses(self) -> Mapping[str, str]:
        """Return a mapping of extension names and statuses to their categories."""
        categories = {}

        for ext in self.bot.all_extensions:
            if ext in self.bot.extensions:
                status = Emojis.status_online
            else:
                status = Emojis.status_offline

            path = ext.split(".")
            if len(path) > BASE_PATH_LEN + 1:
                category = " - ".join(path[BASE_PATH_LEN:-1])
            else:
                category = "uncategorised"

            categories.setdefault(category, []).append(f"{status}  {path[-1]}")

        return categories

    async def batch_manage(self, action: Action, *extensions: str) -> str:
        """
        Apply an action to multiple extensions and return a message with the results.

        If only one extension is given, it is deferred to `manage()`.
        """
        if len(extensions) == 1:
            msg, _ = await self.manage(action, extensions[0])
            return msg

        verb = action.name.lower()
        failures = {}

        for extension in extensions:
            _, error = await self.manage(action, extension)
            if error:
                failures[extension] = error

        emoji = ":x:" if failures else Emojis.ok_hand
        msg = f"{emoji} {len(extensions) - len(failures)} / {len(extensions)} extensions {verb}ed."

        if failures:
            failures = "\n".join(f"{ext}\n    {err}" for ext, err in failures.items())
            msg += f"\nFailures:```\n{failures}\n```"

        log.debug(f"Batch {verb}ed extensions.")

        return msg

    async def manage(self, action: Action, ext: str) -> tuple[str, str | None]:
        """Apply an action to an extension and return the status message and any error message."""
        verb = action.name.lower()
        error_msg = None

        try:
            await action.value(self.bot, ext)
        except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotLoaded):
            if action is Action.RELOAD:
                # When reloading, just load the extension if it was not loaded.
                return await self.manage(Action.LOAD, ext)

            msg = f":x: Extension `{ext}` is already {verb}ed."
            log.debug(msg[4:])
        except Exception as e:
            if hasattr(e, "original"):
                e = e.original

            log.exception(f"Extension '{ext}' failed to {verb}.")

            error_msg = f"{e.__class__.__name__}: {e}"
            msg = f":x: Failed to {verb} extension `{ext}`:\n```\n{error_msg}\n```"
        else:
            msg = f"{Emojis.ok_hand} Extension successfully {verb}ed: `{ext}`."
            log.debug(msg[10:])

        return msg, error_msg

    # This cannot be static (must have a __func__ attribute).
    def cog_check(self, ctx: Context) -> bool:
        """Only allow moderators and core developers to invoke the commands in this cog."""
        return with_role_check(ctx, *MODERATION_ROLES, Roles.core_developers)

    # This cannot be static (must have a __func__ attribute).
    async def cog_command_error(self, ctx: Context, error: Exception) -> None:
        """Handle BadArgument errors locally to prevent the help command from showing."""
        if isinstance(error, commands.BadArgument):
            await ctx.send(str(error))
            error.handled = True


async def setup(bot: Bot) -> None:
    """Load the Extensions cog."""
    await bot.add_cog(Extensions(bot))
