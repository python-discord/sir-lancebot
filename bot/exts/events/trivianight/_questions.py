from random import choice, randrange
from time import perf_counter
from typing import Optional, TypedDict, Union

import discord
from discord import Embed, Interaction
from discord.ui import Button, View

from bot.constants import Colours, NEGATIVE_REPLIES

from . import UserScore
from ._scoreboard import Scoreboard


class CurrentQuestion(TypedDict):
    """Representing the different 'keys' of the question taken from the JSON."""

    number: str
    description: str
    answers: list[str]
    correct: str
    points: Optional[int]
    time: Optional[int]


class QuestionButton(Button):
    """Button subclass for the options of the questions."""

    def __init__(self, label: str, users_picked: dict, view: View):
        self.users_picked = users_picked
        self._view = view
        super().__init__(label=label, style=discord.ButtonStyle.green)

    async def callback(self, interaction: Interaction) -> None:
        """
        When a user interacts with the button, this will be called.

        Parameters:
            - interaction: an instance of discord.Interaction representing the interaction between the user and the
            button.
        """
        original_message = interaction.message
        original_embed = original_message.embeds[0]

        if interaction.user.id not in self.users_picked.keys():
            people_answered = original_embed.footer.text
            people_answered = f"{int(people_answered[0]) + 1} " \
                              f"{'person has' if int(people_answered[0]) + 1 == 1 else 'people have'} answered"
            original_embed.set_footer(text=people_answered)
            await original_message.edit(embed=original_embed, view=self._view)
            self.users_picked[interaction.user.id] = [self.label, True, perf_counter() - self._time]
            await interaction.response.send_message(
                embed=Embed(
                    title="Confirming that..",
                    description=f"You chose answer {self.label}.",
                    color=Colours.soft_green
                ),
                ephemeral=True
            )
        elif self.users_picked[interaction.user.id][1] is True:
            self.users_picked[interaction.user.id] = [
                self.label, False, perf_counter() - self._time
            ]
            await interaction.response.send_message(
                embed=Embed(
                    title="Confirming that..",
                    description=f"You changed your answer to answer {self.label}.",
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

        self.active_question = False

    def create_current_question(self) -> tuple[Embed, int]:
        """
        Helper function to create the embed for the current question.

        Returns an embed containing the question along with each answer choice in the form of a view,
        along with the integer representing the time limit of the current question.
        """
        self.current_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:len(self.current_question["answers"])]
        question_embed = Embed(
            title=f"Question {self.current_question['number']}",
            description=self.current_question["obfuscated_description"],
            color=Colours.python_yellow
        )
        if "_previously_visited" not in self.current_question.keys():
            self.buttons = [QuestionButton(label, self.users_picked, self) for label in self.current_labels]
            for button in self.buttons:
                self.add_item(button)

        for label, answer in zip(self.current_labels, self.current_question["answers"]):
            question_embed.add_field(name=f"Answer {label}", value=answer, inline=False)

        question_embed.set_footer(text="0 people have answered")
        current_time = perf_counter()
        for button in self.buttons:
            button._time = current_time

        time_limit = self.current_question.get("time", 10)

        self.active_question = True

        return question_embed, time_limit

    def end_question(self) -> tuple[dict, Embed, int, int]:
        """
        Ends the question and displays the statistics on who got the question correct, awards points, etc.

        Returns:
            - a dictionary containing all the people who answered and whether or not they got it correct
            - an embed displaying the correct answers and the % of people that chose each answer.
            - an integer showing the time limit of the current question in seconds
            - an integer showing the amount of points the question will award* to those that got it correct
        """
        labels = self.current_labels
        label = labels[self.current_question["answers"].index(self.current_question["correct"])]
        return_dict = {name: (*info, info[0] == label) for name, info in self.users_picked.items()}
        all_players = list(self.users_picked.items())

        answer_embed = Embed(
            title=f"The correct answer for Question {self.current_question['number']} was..",
            description=self.current_question["correct"]
        )

        if len(all_players) != 0:
            answers_chosen = {
                answer_choice: len(
                    tuple(filter(lambda x: x[0] == answer_choice, self.users_picked.values()))
                ) / len(all_players)
                for answer_choice in labels
            }

            for idx, (answer, percent) in enumerate(answers_chosen.items()):
                # Setting the color of answer_embed to the % of people that got it correct via the mapping
                if idx == 0:
                    # Maps the % of people who got it right to a color, from a range of red to green
                    percentage_to_color = [0xFC94A1, 0xFFCCCB, 0xCDFFCC, 0xB0F5AB, 0xB0F5AB]
                    answer_embed.color = percentage_to_color[round(percent * 100) // 25]

                # The `ord` function is used here to change the letter to its corresponding position
                answer_embed.add_field(
                    name=f"{percent * 100:.1f}% of players chose",
                    value=self.current_question['answers'][ord(answer) - 65],
                    inline=False
                )

        self.users_picked = {}

        for button in self.buttons:
            button.users_picked = self.users_picked

        time_limit = self.current_question.get("time", 10)
        question_points = self.current_question.get("points", 10)

        self.active_question = False

        return return_dict, answer_embed, time_limit, question_points


class Questions:
    """An interface to use from the TriviaNight cog for questions."""

    def __init__(self, scoreboard: Scoreboard):
        self.scoreboard = scoreboard
        self.questions = []

    def set_questions(self, questions: list) -> None:
        """
        Setting `self.questions` dynamically via a function to set it.

        Parameters:
            - questions: a list representing all the questions, which is essentially the JSON provided
            to load the questions
        """
        self.questions = questions

    def next_question(self, number: int = None) -> Union[Embed, None]:
        """
        Chooses a random unvisited question from the question bank.

        If the number parameter is specified, it'll head to that specific question.

        Parameters:
            - number: An optional integer representing the question number (only used for `.trivianight question` calls)
        """
        if all("visited" in question.keys() for question in self.questions) and number is None:
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
            question_number = number - 1

        if "visited" in self.questions[question_number].keys():
            self.questions[question_number]["_previously_visited"] = True
        self.questions[question_number]["visited"] = True

        # The `self.view` refers to the QuestionView
        self.view.current_question = self.questions[question_number]

    def list_questions(self) -> Union[Embed, str]:
        """
        Lists all questions from the question bank.

        It will put the following into a message:
            - Question number
            - Question description
            - If the question was already 'visited' (displayed)
        """
        if not self.questions:
            return Embed(
                title=choice(NEGATIVE_REPLIES),
                description="No questions are currently loaded in!",
                color=Colours.soft_red
            )
        spaces = len(
            sorted(
                self.questions, key=lambda question: len(question['description'])
            )[-1]["description"]
        ) + 3
        formatted_string = ""
        for question in self.questions:
            question_description = question["description"]
            formatted_string += f"`Q{question['number']}: {question_description}" \
                                f"{' ' * (spaces - len(question_description) + 2)}" \
                                f"|` {':x:' if not question.get('visited') else ':white_check_mark:'}\n"

        return formatted_string.strip()

    def current_question(self) -> tuple[Embed, QuestionView]:
        """Returns an embed entailing the current question as an embed with a view."""
        return self.view.create_current_question(), self.view

    def end_question(self) -> Embed:
        """
        Terminates answering of the question and displays the correct answer.

        The function returns an embed containing the information about the question such as the following:
            - % of people that chose each option
            - the correct answer
        """
        scores, answer_embed, time_limit, total_points = self.view.end_question()
        for user, score in scores.items():
            time_taken = score[2]
            point_calculation = (1 - (time_taken / time_limit) / 2) * total_points
            if score[-1] is True:
                self.scoreboard[UserScore(user)] = {"points": point_calculation, "speed": time_taken}
            elif score[-1] is False and score[2] <= 2:
                # Get the negative of the point_calculation to deduct it
                self.scoreboard[UserScore(user)] = {"points": -point_calculation}
        return answer_embed
