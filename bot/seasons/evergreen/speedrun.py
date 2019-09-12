import json
import logging
import re
from pathlib import Path
from random import choice

import srcomapi
import srcomapi.datatypes as dt
from discord import Embed, colour
from discord.ext import commands


log = logging.getLogger(__name__)
API = srcomapi.SpeedrunCom()

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

    @speedrun.command(name="platform", aliases=['pf'])
    async def find_by_platform(self, ctx: commands.Context, *, platform: str) -> None:
        """Sends an embed of a random speedrun record by platform."""
        platform = platform.lower()
        res = API.search(dt.Game, {"platform": PLATFORMS[platform], '_bulk': True})
        if len(res) != 0:
            index = 250
            while len(res) % 250 == 0:
                res = API.search(dt.Game, {"platform": PLATFORMS[platform], '_bulk': True, 'offset': index})
                index += 250
            chosen_game = choice(res)
            run = chosen_game.records[0].runs[0]['run']

            await ctx.send(embed=format_embed(chosen_game, run))
        else:
            await ctx.send("There are no speedrun records for this platform.")

    @speedrun.command(name="genre")
    async def find_by_genre(self, ctx: commands.Context, *, genre: str) -> None:
        """Sends an embed of a random speedrun record by genre."""
        genre = genre.lower()
        res = API.search(dt.Game, {'genre': GENRES[genre], '_bulk': True})
        if len(res) != 0:
            index = 250
            while len(res) % 250 == 0:
                res = API.search(dt.Game, {"genre": GENRES[genre], '_bulk': True, 'offset': index})
                index += 250
            chosen_game = choice(res)
            run = chosen_game.records[0].runs[0]['run']

            await ctx.send(embed=format_embed(chosen_game, run))
        else:
            await ctx.send("There are no speedrun records for this genre.")

    @speedrun.command(name="year")
    async def find_by_year(self, ctx: commands.Context, year: int) -> None:
        """Sends an embed of a random speedrun record by year."""
        res = API.search(dt.Game, {'released': year, '_bulk': True})
        if len(res) != 0:
            index = 250
            while len(res) % 250 == 0:
                res += API.search(dt.Game, {'released': year, '_bulk': True, 'offset': index})
                index += 250
            chosen_game = choice(res)
            run = chosen_game.records[0].runs[0]['run']

            await ctx.send(embed=format_embed(chosen_game, run))
        else:
            await ctx.send("There are no speedrun records for this year.")


def format_embed(game: srcomapi.datatypes.Game, run: srcomapi.datatypes.Run) -> Embed:
    """Helper function that formats and returns an embed."""
    game_name = game.data['names']['international']
    vid_link = run.data['videos']['links'][0]['uri']
    embed = Embed(
        color=colour.Color.dark_green()
    )
    embed.add_field(name=game_name, value=run.weblink, inline=False)
    embed.add_field(name="Player", value=run.players[0].name, inline=True)
    embed.add_field(name="Record Time", value=get_time_record(game), inline=True)
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


def get_time_record(game: srcomapi.datatypes.Game) -> str:
    """Helper function that fetches the time and formats it."""
    try:
        time = game.records[0].runs[0]['run'].times['primary']  # this line takes about 5 secs, try to speed it up
        return format_time(time)
    except IndexError:
        return "Error"


def setup(bot: commands.bot) -> None:
    """Load the Speedrun cog."""
    bot.add_cog(Speedrun(bot))
    log.info("Speedrun cog loaded")
