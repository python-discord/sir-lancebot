import asyncio
import json
import logging
import operator
import random
import re
import string
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import discord
from discord.ext import commands, tasks
from rapidfuzz import fuzz

from bot.bot import Bot
from bot.constants import Client, Colours, MODERATION_ROLES, NEGATIVE_REPLIES

logger = logging.getLogger(__name__)

DEFAULT_QUESTION_LIMIT = 7
STANDARD_VARIATION_TOLERANCE = 88
DYNAMICALLY_GEN_VARIATION_TOLERANCE = 97

MAX_ERROR_FETCH_TRIES = 3

WRONG_ANS_RESPONSE = [
    "No one answered correctly!",
    "Better luck next time...",
]

RULES = (
    "No cheating and have fun!",
    "Points for each question reduces by 25 after 10s or after a hint. Total time is 30s per question"
)

WIKI_FEED_API_URL = "https://en.wikipedia.org/api/rest_v1/feed/featured/{date}"
TRIVIA_QUIZ_ICON = (
    "https://raw.githubusercontent.com/python-discord/branding/main/icons/trivia_quiz/trivia-quiz-dist.png"
)
N_PREFIX_STARTS_AT = 5
N_PREFIXES = [
    "penta", "hexa", "hepta", "octa", "nona",
    "deca", "hendeca", "dodeca", "trideca", "tetradeca",
]

PLANETS = [
    ("1st", "Mercury"),
    ("2nd", "Venus"),
    ("3rd", "Earth"),
    ("4th", "Mars"),
    ("5th", "Jupiter"),
    ("6th", "Saturn"),
    ("7th", "Uranus"),
    ("8th", "Neptune"),
]

TAXONOMIC_HIERARCHY = [
    "species", "genus", "family", "order",
    "class", "phylum", "kingdom", "domain",
]

UNITS_TO_BASE_UNITS = {
    "hertz": ("(unit of frequency)", "s^-1"),
    "newton": ("(unit of force)", "m*kg*s^-2"),
    "pascal": ("(unit of pressure & stress)", "m^-1*kg*s^-2"),
    "joule": ("(unit of energy & quantity of heat)", "m^2*kg*s^-2"),
    "watt": ("(unit of power)", "m^2*kg*s^-3"),
    "coulomb": ("(unit of electric charge & quantity of electricity)", "s*A"),
    "volt": ("(unit of voltage & electromotive force)", "m^2*kg*s^-3*A^-1"),
    "farad": ("(unit of capacitance)", "m^-2*kg^-1*s^4*A^2"),
    "ohm": ("(unit of electric resistance)", "m^2*kg*s^-3*A^-2"),
    "weber": ("(unit of magnetic flux)", "m^2*kg*s^-2*A^-1"),
    "tesla": ("(unit of magnetic flux density)", "kg*s^-2*A^-1"),
}


@dataclass(frozen=True)
class QuizEntry:
    """Stores quiz entry (a question and a list of answers)."""

    question: str
    answers: list[str]
    var_tol: int


def linear_system(q_format: str, a_format: str) -> QuizEntry:
    """Generate a system of linear equations with two unknowns."""
    x, y = random.randint(2, 5), random.randint(2, 5)
    answer = a_format.format(x, y)

    coeffs = random.sample(range(1, 6), 4)

    question = q_format.format(
        coeffs[0],
        coeffs[1],
        coeffs[0] * x + coeffs[1] * y,
        coeffs[2],
        coeffs[3],
        coeffs[2] * x + coeffs[3] * y,
    )

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)

def mod_arith(q_format: str, a_format: str) -> QuizEntry:
    """Generate a basic modular arithmetic question."""
    quotient, m, b = random.randint(30, 40), random.randint(10, 20), random.randint(200, 350)
    ans = random.randint(0, 9)  # max remainder is 9, since the minimum modulus is 10
    a = quotient * m + ans - b

    question = q_format.format(a, b, m)
    answer = a_format.format(ans)

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)

def ngonal_prism(q_format: str, a_format: str) -> QuizEntry:
    """Generate a question regarding vertices on n-gonal prisms."""
    n = random.randint(0, len(N_PREFIXES) - 1)

    question = q_format.format(N_PREFIXES[n])
    answer = a_format.format((n + N_PREFIX_STARTS_AT) * 2)

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)

