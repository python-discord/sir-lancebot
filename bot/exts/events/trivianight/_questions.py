from random import choice
from string import ascii_uppercase

import discord
from discord import Embed, Interaction
from discord.ui import Button, View

from bot.constants import Colours, NEGATIVE_REPLIES

from ._game import AlreadyUpdated, Question, QuestionClosed
from ._scoreboard import Scoreboard


class AnswerButton(Button):
    """Button subclass that's used to guess on a particular answer."""

    def __init__(self, label: str, question: Question):
        super().__init__(label=label, style=discord.ButtonStyle.green)

        self.question = question

    async def callback(self, interaction: Interaction) -> None:
        """
        When a user interacts with the button, this will be called.

        Parameters:
            - interaction: an instance of discord.Interaction representing the interaction between the user and the
            button.
        """
        try:
            guess = self.question.guess(interaction.user.id, self.label)
        except AlreadyUpdated:
            await interaction.response.send_message(
                embed=Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="You've already changed your answer more than once!",
                    color=Colours.soft_red
                ),
                ephemeral=True
            )
            return
        except QuestionClosed:
            await interaction.response.send_message(
                embed=Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="The question is no longer accepting guesses!",
                    color=Colours.soft_red
                ),
            )
            return

        if guess[1]:
            await interaction.response.send_message(
                embed=Embed(
                    title="Confirming that..",
                    description=f"You chose answer {self.label}.",
                    color=Colours.soft_green
                ),
                ephemeral=True
            )
        else:
            # guess[1] is False and they cannot change their answer again. Which
            # indicates that they changed it this time around.
            await interaction.response.send_message(
                embed=Embed(
                    title="Confirming that..",
                    description=f"You changed your answer to answer {self.label}.",
                    color=Colours.soft_green
                ),
                ephemeral=True
            )


class QuestionView(View):
    """View for one trivia night question."""

    def __init__(self, question: Question) -> None:
        super().__init__()
        self.question = question

        for letter, _ in self.question.answers:
            self.add_item(AnswerButton(letter, self.question))

    @staticmethod
    def unicodeify(text: str) -> str:
        """
        Takes `text` and adds zero-width spaces to prevent copy and pasting the question.

        Parameters:
            - text: A string that represents the question description to 'unicodeify'
        """
        return "".join(
            f"{letter}\u200b" if letter not in ('\n', '\t', '`', 'p', 'y') else letter
            for idx, letter in enumerate(text)
        )

    def create_embed(self) -> Embed:
        """Helper function to create the embed for the current question."""
        question_embed = Embed(
            title=f"Question {self.question.number}",
            description=self.unicodeify(self.question.description),
            color=Colours.python_yellow
        )

        for label, answer in self.question.answers:
            question_embed.add_field(name=f"Answer {label}", value=answer, inline=False)

        return question_embed

    def end_question(self, scoreboard: Scoreboard) -> Embed:
        """
        Ends the question and displays the statistics on who got the question correct, awards points, etc.

        Returns:
            An embed displaying the correct answers and the % of people that chose each answer.
        """
        guesses = self.question.stop()

        labels = ascii_uppercase[:len(self.question.answers)]

        answer_embed = Embed(
            title=f"The correct answer for Question {self.question.number} was..",
            description=self.question.correct
        )

        if len(guesses) != 0:
            answers_chosen = {
                answer_choice: len(
                    tuple(filter(lambda x: x[0] == answer_choice, guesses.values()))
                ) / len(guesses)
                for answer_choice in labels
            }

            answers_chosen = dict(
                sorted(list(answers_chosen.items()), key=lambda item: item[1], reverse=True)
            )

            for answer, percent in answers_chosen.items():
                # Setting the color of answer_embed to the % of people that got it correct via the mapping
                if dict(self.question.answers)[answer[0]] == self.question.correct:
                    # Maps the % of people who got it right to a color, from a range of red to green
                    percentage_to_color = [0xFC94A1, 0xFFCCCB, 0xCDFFCC, 0xB0F5AB, 0xB0F5AB]
                    answer_embed.color = percentage_to_color[round(percent * 100) // 25]

                # The `ord` function is used here to change the letter to its corresponding position
                answer_embed.add_field(
                    name=f"{percent * 100:.1f}% of players chose",
                    value=self.question.answers[ord(answer) - 65][1],
                    inline=False
                )

            # Assign points to users
            for user_id, answer in guesses.items():
                if dict(self.question.answers)[answer[0]] == self.question.correct:
                    scoreboard.assign_points(
                        int(user_id),
                        points=(1 - (answer[-1] / self.question.time) / 2) * self.question.max_points,
                        speed=answer[-1]
                    )
                elif answer[-1] <= 2:
                    scoreboard.assign_points(
                        int(user_id),
                        points=-(1 - (answer[-1] / self.question.time) / 2) * self.question.max_points
                    )
                else:
                    scoreboard.assign_points(
                        int(user_id),
                        points=0
                    )

        return answer_embed
