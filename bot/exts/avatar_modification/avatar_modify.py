import asyncio
import json
import math
import string
import unicodedata
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Colours, Emojis
from bot.exts.avatar_modification._effects import PfpEffects
from bot.utils.halloween import spookifications

log = get_logger(__name__)

_EXECUTOR = ThreadPoolExecutor(10)

FILENAME_STRING = "{effect}_{author}.png"

MAX_SQUARES = 10_000

GENDER_OPTIONS = json.loads(Path("bot/resources/holidays/pride/gender_options.json").read_text("utf8"))


async def in_executor[T](func: Callable[..., T], *args) -> T:
    """
    Runs the given synchronous function `func` in an executor.

    This is useful for running slow, blocking code within async
    functions, so that they don't block the bot.
    """
    log.trace(f"Running {func.__name__} in an executor.")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, func, *args)


def file_safe_name(effect: str, display_name: str) -> str:
    """Returns a file safe filename based on the given effect and display name."""
    valid_filename_chars = f"-_. {string.ascii_letters}{string.digits}"

    file_name = FILENAME_STRING.format(effect=effect, author=display_name)

    # Replace spaces
    file_name = file_name.replace(" ", "_")

    # Normalize unicode characters
    cleaned_filename = unicodedata.normalize("NFKD", file_name).encode("ASCII", "ignore").decode()

    # Remove invalid filename characters
    cleaned_filename = "".join(c for c in cleaned_filename if c in valid_filename_chars)
    return cleaned_filename


