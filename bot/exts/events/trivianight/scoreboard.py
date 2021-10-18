from typing import Union

import discord.ui
from discord import ButtonStyle, Embed, Interaction
from discord.ui import Button, View

from bot.bot import Bot
from bot.constants import Colours


class ScoreboardView(View):
    """View for the scoreboard."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.points = {}
        self.speed = {}

    def create_main_leaderboard(self) -> Embed:
        """Helper function that iterates through `self.points` to generate the main leaderboard embed."""
        main_embed = Embed(
            title="Winners of the Trivia Night",
            description="See the leaderboard for who got the most points during the Trivia Night!",
            color=Colours.python_blue,
        )
        for user, points in list(self.points.items())[:10]:
            main_embed.add_field(name=self.bot.get_user(user), value=f"`{points}` pts", inline=False)

        return main_embed

    def _create_speed_embed(self) -> Embed:
        """Helper function that iterates through `self.speed` to generate a leaderboard embed."""
        speed_embed = Embed(
            title="Average Time Taken to Answer a Question",
            description="See the leaderboard for how fast each user took to answer a question correctly!",
            color=Colours.python_blue,
        )
        for user, time_taken in list(self.speed.items())[:10]:
            speed_embed.add_field(
                name=self.bot.get_user(user),
                value=f"`{(time_taken[1] / time_taken[0]):.3f}s` (on average)",
                inline=False
            )

        return speed_embed

    @discord.ui.button(label="Scoreboard for Speed", style=ButtonStyle.green)
    async def speed_leaderboard(self, button: Button, interaction: Interaction) -> None:
        """Send an ephemeral message with the speed leaderboard embed."""
        await interaction.response.send_message(embed=self._create_speed_embed(), ephemeral=True)


class Scoreboard:
    """Class for the scoreboard for the trivianight event."""

    def __init__(self):
        self.view = ScoreboardView()

    def __setitem__(self, key: str, value: int):
        if key.startswith("points: "):
            key = key.removeprefix("points: ")
            if key not in self.view.points.keys():
                self.view.points[key] = value
            else:
                self.view.points[key] += self.view.points[key]
        elif key.startswith("speed: "):
            key = key.removeprefix("speed: ")
            if key not in self.view.speed.keys():
                self.view.speed[key] = [1, value]
            else:
                self.view.speed[key] = [self.view.speed[key][0] + 1, self.view.speed[key][1] + value]

    def __getitem__(self, item: str):
        if item.startswith("points: "):
            return self.view.points[item.removeprefix("points: ")]
        elif item.startswith("speed: "):
            return self.view.speed[item.removepreix("speed: ")]

    def display(self) -> Union[Embed, View]:
        """Returns the embed of the main leaderboard along with the ScoreboardView."""
        return self.view.create_main_leaderboard(), self.view
