import asyncio
import datetime

from discord.ext import commands

from bot.seasons import get_season


class Season:
    """
    A cog for switching seasons.
    """

    def __init__(self, bot):
        self.bot = bot
        self.season = get_season(self.bot, date=datetime.date.today())

    async def on_ready(self):
        await self.season.load()

        while True:
            await asyncio.sleep(86400)  # sleep for 24 hours
            # If the season has changed, load it.
            new_season = get_season(self.bot, date=datetime.date.today())
            if new_season != self.season:
                await self.season.load()

    @commands.command(name="change_season")
    async def change_season(self, ctx, new_season):
        """
        Changes the currently active season on the bot.
        """
        self.season = get_season(self.bot, season_name=new_season)
        await self.season.load()
        await ctx.send(f"Season changed to {new_season}.")


# Required in order to load the cog, use the class name in the add_cog function.
def setup(bot):
    bot.add_cog(Season(bot))
