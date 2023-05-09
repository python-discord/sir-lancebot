import logging
import random
import textwrap
from collections import defaultdict
from datetime import UTC, datetime

from discord import Color, Embed, Emoji
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, ERROR_REPLIES
from bot.utils.pagination import LinePaginator
from bot.utils.time import time_since

log = logging.getLogger(__name__)


class Emojis(commands.Cog):
    """A collection of commands related to emojis in the server."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @staticmethod
    def embed_builder(emoji: dict) -> tuple[Embed, list[str]]:
        """Generates an embed with the emoji names and count."""
        embed = Embed(
            color=Colours.orange,
            title="Emoji Count",
            timestamp=datetime.now(tz=UTC)
        )
        msg = []

        if len(emoji) == 1:
            for category_name, category_emojis in emoji.items():
                if len(category_emojis) == 1:
                    msg.append(f"There is **{len(category_emojis)}** emoji in the **{category_name}** category.")
                else:
                    msg.append(f"There are **{len(category_emojis)}** emojis in the **{category_name}** category.")
                embed.set_thumbnail(url=random.choice(category_emojis).url)

        else:
            for category_name, category_emojis in emoji.items():
                emoji_choice = random.choice(category_emojis)
                if len(category_emojis) > 1:
                    emoji_info = f"There are **{len(category_emojis)}** emojis in the **{category_name}** category."
                else:
                    emoji_info = f"There is **{len(category_emojis)}** emoji in the **{category_name}** category."
                if emoji_choice.animated:
                    msg.append(f"<a:{emoji_choice.name}:{emoji_choice.id}> {emoji_info}")
                else:
                    msg.append(f"<:{emoji_choice.name}:{emoji_choice.id}> {emoji_info}")
        return embed, msg

    @staticmethod
    def generate_invalid_embed(emojis: list[Emoji]) -> tuple[Embed, list[str]]:
        """Generates error embed for invalid emoji categories."""
        embed = Embed(
            color=Colours.soft_red,
            title=random.choice(ERROR_REPLIES)
        )
        msg = []

        emoji_dict = defaultdict(list)
        for emoji in emojis:
            emoji_dict[emoji.name.split("_")[0]].append(emoji)

        error_comp = ", ".join(emoji_dict)
        msg.append(f"These are the valid emoji categories:\n```\n{error_comp}\n```")
        return embed, msg

    @commands.group(name="emoji", invoke_without_command=True)
    async def emoji_group(self, ctx: commands.Context, emoji: Emoji | None) -> None:
        """A group of commands related to emojis."""
        if emoji is not None:
            await ctx.invoke(self.info_command, emoji)
        else:
            await self.bot.invoke_help_command(ctx)

    @emoji_group.command(name="count", aliases=("c",))
    async def count_command(self, ctx: commands.Context, *, category_query: str = None) -> None:
        """Returns embed with emoji category and info given by the user."""
        emoji_dict = defaultdict(list)

        if not ctx.guild.emojis:
            await ctx.send("No emojis found.")
            return
        log.trace(f"Emoji Category {'' if category_query else 'not '}provided by the user.")
        for emoji in ctx.guild.emojis:
            emoji_category = emoji.name.split("_")[0]

            if category_query is not None and emoji_category not in category_query:
                continue

            emoji_dict[emoji_category].append(emoji)

        if not emoji_dict:
            log.trace("Invalid name provided by the user")
            embed, msg = self.generate_invalid_embed(ctx.guild.emojis)
        else:
            embed, msg = self.embed_builder(emoji_dict)
        await LinePaginator.paginate(lines=msg, ctx=ctx, embed=embed)

    @emoji_group.command(name="info", aliases=("i",))
    async def info_command(self, ctx: commands.Context, emoji: Emoji) -> None:
        """Returns relevant information about a Discord Emoji."""
        emoji_information = Embed(
            title=f"Emoji Information: {emoji.name}",
            description=textwrap.dedent(f"""
                **Name:** {emoji.name}
                **Created:** {time_since(emoji.created_at.replace(tzinfo=None), precision="hours")}
                **Date:** {datetime.strftime(emoji.created_at.replace(tzinfo=None), "%d/%m/%Y")}
                **ID:** {emoji.id}
            """),
            color=Color.og_blurple(),
            url=str(emoji.url),
        ).set_thumbnail(url=emoji.url)

        await ctx.send(embed=emoji_information)


async def setup(bot: Bot) -> None:
    """Load the Emojis cog."""
    await bot.add_cog(Emojis(bot))
