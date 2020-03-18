import asyncio
import itertools
import logging
import random
import typing as t
from datetime import datetime, time, timedelta

import discord
from discord.ext import commands

from bot.bot import SeasonalBot
from bot.constants import Client, MODERATION_ROLES
from bot.decorators import with_role
from bot.seasons import SeasonBase, get_current_season, get_season

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

FILE_BANNER = "banner.png"
FILE_AVATAR = "avatar.png"
SERVER_ICONS = "server_icons"

BRANDING_URL = "https://api.github.com/repos/python-discord/branding/contents"

HEADERS = {"Accept": "application/vnd.github.v3+json"}  # Ensure we use API v3
PARAMS = {"ref": "seasonal-structure"}  # Target branch


class GithubFile(t.NamedTuple):
    """
    Represents a remote file on Github.

    The sha hash is kept so that we can determine that a file has changed,
    despite its filename remaining unchanged.
    """

    download_url: str
    path: str
    sha: str


async def pretty_files(files: t.Iterable[GithubFile]) -> str:
    """Provide a human-friendly representation of `files`."""
    return ", ".join(file.path for file in files)


async def seconds_until_midnight() -> float:
    """
    Give the amount of seconds needed to wait until the next-up UTC midnight.

    The exact `midnight` moment is actually delayed to 5 seconds after, in order
    to avoid potential problems due to imprecise sleep.
    """
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    midnight = datetime.combine(tomorrow, time(second=5))

    return (midnight - now).total_seconds()


