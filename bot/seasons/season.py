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
    """
    Returns all the Season objects
    located in bot/seasons/
    """
    seasons = []

    for module in pkgutil.iter_modules([Path('bot', 'seasons')]):
        if module.ispkg:
            seasons.append(module[1])

    return seasons


def get_season_class(season_name):
    season_lib = importlib.import_module(f'bot.seasons.{season_name}')
    return getattr(season_lib, season_name.capitalize())


def get_season(bot, season_name: str = None, date: datetime.date = None):
    """
    Returns a Season object based on either a string or a date.
    """

    # If either both or neither are set, raise an error.
    if not bool(season_name) ^ bool(date):
        raise UserWarning("This function requires either a season or a date in order to run.")

    seasons = get_seasons()

    # Use season override if season name not provided
    if not season_name and Client.season_override:
        log.debug(f"Season override found: {Client.season_override}")
        season_name = Client.season_override

    # If name provided grab the specified class or fallback to evergreen.
    if season_name:
        season_name = season_name.lower()
        if season_name not in seasons:
            season_name = 'evergreen'
        season_class = get_season_class(season_name)
        return season_class(bot)

    # If not, we have to figure out if the date matches any of the seasons.
    seasons.remove('evergreen')
    for season_name in seasons:
        season_class = get_season_class(season_name)
        # check if date matches before returning an instance
        if season_class.start() <= date <= season_class.end():
            return season_class(bot)
    else:
        evergreen_class = get_season_class('evergreen')
        return evergreen_class(bot)


class SeasonBase:
    name = None
    date_format = "%d/%m-%Y"

    @staticmethod
    def current_year():
        return datetime.date.today().year

    @classmethod
    def start(cls):
        return datetime.datetime.strptime(f"{cls.start_date}-{cls.current_year()}", cls.date_format).date()

    @classmethod
    def end(cls):
        return datetime.datetime.strptime(f"{cls.end_date}-{cls.current_year()}", cls.date_format).date()

    @staticmethod
    def avatar_path(*path_segments):
        return Path('bot', 'resources', 'avatars', *path_segments)

    async def load(self):
        """
        Loads in the bot name, the bot avatar,
        and the extensions that are relevant to that season.
        """

        guild = self.bot.get_guild(Client.guild)

        # Change only nickname if in debug mode due to ratelimits for user edits
        if Client.debug:
            if guild.me.display_name != self.bot_name:
                log.debug(f"Changing nickname to {self.bot_name}")
                await guild.me.edit(nick=self.bot_name)
        else:
            if self.bot.user.name != self.bot_name:
                # attempt to change user details
                log.debug(f"Changing username to {self.bot_name}")
                await self.bot.user.edit(name=self.bot_name, avatar=self.bot_avatar)

                # fallback on nickname if failed due to ratelimit
                if self.bot.user.name != self.bot_name:
                    log.info(f"User details failed to change: Changing nickname to {self.bot_name}")
                    await guild.me.edit(nick=self.bot_name)

            # remove nickname if an old one exists
            if guild.me.nick and guild.me.nick != self.bot_name:
                log.debug(f"Clearing old nickname of {guild.me.nick}")
                await guild.me.edit(nick=None)

        # Prepare all the seasonal cogs, and then the evergreen ones.
        extensions = []
        for ext_folder in {self.name, "evergreen"}:
            if ext_folder:
                log.info(f'Start loading extensions from seasons/{ext_folder}/')
                path = Path('bot', 'seasons', ext_folder)
                for ext_name in [i[1] for i in pkgutil.iter_modules([path])]:
                    extensions.append(f"bot.seasons.{ext_folder}.{ext_name}")

        # Finally we can load all the cogs we've prepared.
        self.bot.load_extensions(extensions)


class SeasonManager:
    """
    A cog for managing seasons.
    """

    def __init__(self, bot):
        self.bot = bot
        self.season = get_season(bot, date=datetime.date.today())
        self.season_task = bot.loop.create_task(self.load_seasons())

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

    def __unload(self):
        self.season_task.cancel()
