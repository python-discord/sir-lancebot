import logging
import json
from discord.ext import commands
from discord.ext.commands import Bot, Context
import discord
from typing import Optional
import aiohttp
from http import HTTPStatus

log = logging.getLogger(__name__)


class MonsterSurvey:

    def __init__(self, bot: Bot):
        self.bot = Bot
        self._monsters = None

    async def monster_summary(self, monster):
        monster = monster.replace(' ', '_')
        wiki_url = "http://en.wikipedia.org/w/api.php" \
                   "?format=json" \
                   "&action=query" \
                   "&prop=extracts" \
                   "&prop=pageimages" \
                   "&explaintext&exintro" \
                   "&redirects=1" \
                   f"&titles={monster}"
        print(wiki_url)
        async with aiohttp.ClientSession() as session:
            response = await session.get(wiki_url)
            if response.status == HTTPStatus.OK:
                result = json.loads(await response.text())
                return next(iter(result['query']['pages'].values()))['extract']

    @property
    def survey_data(self) -> dict:
        """Get an updated instance of the survey data at all times"""
        with open('../bot/resources/monstersurvey.json', 'r') as f:
            self.monsters = json.load(f)
        return self.monsters

    @commands.group(name='monster', aliases=('ms',), invoke_without_command=True)
    async def monster_group(self, ctx: Context):
        await ctx.invoke(self.bot.get_command(name="help"), 'monstersurvey')

    @monster_group.command(name='vote')
    async def monster_vote(self, ctx: Context, name: Optional[str] = None):
        embed = discord.Embed(name='Vote for your favorite monster')
        if not name:
            for k,v in self.monsters.items():
                msg = f"`!monster show {k}` for more information\n" \
                      f"`!monster vote {k}` to cast your vote for this monster."
                embed.add_field(name=f"{k}", value=f"{msg}", inline=False)

        await ctx.send(embed=embed)

    @monster_group.command(name='show')
    async def monster_show(self, ctx: Context, *monster: str):
        monster = ' '.join(monster)
        if self.monsters.get(monster, None):
            summary = await self.monster_summary(monster)
            embed = discord.Embed(name=monster)
            embed.add_field(name=f"About {monster}", value=summary)
            await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(MonsterSurvey(bot))





