import discord
from async_rediscache import RedisCache
from discord import ButtonStyle, Interaction, ui
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, MODERATION_ROLES
from bot.utils.decorators import with_role
from bot.utils.leaderboard import get_daily_leaderboard, get_leaderboard, get_user_points, get_user_rank
from bot.utils.pagination import LinePaginator

DUCK_COIN_THUMBNAIL = (
    "https://raw.githubusercontent.com/python-discord/sir-lancebot/main/bot/resources/fun/duck-coin.png"
)

MEDALS = (
    "\N{FIRST PLACE MEDAL}",
    "\N{SECOND PLACE MEDAL}",
    "\N{THIRD PLACE MEDAL}",
)


def _format_leaderboard_lines(records: list[tuple[int, int]]) -> list[str]:
    """Format leaderboard records into display lines."""
    lines = []
    for rank, (user_id, score) in enumerate(records):
        if rank < len(MEDALS):
            prefix = MEDALS[rank]
        else:
            prefix = f"**#{rank + 1}**"
        lines.append(f"{prefix} <@{user_id}>: **{score}** pts")
    return lines


class ConfirmClear(ui.View):
    """A confirmation view for clearing the leaderboard."""

    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=15)
        self.author_id = author_id

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Only the invoking admin can interact."""
        if interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            "You are not authorized to perform this action.",
            ephemeral=True,
        )
        return False

    @ui.button(label="Confirm", style=ButtonStyle.danger)
    async def confirm(self, interaction: Interaction, _button: ui.Button) -> None:
        """Clear the leaderboard on confirmation."""
        from bot.utils.leaderboard import _get_points_cache

        points_cache = await _get_points_cache()
        await points_cache.clear()
        await interaction.response.send_message("Leaderboard has been cleared.")
        self.stop()

    @ui.button(label="Cancel", style=ButtonStyle.secondary)
    async def cancel(self, interaction: Interaction, _button: ui.Button) -> None:
        """Abort the clear operation."""
        await interaction.response.send_message("Clearing aborted.")
        self.stop()


class Leaderboard(commands.Cog):
    """Global leaderboard cog that tracks points across all games."""

    points_cache = RedisCache(namespace="leaderboard:points")

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="leaderboard", aliases=("lb", "points"), invoke_without_command=True)
    async def leaderboard_command(self, ctx: commands.Context) -> None:
        """Show the global game points leaderboard."""
        records = await get_leaderboard(self.bot)

        if not records:
            await ctx.send("No one has earned any points yet. Play some games!")
            return

        lines = _format_leaderboard_lines(records)

        embed = discord.Embed(
            colour=Colours.gold,
            title="Global Game Leaderboard",
        )
        embed.set_thumbnail(url=DUCK_COIN_THUMBNAIL)

        user_score = await get_user_points(self.bot, ctx.author.id)
        rank = await get_user_rank(self.bot, ctx.author.id)
        if rank:
            footer = f"Your rank: #{rank} | Your total: {user_score} pts"
        else:
            footer = "You're not on the leaderboard yet!"

        await LinePaginator.paginate(
            lines,
            ctx,
            embed,
            max_lines=10,
            max_size=2000,
            empty=False,
            footer_text=footer,
        )

    @leaderboard_command.command(name="today", aliases=("t",))
    async def leaderboard_today(self, ctx: commands.Context) -> None:
        """Show today's game points leaderboard."""
        records = await get_daily_leaderboard(self.bot)

        if not records:
            await ctx.send("No one has earned any points today yet. Play some games!")
            return

        lines = _format_leaderboard_lines(records)

        embed = discord.Embed(
            colour=Colours.gold,
            title="Today's Game Leaderboard",
        )
        embed.set_thumbnail(url=DUCK_COIN_THUMBNAIL)

        user_score = await get_user_points(self.bot, ctx.author.id)
        footer = f"Your total: {user_score} pts"

        await LinePaginator.paginate(
            lines,
            ctx,
            embed,
            max_lines=10,
            max_size=2000,
            empty=False,
            footer_text=footer,
        )

    @leaderboard_command.command(name="me")
    async def leaderboard_me(self, ctx: commands.Context) -> None:
        """Show your own global points."""
        score = await get_user_points(self.bot, ctx.author.id)
        rank = await get_user_rank(self.bot, ctx.author.id)

        description = f"{ctx.author.mention}: **{score}** pts"
        if rank:
            description += f" (Rank #{rank})"

        embed = discord.Embed(
            colour=Colours.blue,
            title="Your Global Points",
            description=description,
        )
        await ctx.send(embed=embed)

    @leaderboard_command.command(name="user")
    async def leaderboard_user(self, ctx: commands.Context, user: discord.User) -> None:
        """Show a specific user's global points."""
        score = await get_user_points(self.bot, user.id)
        rank = await get_user_rank(self.bot, user.id)

        description = f"{user.mention}: **{score}** pts"
        if rank:
            description += f" (Rank #{rank})"

        embed = discord.Embed(
            colour=Colours.blue,
            title=f"{user.display_name}'s Global Points",
            description=description,
        )
        await ctx.send(embed=embed)

    @leaderboard_command.command(name="clear")
    @with_role(*MODERATION_ROLES)
    async def leaderboard_clear(self, ctx: commands.Context) -> None:
        """Clear the global leaderboard (admin only)."""
        view = ConfirmClear(ctx.author.id)
        msg = await ctx.send(
            "**Warning:** This will irreversibly clear the entire global leaderboard. Are you sure?",
            view=view,
        )
        timed_out = await view.wait()
        if timed_out:
            await msg.edit(content="Clearing aborted (timed out).", view=None)
        else:
            for child in view.children:
                child.disabled = True
            await msg.edit(view=view)


async def setup(bot: Bot) -> None:
    """Load the Leaderboard cog."""
    await bot.add_cog(Leaderboard(bot))
