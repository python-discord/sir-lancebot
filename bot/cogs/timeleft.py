from discord.ext import commands
from dateutil.relativedelta import relativedelta
import logging
import aiohttp
import discord
import datetime

bot = commands.Bot(command_prefix='.', description='pr bot')

@bot.command()
async def timeleft():
    tl = datetime.datetime(2018, 10, 31) - datetime.datetime.now()
    days = tl.days
    sec = tl.seconds
    hours =  sec //3600
    minutes = sec //60 % 60
    sec = sec % 60

    message = f"{days} days, {hours} hours, {minutes} minutes, {sec} seconds left until Hacktoberfest is over!"
    await bot.say(message)


bot.run('NTA1ODY3ODM2NzgzMzI5MzAw.Dre_iQ.YpwNKPKrH-TI9UMItqPpQmYMwtY')
