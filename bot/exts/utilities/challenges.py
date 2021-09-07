import logging
from random import choice

from bs4 import BeautifulSoup
from discord import Color, Embed
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Emojis, NEGATIVE_REPLIES

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
    async def challenge(self, ctx: commands.Context, language: str = 'python', *, query: str = None) -> None:
        """
        The challenge command pulls a random kata (challenge) from codewars.com.

        The different ways to use this command are:
        `.challenge <language>` - Pulls a random challenge within that language's scope.
        `.challenge <language> <difficulty>` - The difficulty can be from 1-8,
        1 being the hardest, 8 being the easiest. This pulls a random challenge within that difficulty & language.
        `.challenge <language> <query>` - Pulls a random challenge with the query provided under the language
        `.challenge <language> <query>, <difficulty>` - Pulls a random challenge with the query provided,
        under that difficulty within the language's scope.
        """
        get_kata_link = f'https://codewars.com/kata/search/{language}'

        if language and not query:
            level = f"-{choice(['1', '2', '3', '4', '5', '6', '7', '8'])}"
        elif ',' in query or ', ' in query:
            query_splitted = query.split(',' if ', ' not in query else ', ')

            if len(query_splitted) > 2:
                raise commands.BadArgument(
                    "There can only be one comma within the query, separating the difficulty and the query itself."
                )

            query, level = query_splitted
            level = f'-{level}'
        elif query.isnumeric():
            level, query = f'-{query}', None
        else:
            level = None

        params = {name: value for name, value in zip(['q', 'r[]'], [query, level]) if value}
        params = {**params, 'beta': 'false'}
        async with self.bot.http_session.get(get_kata_link, params=params) as response:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from codewars.com"
                )
            soup = BeautifulSoup(await response.text(), features='lxml')
            first_kata_div = soup.find_all('div', class_='item-title px-0')

            if not first_kata_div:
                no_results_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="No results could be found with the filters provided.",
                    color=Colours.soft_red,
                )
                await ctx.send(embed=no_results_embed)
                return
            elif not query:
                first_kata_div = choice(first_kata_div)
            elif len(first_kata_div) >= 3:
                first_kata_div = choice(first_kata_div[:3])
            else:
                first_kata_div = first_kata_div[0]

            # there are numerous divs before arriving at the id of the kata, which can be used for the link.
            first_kata_id = first_kata_div.a['href'].split('/')[-1]

        async with self.bot.http_session.get(API_ROOT.format(kata_id=first_kata_id)) as kata_information:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from codewars.com/api/v1"
                )
            kata_information = await kata_information.json()
            # maps specific rgb codes to kyu (difficulty) of kata
            mapping_of_kyu = {
                -8: (221, 219, 218), -7: (221, 219, 218), -6: (236, 182, 19), -5: (236, 182, 19),
                -4: (60, 126, 187), -3: (60, 126, 187), -2: (134, 108, 199), -1: (134, 108, 199)
            }
            description_of_kata = [line for line in kata_information["description"].split('\n') if '##' not in line]
            description_of_kata = description_of_kata[0] if len(description_of_kata) == 1 else \
                description_of_kata[0] + f'\n\n[Read more...](https://codewars.com/kata/{first_kata_id})'

            languages_of_kata = ', '.join(map(str.title, kata_information['languages']))
            creator = kata_information['createdBy']
            kata_embed = Embed(
                title=kata_information['name'],
                description=description_of_kata,
                color=Color.from_rgb(*mapping_of_kyu[kata_information['rank']['id']]),
                url=f'https://codewars.com/kata/{first_kata_id}',
            )
            kata_embed.add_field(
                name=f"Information about {kata_information['name']}",
                value=(
                    f"{Emojis.reddit_users} [{creator['username']}]({creator['url']})\n"
                    f"{Emojis.reddit_post_text} `{languages_of_kata}`\n"
                    f"{Emojis.stackoverflow_tag} `{', '.join(kata_information['tags'])}`\n"
                    f"{Emojis.reddit_upvote} `{kata_information['voteScore']}`\n"
                    f"⭐ `{kata_information['totalStars']}`\n"
                    f"🏁 `{kata_information['totalCompleted']}`\n"
                    f"{Emojis.stackoverflow_views} `{kata_information['totalAttempts']}`"
                ),
                inline=True,
            )
            await ctx.send(embed=kata_embed)


def setup(bot: Bot) -> None:
    """Sets up Challenges cog."""
    bot.add_cog(Challenges(bot))
