from random import choice

import discord.ui
from discord import ButtonStyle, Embed, Interaction, Member
from discord.ui import Button, View

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES


class ScoreboardView(View):
    """View for the scoreboard."""

    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    @staticmethod
    def _int_to_ordinal(number: int) -> str:
        """
        Converts an integer into an ordinal number, i.e. 1 to 1st.

        Parameters:
            - number: an integer representing the number to convert to an ordinal number.
        """
        suffix = ["th", "st", "nd", "rd", "th"][min(number % 10, 4)]
        if (number % 100) in {11, 12, 13}:
            suffix = "th"

        return str(number) + suffix

    async def create_main_leaderboard(self) -> Embed:
        """
        Helper function that iterates through `self.points` to generate the main leaderboard embed.

        The main leaderboard would be formatted like the following:
        **1**. @mention of the user (# of points)
        along with the 29 other users who made it onto the leaderboard.
        """
        formatted_string = ""

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
        """
        Helper function that iterates through `self.speed` to generate a leaderboard embed.

        The speed leaderboard would be formatted like the following:
        **1**. @mention of the user ([average speed as a float with the precision of one decimal point]s)
        along with the 29 other users who made it onto the leaderboard.
        """
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
        """
        Gets the member's rank for the points leaderboard and speed leaderboard.

        Parameters:
            - member: An instance of discord.Member representing the person who is trying to get their rank.
        """
        rank_embed = Embed(title=f"Ranks for {member.display_name}", color=Colours.python_blue)
        # These are stored as strings so that the last digit can be determined to choose the suffix
        try:
            points_rank = str(list(self.points).index(member.id) + 1)
            speed_rank = str(list(self.speed).index(member.id) + 1)
        except ValueError:
            return Embed(
                title=choice(NEGATIVE_REPLIES),
                description="It looks like you didn't participate in the Trivia Night event!",
                color=Colours.soft_red
            )

        rank_embed.add_field(
            name="Total Points",
            value=(
                f"You got {self._int_to_ordinal(int(points_rank))} place"
                f" with {self.points[member.id]:.1f} points."
            ),
            inline=False
        )

        rank_embed.add_field(
            name="Average Speed",
            value=(
                f"You got {self._int_to_ordinal(int(speed_rank))} place"
                f" with a time of {(self.speed[member.id][1] / self.speed[member.id][0]):.1f} seconds."
            ),
            inline=False
        )
        return rank_embed

    @discord.ui.button(label="Scoreboard for Speed", style=ButtonStyle.green)
    async def speed_leaderboard(self, interaction: Interaction, _: Button) -> None:
        """
        Send an ephemeral message with the speed leaderboard embed.

        Parameters:
            - interaction: The discord.Interaction instance containing information on the interaction between the user
            and the button.
            - button: The discord.ui.Button instance representing the `Speed Leaderboard` button.
        """
        await interaction.response.send_message(embed=await self._create_speed_embed(), ephemeral=True)

    @discord.ui.button(label="What's my rank?", style=ButtonStyle.blurple)
    async def rank_button(self, interaction: Interaction, _: Button) -> None:
        """
        Send an ephemeral message with the user's rank for the overall points/average speed.

        Parameters:
            - interaction: The discord.Interaction instance containing information on the interaction between the user
            and the button.
            - button: The discord.ui.Button instance representing the `What's my rank?` button.
        """
        await interaction.response.send_message(embed=self._get_rank(interaction.user), ephemeral=True)


class Scoreboard:
    """Class for the scoreboard for the Trivia Night event."""

    def __init__(self, bot: Bot):
        self._bot = bot
        self._points = {}
        self._speed = {}

    def assign_points(self, user_id: int, *, points: int | None = None, speed: float | None = None) -> None:
        """
        Assign points or deduct points to/from a certain user.

        This method should be called once the question has finished and all answers have been registered.
        """
        if points is not None and user_id not in self._points.keys():
            self._points[user_id] = points
        elif points is not None:
            self._points[user_id] += points

        if speed is not None and user_id not in self._speed.keys():
            self._speed[user_id] = [1, speed]
        elif speed is not None:
            self._speed[user_id] = [
                self._speed[user_id][0] + 1, self._speed[user_id][1] + speed
            ]

    async def display(self, speed_leaderboard: bool = False) -> tuple[Embed, View]:
        """Returns the embed of the main leaderboard along with the ScoreboardView."""
        view = ScoreboardView(self._bot)

        view.points = dict(sorted(self._points.items(), key=lambda item: item[-1], reverse=True))
        view.speed = dict(sorted(self._speed.items(), key=lambda item: item[-1][1] / item[-1][0]))

        return (
            await view.create_main_leaderboard(),
            view if not speed_leaderboard else await view._create_speed_embed()
        )
