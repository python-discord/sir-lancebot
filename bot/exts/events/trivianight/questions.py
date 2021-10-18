from random import choice
from time import perf_counter

from discord import ButtonStyle, Embed, Interaction
from discord.ui import Button, View

from bot.constants import Colours, NEGATIVE_REPLIES
from .scoreboard import Scoreboard


class QuestionButton(Button):
    """Button subclass for the options of the questions."""

    def __init__(self, label: str):
        self._time = perf_counter()
        self.users_picked = {}
        super().__init__(label=label, style=ButtonStyle.green)

    def answer(self, label: str) -> dict:
        """Returns the dictionary of the users who picked the answer only if it was correct."""
        return self.users_picked if label == self.label else {}

    async def callback(self, interaction: Interaction) -> None:
        """When a user interacts with the button, this will be called."""
        if interaction.user.id not in self.users_picked.keys():
            self.users_picked[interaction.user.id] = [self.label, 1, perf_counter() - self._time]
        elif self.users_picked[interaction.user.id][1] < 3:
            self.users_picked[interaction.user.id] = [
                self.label, self.users_picked[interaction.user.id][0] + 1, perf_counter() - self._time
            ]
        else:
            await interaction.response.send_message(
                embed=Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="You've already changed your answer more than once!",
                    color=Colours.soft_red
                ),
                ephemeral=True
            )


class QuestionView(View):
    """View for the questions."""

    def __init__(self, scoreboard: Scoreboard):
        self.scoreboard = scoreboard
        self.current_question = {}
        self._users_picked = {}

    def _create_current_question(self) -> Embed:
        """Helper function to create the embed for the current question."""
        question_embed = Embed(
            title=f"Question {self.current_question['number']}",
            description=self.current_question["description"],
            color=Colours.python_yellow
        )
        for label, answer in zip(("A", "B", "C", "D"), self.current_question["answers"]):
            question_embed.add_field(name=label, value=answer, inline=False)

        self.buttons = [QuestionButton(label) for label in ("A", "B", "C", "D")]
        return question_embed

    def end_question(self) -> dict:
        """Returns the dictionaries from the corresponding buttons for those who got it correct."""
        labels = ("A", "B", "C", "D")
        label = labels[self.current_question["correct"].index(self.current_question["answers"])]
        return_dict = {}
        for button in self.buttons:
            return_dict.update(button.answer(label))

        return return_dict
