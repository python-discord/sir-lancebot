import time
from random import randrange
from string import ascii_uppercase
from typing import Iterable, Optional, TypedDict


DEFAULT_QUESTION_POINTS = 10
DEFAULT_QUESTION_TIME = 10


class QuestionData(TypedDict):
    """Representing the different 'keys' of the question taken from the JSON."""

    number: str
    description: str
    answers: list[str]
    correct: str
    points: Optional[int]
    time: Optional[int]


UserGuess = tuple[
    str,  # The answer that was guessed
    bool,  # Whether the answer can be changed again
    float  # The time it took to guess
]


class QuestionClosed(RuntimeError):
    """Exception raised when the question is not open for guesses anymore."""


class AlreadyUpdated(RuntimeError):
    """Exception raised when the user has already updated their guess once."""


class Question:
    """Interface for one question in a trivia night game."""

    def __init__(self, data: QuestionData):
        self._data = data
        self._guesses: dict[int, UserGuess] = {}
        self._started = None

    # These properties are mostly proxies to the underlying data:

    @property
    def number(self) -> str:
        """The number of the question."""
        return self._data["number"]

    @property
    def description(self) -> str:
        """The description of the question."""
        return self._data["description"]

    @property
    def answers(self) -> list[tuple[str, str]]:
        """The possible answers for this answer.

        This is a property that returns a list of letter, answer pairs.
        """
        return [(ascii_uppercase[i], q) for (i, q) in enumerate(self._data["answers"])]

    @property
    def correct(self) -> str:
        """The correct answer for this question."""
        return self._data["correct"]

    @property
    def max_points(self) -> int:
        """The maximum points that can be awarded for this question."""
        return self._data.get("points") or DEFAULT_QUESTION_POINTS

    @property
    def time(self) -> float:
        """The time allowed to answer the question."""
        return self._data.get("time") or DEFAULT_QUESTION_TIME

    def start(self) -> float:
        """Start the question and return the time it started."""
        self._started = time.perf_counter()
        return self._started

    def _update_guess(self, user: int, answer: str) -> UserGuess:
        """Update an already existing guess."""
        if self._started is None:
            raise QuestionClosed("Question is not open for answers.")

        if self._guesses[user][1] is False:
            raise AlreadyUpdated(f"User({user}) has already updated their guess once.")

        self._guesses[user] = (answer, False, time.perf_counter() - self._started)
        return self._guesses[user]

    def guess(self, user: int, answer: str) -> UserGuess:
        """Add a guess made by a user to the current question."""
        if user in self._guesses:
            return self._update_guess(user, answer)

        if self._started is None:
            raise QuestionClosed("Question is not open for answers.")

        self._guesses[user] = (answer, True, time.perf_counter() - self._started)
        return self._guesses[user]

    def stop(self) -> dict[int, UserGuess]:
        """Stop the question and return the guesses that were made."""
        guesses = self._guesses

        self._started = None
        self._guesses = {}

        return guesses


class TriviaNightGame:
    """Interface for managing a game of trivia night."""

    def __init__(self, data: list[QuestionData]) -> None:
        self._questions = [Question(q) for q in data]
        self.current_question: Optional[Question] = None

    def __iter__(self) -> Iterable[Question]:
        return iter(self._questions)

    def next_question(self, number: str = None) -> Question:
        """
        Consume one random question from the trivia night game.

        One question is randomly picked from the list of questions which is then removed and returned.
        """
        if self.current_question is not None:
            raise RuntimeError("Cannot call next_question() when there is a current question.")

        if number is not None:
            try:
                question = [q for q in self._questions if q.number == number][0]
            except IndexError:
                raise ValueError(f"Question number {number} does not exist.")
        else:
            question = self._questions.pop(randrange(len(self._questions)))

        self.current_question = question
        return question

    def end_question(self) -> None:
        """
        End the current question.

        This method should be called when the question has been answered, it must be called before
        attempting to call `next_question()` again.
        """
        if self.current_question is None:
            raise RuntimeError("Cannot call end_question() when there is no current question.")

        self.current_question.stop()
        self.current_question = None
