import asyncio
import contextlib
import logging
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

from bot.bot import bot
from bot.constants import Channels, Client, Roles as MainRoles
from bot.decorators import with_role
from .constants import Colours, EggHuntSettings, Emoji, Roles

log = logging.getLogger(__name__)

DB_PATH = Path("bot/resources/persist/egg_hunt.sqlite")

TEAM_MAP = {
    Roles.white: Emoji.egg_white,
    Roles.blurple: Emoji.egg_blurple,
    Emoji.egg_white: Roles.white,
    Emoji.egg_blurple: Roles.blurple
}

GUILD = bot.get_guild(Client.guild)

MUTED = GUILD.get_role(MainRoles.muted)


def get_team_role(user: discord.Member) -> discord.Role:
    """Helper function to get the team role for a member."""
    if Roles.white in user.roles:
        return Roles.white
    if Roles.blurple in user.roles:
        return Roles.blurple


async def assign_team(user: discord.Member) -> discord.Member:
    """Helper function to assign a new team role for a member."""
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    c.execute(f"SELECT team FROM user_scores WHERE user_id = {user.id}")
    result = c.fetchone()
    if not result:
        c.execute(
            "SELECT team, COUNT(*) AS count FROM user_scores "
            "GROUP BY team ORDER BY count ASC LIMIT 1;"
        )
        result = c.fetchone()
        result = result[0] if result else "WHITE"

    if result[0] == "WHITE":
        new_team = Roles.white
    else:
        new_team = Roles.blurple

    db.close()

    log.debug(f"Assigned role {new_team} to {user}.")

    await user.add_roles(new_team)
    return GUILD.get_member(user.id)


class EggMessage:
    """Handles a single egg reaction drop session."""

    def __init__(self, message: discord.Message, egg: discord.Emoji):
        self.message = message
        self.egg = egg
        self.first = None
        self.users = set()
        self.teams = {Roles.white: "WHITE", Roles.blurple: "BLURPLE"}
        self.new_team_assignments = {}
        self.timeout_task = None

    @staticmethod
    def add_user_score_sql(user_id: int, team: str, score: int) -> str:
        """Builds the SQL for adding a score to a user in the database."""
        return (
            "INSERT INTO user_scores(user_id, team, score)"
            f"VALUES({user_id}, '{team}', {score})"
            f"ON CONFLICT (user_id) DO UPDATE SET score=score+{score}"
        )

    @staticmethod
    def add_team_score_sql(team_name: str, score: int) -> str:
        """Builds the SQL for adding a score to a team in the database."""
        return f"UPDATE team_scores SET team_score=team_score+{score} WHERE team_id='{team_name}'"

    def finalise_score(self):
        """Sums and actions scoring for this egg drop session."""
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()

        team_scores = {"WHITE": 0, "BLURPLE": 0}

        first_team = get_team_role(self.first)
        if not first_team:
            log.debug("User without team role!")
            db.close()
            return

        score = 3 if first_team == TEAM_MAP[first_team] else 2

        c.execute(self.add_user_score_sql(self.first.id, self.teams[first_team], score))
        team_scores[self.teams[first_team]] += score

        for user in self.users:
            team = get_team_role(user)
            if not team:
                log.debug("User without team role!")
                continue

            team_name = self.teams[team]
            team_scores[team_name] += 1
            score = 2 if team == first_team else 1
            c.execute(self.add_user_score_sql(user.id, team_name, score))

        for team_name, score in team_scores.items():
            if not score:
                continue
            c.execute(self.add_team_score_sql(team_name, score))

        db.commit()
        db.close()

        log.debug(
            f"EggHunt session finalising: ID({self.message.id}) "
            f"FIRST({self.first}) REST({self.users})."
        )

    async def start_timeout(self, seconds: int = 5):
        """Begins a task that will sleep until the given seconds before finalizing the session."""
        if self.timeout_task:
            self.timeout_task.cancel()
            self.timeout_task = None

        await asyncio.sleep(seconds)

        bot.remove_listener(self.collect_reacts, name="on_reaction_add")

        with contextlib.suppress(discord.Forbidden):
            await self.message.clear_reactions()

        if self.first:
            self.finalise_score()

    def is_valid_react(self, reaction: discord.Reaction, user: discord.Member) -> bool:
        """Validates a reaction event was meant for this session."""
        if user.bot:
            return False
        if reaction.message.id != self.message.id:
            return False
        if reaction.emoji != self.egg:
            return False

        # Ignore the punished
        if MUTED in user.roles:
            return False

        return True

    async def collect_reacts(self, reaction: discord.Reaction, user: discord.Member):
        """Handles emitted reaction_add events via listener."""
        if not self.is_valid_react(reaction, user):
            return

        team = get_team_role(user)
        if not team:
            log.debug(f"Assigning a team for {user}.")
            user = await assign_team(user)

        if not self.first:
            log.debug(f"{user} was first to react to egg on {self.message.id}.")
            self.first = user
            await self.start_timeout()
        else:
            if user != self.first:
                self.users.add(user)

    async def start(self):
        """Starts the egg drop session."""
        log.debug(f"EggHunt session started for message {self.message.id}.")
        bot.add_listener(self.collect_reacts, name="on_reaction_add")
        with contextlib.suppress(discord.Forbidden):
            await self.message.add_reaction(self.egg)
        self.timeout_task = asyncio.create_task(self.start_timeout(300))
        while True:
            if not self.timeout_task:
                break
            if not self.timeout_task.done():
                await self.timeout_task
            else:
                # make sure any exceptions raise if necessary
                self.timeout_task.result()
                break


