import discord
from discord.ext import commands
import asyncio
import sys
import traceback
import math


class CommandErrorHandler:
    def __init__(self, bot):
        self.bot = bot
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        error = getattr(error, 'original', error)
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.UserInputError):
            return await ctx.send(
                ":no_entry: The command you specified failed to run.",
                "This is because the arguments you provided were invalid."
            )
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                "This command is on cooldown,",
                "please retry in {}s.".format(math.ceil(error.retry_after))
            )
        if isinstance(error, commands.DisabledCommand):
            return await ctx.send(
                ":no_entry: This command has been disabled."
            )
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(
                    ":no_entry: This command can only be used inside a server."
                )
            except:
                pass
        if isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                return await ctx.send(
                    "I could not find that member. Please try again."
                )
            else:
                return await ctx.send(
                    "The argument you provided was invalid."
                )
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                ":no_entry: You do not have permission to use this command."
            )
        print(
            "Ignoring exception in command {}:".format(ctx.command),
            file=sys.stderr
        )
        traceback.print_exception(
            type(error),
            error,
            error.__traceback__,
            file=sys.stderr
        )


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
