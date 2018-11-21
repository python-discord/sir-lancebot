import logging
from json import load
from pathlib import Path
from random import choice

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

log = logging.getLogger(__name__)


class Halloweenify:
    """
    A cog to change a invokers nickname to a spooky one!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 300, BucketType.user)
    @commands.command()
    async def halloweenify(self, ctx):
        """
        Change your nickname into a much spookier one!
        """
        async with ctx.typing():
            with open(Path('bot', 'resources', 'halloween', 'halloweenify.json'), 'r') as f:
                data = load(f)

            # Choose a random character from our list we loaded above and set apart the nickname and image url.
            character = choice(data['characters'])
            nickname = ''.join([nickname for nickname in character])
            image = ''.join([character[nickname] for nickname in character])

            # Build up a Embed
            embed = discord.Embed()
            embed.colour = discord.Colour.dark_orange()
            embed.title = 'Not spooky enough?'
            embed.description = (
                f'**{ctx.author.display_name}** wasn\'t spooky enough for you? That\'s understandable, '
                f'{ctx.author.display_name} isn\'t scary at all! '
                'Let me think of something better. Hmm... I got it!\n\n '
                f'Your new nickname will be: \n :ghost: **{nickname}** :jack_o_lantern:'
            )
            embed.set_image(url=image)

            await ctx.author.edit(nick=nickname)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Halloweenify(bot))
    log.debug("Halloweenify cog loaded")
