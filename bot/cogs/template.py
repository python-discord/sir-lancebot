from os import system


from discord.ext import commands


"""A template cog that contains examples of commands and command groups."""


class Template:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='repo', aliases=['repository', 'project'], brief='A link to the repository of this bot.')
    async def repository(self, ctx):
        await ctx.send('https://github.com/discord-python/hacktoberbot')

    # A command group with the name git. You can now create sub-commands such as git commit.
    @commands.group(name='git', invoke_without_command=True)
    async def github(self, ctx):
        await ctx.send('Resources to learn **Git**: https://try.github.io/.')

    # A command that belongs to the git command group. Invoked using git commit.
    @github.command()
    async def commit(self, ctx):
        system('git commit -m "A huge commit adding many revolutionary features!"')


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Template(bot))
