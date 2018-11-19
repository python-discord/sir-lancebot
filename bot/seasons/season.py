import asyncio
import datetime
import importlib
import logging
import pkgutil
from pathlib import Path

from discord.ext import commands

from bot.constants import Client, Roles
from bot.decorators import with_role

log = logging.getLogger(__name__)


def get_seasons():
    return [i[1] for i in pkgutil.iter_modules([Path('bot', 'seasons')]) if i.ispkg]


def get_season(bot, season_name: str = None, date: datetime.date = None):
    """
    Returns a Season object based on either a string or a date.
    """

    # If either both or neither are set, raise an error.
    if not bool(season_name) ^ bool(date):
        raise UserWarning("This function requires either a season or a date in order to run.")

    seasons = get_seasons()

    # If there's a season name, we can just grab the correct class.
    if season_name:
        season_name = season_name.lower()
        if season_name not in seasons:
            season_name = 'evergreen'

        season_lib = importlib.import_module(f'bot.seasons.{season_name}')
        season_class = getattr(season_lib, season_name.capitalize())
        return season_class(bot)

    # If not, we have to figure out if the date matches any of the seasons.
    seasons.remove('evergreen')

    for season_name in seasons:
        season_lib = importlib.import_module(f'bot.seasons.{season_name}')
        season_class = getattr(season_lib, season_name.capitalize())
        season_object = season_class(bot)
        if season_object.start <= date <= season_object.end:
            return season_object
    else:
        evergreen_lib = importlib.import_module(f'bot.seasons.evergreen')
        return evergreen_lib.Evergreen(bot)


class SeasonBase:
    name = None

    def __init__(self):
        current_year = datetime.date.today().year
        date_format = "%d/%m-%Y"
        self.start = datetime.datetime.strptime(f"{self.start_date}-{current_year}", date_format).date()
        self.end = datetime.datetime.strptime(f"{self.end_date}-{current_year}", date_format).date()

    async def load(self):
        """
        Loads in the bot name, the bot avatar,
        and the extensions that are relevant to that season.
        """

        # Change the name
        bot_member = self.bot.get_guild(Client.guild).get_member(self.bot.user.id)
        await bot_member.edit(nick=self.bot_name)

        await self.bot.user.edit(avatar=self.bot_avatar)

        # Loads all the cogs for that season, and then the evergreen ones.
        exts = []
        for ext_folder in {self.name, "evergreen"}:
            if ext_folder:
                log.info(f'Start loading extensions from seasons/{ext_folder}/{ext_folder}/')
                path = Path('bot', 'seasons', ext_folder)
                for ext_name in [i[1] for i in pkgutil.iter_modules([path])]:
                    exts.append(f"bot.seasons.{ext_folder}.{ext_name}")

        self.bot.load_extensions(exts)


class SeasonManager:
    """
    A cog for managing seasons.
    """

    def __init__(self, bot):
        self.bot = bot
        self.season = get_season(bot, date=datetime.date.today())
        bot.loop.create_task(self.load_seasons())

        if not hasattr(bot, 'loaded_seasons'):
            bot.loaded_seasons = []

        # Figure out number of seconds until a minute past midnight
        tomorrow = datetime.datetime.now() + datetime.timedelta(1)
        midnight = datetime.datetime(
            year=tomorrow.year,
            month=tomorrow.month,
            day=tomorrow.day,
            hour=0,
            minute=0,
            second=0
        )
        self.sleep_time = (midnight - datetime.datetime.now()).seconds + 60

    async def load_seasons(self):
        await self.bot.wait_until_ready()
        await self.season.load()

        while True:
            await asyncio.sleep(self.sleep_time)  # sleep until midnight
            self.sleep_time = 86400  # next time, sleep for 24 hours.

            # If the season has changed, load it.
            new_season = get_season(self.bot, date=datetime.date.today())
            if new_season != self.season:
                await self.season.load()

    @with_role(Roles.moderator, Roles.admin, Roles.owner)
    @commands.command('season')
    async def change_season(self, ctx, new_season: str):
        """
        Changes the currently active season on the bot.
        """

        self.season = get_season(self.bot, season_name=new_season)
        await self.season.load()
        await ctx.send(f"Season changed to {new_season}.")
