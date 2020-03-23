import asyncio
import itertools
import logging
import random
import typing as t
from datetime import datetime, time, timedelta

import arrow
import discord
from discord.embeds import EmptyEmbed
from discord.ext import commands

from bot.bot import SeasonalBot
from bot.constants import Branding, Colours, Emojis, MODERATION_ROLES, Tokens
from bot.decorators import with_role
from bot.exceptions import BrandingError
from bot.seasons import SeasonBase, get_current_season, get_season

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

STATUS_OK = 200  # HTTP status code

FILE_BANNER = "banner.png"
FILE_AVATAR = "avatar.png"
SERVER_ICONS = "server_icons"

BRANDING_URL = "https://api.github.com/repos/python-discord/branding/contents"

PARAMS = {"ref": "seasonal-structure"}  # Target branch
HEADERS = {"Accept": "application/vnd.github.v3+json"}  # Ensure we use API v3

# A Github token is not necessary for the cog to operate,
# unauthorized requests are however limited to 60 per hour
if Tokens.github:
    HEADERS["Authorization"] = f"token {Tokens.github}"


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
    return "\n".join(file.path for file in files)


async def time_until_midnight() -> timedelta:
    """
    Determine amount of time until the next-up UTC midnight.

    The exact `midnight` moment is actually delayed to 5 seconds after, in order
    to avoid potential problems due to imprecise sleep.
    """
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    midnight = datetime.combine(tomorrow, time(second=5))

    return midnight - now


