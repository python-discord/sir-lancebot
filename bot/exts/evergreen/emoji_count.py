import datetime
import logging
import random
from collections import defaultdict

import discord
from discord.ext import commands

from bot.constants import Colours, ERROR_REPLIES
from bot.utils.pagination import LinePaginator

log = logging.getLogger(__name__)


class EmojiCount(commands.Cog):
    """Command that give random emoji based on category."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def embed_builder(emoji: dict) -> [discord.Embed, str]:
        """Generates an embed with the emoji names and count."""
        embed = discord.Embed(
            color=Colours.orange,
            title="Emoji Count",
            timestamp=datetime.datetime.utcnow()
        )
        msg = []

        if len(emoji) == 1:
            for category_name, category_emojis in emoji.items():
                msg.append(f"There is **{len(category_emojis)}** emoji in the **{category_name}** category")
                embed.set_thumbnail(url=random.choice(category_emojis).url)

        else:
            for category_name, category_emojis in emoji.items():
                emoji_choice = random.choice(category_emojis)
                emoji_info = f'There are **{len(category_emojis)}** emojis in the **{category_name}** category\n'
                if emoji_choice.animated:
                    msg.append(f'<a:{emoji_choice.name}:{emoji_choice.id}> {emoji_info}')
                else:
                    msg.append(f'<:{emoji_choice.name}:{emoji_choice.id}> {emoji_info}')
        return embed, msg

    @staticmethod
    def generate_invalid_embed(ctx: commands.Context) -> [discord.Embed, str]:
        """Generates error embed."""
        embed = discord.Embed(
            color=Colours.soft_red,
            title=random.choice(ERROR_REPLIES)
        )
        msg = []

        emoji_dict = defaultdict(list)
        for emoji in ctx.guild.emojis:
            emoji_dict[emoji.name.split("_")[0]].append(emoji)

        error_comp = ', '.join(emoji_category for emoji_category in emoji_dict)
        msg.append(f"These are the valid categories\n```{error_comp}```")
        return embed, msg

    @commands.command(name="emoji_count", aliases=["ec"])
    async def emoji_count(self, ctx: commands.Context, *, category_query: str = None) -> None:
        """Returns embed with emoji category and info given by the user."""
        emoji_dict = defaultdict(list)

        if not ctx.guild.emojis:
            await ctx.send("No emojis found.")
            return
        log.trace(f"Emoji Category {'' if category_query else 'not '}provided by the user")
        for emoji in ctx.guild.emojis:
            emoji_category = emoji.name.split("_")[0]

            if category_query is not None and emoji_category not in category_query:
                continue

            emoji_dict[emoji_category].append(emoji)

        if len(emoji_dict) == 0:
            log.trace("Invalid name provided by the user")
            embed, msg = self.generate_invalid_embed(ctx)
        else:
            embed, msg = self.embed_builder(emoji_dict)
        await LinePaginator.paginate(lines=msg, ctx=ctx, embed=embed)


def setup(bot: commands.Bot) -> None:
    """Emoji Count Cog load."""
    bot.add_cog(EmojiCount(bot))
