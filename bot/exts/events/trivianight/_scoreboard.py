from random import choice

import discord.ui
from discord import ButtonStyle, Embed, Interaction, Member
from discord.ui import Button, View

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES

from . import UserScore


class ScoreboardView(View):
    """View for the scoreboard."""

    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot
        self.points = {}
        self.speed = {}

    async def create_main_leaderboard(self) -> Embed:
        """Helper function that iterates through `self.points` to generate the main leaderboard embed."""
        formatted_string = ""
        self.points = dict(sorted(self.points.items(), key=lambda item: item[-1], reverse=True))
        self.speed = dict(sorted(self.speed.items(), key=lambda item: item[-1]))

        for current_placement, (user, points) in enumerate(self.points.items()):
            if current_placement + 1 > 30:
                break

            user = await self.bot.fetch_user(int(user))
            formatted_string += f"**{current_placement + 1}.** {user.mention} "
            formatted_string += f"({points:.1f} pts)\n"
            if (current_placement + 1) % 10 == 0:
                formatted_string += "⎯⎯⎯⎯⎯⎯⎯⎯\n"

        main_embed = Embed(
            title="Winners of the Trivia Night",
            description=formatted_string,
            color=Colours.python_blue,
        )

        return main_embed

    async def _create_speed_embed(self) -> Embed:
        """Helper function that iterates through `self.speed` to generate a leaderboard embed."""
        formatted_string = ""

        for current_placement, (user, time_taken) in enumerate(self.speed.items()):
            if current_placement + 1 > 30:
                break

            user = await self.bot.fetch_user(int(user))
            formatted_string += f"**{current_placement + 1}.** {user.mention} "
            formatted_string += f"({(time_taken[-1] / time_taken[0]):.1f}s)\n"
            if (current_placement + 1) % 10 == 0:
                formatted_string += "⎯⎯⎯⎯⎯⎯⎯⎯\n"

        speed_embed = Embed(
            title="Average time taken to answer a question",
            description=formatted_string,
            color=Colours.python_blue
        )
        return speed_embed

    def _get_rank(self, member: Member) -> Embed:
        """Gets the member's rank for the points leaderboard and speed leaderboard."""
        rank_embed = Embed(title=f"Ranks for {member.display_name}", color=Colours.python_blue)
        # These are stored as strings so that the last digit can be determined to choose the suffix
        try:
            points_rank = str(list(self.points.keys()).index(member.id) + 1)
            speed_rank = str(list(self.speed.keys()).index(member.id) + 1)
        except ValueError:
            return Embed(
                title=choice(NEGATIVE_REPLIES),
                description="It looks like you didn't participate in the Trivia Night event!",
                color=Colours.soft_red
            )

        suffixes = {"1": "st", "2": "nd", "3": "rd"}
        rank_embed.add_field(
            name="Total Points",
            value=(
                f"You got {points_rank}{'th' if not (suffix := suffixes.get(points_rank[-1])) else suffix} place"
                f" with {self.points[member.id]:.1f} points."
            ),
            inline=False
        )
        rank_embed.add_field(
            name="Average Speed",
            value=(
                f"You got {speed_rank}{'th' if not (suffix := suffixes.get(speed_rank[-1])) else suffix} place"
                f" with a time of {(self.speed[member.id][1] / self.speed[member.id][0]):.1f} seconds."
            ),
            inline=False
        )
        return rank_embed

    @discord.ui.button(label="Scoreboard for Speed", style=ButtonStyle.green)
    async def speed_leaderboard(self, button: Button, interaction: Interaction) -> None:
        """Send an ephemeral message with the speed leaderboard embed."""
        await interaction.response.send_message(embed=await self._create_speed_embed(), ephemeral=True)

    @discord.ui.button(label="What's my rank?", style=ButtonStyle.blurple)
    async def rank_button(self, button: Button, interaction: Interaction) -> None:
        """Send an ephemeral message with the user's rank for the overall points/average speed."""
        await interaction.response.send_message(embed=self._get_rank(interaction.user), ephemeral=True)


class Scoreboard:
    """Class for the scoreboard for the Trivia Night event."""

    def __setitem__(self, key: UserScore, value: dict):
        if value.get("points") and key.user_id not in self.view.points.keys():
            self.view.points[key.user_id] = value["points"]
        elif value.get("points"):
            self.view.points[key.user_id] += self.view.points[key.user_id]

        if value.get("speed") and key.user_id not in self.view.speed.keys():
            self.view.speed[key.user_id] = [1, value["speed"]]
        elif value.get("speed"):
            self.view.speed[key.user_id] = [
                self.view.speed[key.user_id][0] + 1, self.view.speed[key.user_id][1] + value["speed"]
            ]

    async def display(self) -> tuple[Embed, View]:
        """Returns the embed of the main leaderboard along with the ScoreboardView."""
        return await self.view.create_main_leaderboard(), self.view
