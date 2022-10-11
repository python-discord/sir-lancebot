from copy import copy
from time import perf_counter

from discord import Message
from discord.ext import commands

from bot.bot import Bot


class TimedCommands(commands.Cog):
    """Time the command execution of a command."""

    @staticmethod
    async def create_execution_context(ctx: commands.Context, command: str) -> commands.Context:
        """Get a new execution context for a command."""
        msg: Message = copy(ctx.message)
        msg.content = f"{ctx.prefix}{command}"

        return await ctx.bot.get_context(msg)

    @commands.command(name="timed", aliases=("time", "t"))
    async def timed(self, ctx: commands.Context, *, command: str) -> None:
        """Time the command execution of a command."""
        new_ctx = await self.create_execution_context(ctx, command)

        ctx.subcontext = new_ctx

        if not ctx.subcontext.command:
            help_command = f"{ctx.prefix}help"
            error = f"The command you are trying to time doesn't exist. Use `{help_command}` for a list of commands."

            await ctx.send(error)
            return

        if new_ctx.command.qualified_name == "timed":
            await ctx.send("You are not allowed to time the execution of the `timed` command.")
            return

        t_start = perf_counter()
        await new_ctx.command.invoke(new_ctx)
        t_end = perf_counter()

        await ctx.send(f"Command execution for `{new_ctx.command}` finished in {(t_end - t_start):.4f} seconds.")


async def setup(bot: Bot) -> None:
    """Load the Timed cog."""
    await bot.add_cog(TimedCommands())