class AvatarModify(commands.Cog):
    """Various commands for users to apply affects to their own avatars."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def _fetch_user(self, user_id: int) -> discord.User | None:
        """
        Fetches a user and handles errors.

        This helper function is required as the member cache doesn't always have the most up to date
        profile picture. This can lead to errors if the image is deleted from the Discord CDN.
        fetch_member can't be used due to the avatar url being part of the user object, and
        some weird caching that D.py does
        """
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.errors.NotFound:
            log.debug(f"User {user_id} could not be found.")
            return None
        except discord.HTTPException:
            log.exception(f"Exception while trying to retrieve user {user_id} from Discord.")
            return None

        return user

    @commands.group(aliases=("avatar_mod", "pfp_mod", "avatarmod", "pfpmod"))
    async def avatar_modify(self, ctx: commands.Context) -> None:
        """Groups all of the pfp modifying commands to allow a single concurrency limit."""
        if not ctx.invoked_subcommand:
            await self.bot.invoke_help_command(ctx)

    @avatar_modify.command(name="8bitify", root_aliases=("8bitify",))
    async def eightbit_command(self, ctx: commands.Context) -> None:
        """Pixelates your avatar and changes the palette to an 8bit one."""
        async with ctx.typing():
            user = await self._fetch_user(ctx.author.id)
            if not user:
                await ctx.send(f"{Emojis.cross_mark} Could not get user info.")
                return

            image_bytes = await user.display_avatar.replace(size=1024).read()
            file_name = file_safe_name("eightbit_avatar", ctx.author.display_name)

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
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=user.display_avatar.url)

        await ctx.send(embed=embed, file=file)

    @avatar_modify.command(name="reverse", root_aliases=("reverse",))
    async def reverse(self, ctx: commands.Context, *, text: str | None) -> None:
        """
        Reverses the sent text.

        If no text is provided, the user's profile picture will be reversed.
        """
        if text:
            await ctx.send(f"> {text[::-1]}", allowed_mentions=discord.AllowedMentions.none())
            return

        async with ctx.typing():
            user = await self._fetch_user(ctx.author.id)
            if not user:
                await ctx.send(f"{Emojis.cross_mark} Could not get user info.")
                return

            image_bytes = await user.display_avatar.replace(size=1024).read()
            filename = file_safe_name("reverse_avatar", ctx.author.display_name)

            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                PfpEffects.flip_effect,
                filename
            )

            embed = discord.Embed(
                title="Your reversed avatar.",
                description="Here is your reversed avatar. I think it is a spitting image of you."
            )

            embed.set_image(url=f"attachment://{filename}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=user.display_avatar.url)

            await ctx.send(embed=embed, file=file)

    @avatar_modify.command(aliases=("easterify",), root_aliases=("easterify", "avatareasterify"))
    async def avatareasterify(self, ctx: commands.Context, *colours: discord.Colour | str) -> None:
        """
        Easterify the user's avatar.

        Given colours will produce a personalised egg in the corner, similar to the egg_decorate command.
        If colours are not given, a nice little chocolate bunny will sit in the corner.
        Colours are split by spaces, unless you wrap the colour name in double quotes.
        Discord colour names, HTML colour names, XKCD colour names and hex values are accepted.
        """
        async def send(*args, **kwargs) -> str:
            """
            Replace the original ctx.send.

            When invoking the egg decorating command, the egg itself doesn't print to to the channel.
            Return the message content so that if any errors occur, the error message can be output.
            """
            if args:
                return args[0]
            return None

        async with ctx.typing():
            user = await self._fetch_user(ctx.author.id)
            if not user:
                await ctx.send(f"{Emojis.cross_mark} Could not get user info.")
                return

            egg = None
            if colours:
                send_message = ctx.send
                ctx.send = send  # Assigns ctx.send to a fake send
                egg = await ctx.invoke(self.bot.get_command("eggdecorate"), *colours)
                if isinstance(egg, str):  # When an error message occurs in eggdecorate.
                    await send_message(egg)
                    return
                ctx.send = send_message  # Reassigns ctx.send

            image_bytes = await user.display_avatar.replace(size=256).read()
            file_name = file_safe_name("easterified_avatar", ctx.author.display_name)

            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                PfpEffects.easterify_effect,
                file_name,
                egg
            )

            embed = discord.Embed(
                title="Your Lovely Easterified Avatar!",
                description="Here is your lovely avatar, all bright and colourful\nwith Easter pastel colours. Enjoy :D"
            )
            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=user.display_avatar.url)

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
            file_name = file_safe_name("pride_avatar", ctx.author.display_name)

            file = await in_executor(
                PfpEffects.apply_effect,
                image_bytes,
                PfpEffects.pridify_effect,
                file_name,
                pixels,
                flag
            )

            embed = discord.Embed(
                title="Your Lovely Pride Avatar!",
                description=f"Here is your lovely avatar, surrounded by\n a beautiful {option} flag. Enjoy :D"
            )
            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=ctx.author.display_avatar.url)
            await ctx.send(file=file, embed=embed)

    @avatar_modify.group(
        aliases=("avatarpride", "pridepfp", "prideprofile"),
        root_aliases=("prideavatar", "avatarpride", "pridepfp", "prideprofile"),
        invoke_without_command=True
    )
    async def prideavatar(self, ctx: commands.Context, option: str = "lgbt", pixels: int = 64) -> None:
        """
        Surround an avatar with a border of a specified LGBT flag.

        Default to the LGBT rainbow flag if none is given.
        The amount of pixels can be given which determines the thickness of the flag border.
        A maximum of 512px is enforced, defaults to a 64px border.
        The full image is 1024x1024.
        """
        option = option.lower()
        pixels = max(0, min(512, pixels))
        flag = GENDER_OPTIONS.get(option)
        if flag is None:
            await ctx.send("I don't have that flag!")
            return

        async with ctx.typing():
            user = await self._fetch_user(ctx.author.id)
            if not user:
                await ctx.send(f"{Emojis.cross_mark} Could not get user info.")
                return
            image_bytes = await user.display_avatar.replace(size=1024).read()
            await self.send_pride_image(ctx, image_bytes, pixels, flag, option)

    @prideavatar.command()
    async def flags(self, ctx: commands.Context) -> None:
        """Lists the flags that can be used with the prideavatar command."""
        choices = sorted(set(GENDER_OPTIONS.values()))
        options = "• " + "\n• ".join(choices)
        embed = discord.Embed(
            title="I have the following flags:",
            description=options,
            colour=Colours.soft_red
        )
        await ctx.send(embed=embed)

    @avatar_modify.command(
        aliases=("savatar", "spookify"),
        root_aliases=("spookyavatar", "spookify", "savatar"),
        brief="Spookify a user's avatar."
    )
    async def spookyavatar(self, ctx: commands.Context) -> None:
        """Spookify the user's avatar, with a random *spooky* effect."""
        user = await self._fetch_user(ctx.author.id)
        if not user:
            await ctx.send(f"{Emojis.cross_mark} Could not get user info.")
            return

        async with ctx.typing():
            image_bytes = await user.display_avatar.replace(size=1024).read()

            file_name = file_safe_name("spooky_avatar", ctx.author.display_name)

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
            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}.", icon_url=ctx.author.display_avatar.url)

            await ctx.send(file=file, embed=embed)

    @avatar_modify.command(name="mosaic", root_aliases=("mosaic",))
    async def mosaic_command(self, ctx: commands.Context, squares: int = 16) -> None:
        """Splits your avatar into x squares, randomizes them and stitches them back into a new image!"""
        async with ctx.typing():
            user = await self._fetch_user(ctx.author.id)
            if not user:
                await ctx.send(f"{Emojis.cross_mark} Could not get user info.")
                return

            if not 1 <= squares <= MAX_SQUARES:
                raise commands.BadArgument(f"Squares must be a positive number less than or equal to {MAX_SQUARES:,}.")

            sqrt = math.sqrt(squares)

            if not sqrt.is_integer():
                squares = math.ceil(sqrt) ** 2  # Get the next perfect square

            file_name = file_safe_name("mosaic_avatar", ctx.author.display_name)

            img_bytes = await user.display_avatar.replace(size=1024).read()

            file = await in_executor(
                PfpEffects.apply_effect,
                img_bytes,
                PfpEffects.mosaic_effect,
                file_name,
                squares,
            )

            if squares == 1:
                title = "Hooh... that was a lot of work"
                description = "I present to you... Yourself!"
            elif squares == MAX_SQUARES:
                title = "Testing the limits I see..."
                description = "What a masterpiece. :star:"
            else:
                title = "Your mosaic avatar"
                description = f"Here is your avatar. I think it looks a bit *puzzling*\nMade with {squares} squares."

            embed = discord.Embed(
                title=title,
                description=description,
                colour=Colours.blue
            )

            embed.set_image(url=f"attachment://{file_name}")
            embed.set_footer(text=f"Made by {ctx.author.display_name}", icon_url=user.display_avatar.url)

            await ctx.send(file=file, embed=embed)


async def setup(bot: Bot) -> None:
    """Load the AvatarModify cog."""
    await bot.add_cog(AvatarModify(bot))
