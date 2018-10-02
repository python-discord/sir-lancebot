from discord.ext import commands


class Template:
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def template(self, ctx):
      await ctx.send('It indeed is a template cog!')
    

def setup(bot):
    bot.add_cog(Template(bot))
