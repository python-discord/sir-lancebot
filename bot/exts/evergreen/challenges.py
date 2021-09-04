import logging

from bs4 import BeautifulSoup
from discord import Color, Embed
from discord.ext import commands

from bot.bot import Bot

logger = logging.getLogger(__name__)
API_ROOT = 'https://www.codewars.com/api/v1/code-challenges/{kata_id}'


class Challenges(commands.Cog):
    """
    Cog for a challenge command.

    Pulls a random kata from codewars.com, and can be filtered through.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["kata"])
    async def challenge(self, ctx: commands.Context, language: str = 'python',
                        level: str = None, *, query: str = None) -> None:
        """Challenge command."""
        get_kata_link = f'https://codewars.com/kata/search/{language}'

        level = f'-{level}' if level else None
        params = {name: value for name, value in zip(['q', 'r[]'], [query, level]) if value}
        params = {**params, 'beta': 'false'}
        async with self.bot.http_session.get(get_kata_link, params=params) as response:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from codewars.com"
                )
            soup = BeautifulSoup(await response.text(), features='lxml')
            section_katas = soup.body.div.div.main.section
            div_of_katas = section_katas.find("div", class_='w-full md:w-9/12 md:pl-4 pr-0 space-y-2')
            first_kata_div = div_of_katas.find("div", class_='list-item-kata bg-ui-section p-4 rounded-lg shadow-md')
            if not first_kata_div:
                no_results_embed = Embed(title="I could not find any results for the filters you provided.",
                                         color=Color.red())
                await ctx.send(embed=no_results_embed)
                return
            first_kata_id = first_kata_div.div.div.div.a['href'].split('/')[-1]

        async with self.bot.http_session.get(API_ROOT.format(kata_id=first_kata_id)) as kata_information:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from codewars.com/api/v1"
                )
            kata_information = await kata_information.json()
            # maps specific rgb codes to kyu (difficulty) of kata
            mapping_of_kyu = {-8: (221, 219, 218), -7: (221, 219, 218), -6: (236, 182, 19), -5: (236, 182, 19),
                              -4: (60, 126, 187), -3: (60, 126, 187), -2: (134, 108, 199), -1: (134, 108, 199)}
            kata_embed = Embed(title=f"{kata_information['name']}",
                               color=Color.from_rgb(*mapping_of_kyu[kata_information['rank']['id']]),
                               url=f'https://codewars.com/kata/{first_kata_id}')
            await ctx.send(embed=kata_embed)


def setup(bot: Bot) -> None:
    """Sets up Challenges cog."""
    bot.add_cog(Challenges(bot))