def imag_sqrt(q_format: str, a_format: str) -> QuizEntry:
    """Generate a negative square root question."""
    ans_coeff = random.randint(3, 10)

    question = q_format.format(ans_coeff ** 2)
    answer = a_format.format(ans_coeff)

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)

def binary_calc(q_format: str, a_format: str) -> QuizEntry:
    """Generate a binary calculation question."""
    a = random.randint(15, 20)
    b = random.randint(10, a)
    oper = random.choice(
        (
            ("+", operator.add),
            ("-", operator.sub),
            ("*", operator.mul),
        )
    )

    # if the operator is multiplication, lower the values of the two operands to make it easier
    if oper[0] == "*":
        a -= 5
        b -= 5

    question = q_format.format(a, oper[0], b)
    answer = a_format.format(oper[1](a, b))

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)

def solar_system(q_format: str, a_format: str) -> QuizEntry:
    """Generate a question on the planets of the Solar System."""
    planet = random.choice(PLANETS)

    question = q_format.format(planet[0])
    answer = a_format.format(planet[1])

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)

def taxonomic_rank(q_format: str, a_format: str) -> QuizEntry:
    """Generate a question on taxonomic classification."""
    level = random.randint(0, len(TAXONOMIC_HIERARCHY) - 2)

    question = q_format.format(TAXONOMIC_HIERARCHY[level])
    answer = a_format.format(TAXONOMIC_HIERARCHY[level + 1])

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)


def base_units_convert(q_format: str, a_format: str) -> QuizEntry:
    """Generate a SI base units conversion question."""
    unit = random.choice(list(UNITS_TO_BASE_UNITS))

    question = q_format.format(
        unit + " " + UNITS_TO_BASE_UNITS[unit][0]
    )
    answer = a_format.format(
        UNITS_TO_BASE_UNITS[unit][1]
    )

    return QuizEntry(question, [answer], DYNAMICALLY_GEN_VARIATION_TOLERANCE)


DYNAMIC_QUESTIONS_FORMAT_FUNCS = {
    201: linear_system,
    202: mod_arith,
    203: ngonal_prism,
    204: imag_sqrt,
    205: binary_calc,
    301: solar_system,
    302: taxonomic_rank,
    303: base_units_convert,
}