class BrandingManager(commands.Cog):
    """
    Manages the guild's branding.

    The purpose of this cog is to help automate the synchronization of the branding
    repository with the guild. It is capable of discovering assets in the repository
    via Github's API, resolving download urls for them, and delegating
    to the `bot` instance to upload them to the guild.

    The cog is designed to be entirely autonomous. The `daemon` background task awakens once
    a day (see `time_until_midnight`) to detect new seasons, or to cycle icons within a single
    season. If the `Branding.autostart` constant is True, the `daemon` will launch on start-up,
    otherwise it can be controlled via the `daemon` cmd group.

    All supported operations, e.g. setting seasons, applying the branding, or cycling icons, can
    also be invoked manually, via the following API:

        branding set <season_name>
            - Set the cog's internal state to represent `season_name`, if it exists.
            - If no `season_name` is given, set chronologically current season.
            - This will not automatically apply the season's branding to the guild,
              the cog's state can be detached from the guild.
            - Seasons can therefore be 'previewed' using this command.

        branding info
            - View detailed information about resolved assets for current season.

        branding refresh
            - Refresh internal state, i.e. synchronize with branding repository.

        branding apply
            - Apply the current internal state to the guild, i.e. upload the assets.

        branding cycle
            - If there are multiple available icons for current season, randomly pick
              and apply the next one.

    The daemon calls these methods autonomously as appropriate. The use of this cog
    is locked to moderation roles. As it performs media asset uploads, it is prone to
    rate-limits - the `apply` command should be used with caution. The `set` command can,
    however, be used freely to 'preview' seasonal branding and check whether paths have been
    resolved as appropriate.
    """

    current_season: t.Type[SeasonBase]

    banner: t.Optional[GithubFile]
    avatar: t.Optional[GithubFile]

    available_icons: t.List[GithubFile]
    remaining_icons: t.List[GithubFile]

    should_cycle: t.Iterator

    daemon: t.Optional[asyncio.Task]

    def __init__(self, bot: SeasonalBot) -> None:
        """
        Assign safe default values on init.

        At this point, we don't have information about currently available branding.
        Most of these attributes will be overwritten once the daemon connects, or once
        the `refresh` command is used.
        """
        self.bot = bot
        self.current_season = get_current_season()

        self.banner = None
        self.avatar = None

        self.should_cycle = itertools.cycle([False])

        self.available_icons = []
        self.remaining_icons = []

        if Branding.autostart:
            self.daemon = self.bot.loop.create_task(self._daemon_func())
        else:
            self.daemon = None

    @property
    def _daemon_running(self) -> bool:
        """True if the daemon is currently active, False otherwise."""
        return self.daemon is not None and not self.daemon.done()

    async def _daemon_func(self) -> None:
        """
        Manage all automated behaviour of the BrandingManager cog.

        Once a day, the daemon will perform the following tasks:
            - Update `current_season`
            - Poll Github API to see if the available branding for `current_season` has changed
            - Update assets if changes are detected (banner, guild icon, bot avatar, bot nickname)
            - Check whether it's time to cycle guild icons

        The internal loop runs once when activated, then periodically at the time
        given by `time_until_midnight`.

        All method calls in the internal loop are considered safe, i.e. no errors propagate
        to the daemon's loop. The daemon itself does not perform any error handling on its own.
        """
        await self.bot.wait_until_ready()

        while True:
            self.current_season = get_current_season()
            branding_changed = await self.refresh()

            if branding_changed:
                await self.apply()

            elif next(self.should_cycle):
                await self.cycle()

            until_midnight = await time_until_midnight()
            await asyncio.sleep(until_midnight.total_seconds())

    async def _info_embed(self) -> discord.Embed:
        """Make an informative embed representing current season."""
        info_embed = discord.Embed(description=self.current_season.description, colour=self.current_season.colour)

        # If we're in a non-evergreen season, also show active months
        if self.current_season is not SeasonBase:
            active_months = ", ".join(m.name for m in self.current_season.months)
            title = f"{self.current_season.season_name} ({active_months})"
        else:
            title = self.current_season.season_name

        # Use the author field to show the season's name and avatar if available
        info_embed.set_author(name=title, icon_url=self.avatar.download_url if self.avatar else EmptyEmbed)

        banner = self.banner.path if self.banner is not None else "Unavailable"
        info_embed.add_field(name="Banner", value=banner, inline=False)

        avatar = self.avatar.path if self.avatar is not None else "Unavailable"
        info_embed.add_field(name="Avatar", value=avatar, inline=False)

        icons = await pretty_files(self.available_icons) or "Unavailable"
        info_embed.add_field(name="Available icons", value=icons, inline=False)

        # Only display cycle frequency if we're actually cycling
        if len(self.available_icons) > 1 and Branding.cycle_frequency:
            info_embed.set_footer(text=f"Icon cycle frequency: {Branding.cycle_frequency}")

        return info_embed

    async def _reset_remaining_icons(self) -> None:
        """Set `remaining_icons` to a shuffled copy of `available_icons`."""
        self.remaining_icons = random.sample(self.available_icons, k=len(self.available_icons))

    async def _reset_should_cycle(self) -> None:
        """
        Reset the `should_cycle` counter based on configured frequency.

        Counter will always yield False if either holds:
            - Branding.cycle_frequency is falsey
            - There are fewer than 2 available icons for current season

        Cycling can be easily turned off, and we prevent re-uploading the same icon repeatedly.
        """
        if len(self.available_icons) > 1 and Branding.cycle_frequency:
            wait_period = [False] * (Branding.cycle_frequency - 1)
            counter = itertools.cycle(wait_period + [True])
        else:
            counter = itertools.cycle([False])

        self.should_cycle = counter

    async def _get_files(self, path: str) -> t.Dict[str, GithubFile]:
        """
        Poll `path` in branding repo for information about present files.

        Return dict mapping from filename to corresponding `GithubFile` instance.
        This may return an empty dict if the response status is non-200,
        or if the target directory is empty.
        """
        url = f"{BRANDING_URL}/{path}"
        async with self.bot.http_session.get(url, headers=HEADERS, params=PARAMS) as resp:
            # Short-circuit if we get non-200 response
            if resp.status != STATUS_OK:
                log.error(f"Github API returned non-200 response: {resp}")
                return {}
            directory = await resp.json()  # Directory at `path`

        return {
            file["name"]: GithubFile(file["download_url"], file["path"], file["sha"])
            for file in directory
        }

    async def refresh(self) -> bool:
        """
        Poll Github API to refresh currently available icons.

        If the current season is not the evergreen, and lacks at least one asset,
        we also poll the evergreen seasonal dir as fallback for missing assets.

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

        if branding_changed:
            log.info(f"New branding detected (season: {self.current_season.season_name})")
            await self._reset_remaining_icons()
            await self._reset_should_cycle()

        return branding_changed

    async def cycle(self) -> bool:
        """
        Apply the next-up server icon.

        Returns True if an icon is available and successfully gets applied, False otherwise.
        """
        if not self.available_icons:
            log.info("Cannot cycle: no icons for this season")
            return False

        if not self.remaining_icons:
            await self._reset_remaining_icons()
            log.info(f"Set remaining icons: {await pretty_files(self.remaining_icons)}")

        next_up, *self.remaining_icons = self.remaining_icons
        success = await self.bot.set_icon(next_up.download_url)

        return success

    async def apply(self) -> t.List[str]:
        """
        Apply current branding to the guild and bot.

        This delegates to the bot instance to do all the work. We only provide download urls
        for available assets. Assets unavailable in the branding repo will be ignored.

        Returns a list of names of all failed assets. An asset is considered failed
        if it isn't found in the branding repo, or if something goes wrong while the
        bot is trying to apply it.

        An empty list denotes that all assets have been applied successfully.
        """
        report = {asset: False for asset in ("banner", "avatar", "nickname", "icon")}

        if self.banner is not None:
            report["banner"] = await self.bot.set_banner(self.banner.download_url)

        if self.avatar is not None:
            report["avatar"] = await self.bot.set_avatar(self.avatar.download_url)

        if self.current_season.bot_name:
            report["nickname"] = await self.bot.set_nickname(self.current_season.bot_name)

        report["icon"] = await self.cycle()

        failed_assets = [asset for asset, succeeded in report.items() if not succeeded]
        return failed_assets

    @with_role(*MODERATION_ROLES)
    @commands.group(name="branding")
    async def branding_cmds(self, ctx: commands.Context) -> None:
        """Group for commands allowing manual control of the cog."""
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
        """Apply the next-up guild icon, if multiple are available."""
        async with ctx.typing():
            success = await self.cycle()
            if not success:
                raise BrandingError("Failed to cycle icon")

            response = discord.Embed(description=f"Success {Emojis.ok_hand}", colour=Colours.soft_green)
            await ctx.send(embed=response)

    @branding_cmds.command(name="apply")
    async def branding_apply(self, ctx: commands.Context) -> None:
        """Apply current branding (i.e. internal state) to the guild."""
        async with ctx.typing():
            failed_assets = await self.apply()
            if failed_assets:
                raise BrandingError(f"Failed to apply following assets: {', '.join(failed_assets)}")

            response = discord.Embed(description=f"All assets applied {Emojis.ok_hand}", colour=Colours.soft_green)
            await ctx.send(embed=response)

    @branding_cmds.command(name="set")
    async def branding_set(self, ctx: commands.Context, *, season_name: t.Optional[str] = None) -> None:
        """
        Manually set season if `season_name` is provided, otherwise reset to current.

        This only pre-loads the cog's internal state to the chosen season, but does not
        automatically apply the branding. As that is an expensive operation, the `apply`
        command must be called explicitly after this command finishes.

        This means that this command can be used to 'preview' a season gathering info
        about its available assets, without applying them to the guild.

        If the daemon is running, it will automatically reset the season to current when
        it wakes up. The season set via this command can therefore remain 'detached' from
        what it should be - the daemon will make sure that it's set back properly.
        """
        if season_name is None:
            new_season = get_current_season()
        else:
            new_season = get_season(season_name)
            if new_season is None:
                raise BrandingError("No such season exists")

        if self.current_season is new_season:
            raise BrandingError(f"Season {self.current_season.season_name} already active")

        self.current_season = new_season
        async with ctx.typing():
            await self.refresh()
            await self.branding_info(ctx)

    @branding_cmds.group(name="daemon", aliases=["d"])
    async def daemon_group(self, ctx: commands.Context) -> None:
        """
        Check whether the daemon is currently active.

        Sub-commands allow starting and stopping the daemon.
        """
        if not ctx.invoked_subcommand:
            if self._daemon_running:
                remaining_time = (arrow.utcnow() + await time_until_midnight()).humanize()
                response = discord.Embed(description=f"Daemon running {Emojis.ok_hand}", colour=Colours.soft_green)
                response.set_footer(text=f"Next refresh {remaining_time}")
            else:
                response = discord.Embed(description="Daemon not running", colour=Colours.soft_red)

            await ctx.send(embed=response)

    @daemon_group.command(name="start")
    async def daemon_start(self, ctx: commands.Context) -> None:
        """If the daemon isn't running, start it."""
        if self._daemon_running:
            raise BrandingError("Daemon already running!")

        self.daemon = self.bot.loop.create_task(self._daemon_func())
        response = discord.Embed(description=f"Daemon started {Emojis.ok_hand}", colour=Colours.soft_green)
        await ctx.send(embed=response)

    @daemon_group.command(name="stop")
    async def daemon_stop(self, ctx: commands.Context) -> None:
        """If the daemon is running, stop it."""
        if not self._daemon_running:
            raise BrandingError("Daemon not running!")

        self.daemon.cancel()
        response = discord.Embed(description=f"Daemon stopped {Emojis.ok_hand}", colour=Colours.soft_green)
        await ctx.send(embed=response)


def setup(bot: SeasonalBot) -> None:
    """Load BrandingManager cog."""
    bot.add_cog(BrandingManager(bot))
    log.info("BrandingManager cog loaded")
