import logging
import json
from discord.ext import commands
from discord.ext.commands import Bot, Context
import discord
from typing import Optional, Tuple
import aiohttp
from http import HTTPStatus

log = logging.getLogger(__name__)


EMOJIS = {
    'SUCCESS': u"\u2705",
    'ERROR': u"\u274C",
}

class MonsterSurvey:

    def __init__(self, bot: Bot):
        self.bot = Bot
        self._monsters = None

    @property
    def monsters(self) -> dict:
        """Always get the most up to date version"""
        path = '../bot/resources/monstersurvey/monstersurvey.json'
        with open(path, 'r') as f:
            self._monsters = json.load(f)
        return self._monsters

    async def monster_info(self, monster) -> Tuple[Optional[str], Optional[str]]:
        """Gets information relating to each monster. This first checks if there
        are 'summary' and 'image' keys in the json file. If this fails, it will
        attempt to pull summary information from Wikipedia.
        """
        async def fetch_url(session: aiohttp.ClientSession, url: str) -> dict:
            """Use wikipedia api url calls"""
            response = await session.get(url)
            if response.status == HTTPStatus.OK:
                result = json.loads(await response.text())
                return next(iter(result['query']['pages'].values()))
        summary_url = "http://en.wikipedia.org/w/api.php" \
                      "?format=json" \
                      "&action=query" \
                      "&prop=extracts" \
                      "&explaintext&exintro" \
                      "&redirects=1" \
                      f"&titles={monster}"
        image_url = "http://en.wikipedia.org/w/api.php" \
                    "?action=query" \
                    "&prop=pageimages" \
                    "&format=json" \
                    "&piprop=original" \
                    f"&titles={monster}"
        async with aiohttp.ClientSession() as s:
            summary = self.monsters[monster].get('summary') \
                or (await fetch_url(s, summary_url)).get('extract')

            image = self.monsters[monster].get('image') \
                or (await fetch_url(s, image_url)).get('original', {}).get('source')
            return summary, image

    @commands.group(name='monster', aliases=('ms',), invoke_without_command=True)
    async def monster_group(self, ctx: Context):
        pass

    @monster_group.command(name='vote')
    async def monster_vote(self, ctx: Context, name: Optional[str] = None):
        """Casts a vote for a particular monster, or displays a list of all
        monsters that are available for voting.
        """
        embed = discord.Embed(name='Vote for your favorite monster')
        if not name:
            for k,v in self.monsters.items():
                msg = f"`.monster show {k}` for more information\n" \
                      f"`.monster vote {k}` to cast your vote for this monster."
                embed.add_field(name=f"{k}", value=f"{msg}", inline=False)
        # TODO: Add logic for voting
        await ctx.send(embed=embed)

    @monster_group.command(name='show')
    async def monster_show(self, ctx: Context, *monster: str):
        """Display a detailed description for the monster, and image."""
        monster = ' '.join(monster)
        if self.monsters.get(monster, None):
            summary, image = await self.monster_info(monster)
            embed = discord.Embed(name=monster)
            embed.add_field(name=f"About {monster}", value=summary or "No information")
            if image:
                embed.set_image(url=image)
            embed.set_footer(text=f"To vote for {monster}, type `.monster vote {monster}`")
            await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction(EMOJIS['ERROR'])


def setup(bot: Bot):
    bot.add_cog(MonsterSurvey(bot))