class TriviaQuiz(commands.Cog):
    """A cog for all quiz commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.game_status = {}  # A variable to store the game status: either running or not running.
        self.game_owners = {}  # A variable to store the person's ID who started the quiz game in a channel.

        self.questions = self.load_questions()
        self.question_limit = 0

        self.player_scores = defaultdict(int)  # A variable to store all player's scores for a bot session.
        self.game_player_scores = {}  # A variable to store temporary game player's scores.

        self.categories = {
            "general": "Test your general knowledge.",
            "retro": "Questions related to retro gaming.",
            "math": "General questions about mathematics ranging from grade 8 to grade 12.",
            "science": "Put your understanding of science to the test!",
            "cs": "A large variety of computer science questions.",
            "python": "Trivia on our amazing language, Python!",
            "wikipedia": "Guess the title of random wikipedia passages.",
        }

        self.get_wiki_questions.start()

    def cog_unload(self) -> None:
        """Cancel `get_wiki_questions` task when Cog will unload."""
        self.get_wiki_questions.cancel()

    @tasks.loop(hours=24.0)
    async def get_wiki_questions(self) -> None:
        """Get yesterday's most read articles from wikipedia and format them like trivia questions."""
        error_fetches = 0
        wiki_questions = []
        # trivia_quiz.json follows a pattern, every new category starts with the next century.
        start_id = 501
        yesterday = datetime.strftime(datetime.now(tz=UTC) - timedelta(1), "%Y/%m/%d")

        while error_fetches < MAX_ERROR_FETCH_TRIES:
            async with self.bot.http_session.get(url=WIKI_FEED_API_URL.format(date=yesterday)) as r:
                if r.status != 200:
                    error_fetches += 1
                    continue
                raw_json = await r.json()
                articles_raw = raw_json["mostread"]["articles"]

                for article in articles_raw:
                    question = article.get("extract")
                    if not question:
                        continue

                    # Normalize the wikipedia article title to remove all punctuations from it
                    for word in re.split(r"[\s-]", title := article["normalizedtitle"]):
                        cleaned_title = re.sub(
                            rf"\b{word.strip(string.punctuation)}\b", word, title, flags=re.IGNORECASE
                        )

                    # Since the extract contains the article name sometimes this would replace all the matching words
                    # in that article with *** of that length.
                    # NOTE: This removes the "answer" for 99% of the cases, but sometimes the wikipedia article is
                    # very different from the words in the extract, for example the title would be the nickname of a
                    # person (Bob Ross) whereas in the extract it would the full name (Robert Norman Ross) so it comes
                    # out as (Robert Norman ****) and (Robert Norman Ross) won't be a right answer :(
                    for word in re.split(r"[\s-]", cleaned_title):
                        word = word.strip(string.punctuation)
                        secret_word = r"\*" * len(word)
                        question = re.sub(rf"\b{word}\b", f"**{secret_word}**", question, flags=re.IGNORECASE)

                    formatted_article_question = {
                        "id": start_id,
                        "question": f"Guess the title of the Wikipedia article.\n\n{question}",
                        "answer": cleaned_title,
                        "info": article["extract"]
                    }
                    start_id += 1
                    wiki_questions.append(formatted_article_question)

                # If everything has gone smoothly until now, we can break out of the while loop
                break

        if error_fetches < MAX_ERROR_FETCH_TRIES:
            self.questions["wikipedia"] = wiki_questions.copy()
        else:
            del self.categories["wikipedia"]
            logger.warning(f"Not loading wikipedia guess questions, hit max error fetches: {MAX_ERROR_FETCH_TRIES}.")

    @staticmethod
    def load_questions() -> dict:
        """Load the questions from the JSON file."""
        p = Path("bot", "resources", "fun", "trivia_quiz.json")

        return json.loads(p.read_text(encoding="utf-8"))

    @commands.group(name="quiz", aliases=("trivia", "triviaquiz"), invoke_without_command=True)
    async def quiz_game(self, ctx: commands.Context, category: str | None, questions: int | None) -> None:
        """
        Start a quiz!

        Questions for the quiz can be selected from the following categories:
        - general: Test your general knowledge.
        - retro: Questions related to retro gaming.
        - math: General questions about mathematics ranging from grade 8 to grade 12.
        - science: Put your understanding of science to the test!
        - cs: A large variety of computer science questions.
        - python: Trivia on our amazing language, Python!
        - wikipedia: Guess the title of random wikipedia passages.

        (More to come!)
        """
        if ctx.channel.id not in self.game_status:
            self.game_status[ctx.channel.id] = False

        if ctx.channel.id not in self.game_player_scores:
            self.game_player_scores[ctx.channel.id] = {}

        # Stop game if running.
        if self.game_status[ctx.channel.id]:
            await ctx.send(
                "Game is already running... "
                f"do `{Client.prefix}quiz stop`"
            )
            return

        # Send embed showing available categories if inputted category is invalid.
        if category is None:
            category = random.choice(list(self.categories))

        category = category.lower()
        if category not in self.categories:
            embed = self.category_embed()
            await ctx.send(embed=embed)
            return

        topic = self.questions[category]
        topic_length = len(topic)

        if questions is None:
            self.question_limit = min(DEFAULT_QUESTION_LIMIT, topic_length)
        else:
            if questions > topic_length:
                await ctx.send(
                    embed=self.make_error_embed(
                        f"This category only has {topic_length} questions. "
                        "Please input a lower value!"
                    )
                )
                return

            if questions < 1:
                await ctx.send(
                    embed=self.make_error_embed(
                        "You must choose to complete at least one question. "
                        f"(or enter nothing for the default value of {DEFAULT_QUESTION_LIMIT} questions)"
                    )
                )
                return

            self.question_limit = questions

        # Start game if not running.
        if not self.game_status[ctx.channel.id]:
            self.game_owners[ctx.channel.id] = ctx.author
            self.game_status[ctx.channel.id] = True
            start_embed = self.make_start_embed(category)

            await ctx.send(embed=start_embed)  # send an embed with the rules
            await asyncio.sleep(5)

        done_questions = []
        hint_no = 0
        quiz_entry = None

        while self.game_status[ctx.channel.id]:
            # Exit quiz if number of questions for a round are already sent.
            if len(done_questions) == self.question_limit and hint_no == 0:
                await ctx.send("The round has ended.")
                await self.declare_winner(ctx.channel, self.game_player_scores[ctx.channel.id])

                self.game_status[ctx.channel.id] = False
                del self.game_owners[ctx.channel.id]
                self.game_player_scores[ctx.channel.id] = {}

                break

            # If no hint has been sent or any time alert. Basically if hint_no = 0  means it is a new question.
            if hint_no == 0:
                # Select a random question which has not been used yet.
                while True:
                    question_dict = random.choice(topic)
                    if question_dict["id"] not in done_questions:
                        done_questions.append(question_dict["id"])
                        break

                if "dynamic_id" not in question_dict:
                    quiz_entry = QuizEntry(
                        question_dict["question"],
                        quiz_answers if isinstance(quiz_answers := question_dict["answer"], list) else [quiz_answers],
                        STANDARD_VARIATION_TOLERANCE
                    )
                else:
                    format_func = DYNAMIC_QUESTIONS_FORMAT_FUNCS[question_dict["dynamic_id"]]
                    quiz_entry = format_func(
                        question_dict["question"],
                        question_dict["answer"],
                    )

                embed = discord.Embed(
                    colour=Colours.gold,
                    title=f"Question #{len(done_questions)}",
                    description=quiz_entry.question,
                )

                if img_url := question_dict.get("img_url"):
                    embed.set_image(url=img_url)

                await ctx.send(embed=embed)

            def check_func(variation_tolerance: int) -> Callable[[discord.Message], bool]:
                def contains_correct_answer(m: discord.Message) -> bool:
                    return m.channel == ctx.channel and any(
                        fuzz.ratio(answer.lower(), m.content.lower()) > variation_tolerance
                        for answer in quiz_entry.answers  # noqa: B023
                    )

                return contains_correct_answer

            try:
                msg = await self.bot.wait_for("message", check=check_func(quiz_entry.var_tol), timeout=10)
            except asyncio.TimeoutError:
                # In case of TimeoutError and the game has been stopped, then do nothing.
                if not self.game_status[ctx.channel.id]:
                    break

                if hint_no < 2:
                    hint_no += 1

                    if "hints" in question_dict:
                        hints = question_dict["hints"]

                        await ctx.send(f"**Hint #{hint_no}\n**{hints[hint_no - 1]}")
                    else:
                        await ctx.send(f"{30 - hint_no * 10}s left!")

                # Once hint or time alerts has been sent 2 times, the hint_no value will be 3
                # If hint_no > 2, then it means that all hints/time alerts have been sent.
                # Also means that the answer is not yet given and the bot sends the answer and the next question.
                else:
                    if self.game_status[ctx.channel.id] is False:
                        break

                    response = random.choice(WRONG_ANS_RESPONSE)
                    await ctx.send(response)

                    await self.send_answer(
                        ctx.channel,
                        quiz_entry.answers,
                        False,
                        question_dict,
                        self.question_limit - len(done_questions),
                    )
                    await asyncio.sleep(1)

                    hint_no = 0  # Reset the hint counter so that on the next round, it's in the initial state

                    await self.send_score(ctx.channel, self.game_player_scores[ctx.channel.id])
                    await asyncio.sleep(2)
            else:
                if self.game_status[ctx.channel.id] is False:
                    break

                points = 100 - 25 * hint_no
                if msg.author in self.game_player_scores[ctx.channel.id]:
                    self.game_player_scores[ctx.channel.id][msg.author] += points
                else:
                    self.game_player_scores[ctx.channel.id][msg.author] = points

                # Also updating the overall scoreboard.
                if msg.author in self.player_scores:
                    self.player_scores[msg.author] += points
                else:
                    self.player_scores[msg.author] = points

                hint_no = 0

                await ctx.send(f"{msg.author.mention} got the correct answer :tada: {points} points!")

                await self.send_answer(
                    ctx.channel,
                    quiz_entry.answers,
                    True,
                    question_dict,
                    self.question_limit - len(done_questions),
                )
                await self.send_score(ctx.channel, self.game_player_scores[ctx.channel.id])

                await asyncio.sleep(2)

    def make_start_embed(self, category: str) -> discord.Embed:
        """Generate a starting/introduction embed for the quiz."""
        rules = "\n".join([f"{index}: {rule}" for index, rule in enumerate(RULES, start=1)])

        start_embed = discord.Embed(
            title="Quiz game Starting!!",
            description=(
                f"Each game consists of {self.question_limit} questions.\n"
                f"**Rules :**\n{rules}"
                f"\n **Category** : {category}"
            ),
            colour=Colours.blue
        )
        start_embed.set_thumbnail(url=TRIVIA_QUIZ_ICON)

        return start_embed

    @staticmethod
    def make_error_embed(desc: str) -> discord.Embed:
        """Generate an error embed with the given description."""
        error_embed = discord.Embed(
            colour=Colours.soft_red,
            title=random.choice(NEGATIVE_REPLIES),
            description=desc,
        )

        return error_embed

    @quiz_game.command(name="stop")
    async def stop_quiz(self, ctx: commands.Context) -> None:
        """
        Stop a quiz game if its running in the channel.

        Note: Only mods or the owner of the quiz can stop it.
        """
        try:
            if self.game_status[ctx.channel.id]:
                # Check if the author is the game starter or a moderator.
                if ctx.author == self.game_owners[ctx.channel.id] or any(
                    role.id in MODERATION_ROLES for role in getattr(ctx.author, "roles", [])
                ):
                    self.game_status[ctx.channel.id] = False
                    del self.game_owners[ctx.channel.id]
                    self.game_player_scores[ctx.channel.id] = {}

                    await ctx.send("Quiz stopped.")
                    await self.declare_winner(ctx.channel, self.game_player_scores[ctx.channel.id])

                else:
                    await ctx.send(f"{ctx.author.mention}, you are not authorised to stop this game :ghost:!")
            else:
                await ctx.send("No quiz running.")
        except KeyError:
            await ctx.send("No quiz running.")

    @quiz_game.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context) -> None:
        """View everyone's score for this bot session."""
        await self.send_score(ctx.channel, self.player_scores)

    @staticmethod
    async def send_score(channel: discord.TextChannel, player_data: dict) -> None:
        """Send the current scores of players in the game channel."""
        if len(player_data) == 0:
            await channel.send("No one has made it onto the leaderboard yet.")
            return

        embed = discord.Embed(
            colour=Colours.blue,
            title="Score Board",
            description="",
        )
        embed.set_thumbnail(url=TRIVIA_QUIZ_ICON)

        sorted_dict = sorted(player_data.items(), key=operator.itemgetter(1), reverse=True)
        for item in sorted_dict:
            embed.description += f"{item[0]}: {item[1]}\n"

        await channel.send(embed=embed)

    @staticmethod
    async def declare_winner(channel: discord.TextChannel, player_data: dict) -> None:
        """Announce the winner of the quiz in the game channel."""
        if player_data:
            highest_points = max(list(player_data.values()))
            no_of_winners = list(player_data.values()).count(highest_points)

            # Check if more than 1 player has highest points.
            if no_of_winners > 1:
                winners = []
                points_copy = list(player_data.values()).copy()

                for _ in range(no_of_winners):
                    index = points_copy.index(highest_points)
                    winners.append(list(player_data.keys())[index])
                    points_copy[index] = 0

                winners_mention = " ".join(winner.mention for winner in winners)
            else:
                author_index = list(player_data.values()).index(highest_points)
                winner = list(player_data.keys())[author_index]
                winners_mention = winner.mention

            await channel.send(
                f"{winners_mention} Congratulations "
                f"on winning this quiz game with a grand total of {highest_points} points :tada:"
            )

    def category_embed(self) -> discord.Embed:
        """Build an embed showing all available trivia categories."""
        embed = discord.Embed(
            colour=Colours.blue,
            title="The available question categories are:",
            description="",
        )

        embed.set_footer(text="If a category is not chosen, a random one will be selected.")

        for cat, description in self.categories.items():
            embed.description += (
                f"**- {cat.capitalize()}**\n"
                f"{description.capitalize()}\n"
            )

        return embed

    @staticmethod
    async def send_answer(
        channel: discord.TextChannel,
        answers: list[str],
        answer_is_correct: bool,
        question_dict: dict,
        q_left: int,
    ) -> None:
        """Send the correct answer of a question to the game channel."""
        info = question_dict.get("info")

        plurality = " is" if len(answers) == 1 else "s are"

        embed = discord.Embed(
            color=Colours.bright_green,
            title=(
                ("You got it! " if answer_is_correct else "")
                + f"The correct answer{plurality} **`{', '.join(answers)}`**\n"
            ),
            description="",
        )

        # Don't check for info is not None, as we want to filter out empty strings.
        if info:
            embed.description += f"**Information**\n{info}\n\n"

        embed.description += (
            ("Let's move to the next question." if q_left > 0 else "")
            + f"\nRemaining questions: {q_left}"
        )
        await channel.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the TriviaQuiz cog."""
    await bot.add_cog(TriviaQuiz(bot))
