import asyncio
import random
from typing import Union

import discord
from discord import User
from discord.ext import commands


class MatchMakingAlgo(commands.Cog):
    """Defines the matchmaking algorithm"""
    def __init__(self, bot: commands.Bot) -> None:
        """Creates matchmaking pool"""
        self.bot = bot
        self.matchmaking_pool = []

    async def search_teammate(self) -> Union[User, None]:
        """Looks for a teammate in the matchmaking pool"""
        if self.matchmaking_pool == []:
            await asyncio.sleep(5)
            return await self.search_teammate()
        t = random.choice(self.matchmaking_pool())
        return self.matchmaking_pool.pop(t, None)

    @commands.command()
    async def find_teammate(self, ctx: commands.Context) -> None:
        """Direct command to look for a teammate"""
        self.matchmaking_pool.append(ctx.author)
        embed = discord.Embed(title="Searcing for a teammate...",
                              color=0xFF0000)
        message: discord.Message = await ctx.send(embed=embed)
        teammate = self.search_teammate()
        embed = discord.Embed(title="Teammate found!",
                              color=0x00FF00)
        await message.edit(content=f"Hello {teammate.mention} and"
                                   f"{ctx.user.mention}",
                                   embed=embed)


def setup(bot: commands.Bot) -> None:
    """Setups the bot"""
    bot.add_cog(MatchMakingAlgo(bot))
