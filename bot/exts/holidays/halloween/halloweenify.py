import logging
from json import loads
from pathlib import Path
from random import choice

import discord
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext.commands import BucketType

from bot.bot import Bot

log = logging.getLogger(__name__)

HALLOWEENIFY_DATA = loads(Path("bot/resources/holidays/halloween/halloweenify.json").read_text("utf8"))


class Halloweenify(commands.Cog):
    """A cog to change a invokers nickname to a spooky one!"""

    @commands.cooldown(1, 300, BucketType.user)
    @commands.command()
    async def halloweenify(self, ctx: commands.Context) -> None:
        """Change your nickname into a much spookier one!"""
        async with ctx.typing():
            # Choose a random character from our list we loaded above and set apart the nickname and image url.
            character = choice(HALLOWEENIFY_DATA["characters"])
            nickname = "".join(nickname for nickname in character)
            image = "".join(character[nickname] for nickname in character)

            # Build up a Embed
            embed = discord.Embed()
            embed.colour = discord.Colour.dark_orange()
            embed.title = "Not spooky enough?"
            embed.description = (
                f"**{ctx.author.display_name}** wasn't spooky enough for you? That's understandable, "
                f"{ctx.author.display_name} isn't scary at all! "
                "Let me think of something better. Hmm... I got it!\n\n "
            )
            embed.set_image(url=image)

            if isinstance(ctx.author, discord.Member):
                try:
                    await ctx.author.edit(nick=nickname)
                    embed.description += f"Your new nickname will be: \n:ghost: **{nickname}** :jack_o_lantern:"

                except Forbidden:   # The bot doesn't have enough permission
                    embed.description += (
                        f"Your new nickname should be: \n :ghost: **{nickname}** :jack_o_lantern: \n\n"
                        f"It looks like I cannot change your name, but feel free to change it yourself."
                    )

            else:   # The command has been invoked in DM
                embed.description += (
                    f"Your new nickname should be: \n :ghost: **{nickname}** :jack_o_lantern: \n\n"
                    f"Feel free to change it yourself, or invoke the command again inside the server."
                )

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Halloweenify Cog."""
    await bot.add_cog(Halloweenify())
