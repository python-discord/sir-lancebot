from random import choice, randrange
from time import perf_counter
from typing import TypedDict, Union

import discord
from discord import Embed, Interaction
from discord.ui import Button, View

from bot.constants import Colours, NEGATIVE_REPLIES
from ._scoreboard import Scoreboard


class CurrentQuestion(TypedDict):
    """Representing the different 'keys' of the question taken from the JSON."""

    number: str
    description: str
    answers: list[str]
    correct: str


class QuestionButton(Button):
    """Button subclass for the options of the questions."""

    def __init__(self, label: str, users_picked: dict):
        self.users_picked = users_picked
        super().__init__(label=label, style=discord.ButtonStyle.green)

    def set_time(self) -> None:
        """Sets an instance attribute to a perf counter simulating the question beginning."""
        self._time = perf_counter()

    async def callback(self, interaction: Interaction) -> None:
        """When a user interacts with the button, this will be called."""
        if interaction.user.id not in self.users_picked.keys():
            self.users_picked[interaction.user.id] = [self.label, 1, perf_counter() - self._time]
            await interaction.response.send_message(
                embed=Embed(
                    title="Success!",
                    description=f"You chose answer {self.label}.",
                    color=Colours.soft_green
                ),
                ephemeral=True
            )
        elif self.users_picked[interaction.user.id][1] < 2:
            self.users_picked[interaction.user.id] = [
                self.label, self.users_picked[interaction.user.id][1] + 1, perf_counter() - self._time
            ]
            await interaction.response.send_message(
                embed=Embed(
                    title="Success!",
                    description=f"You changed your answer to answer choice {self.label}.",
                    color=Colours.soft_green
                ),
                ephemeral=True
            )
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

    def __init__(self):
        super().__init__()
        self.current_question: CurrentQuestion
        self.users_picked = {}
        self.buttons = [QuestionButton(label, self.users_picked) for label in ("A", "B", "C", "D")]
        for button in self.buttons:
            self.add_item(button)

    def create_current_question(self) -> Embed:
        """Helper function to create the embed for the current question."""
        question_embed = Embed(
            title=f"Question {self.current_question['number']}",
            description=self.current_question["description"],
            color=Colours.python_yellow
        )
        for label, answer in zip("ABCD", self.current_question["answers"]):
            question_embed.add_field(name=f"Answer {label}", value=answer, inline=False)

        for button in self.buttons:
            button.set_time()

        return question_embed

    def end_question(self) -> tuple[dict, Embed]:
        """Returns the dictionaries from the corresponding buttons for those who got it correct."""
        labels = ("A", "B", "C", "D")
        label = labels[self.current_question["answers"].index(self.current_question["correct"])]
        return_dict = {name: info for name, info in self.users_picked.items() if info[0] == label}
        self.users_picked = {}

        for button in self.buttons:
            button.users_picked = self.users_picked

        answer_embed = Embed(
            title=f"The correct answer for Question {self.current_question['number']} was",
            description=self.current_question["correct"],
            color=Colours.soft_green
        )

        return return_dict, answer_embed


class Questions:
    """An interface to use from the TriviaNight cog for questions."""

    def __init__(self, scoreboard: Scoreboard):
        self.scoreboard = scoreboard
        self.questions = []

    def set_questions(self, questions: list) -> None:
        """Setting `self.questions` dynamically via a function to set it."""
        self.questions = questions

    def next_question(self, number: int = None) -> Union[Embed, None]:
        """
        Chooses a random unvisited question from the question bank.

        If the number parameter is specified, it'll head to that specific question.
        """
        if all("visited" in question.keys() for question in self.questions):
            return Embed(
                title=choice(NEGATIVE_REPLIES),
                description="All of the questions in the question bank have been used.",
                color=Colours.soft_red
            )

        if number is None:
            question_number = randrange(0, len(self.questions))
            while "visited" in self.questions[question_number].keys():
                question_number = randrange(0, len(self.questions))
        else:
            question_number = number

        self.questions[question_number]["visited"] = True
        self.view.current_question = self.questions[question_number]

    def list_questions(self) -> str:
        """
        Lists all questions from the question bank.

        It will put the following into a message:
            - Question number
            - Question description
            - If the question was already 'visited' (displayed)
        """
        spaces = len(sorted(self.questions, key=lambda question: len(question['description']))[-1]["description"]) + 3
        formatted_string = ""
        for question in self.questions:
            formatted_string += f"`Q{question['number']}: {question['description']!r}" \
                                f"{' ' * (spaces - len(question['description']) + 2)}" \
                                f"|` {':x:' if not question.get('visited') else ':checkmark:'}\n"

        return formatted_string.strip()

    def current_question(self) -> tuple[Embed, QuestionView]:
        """Returns an embed entailing the current question as an embed with a view."""
        return self.view.create_current_question(), self.view

    def end_question(self) -> Embed:
        """Terminates answering of the question and displays the correct answer."""
        scores, answer_embed = self.view.end_question()
        for user, score in scores.items():
            self.scoreboard[f"points: {user}"] = 1
            self.scoreboard[f"speed: {user}"] = score[2]

        return answer_embed
