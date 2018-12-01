import asyncio
import datetime
import importlib
import logging
import pkgutil
from pathlib import Path

import discord
from discord.ext import commands

from bot.constants import Client, Roles, bot
from bot.decorators import with_role

log = logging.getLogger(__name__)


def get_seasons():
    """
    Returns all the Season objects located in bot/seasons/
    """
    seasons = []

    for module in pkgutil.iter_modules([Path("bot", "seasons")]):
        if module.ispkg:
            seasons.append(module.name)

    return seasons


def get_season_class(season_name):
    season_lib = importlib.import_module(f"bot.seasons.{season_name}")
    return getattr(season_lib, season_name.capitalize())


def get_season(season_name: str = None, date: datetime.datetime = None):
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
            season_name = "evergreen"
        season_class = get_season_class(season_name)
        return season_class()

    # If not, we have to figure out if the date matches any of the seasons.
    seasons.remove("evergreen")
    for season_name in seasons:
        season_class = get_season_class(season_name)
        # check if date matches before returning an instance
        if season_class.is_between_dates(date):
            return season_class()
    else:
        evergreen_class = get_season_class("evergreen")
        return evergreen_class()


class SeasonBase:
    name = None
    date_format = "%d/%m/%Y"
    start_date = None
    end_date = None
    bot_name: str = "SeasonalBot"
    icon: str = "/logos/logo_full/logo_full.png"

    @staticmethod
    def current_year():
        return datetime.date.today().year

    @classmethod
    def start(cls):
        if not cls.start_date:
            return datetime.datetime.min
        return datetime.datetime.strptime(f"{cls.start_date}/{cls.current_year()}", cls.date_format)

    @classmethod
    def end(cls):
        if not cls.end_date:
            return datetime.datetime.max
        return datetime.datetime.strptime(f"{cls.end_date}/{cls.current_year()}", cls.date_format)

    @classmethod
    def is_between_dates(cls, date):
        return cls.start() <= date <= cls.end()

    async def get_icon(self):
        base_url = "https://raw.githubusercontent.com/python-discord/branding/master"
        async with bot.http_session.get(base_url + self.icon) as resp:
            avatar = await resp.read()
            return bytearray(avatar)

    async def apply_username(self, *, debug: bool = False):
        """
        Applies the username for the current season. Returns if it was successful.
        """

        guild = bot.get_guild(Client.guild)
        result = None

        # Change only nickname if in debug mode due to ratelimits for user edits
        if debug:
            if guild.me.display_name != self.bot_name:
                log.debug(f"Changing nickname to {self.bot_name}")
                await guild.me.edit(nick=self.bot_name)

        else:
            if bot.user.name != self.bot_name:
                # attempt to change user details
                log.debug(f"Changing username to {self.bot_name}")
                await bot.user.edit(username=self.bot_name)

                # fallback on nickname if failed due to ratelimit
                if bot.user.name != self.bot_name:
                    log.info(f"Username failed to change: Changing nickname to {self.bot_name}")
                    await guild.me.edit(nick=self.bot_name)
                    result = False
                else:
                    result = True

            # remove nickname if an old one exists
            if guild.me.nick and guild.me.nick != self.bot_name:
                log.debug(f"Clearing old nickname of {guild.me.nick}")
                await guild.me.edit(nick=None)

            return result

    async def apply_avatar(self):
        """
        Applies the avatar for the current season. Returns if it was successful.
        """

        # track old avatar hash for later comparison
        old_avatar = bot.user.avatar

        # attempt the change
        log.debug(f"Changing avatar to {self.icon}")
        avatar = await self.get_icon()
        await bot.user.edit(avatar=avatar)

        if bot.user.avatar != old_avatar:
            log.debug(f"Avatar changed to {self.icon}")
            return True
        else:
            log.debug(f"Changing avatar failed: {self.icon}")
            return False

    async def apply_server_icon(self):
        """
        Applies the server icon for the current season. Returns if it was successful.
        """

        guild = bot.get_guild(Client.guild)

        # track old icon hash for later comparison
        old_icon = guild.icon

        # attempt the change
        log.debug(f"Changing server icon to {self.icon}")
        avatar = await self.get_icon()
        await guild.edit(icon=avatar, reason=f"Seasonbot Season Change: {self.__name__}")

        new_icon = bot.get_guild(Client.guild).icon
        if new_icon != old_icon:
            log.debug(f"Server icon changed to {self.icon}")
            return True
        else:
            log.debug(f"Changing server icon failed: {self.icon}")
            return False

    async def load(self):
        """
        Loads in the bot name, the bot avatar, and the extensions that are relevant to that season.
        """

        await self.apply_username(debug=Client.debug)
        await self.apply_avatar()

        if not Client.debug:
            await self.apply_server_icon()

        # Prepare all the seasonal cogs, and then the evergreen ones.
        extensions = []
        for ext_folder in {self.name, "evergreen"}:
            if ext_folder:
                log.info(f"Start loading extensions from seasons/{ext_folder}/")
                path = Path("bot", "seasons", ext_folder)
                for ext_name in [i[1] for i in pkgutil.iter_modules([path])]:
                    extensions.append(f"bot.seasons.{ext_folder}.{ext_name}")

        # Finally we can load all the cogs we've prepared.
        bot.load_extensions(extensions)


