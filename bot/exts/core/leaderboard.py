import logging
from collections import Counter
from datetime import datetime

import discord
from async_rediscache import RedisCache
from discord import ButtonStyle, Colour, Interaction, ui
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Roles
from bot.utils.decorators import with_role

log = logging.getLogger(__name__)
DUCKY_COINS_THUMBNAIL = (
    "https://media.discordapp.net/attachments/753252897059373066/902713599884152872/"
    "new_duck.png?width=230&height=231"
)


class ParentCogConvertor(commands.Converter):
    """Return the parent cog name for the argument."""

    @staticmethod
    async def convert(ctx: commands.Context, argument: str) -> str:
        """Return the parent cog name for the argument."""
        cog: commands.Cog = ctx.bot.get_cog(argument)
        if cog:
            return cog.qualified_name

        cmd: commands.Command = ctx.bot.get_command(argument)
        if cmd:
            return cmd.cog_name

        raise commands.BadArgument(
            f"Unable to convert `{argument}` to valid command or Cog."
        )


class ConfirmClear(ui.View):
    """A confirmation view for clearing the leaderboard caches."""

    def __init__(self, author_id: int, bot: Bot) -> None:
        super().__init__(timeout=5)
        self.confirmed = None
        self.interaction = None
        self.authorization = author_id
        self.bot = bot

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Check the interactor is authorised."""
        if interaction.user.id == self.authorization:
            return True

        await interaction.response.send_message(
            ":no_entry_sign: You are not authorized to perform this action.",
            ephemeral=True,
        )

        return False

    @ui.button(label="Confirm", style=ButtonStyle.green, row=0)
    async def confirm(self, _button: ui.Button, interaction: Interaction) -> None:
        """Redeploy the specified service."""
        for global_lb, _ in self.bot.games_leaderboard.values():
            await global_lb.clear()

        log.info(f"The leaderboard was cleared by Member({self.authorization})")
        await interaction.response.send_message(
            content=":white_check_mark: Cleared all game leaderboards.",
            ephemeral=False
        )

        self.stop()

    @ui.button(label="Cancel", style=ButtonStyle.grey, row=0)
    async def cancel(self, _button: ui.Button, interaction: Interaction) -> None:
        """Logic for if the deployment is not approved."""
        await interaction.response.send_message(
            content=":x: Clearing cache aborted!",
            ephemeral=False,
        )
        self.stop()


class Leaderboard(commands.Cog):
    """Cog for getting game leaderboards."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def ordinal_number(n: int) -> str:
        """Get the ordinal number for `n`."""
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        return str(n) + suffix

    async def make_leaderboard(self, cached_leaderboard: list[RedisCache]) -> discord.Embed:
        """Make a discord embed for the current top 10 members in the cached leaderboard."""
        if len(cached_leaderboard) == 1:
            game_leaderboard = await cached_leaderboard[0].to_dict()
            leaderboard = Counter(game_leaderboard)
        else:
            leaderboard = Counter()
            for lb in cached_leaderboard:
                game_leaderboard = await lb.to_dict()
                leaderboard += Counter(game_leaderboard)

        top_ten = leaderboard.most_common(10)

        lines = []
        for index, (member_id, score) in enumerate(top_ten, start=1):
            rank = format(self.ordinal_number(index), " >4")
            score = format(score, " >4")
            mention = f"<@{member_id}>"
            lines.append(f"`{rank} |  {score} |` {mention}")

        board_formatted = "\n".join(lines) if lines else "(no entries yet)"
        description = f"`Rank | Score |` Member\n{board_formatted}"

        embed = discord.Embed(
            title="Top 10",
            description=description,
            colour=Colour.from_rgb(255, 230, 102),
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=DUCKY_COINS_THUMBNAIL)

        return embed

    @commands.group(aliases=("lb",), invoke_without_command=True)
    async def leaderboard(self, ctx: commands.Context, game: ParentCogConvertor = None) -> None:
        """Get overall leaderboard if not game specified, else leaderboard for that game."""
        if ctx.invoked_subcommand:
            return

        if game:
            leaderboards = self.bot.games_leaderboard.get(game)
            if not leaderboards:
                raise commands.BadArgument(f"Leaderboard for game {game} not found.")
            leaderboard = [leaderboards[0]]
        else:
            leaderboard = [lb for lb, _ in self.bot.games_leaderboard.values()]

        embed = await self.make_leaderboard(leaderboard)
        await ctx.send(embed=embed)

    @leaderboard.command(name="today", aliases=("t",))
    async def per_day_leaderboard(self, ctx: commands.Context, game: ParentCogConvertor = None) -> None:
        """Get today's overall leaderboard if not game specified, else leaderboard for that game."""
        if game:
            leaderboards = self.bot.games_leaderboard.get(game)
            if not leaderboards:
                raise commands.BadArgument(f"Leaderboard for game {game} not found.")
            leaderboard = [leaderboards[1]]
        else:
            leaderboard = [lb for _, lb in self.bot.games_leaderboard.values()]

        embed = await self.make_leaderboard(leaderboard)
        await ctx.send(embed=embed)

    @leaderboard.command(name="clear")
    @with_role(Roles.admin)
    async def clear_leaderboard(self, ctx: commands.Context) -> None:
        """Clear the current scoreboard."""
        confirmation = ConfirmClear(ctx.author.id, self.bot)

        msg = await ctx.send(
            ":warning: THIS WILL IRREVOCABLY CLEAR THE LEADERBOARD. ARE YOU SURE?",
            view=confirmation,
        )

        timed_out = await confirmation.wait()

        if timed_out:
            await msg.edit(
                content=":x: Clearing cache aborted! You took too long."
            )

        # Disable the confirmation button
        confirmation.children[0].disabled = True
        confirmation.children[1].disabled = True

        await msg.edit(view=confirmation)


def setup(bot: Bot) -> None:
    """Load the Leaderboard cog."""
    bot.add_cog(Leaderboard(bot))