class SuperEggMessage(EggMessage):
    """Handles a super egg session."""

    def __init__(self, message: discord.Message, egg: discord.Emoji, window: int):
        super().__init__(message, egg)
        self.window = window

    async def finalise_score(self):
        """Sums and actions scoring for this super egg session."""
        try:
            message = await self.message.channel.fetch_message(self.message.id)
        except discord.NotFound:
            return

        count = 0
        white = 0
        blurple = 0
        react_users = []
        for reaction in message.reactions:
            if reaction.emoji == self.egg:
                react_users = await reaction.users().flatten()
                for user in react_users:
                    team = get_team_role(user)
                    if team == Roles.white:
                        white += 1
                    elif team == Roles.blurple:
                        blurple += 1
                count = reaction.count - 1
                break

        score = 50 if self.egg == Emoji.egg_gold else 100
        if white == blurple:
            log.debug("Tied SuperEgg Result.")
            team = None
            score /= 2
        elif white > blurple:
            team = Roles.white
        else:
            team = Roles.blurple

        embed = self.message.embeds[0]

        db = sqlite3.connect(DB_PATH)
        c = db.cursor()

        user_bonus = 5 if self.egg == Emoji.egg_gold else 10
        for user in react_users:
            if user.bot:
                continue
            role = get_team_role(user)
            if not role:
                print("issue")
            user_score = 1 if user != self.first else user_bonus
            c.execute(self.add_user_score_sql(user.id, self.teams[role], user_score))

        if not team:
            embed.description = f"{embed.description}\n\nA Tie!\nBoth got {score} points!"
            c.execute(self.add_team_score_sql(self.teams[Roles.white], score))
            c.execute(self.add_team_score_sql(self.teams[Roles.blurple], score))
            team_name = "TIE"
        else:
            team_name = self.teams[team]
            embed.description = (
                f"{embed.description}\n\nTeam {team_name.capitalize()} won the points!"
            )
            c.execute(self.add_team_score_sql(team_name, score))

        c.execute(
            "INSERT INTO super_eggs (message_id, egg_type, team, window) "
            f"VALUES ({self.message.id}, '{self.egg.name}', '{team_name}', {self.window});"
        )

        log.debug("Committing Super Egg scores.")
        db.commit()
        db.close()

        embed.set_footer(text=f"Finished with {count} total reacts.")
        with contextlib.suppress(discord.HTTPException):
            await self.message.edit(embed=embed)

    async def start_timeout(self, seconds=None):
        """Starts the super egg session."""
        if not seconds:
            return
        count = 4
        for _ in range(count):
            await asyncio.sleep(60)
            embed = self.message.embeds[0]
            embed.set_footer(text=f"Finishing in {count} minutes.")
            try:
                await self.message.edit(embed=embed)
            except discord.HTTPException:
                break
            count -= 1
        bot.remove_listener(self.collect_reacts, name="on_reaction_add")
        await self.finalise_score()