class SeasonManager:
    """
    A cog for managing seasons.
    """

    def __init__(self, bot):
        self.bot = bot
        self.season = get_season(date=datetime.datetime.utcnow())
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
            new_season = get_season(date=datetime.datetime.utcnow())
            if new_season != self.season:
                await self.season.load()

    @with_role(Roles.moderator, Roles.admin, Roles.owner)
    @commands.command(name='season')
    async def change_season(self, ctx, new_season: str):
        """
        Changes the currently active season on the bot.
        """

        self.season = get_season(season_name=new_season)
        await self.season.load()
        await ctx.send(f"Season changed to {new_season}.")

    @with_role(Roles.moderator, Roles.admin, Roles.owner)
    @commands.command(name="seasons")
    async def show_seasons(self, ctx):
        """
        Shows the available seasons and their dates.
        """

        # sort by start order, followed by lower duration
        def season_key(season: SeasonBase):
            return season.start(), season.end() - datetime.datetime.max

        current_season = self.season.name

        entries = []
        seasons = [get_season_class(s) for s in get_seasons()]
        for season in sorted(seasons, key=season_key):
            start = season.start_date
            end = season.end_date
            if start and not end:
                period = f"From {start}"
            elif end and not start:
                period = f"Until {end}"
            elif not end and not start:
                period = f"Always"
            else:
                period = f"{start} to {end}"

            # bold period if current date matches season date range
            is_current = season.is_between_dates(datetime.datetime.utcnow())
            pdec = "**" if is_current else ""

            # underline currently active season
            is_active = current_season == season.name
            sdec = "__" if is_active else ""

            forced_space = "\u200b "
            entries.append(
                f"**{sdec}{season.__name__}:{sdec}**\n"
                f"{forced_space*3}{pdec}{period}{pdec}"
            )

        embed = discord.Embed(description="\n".join(entries), colour=ctx.guild.me.colour)
        embed.set_author(name="Seasons")
        await ctx.send(embed=embed)

    @with_role(Roles.moderator, Roles.admin, Roles.owner)
    @commands.group()
    async def refresh(self, ctx):
        """
        Refreshes certain seasonal elements without reloading seasons.
        """
        if not ctx.invoked_subcommand:
            await ctx.invoke(bot.get_command("help"), "refresh")

    @refresh.command(name="avatar")
    async def refresh_avatar(self, ctx):
        """
        Re-applies the bot avatar for the currently loaded season.
        """

        # attempt the change
        is_changed = await self.season.apply_avatar()

        if is_changed:
            colour = ctx.guild.me.colour
            title = "Avatar Refreshed"
        else:
            colour = discord.Colour.red()
            title = "Avatar Failed to Refresh"

        # report back details
        season_name = type(self.season).__name__
        embed = discord.Embed(
            description=f"**Season:** {season_name}\n**Avatar:** {self.season.icon}",
            colour=colour
        )
        embed.set_author(name=title)
        embed.set_thumbnail(url=bot.user.avatar_url_as(format="png"))
        await ctx.send(embed=embed)

    @refresh.command(name="icon")
    async def refresh_server_icon(self, ctx):
        """
        Re-applies the server icon for the currently loaded season.
        """

        # attempt the change
        is_changed = await self.season.apply_server_icon()

        if is_changed:
            colour = ctx.guild.me.colour
            title = "Server Icon Refreshed"
        else:
            colour = discord.Colour.red()
            title = "Server Icon Failed to Refresh"

        # report back details
        season_name = type(self.season).__name__
        embed = discord.Embed(
            description=f"**Season:** {season_name}\n**Icon:** {self.season.icon}",
            colour=colour
        )
        embed.set_author(name=title)
        embed.set_thumbnail(url=bot.get_guild(Client.guild).icon_url_as(format='png'))
        await ctx.send(embed=embed)

    @refresh.command(name="username", aliases=("name",))
    async def refresh_username(self, ctx):
        """
        Re-applies the bot username for the currently loaded season.
        """

        old_username = str(bot.user)
        old_display_name = ctx.guild.me.display_name

        # attempt the change
        is_changed = await self.season.apply_username()

        if is_changed:
            colour = ctx.guild.me.colour
            title = "Username Refreshed"
            changed_element = "Username"
            old_name = old_username
            new_name = str(bot.user)
        else:
            colour = discord.Colour.red()

            # if None, it's because it wasn't meant to change username
            if is_changed is None:
                title = "Nickname Refreshed"
            else:
                title = "Username Failed to Refresh"
            changed_element = "Nickname"
            old_name = old_display_name
            new_name = self.season.bot_name

        # report back details
        season_name = type(self.season).__name__
        embed = discord.Embed(
            description=f"**Season:** {season_name}\n"
                        f"**Old {changed_element}:** {old_name}\n"
                        f"**New {changed_element}:** {new_name}",
            colour=colour
        )
        embed.set_author(name=title)
        await ctx.send(embed=embed)

    def __unload(self):
        self.season_task.cancel()
