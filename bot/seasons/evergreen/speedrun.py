import json
import logging
import re
from pathlib import Path
from random import choice

import aiohttp
from discord import Embed, colour
from discord.ext import commands


log = logging.getLogger(__name__)
URL = 'http://www.speedrun.com/api/v1/'


with Path('bot/resources/evergreen/speedrun_resources.json').open(encoding='utf-8') as file:
    data = json.load(file)
    PLATFORMS = data[0]
    GENRES = data[1]
    LINKS = data[2]


class Speedrun(commands.Cog):
    """Commands about the video game speedrunning community."""

    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    @commands.group(name="speedrun", invoke_without_command=True)
    async def speedrun(self, ctx: commands.context) -> None:
        """Commands for the Speedrun cog."""
        await ctx.send_help(ctx.command)

    @speedrun.command(name="video")
    async def get_speedrun_video(self, ctx: commands.Context) -> None:
        """Sends a link to a video of a random speedrun."""
        await ctx.send(choice(LINKS))

    @speedrun.command(name='year')
    async def find_by_year(self, ctx: commands.Context, year: int) -> None:
        """Sends an embed of a random speedrun record by year."""
        async with aiohttp.ClientSession() as session:
            page_size, page_max = 0, 0
            uri = URL + f'games?released={year}&_bulk=True'
            games = []
            while page_size == page_max:
                resp = await fetch(session, uri)
                if len(resp['data']) == 0:
                    await ctx.send(f'There are no records for the year "{year}"')
                    return
                games += resp['data']
                pagination = resp['pagination']
                uri = pagination['links'][len(pagination['links']) - 1]['uri']
                page_size, page_max = pagination['size'], pagination['max']
            chosen_game = choice(games)
            embed = await format_embed_async(session, chosen_game)
            if embed is None:
                await ctx.send("There are no speedrun records for the selected game, please try the command again")
            else:
                await ctx.send(embed=embed)

    @speedrun.command(name='platform', aliases=['pf'])
    async def find_by_platform(self, ctx: commands.Context, *, platform: str) -> None:
        """Sends an embed of a random speedrun record by platform."""
        async with aiohttp.ClientSession() as session:
            page_size, page_max = 0, 0
            try:
                uri = URL + f'games?platform={PLATFORMS[platform.lower()]}&_bulk=True'
            except KeyError:
                await ctx.send(f'There are no records for the platform "{platform}"')
                return
            games = []
            while page_size == page_max:
                resp = await fetch(session, uri)
                games += resp['data']
                pagination = resp['pagination']
                uri = pagination['links'][len(pagination['links']) - 1]['uri']
                page_size, page_max = pagination['size'], pagination['max']
            chosen_game = choice(games)
            embed = await format_embed_async(session, chosen_game)
            if embed is None:
                await ctx.send("There are no speedrun records for the selected game, please try the command again")
            else:
                await ctx.send(embed=embed)

    @speedrun.command(name='genre')
    async def find_by_genre(self, ctx: commands.Context, *, genre: str) -> None:
        """Sends an embed of a random speedrun record by year."""
        async with aiohttp.ClientSession() as session:
            page_size, page_max = 0, 0
            try:
                uri = URL + f'games?genre={GENRES[genre.lower()]}&_bulk=True'
            except KeyError:
                await ctx.send(f'There are no records for the genre "{genre}"')
                return
            games = []
            while page_size == page_max:
                resp = await fetch(session, uri)
                games += resp['data']
                pagination = resp['pagination']
                uri = pagination['links'][len(pagination['links']) - 1]['uri']
                page_size, page_max = pagination['size'], pagination['max']
            chosen_game = choice(games)
            embed = await format_embed_async(session, chosen_game)
            if embed is None:
                await ctx.send("There are no speedrun records for the selected game, please try the command again")
            else:
                await ctx.send(embed=embed)


async def format_embed_async(session: aiohttp.client.ClientSession, game: dict) -> Embed:
    """Helper function that formats and returns an embed."""
    record = await fetch(session, URL + f'games/{game["id"]}/records?top=1')
    try:
        run = record['data'][0]['runs'][0]['run']
    except IndexError:
        return None
    else:
        player = await fetch(session, URL + f'users/{run["players"][0]["id"]}')
        record_time = format_time(run['times']['primary'])
        vid_link = run['videos']['links'][0]['uri']

        embed = Embed(
            color=colour.Color.dark_green()
        )
        embed.add_field(name=game['names']['international'], value=run['weblink'], inline=False)
        embed.add_field(name="Player", value=player['data']['names']['international'], inline=True)
        embed.add_field(name="Record Time", value=format_time(record_time), inline=True)
        embed.add_field(name="Video Link", value="None" if vid_link is None else vid_link, inline=False)
        return embed


def format_time(time: str) -> str:
    """Helper function that returns the formatted time."""
    msecs = None
    ret_string = ''
    time_formats = ['secs', "mins", "hrs", 'days']

    if '.' in time:     # Creates an msec var if present in the time
        time_list = time.split('.')
        time, msecs = time_list[0], time_list[1]
    times = re.findall(r'\d+', time)

    if msecs is not None:
        times[-1] = times[-1] + f'.{msecs[:-1]}'
    index = 0
    for item in reversed(times):
        ret_string = f'{item} {time_formats[index]}, {ret_string}'
        index += 1
    return ret_string[:-2]


async def fetch(session: aiohttp.client.ClientSession, uri: str) -> dict:
    """Helper function to keep session.get() calls clean."""
    async with session.get(uri) as resp:
        return await resp.json()


def setup(bot: commands.Bot) -> None:
    """Load the Speedrun cog."""
    bot.add_cog(Speedrun(bot))
    log.info("Speedrun cog loaded")