class EggHunt(commands.Cog):
    """Easter Egg Hunt Event."""

    def __init__(self):
        self.event_channel = GUILD.get_channel(Channels.seasonalbot_chat)
        self.super_egg_buffer = 60*60
        self.tables = {
            "super_eggs": (
                "CREATE TABLE super_eggs ("
                "message_id INTEGER NOT NULL "
                "  CONSTRAINT super_eggs_pk PRIMARY KEY, "
                "egg_type   TEXT    NOT NULL, "
                "team       TEXT    NOT NULL, "
                "window     INTEGER);"
            ),
            "team_scores": (
                "CREATE TABLE team_scores ("
                "team_id TEXT, "
                "team_score INTEGER DEFAULT 0);"
            ),
            "user_scores": (
                "CREATE TABLE user_scores("
                "user_id INTEGER NOT NULL "
                "  CONSTRAINT user_scores_pk PRIMARY KEY, "
                "team TEXT NOT NULL, "
                "score INTEGER DEFAULT 0 NOT NULL);"
            ),
            "react_logs": (
                "CREATE TABLE react_logs("
                "member_id INTEGER NOT NULL, "
                "message_id INTEGER NOT NULL, "
                "reaction_id TEXT NOT NULL, "
                "react_timestamp REAL NOT NULL);"
            )
        }
        self.prepare_db()
        self.task = asyncio.create_task(self.super_egg())
        self.task.add_done_callback(self.task_cleanup)

    def prepare_db(self):
        """Ensures database tables all exist and if not, creates them."""
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()

        exists_sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"

        missing_tables = []
        for table in self.tables:
            c.execute(exists_sql.format(table_name=table))
            result = c.fetchone()
            if not result:
                missing_tables.append(table)

        for table in missing_tables:
            log.info(f"Table {table} is missing, building new one.")
            c.execute(self.tables[table])

        db.commit()
        db.close()

    def task_cleanup(self, task):
        """Returns task result and restarts. Used as a done callback to show raised exceptions."""
        task.result()
        self.task = asyncio.create_task(self.super_egg())

    @staticmethod
    def current_timestamp() -> float:
        """Returns a timestamp of the current UTC time."""
        return datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()

    async def super_egg(self):
        """Manages the timing of super egg drops."""
        while True:
            now = int(self.current_timestamp())

            if now > EggHuntSettings.end_time:
                log.debug("Hunt ended. Ending task.")
                break

            if now < EggHuntSettings.start_time:
                remaining = EggHuntSettings.start_time - now
                log.debug(f"Hunt not started yet. Sleeping for {remaining}.")
                await asyncio.sleep(remaining)

            log.debug(f"Hunt started.")

            db = sqlite3.connect(DB_PATH)
            c = db.cursor()

            current_window = None
            next_window = None
            windows = EggHuntSettings.windows.copy()
            windows.insert(0, EggHuntSettings.start_time)
            for i, window in enumerate(windows):
                c.execute(f"SELECT COUNT(*) FROM super_eggs WHERE window={window}")
                already_dropped = c.fetchone()[0]

                if already_dropped:
                    log.debug(f"Window {window} already dropped, checking next one.")
                    continue

                if now < window:
                    log.debug("Drop windows up to date, sleeping until next one.")
                    await asyncio.sleep(window-now)
                    now = int(self.current_timestamp())

                current_window = window
                next_window = windows[i+1]
                break

            count = c.fetchone()
            db.close()

            if not current_window:
                log.debug("No drop windows left, ending task.")
                break

            log.debug(f"Current Window: {current_window}. Next Window {next_window}")

            if not count:
                if next_window < now:
                    log.debug("An Egg Drop Window was missed, dropping one now.")
                    next_drop = 0
                else:
                    next_drop = random.randrange(now, next_window)

                if next_drop:
                    log.debug(f"Sleeping until next super egg drop: {next_drop}.")
                    await asyncio.sleep(next_drop)

                if random.randrange(10) <= 2:
                    egg = Emoji.egg_diamond
                    egg_type = "Diamond"
                    score = "100"
                    colour = Colours.diamond
                else:
                    egg = Emoji.egg_gold
                    egg_type = "Gold"
                    score = "50"
                    colour = Colours.gold

                embed = discord.Embed(
                    title=f"A {egg_type} Egg Has Appeared!",
                    description=f"**Worth {score} team points!**\n\n"
                                "The team with the most reactions after 5 minutes wins!",
                    colour=colour
                )
                embed.set_thumbnail(url=egg.url)
                embed.set_footer(text="Finishing in 5 minutes.")
                msg = await self.event_channel.send(embed=embed)
                await SuperEggMessage(msg, egg, current_window).start()

            log.debug("Sleeping until next window.")
            next_loop = max(next_window - int(self.current_timestamp()), self.super_egg_buffer)
            await asyncio.sleep(next_loop)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Reaction event listener for reaction logging for later anti-cheat analysis."""
        if payload.channel_id not in EggHuntSettings.allowed_channels:
            return

        now = self.current_timestamp()
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        c.execute(
            "INSERT INTO react_logs(member_id, message_id, reaction_id, react_timestamp) "
            f"VALUES({payload.user_id}, {payload.message_id}, '{payload.emoji}', {now})"
        )
        db.commit()
        db.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Message event listener for random egg drops."""
        if self.current_timestamp() < EggHuntSettings.start_time:
            return

        if message.channel.id not in EggHuntSettings.allowed_channels:
            log.debug("Message not in Egg Hunt channel; ignored.")
            return

        if message.author.bot:
            return

        if random.randrange(100) <= 5:
            await EggMessage(message, random.choice([Emoji.egg_white, Emoji.egg_blurple])).start()

    @commands.group(invoke_without_command=True)
    async def hunt(self, ctx):
        """
        For 48 hours, hunt down as many eggs randomly appearing as possible.

        Standard Eggs
        --------------
        Egg React: +1pt
        Team Bonus for Claimed Egg: +1pt
        First React on Other Team Egg: +1pt
        First React on Your Team Egg: +2pt

        If you get first react, you will claim that egg for your team, allowing
        your team to get the Team Bonus point, but be quick, as the egg will
        disappear after 5 seconds of the first react.

        Super Eggs
        -----------
        Gold Egg: 50 team pts, 5pts to first react
        Diamond Egg: 100 team pts, 10pts to first react

        Super Eggs only appear in #seasonalbot-chat so be sure to keep an eye
        out. They stay around for 5 minutes and the team with the most reacts
        wins the points.
        """
        await ctx.invoke(bot.get_command("help"), command="hunt")

    @hunt.command()
    async def countdown(self, ctx):
        """Show the time status of the Egg Hunt event."""
        now = self.current_timestamp()
        if now > EggHuntSettings.end_time:
            return await ctx.send("The Hunt has ended.")

        difference = EggHuntSettings.start_time - now
        if difference < 0:
            difference = EggHuntSettings.end_time - now
            msg = "The Egg Hunt will end in"
        else:
            msg = "The Egg Hunt will start in"

        hours, r = divmod(difference, 3600)
        minutes, r = divmod(r, 60)
        await ctx.send(f"{msg} {hours:.0f}hrs, {minutes:.0f}mins & {r:.0f}secs")

    @hunt.command()
    async def leaderboard(self, ctx):
        """Show the Egg Hunt Leaderboards."""
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        c.execute(f"SELECT *, RANK() OVER(ORDER BY score DESC) AS rank FROM user_scores LIMIT 10")
        user_result = c.fetchall()
        c.execute(f"SELECT * FROM team_scores ORDER BY team_score DESC")
        team_result = c.fetchall()
        db.close()
        output = []
        if user_result:
            # Get the alignment needed for the score
            score_lengths = []
            for result in user_result:
                length = len(str(result[2]))
                score_lengths.append(length)

            score_length = max(score_lengths)
            for user_id, team, score, rank in user_result:
                user = GUILD.get_member(user_id) or user_id
                team = team.capitalize()
                score = f"{score}pts"
                output.append(f"{rank:>2}. {score:>{score_length+3}} - {user} ({team})")
            user_board = "\n".join(output)
        else:
            user_board = "No entries."
        if team_result:
            output = []
            for team, score in team_result:
                output.append(f"{team:<7}: {score}")
            team_board = "\n".join(output)
        else:
            team_board = "No entries."
        embed = discord.Embed(
            title="Egg Hunt Leaderboards",
            description=f"**Team Scores**\n```\n{team_board}\n```\n"
                        f"**Top 10 Members**\n```\n{user_board}\n```"
        )
        await ctx.send(embed=embed)

    @hunt.command()
    async def rank(self, ctx, *, member: discord.Member = None):
        """Get your ranking in the Egg Hunt Leaderboard."""
        member = member or ctx.author
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        c.execute(
            "SELECT rank FROM "
            "(SELECT RANK() OVER(ORDER BY score DESC) AS rank, user_id FROM user_scores)"
            f"WHERE user_id = {member.id};"
        )
        result = c.fetchone()
        db.close()
        if not result:
            embed = discord.Embed().set_author(name=f"Egg Hunt - No Ranking")
        else:
            embed = discord.Embed().set_author(name=f"Egg Hunt - Rank #{result[0]}")
        await ctx.send(embed=embed)

    @with_role(MainRoles.admin)
    @hunt.command()
    async def clear_db(self, ctx):
        """Resets the database to it's initial state."""
        def check(msg):
            if msg.author != ctx.author:
                return False
            if msg.channel != ctx.channel:
                return False
            return True
        await ctx.send(
            "WARNING: This will delete all current event data.\n"
            "Please verify this action by replying with 'Yes, I want to delete all data.'"
        )
        reply_msg = await bot.wait_for('message', check=check)
        if reply_msg.content != "Yes, I want to delete all data.":
            return await ctx.send("Reply did not match. Aborting database deletion.")
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        c.execute("DELETE FROM super_eggs;")
        c.execute("DELETE FROM user_scores;")
        c.execute("UPDATE team_scores SET team_score=0")
        db.commit()
        db.close()
        await ctx.send("Database successfully cleared.")
