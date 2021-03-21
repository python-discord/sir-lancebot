import asyncio
import json
import logging
import typing as t
from concurrent.futures import ThreadPoolExecutor

import discord
from aiohttp import client_exceptions
from discord.ext import commands
from discord.ext.commands.errors import BadArgument

from bot.constants import Colours
from bot.exts.evergreen.profile_pic_modification._effects import PfpEffects
from bot.utils.extensions import invoke_help_command
from bot.utils.halloween import spookifications

log = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(10)

FILENAME_STRING = "{effect}_{author}.png"

with open('bot/resources/pride/gender_options.json') as f:
    GENDER_OPTIONS = json.loads(f.read())


async def in_executor(func: t.Callable, *args) -> t.Any:
    """
    Runs the given synchronus function `func` in an executor.

    This is useful for running slow, blocking code within async
    functions, so that they don't block the bot.
    """
    log.trace(f"Running {func.__name__} in an executor.")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, func, *args)


class PfpModify(commands.Cog):
    """Various commands for users to change their own profile picture."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group()
    async def pfp_modify(self, ctx: commands.Context) -> None:
        """Groups all of the pfp modifying commands to allow a single concurrency limit."""
        if not ctx.invoked_subcommand:
            await invoke_help_command(ctx)

    @pfp_modify.command(name="8bitify", root_aliases=("8bitify",))
    async def eightbit_command(self, ctx: commands.Context) -> None:
        """Pixelates your avatar and changes the palette to an 8bit one."""
        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            file_name = FILENAME_STRING.format(
                effect="eightbit_avatar",
                author=ctx.author.display_name
            )

            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                PfpEffects.eight_bitify_effect,
                file_name
            )

            embed = discord.Embed(
                title="Your 8-bit avatar",
                description="Here is your avatar. I think it looks all cool and 'retro'."
            )

            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed, file=file)

    @pfp_modify.command(pass_context=True, aliases=["easterify"], root_aliases=("easterify", "avatareasterify"))
    async def avatareasterify(self, ctx: commands.Context, *colours: t.Union[discord.Colour, str]) -> None:
        """
        This "Easterifies" the user's avatar.

        Given colours will produce a personalised egg in the corner, similar to the egg_decorate command.
        If colours are not given, a nice little chocolate bunny will sit in the corner.
        Colours are split by spaces, unless you wrap the colour name in double quotes.
        Discord colour names, HTML colour names, XKCD colour names and hex values are accepted.
        """
        async def send(*args, **kwargs) -> str:
            """
            This replaces the original ctx.send.

            When invoking the egg decorating command, the egg itself doesn't print to to the channel.
            Returns the message content so that if any errors occur, the error message can be output.
            """
            if args:
                return args[0]

        async with ctx.typing():
            egg = None
            if colours:
                send_message = ctx.send
                ctx.send = send  # Assigns ctx.send to a fake send
                egg = await ctx.invoke(self.bot.get_command("eggdecorate"), *colours)
                if isinstance(egg, str):  # When an error message occurs in eggdecorate.
                    await send_message(egg)
                    return
                ctx.send = send_message  # Reassigns ctx.send

            image_bytes = await ctx.author.avatar_url_as(size=256).read()
            file_name = FILENAME_STRING.format(
                effect="easterified_avatar",
                author=ctx.author.display_name
            )

            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                PfpEffects.easterify_effect,
                file_name,
                egg
            )

            embed = discord.Embed(
                name="Your Lovely Easterified Avatar!",
                description="Here is your lovely avatar, all bright and colourful\nwith Easter pastel colours. Enjoy :D"
            )
            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=ctx.author.avatar_url)

        await ctx.send(file=file, embed=embed)

    @staticmethod
    async def send_pride_image(
        ctx: commands.Context,
        image_bytes: bytes,
        pixels: int,
        flag: str,
        option: str
    ) -> None:
        """Gets and sends the image in an embed. Used by the pride commands."""
        async with ctx.typing():
            file_name = FILENAME_STRING.format(
                effect="pride_avatar",
                author=ctx.author.display_name
            )

            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                PfpEffects.pridify_effect,
                file_name,
                pixels,
                flag
            )

            embed = discord.Embed(
                name="Your Lovely Pride Avatar!",
                description=f"Here is your lovely avatar, surrounded by\n a beautiful {option} flag. Enjoy :D"
            )
            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=ctx.author.avatar_url)
            await ctx.send(file=file, embed=embed)

    @pfp_modify.group(
        aliases=["avatarpride", "pridepfp", "prideprofile"],
        root_aliases=("prideavatar", "avatarpride", "pridepfp", "prideprofile"),
        invoke_without_command=True
    )
    async def prideavatar(self, ctx: commands.Context, option: str = "lgbt", pixels: int = 64) -> None:
        """
        This surrounds an avatar with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """
        option = option.lower()
        pixels = max(0, min(512, pixels))
        flag = GENDER_OPTIONS.get(option)
        if flag is None:
            await ctx.send("I don't have that flag!")
            return

        async with ctx.typing():
            image_bytes = await ctx.author.avatar_url.read()
            await self.send_pride_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def image(self, ctx: commands.Context, url: str, option: str = "lgbt", pixels: int = 64) -> None:
        """
        This surrounds the image specified by the URL with a border of a specified LGBT flag.

        This defaults to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        This has a maximum of 512px and defaults to a 64px border.
        The full image is 1024x1024.
        """
        option = option.lower()
        pixels = max(0, min(512, pixels))
        flag = GENDER_OPTIONS.get(option)
        if flag is None:
            await ctx.send("I don't have that flag!")
            return

        async with ctx.typing():
            try:
                async with self.bot.http_session.get(url) as response:
                    if response.status != 200:
                        await ctx.send("Bad response from provided URL!")
                        return
                    image_bytes = await response.read()
            except client_exceptions.ClientConnectorError:
                raise BadArgument("Cannot connect to provided URL!")
            except client_exceptions.InvalidURL:
                raise BadArgument("Invalid URL!")

            await self.send_pride_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def flags(self, ctx: commands.Context) -> None:
        """This lists the flags that can be used with the prideavatar command."""
        choices = sorted(set(GENDER_OPTIONS.values()))
        options = "• " + "\n• ".join(choices)
        embed = discord.Embed(
            title="I have the following flags:",
            description=options,
            colour=Colours.soft_red
        )
        await ctx.send(embed=embed)

    @pfp_modify.command(
        name='spookyavatar',
        aliases=('savatar', 'spookify'),
        root_aliases=('spookyavatar', 'spookify', 'savatar'),
        brief='Spookify an user\'s avatar.'
    )
    async def spooky_avatar(self, ctx: commands.Context, user: discord.Member = None) -> None:
        """This "spookifies" the given user's avatar, with a random *spooky* effect."""
        if user is None:
            user = ctx.message.author

        async with ctx.typing():
            image_bytes = await user.avatar_url.read()

            file_name = FILENAME_STRING.format(
                effect="spooky_avatar",
                author=user.display_name
            )
            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                spookifications.get_random_effect,
                file_name
            )

            embed = discord.Embed(
                title="Is this you or am I just really paranoid?",
                colour=Colours.soft_red
            )
            embed.set_author(name=user.name, icon_url=user.avatar_url)
            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=ctx.author.avatar_url)

            await ctx.send(file=file, embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the PfpModify cog."""
    bot.add_cog(PfpModify(bot))
