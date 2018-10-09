from discord.ext import commands


class Template:

    """
    A template cog that contains examples of commands and command groups.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='repo', aliases=['repository', 'project'], brief='A link to the repository of this bot.')
    async def repository(self, ctx):
        """
        A command to send the hacktoberbot github project
        """
        await ctx.send('https://github.com/discord-python/hacktoberbot')

    @commands.group(name='git', invoke_without_command=True)
    async def github(self, ctx):
        """
        A command group with the name git. You can now create sub-commands such as git commit.
        """

        await ctx.send('Resources to learn **Git**: https://try.github.io/.')

    @github.command()
    async def commit(self, ctx):
        """
        A command that belongs to the git command group. Invoked using git commit.
        """

        await ctx.send('`git commit -m "First commit"` commits tracked changes.')


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Template(bot))
