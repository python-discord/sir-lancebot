import logging
from random import randint

import discord
from discord.ext import commands


logger = logging.getLogger(__name__)


LOVE_STAT = {
    '0':
        [
            '\U0001F49B When will you two marry? \U0001F49B',
            '\U0001F49B Now kiss already \U0001F49B'
        ],
    '95':
        [
            '\U0001f496 Love is in the air \U0001f496',
            '\U0001f496 Planned your future yet? \U0001f496'
        ],
    '80': '\U0001f495 Aww look you two fit so well together \U0001f495',
    '60': '\u2764 So when will you two go on a date? \u2764',
    '45': '\U0001F498 You two are really close aren\'t you? \U0001F498',
    '30': '\U0001F497 You seem like you are good friends \U0001F497',
    '20': '\U0001F49C You two seem like casual friends \U0001F49C',
    '5': '\U0001F499 A small acquaintance \U0001F499',
    '1': '\U0001F494 There\'s no real connection between you two \U0001F494'
}
LOVE_TXT = {
    '0': "You two will most likely have the perfect relationship. But don't think that this means you don't have to "
         "do anything for it to work. Talking to each other and spending time together is key, even in a seemingly "
         "perfect relationship.",
    '95': "Your relationship will most likely work out perfect. This doesn't mean thought that you don't need to put "
          "effort into it. Talk to each other, spend time together, and you two wont have a hard time.",
    '80': "Your relationship will most likely work out well. Don't hesitate on making contact with each other though, "
          "as your relationship might suffer from a lack of time spent together. Talking with each other and spending "
          "time together is key.",
    '60': "Your relationship will most likely work out. It won't be perfect and you two need to spend a lot of time "
          "together, but if you keep on having contact, the good times in your relationship will overweigh the bad "
          "ones.",
    '45': "Your relationship has a reasonable amount of working out. But do not overestimate yourself there. Your "
          "relationship will suffer good and bad times. Make sure to not let the bad times destroy your relationship, "
          "so do not hesitate to talk to each other, figure problems out together etc.",
    '30': "The chance of this relationship working is not very high, but its not that low either. If you both want "
          "this relationship to work, and put time and effort into it, meaning spending time together, talking to "
          "each other etc., than nothing shall stand in your way.",
    '20': "The chance of this relationship working is not very high. You both need to put time and effort into this "
          "relationship, if you want it to work out well for both of you. Talk with each other about everything and "
          "don't lock yourself up. Spend time together. This will improve the chances of this relationship's survival "
          "by a lot",
    '5': "There might be a chance of this relationship working out somewhat well, but it is not very high. With a lot "
         "of time and effort you'll get it to work eventually, however don't count on it. It might fall apart quicker "
         "than you'd expect.",
    '1': "The chance of this relationship working out is really low. You can get it to work, but with high costs and "
         "no guarantee of working out. Do not sit back, spend as much time together as possible, talk a lot with each "
         "other to increase the chances of this relationship's survival "
}


class LoveCalculator:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('love_calculator', 'love_calc'))
    async def love(self, ctx, name_one: discord.Member, name_two: discord.Member):
        love_meter = (name_one.id + name_two.id) % 100
        if love_meter >= 95:
            love_status = LOVE_STAT['95'][randint(0, len(LOVE_STAT['95']))]
            love_stat_i = '95'
        elif 80 <= love_meter < 90:
            love_status = LOVE_STAT['80']
            love_stat_i = '80'
        elif 60 <= love_meter < 80:
            love_status = LOVE_STAT['60']
            love_stat_i = '60'
        elif 45 <= love_meter < 60:
            love_status = LOVE_STAT['45']
            love_stat_i = '45'
        elif 30 <= love_meter < 45:
            love_status = LOVE_STAT['30']
            love_stat_i = '30'
        elif 20 <= love_meter < 30:
            love_status = LOVE_STAT['20']
            love_stat_i = '20'
        elif 5 <= love_meter < 20:
            love_status = LOVE_STAT['5']
            love_stat_i = '5'
        elif 1 <= love_meter < 5:
            love_status = LOVE_STAT['1']
            love_stat_i = '1'
        else:
            love_meter = 100
            love_status = LOVE_STAT['0'][randint(0, len(LOVE_STAT['0']))]
            love_stat_i = '0'

        embed = discord.Embed(
            title=love_status,
            description=f'{name_one.display_name} \u2764 {name_two.display_name} scored {love_meter}%!\n\u200b',
            color=discord.Color.dark_magenta()
        )
        embed.add_field(
            name='A letter from Dr. Love:',
            value=LOVE_TXT[love_stat_i]
        )

        await ctx.message.channel.send(embed=embed)

    @love.error
    async def love_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            logger.info(f"{ctx.message.author}, /love: MissingRequiredArgument")

        if isinstance(error, commands.BadArgument):
            logger.info(f"{ctx.message.author} invoked /love with a non-existent username: BadArgument")


def setup(bot):
    bot.add_cog(LoveCalculator(bot))