class BrandingManager(commands.Cog):
    """
    Manages the guild's branding.

    The `daemon` task automatically manages branding across seasons. See its docstring
    for further explanation of the automated behaviour.

    If necessary, or for testing purposes, the Cog can be manually controlled
    via the `branding` command group.
    """

    current_season: t.Type[SeasonBase]

    banner: t.Optional[GithubFile]
    avatar: t.Optional[GithubFile]

    available_icons: t.List[GithubFile]
    remaining_icons: t.List[GithubFile]

    should_cycle: t.Iterator

    daemon: asyncio.Task

    def __init__(self, bot: SeasonalBot) -> None:
        """
        Assign safe default values on init.

        At this point, we don't have information about currently available branding.
        Most of these attributes will be overwritten once the daemon connects.
        """
        self.bot = bot
        self.current_season = get_current_season()

        self.banner = None
        self.avatar = None

        self.should_cycle = itertools.cycle([False])

        self.available_icons = []
        self.remaining_icons = []

        self.daemon = self.bot.loop.create_task(self._daemon_func())

    async def _daemon_func(self) -> None:
        """
        Manage all automated behaviour of the BrandingManager cog.

        Once a day, the daemon will perform the following tasks:
            - Update `current_season`
            - Poll Github API to see if the available branding for `current_season` has changed
            - Update assets if changes are detected (banner, guild icon, bot avatar, bot nickname)
            - Check whether it's time to cycle guild icons

        The daemon awakens on start-up, then periodically at the time given by `seconds_until_midnight`.
        """
        await self.bot.wait_until_ready()

        while True:
            self.current_season = get_current_season()
            branding_changed = await self.refresh()

            if branding_changed:
                await self.apply()

            elif next(self.should_cycle):
                await self.cycle()

            await asyncio.sleep(await seconds_until_midnight())

    async def _info_embed(self) -> discord.Embed:
        """Make an informative embed representing current state."""
        info_embed = discord.Embed(
            title=self.current_season.season_name,
            description=f"Active in {', '.join(m.name for m in self.current_season.months)}",
        ).add_field(
            name="Banner",
            value=self.banner.path if self.banner is not None else "Unavailable",
        ).add_field(
            name="Avatar",
            value=self.avatar.path if self.avatar is not None else "Unavailable",
        ).add_field(
            name="Available icons",
            value=await pretty_files(self.available_icons) or "Unavailable",
            inline=False,
        )
        if len(self.available_icons) > 1 and Client.icon_cycle_frequency:
            info_embed.set_footer(text=f"Icon cycle frequency: {Client.icon_cycle_frequency}")

        return info_embed

    async def _reset_remaining_icons(self) -> None:
        """Set `remaining_icons` to a shuffled copy of `available_icons`."""
        self.remaining_icons = random.sample(self.available_icons, k=len(self.available_icons))

    async def _reset_should_cycle(self) -> None:
        """
        Reset the `should_cycle` counter based on configured frequency.

        Counter will always yield False if either holds:
            - Client.icon_cycle_frequency is falsey
            - There are fewer than 2 available icons for current season

        Cycling can be easily turned off, and we prevent re-uploading the same icon repeatedly.
        """
        if len(self.available_icons) > 1 and Client.icon_cycle_frequency:
            wait_period = [False] * (Client.icon_cycle_frequency - 1)
            counter = itertools.cycle(wait_period + [True])
        else:
            counter = itertools.cycle([False])

        self.should_cycle = counter

    async def _get_files(self, path: str) -> t.Dict[str, GithubFile]:
        """
        Poll `path` in branding repo for information about present files.

        Return dict mapping from filename to corresponding `GithubFile` instance.
        """
        url = f"{BRANDING_URL}/{path}"
        async with self.bot.http_session.get(url, headers=HEADERS, params=PARAMS) as resp:
            directory = await resp.json()

        return {
            file["name"]: GithubFile(file["download_url"], file["path"], file["sha"])
            for file in directory
        }

    async def refresh(self) -> bool:
        """
        Poll Github API to refresh currently available icons.

        If the current season is not the evergreen, and lacks at least one asset,
        we also pol the evergreen seasonal dir as fallback for missing assets.

        Finally, if neither the seasonal nor fallback branding directories contain
        an asset, it will simply be ignored.

        Return True if the branding has changed. This will be the case when we enter
        a new season, or when something changes in the current seasons's directory
        in the branding repository.
        """
        old_branding = (self.banner, self.avatar, self.available_icons)
        seasonal_dir = await self._get_files(self.current_season.branding_path)

        # Only make a call to the fallback directory if there is something to be gained
        branding_incomplete = any(
            asset not in seasonal_dir
            for asset in (FILE_BANNER, FILE_AVATAR, SERVER_ICONS)
        )
        if branding_incomplete and self.current_season is not SeasonBase:
            fallback_dir = await self._get_files(SeasonBase.branding_path)
        else:
            fallback_dir = {}

        # Resolve assets in this directory, None is a safe value
        self.banner = seasonal_dir.get(FILE_BANNER) or fallback_dir.get(FILE_BANNER)
        self.avatar = seasonal_dir.get(FILE_AVATAR) or fallback_dir.get(FILE_AVATAR)

        # Now resolve server icons by making a call to the proper sub-directory
        if SERVER_ICONS in seasonal_dir:
            icons_dir = await self._get_files(f"{self.current_season.branding_path}/{SERVER_ICONS}")
            self.available_icons = list(icons_dir.values())

        elif SERVER_ICONS in fallback_dir:
            icons_dir = await self._get_files(f"{SeasonBase.branding_path}/{SERVER_ICONS}")
            self.available_icons = list(icons_dir.values())

        else:
            self.available_icons = []  # This should never be the case, but an empty list is a safe value

        # GithubFile instances carry a `sha` attr so this will pick up if a file changes
        branding_changed = old_branding != (self.banner, self.avatar, self.available_icons)
        log.info(f"New branding detected: {branding_changed}")

        if branding_changed:
            await self._reset_remaining_icons()
            await self._reset_should_cycle()

        return branding_changed

    async def cycle(self) -> bool:
        """Apply the next-up server icon."""
        if not self.available_icons:
            log.info("Cannot cycle: no icons for this season")
            return False

        if not self.remaining_icons:
            await self._reset_remaining_icons()
            log.info(f"Set remaining icons: {await pretty_files(self.remaining_icons)}")

        next_up, *self.remaining_icons = self.remaining_icons
        # await self.bot.set_icon(next_up.download_url)
        log.info(f"Applying icon: {next_up}")

        return True

    async def apply(self) -> None:
        """
        Apply current branding to the guild and bot.

        This delegates to the bot instance to do all the work. We only provide download urls
        for available assets. Assets unavailable in the branding repo will be ignored.
        """
        if self.banner is not None:
            # await self.bot.set_banner(self.banner.download_url)
            log.info(f"Applying banner: {self.banner.download_url}")

        if self.avatar is not None:
            # await self.bot.set_avatar(self.avatar.download_url)
            log.info(f"Applying avatar: {self.avatar.download_url}")

        # await self.bot.set_nickname(self.current_season.bot_name)
        log.info(f"Applying nickname: {self.current_season.bot_name}")

        await self.cycle()

    @with_role(*MODERATION_ROLES)
    @commands.group(name="branding")
    async def branding_cmds(self, ctx: commands.Context) -> None:
        """Group for commands allowing manual control of the `SeasonManager` cog."""
        if not ctx.invoked_subcommand:
            await self.branding_info(ctx)

    @branding_cmds.command(name="info", aliases=["status"])
    async def branding_info(self, ctx: commands.Context) -> None:
        """Provide an information embed representing current branding situation."""
        await ctx.send(embed=await self._info_embed())

    @branding_cmds.command(name="refresh")
    async def branding_refresh(self, ctx: commands.Context) -> None:
        """Poll Github API to refresh currently available branding, dispatch info embed."""
        async with ctx.typing():
            await self.refresh()
            await self.branding_info(ctx)

    @branding_cmds.command(name="cycle")
    async def branding_cycle(self, ctx: commands.Context) -> None:
        """Force cycle guild icon."""
        async with ctx.typing():
            success = self.cycle()
            await ctx.send("Icon cycle successful" if success else "Icon cycle failed")

    @branding_cmds.command(name="apply")
    async def branding_apply(self, ctx: commands.Context) -> None:
        """Force apply current branding."""
        async with ctx.typing():
            await self.apply()
            await ctx.send("Branding applied")

    @branding_cmds.command(name="set")
    async def branding_set(self, ctx: commands.Context, *, season_name: t.Optional[str] = None) -> None:
        """Manually set season if `season_name` is provided, otherwise reset to current."""
        if season_name is None:
            new_season = get_current_season()
        else:
            new_season = get_season(season_name)
            if new_season is None:
                raise commands.BadArgument("No such season exists")

        if self.current_season is not new_season:
            async with ctx.typing():
                self.current_season = new_season
                await self.refresh()
                await self.apply()
                await self.branding_info(ctx)
        else:
            await ctx.send(f"Season {self.current_season.season_name} already active")


def setup(bot: SeasonalBot) -> None:
    """Load BrandingManager cog."""
    bot.add_cog(BrandingManager(bot))
    log.info("BrandingManager cog loaded")
