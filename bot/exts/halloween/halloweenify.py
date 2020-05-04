import logging
from json import load
from pathlib import Path
from random import choice

import discord
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

log = logging.getLogger(__name__)


class Halloweenify(commands.Cog):
    """A cog to change a invokers nickname to a spooky one!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(1, 300, BucketType.user)
    @commands.command()
    async def halloweenify(self, ctx: commands.Context) -> None:
        """Change your nickname into a much spookier one!"""
        async with ctx.typing():
            with open(Path("bot/resources/halloween/halloweenify.json"), "r") as f:
                data = load(f)

            # Choose a random character from our list we loaded above and set apart the nickname and image url.
            character = choice(data["characters"])
            nickname = ''.join([nickname for nickname in character])
            image = ''.join([character[nickname] for nickname in character])

            # Build up a Embed
            embed = discord.Embed()
            embed.colour = discord.Colour.dark_orange()
            embed.title = "Not spooky enough?"
            embed.description = (
                f"**{ctx.author.display_name}** wasn\'t spooky enough for you? That\'s understandable, "
                f"{ctx.author.display_name} isn\'t scary at all! "
                "Let me think of something better. Hmm... I got it!\n\n "
            )
            embed.set_image(url=image)

            try:
                if isinstance(ctx.author, discord.Member):
                    await ctx.author.edit(nick=nickname)
                    embed.description += f"Your new nickname will be: \n:ghost: **{nickname}** :jack_o_lantern:"

                else:   # The command has been invoked in DM
                    embed.description += (
                        f"Your new nickname should be: \n :ghost: **{nickname}** :jack_o_lantern: \n\n"
                        f"Feel free to change it yourself, or invoke the command again inside the server."
                    )

            except Forbidden:   # The bot doesn't have enough permission
                embed.description += (
                    f"Your new nickname should be: \n :ghost: **{nickname}** :jack_o_lantern: \n\n"
                    f"Although it looks like I can't change it myself, but feel free to change it yourself."
                )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Halloweenify Cog load."""
    bot.add_cog(Halloweenify(bot))
