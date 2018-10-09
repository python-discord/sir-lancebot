from pathlib import Path
from json import load
from random import choice


import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType


class Halloweenify:

    """
    A cog to change a invokers nickname to a spooky one!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 300, BucketType.user)
    @commands.command()
    async def halloweenify(self, ctx):
        with open(Path('../bot/resources', 'halloweenify.json'), 'r') as f:
            data = load(f)

        # Choose a random character from our list we loaded above and set apart the nickname and image url.
        character = choice(data['characters'])
        nickname = ''.join([nickname for nickname in character])
        image = ''.join([character[nickname] for nickname in character])

        # Build up a Embed
        embed = discord.Embed()
        embed.colour = discord.Colour.dark_orange()
        embed.title = 'Wow!'
        embed.description = (
            f'Your previous nickname, **{ctx.author.display_name}**, wasn\'t spooky enough for you that you have '
            f'decided to change it?! Okay, your new nickname will be **{nickname}**.\n\n'
        )
        embed.set_image(url=image)

        await ctx.author.edit(nick=nickname)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Halloweenify(bot))
