import datetime
import logging
import random
from typing import Dict, Optional

import discord
from discord.ext import commands

from bot.constants import Colours

log = logging.getLogger(__name__)


class EmojiCount(commands.Cog):
    """Command that give random emoji based on category."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def embed_builder(self, emoji: dict) -> discord.Embed:
        """Generates an embed with the emoji names and count."""
        embed = discord.Embed()
        embed.color = Colours.orange
        embed.title = "Emoji Count"
        embed.timestamp = datetime.datetime.utcnow()
        if len(emoji) == 1:
            for key, value in emoji.items():
                print(key)
                embed.description = f"There are **{len(value)}** emojis in the **{key}** category"
                embed.set_thumbnail(url=random.choice(value).url)
        else:
            msg = ''
            for key, value in emoji.items():
                emoji_choice = random.choice(value)
                error_msg = f'There are **{len(value)}** emojis in the **{key}** category\n'
                msg += f'<:{emoji_choice.name}:{emoji_choice.id}> {error_msg}'
            embed.description = msg
        log.trace('Emoji embed sent')
        return embed

    @staticmethod
    def generate_invalid_embed(ctx: commands.Context) -> discord.Embed:
        """Genrates error embed."""
        embed = discord.Embed()
        embed.color = Colours.soft_red
        embed.title = "Invalid Input"
        emoji_dict = {}
        for emoji in ctx.guild.emojis:
            emoji_dict.update({emoji.name.split("_")[0]: []})
        error_comp = ', '.join(key for key in emoji_dict.keys())
        embed.description = f"These are the valid categories\n```{error_comp}```"
        log.trace("Error embed sent")
        return embed

    def emoji_list(self, ctx: commands.Context, emojis: dict) -> Dict:
        """Genrates dictionary of emojis given by the user."""
        for emoji in ctx.guild.emojis:
            for key, value in emojis.items():
                if emoji.name.split("_")[0] == key:
                    value.append(emoji)
        log.trace("Emoji dict sent")
        return emojis

    @commands.command(name="ec")
    async def ec(self, ctx: commands.Context, *, emoji: str = None) -> Optional[str]:
        """Returns embed with emoji category and info given by user."""
        emoji_dict = {}
        for a in ctx.guild.emojis:
            if emoji is None:
                log.trace("Emoji Category not provided by the user")
                emoji_dict.update({a.name.split("_")[0]: []})
            elif a.name.split("_")[0] in emoji:
                log.trace("Emoji Category provided by the user")
                emoji_dict.update({a.name.split("_")[0]: []})
        emoji_dict = self.emoji_list(ctx, emoji_dict)
        if len(emoji_dict) == 0:
            embed = self.generate_invalid_embed(ctx)
            log.trace("Error embed received")
        else:
            embed = self.embed_builder(emoji_dict)
            log.trace("Emoji embed received")
        await ctx.send(embed=embed)
        log.trace("Embed sent")


def setup(bot: commands.Bot) -> None:
    """Emoji Count Cog load."""
    bot.add_cog(EmojiCount(bot))
