"""
Wordle Bot — standalone test build
Token goes in .env as DISCORD_TOKEN=...
"""
import asyncio
import json
import os
import random
import time
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

MAX_GUESSES      = 6
WORD_LENGTH      = 5
LEADERBOARD_FILE = Path(__file__).parent / "leaderboard.json"

GREEN  = "🟩"
YELLOW = "🟨"
RED    = "🟥"
BLANK  = "⬜"

def letter_emoji(ch: str) -> str:
    return chr(0x1F1E6 + ord(ch.upper()) - ord("A"))

# Load answer list (small list)
_answers_file = Path(__file__).parent / "wordle_answers.txt"
ANSWERS: list[str] = []
if _answers_file.exists():
    ANSWERS = [w.strip().lower() for w in _answers_file.read_text().splitlines() if len(w.strip()) == 5]

# Load valid guess list (big list)
_guesses_file = Path(__file__).parent / "wordle_valid_guesses.txt"
VALID_GUESSES: set[str] = set()
if _guesses_file.exists():
    VALID_GUESSES = {w.strip().lower() for w in _guesses_file.read_text().splitlines() if len(w.strip()) == 5}

# Fallback if files missing
if not ANSWERS:
    ANSWERS = ["crane", "slate", "trace", "stare", "snare"]
if not VALID_GUESSES:
    VALID_GUESSES = set(ANSWERS)


# ── Leaderboard ───────────────────────────────────────────────────────────────

def _load_lb() -> dict:
    if LEADERBOARD_FILE.exists():
        try:
            return json.loads(LEADERBOARD_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_lb(data: dict) -> None:
    LEADERBOARD_FILE.write_text(json.dumps(data, indent=2))

def _get_player(data: dict, user_id: int) -> dict:
    key = str(user_id)
    if key not in data:
        data[key] = {
            "name": "Unknown", "games_played": 0, "games_won": 0,
            "total_guesses": 0, "best_guesses": None,
            "giveups": 0, "win_streak": 0, "best_streak": 0,
        }
    return data[key]

def record_game(user, guesses_used: int, won: bool, gave_up: bool) -> None:
    data = _load_lb()
    p    = _get_player(data, user.id)
    p["name"]           = str(user)
    p["games_played"]  += 1
    p["total_guesses"] += guesses_used
    if gave_up:
        p["giveups"]    += 1
        p["win_streak"]  = 0
    elif won:
        p["games_won"]  += 1
        p["win_streak"]  = p.get("win_streak", 0) + 1
        if p["win_streak"] > p.get("best_streak", 0):
            p["best_streak"] = p["win_streak"]
        if p["best_guesses"] is None or guesses_used < p["best_guesses"]:
            p["best_guesses"] = guesses_used
    else:
        p["win_streak"] = 0
    _save_lb(data)


# ── Game state ────────────────────────────────────────────────────────────────

class WordleGame:
    def __init__(self, word: str, player: discord.User) -> None:
        self.word    = word
        self.player  = player
        self.guesses: list[str]       = []
        self.results: list[list[str]] = []

    @property
    def guesses_remaining(self) -> int:
        return MAX_GUESSES - len(self.guesses)

    @property
    def is_won(self) -> bool:
        return bool(self.guesses) and self.guesses[-1] == self.word

    @property
    def is_over(self) -> bool:
        return self.is_won or self.guesses_remaining == 0

    def evaluate_guess(self, guess: str) -> list[str]:
        result      = [RED] * WORD_LENGTH
        answer_pool = list(self.word)
        for i, (g, a) in enumerate(zip(guess, self.word)):
            if g == a:
                result[i]      = GREEN
                answer_pool[i] = None
        for i, g in enumerate(guess):
            if result[i] == GREEN:
                continue
            if g in answer_pool:
                result[i] = YELLOW
                answer_pool[answer_pool.index(g)] = None
        return result

    def record_guess(self, guess: str) -> list[str]:
        colours = self.evaluate_guess(guess)
        self.guesses.append(guess)
        self.results.append(colours)
        return colours

    def new_letters_found(self, colours: list[str]) -> int:
        return sum(1 for c in colours if c in (GREEN, YELLOW))

    def board_text(self) -> str:
        rows = []
        for guess, colours in zip(self.guesses, self.results):
            letters = " ".join(letter_emoji(ch) for ch in guess)
            dots    = " ".join(colours)
            rows.append(f"{letters}\n{dots}")
        blank_row = " ".join([BLANK] * WORD_LENGTH)
        for _ in range(self.guesses_remaining):
            rows.append(blank_row)
        return "\n\n".join(rows)

    def letter_status(self) -> dict[str, str]:
        """
        Track best-known status per letter:
        GREEN > YELLOW > RED
        """
        priority = {GREEN: 3, YELLOW: 2, RED: 1}
        status: dict[str, str] = {}
        for guess, colours in zip(self.guesses, self.results):
            for ch, col in zip(guess, colours):
                ch = ch.upper()
                if ch not in status or priority[col] > priority[status[ch]]:
                    status[ch] = col
        return status


# ── Message builders ──────────────────────────────────────────────────────────

FOOTER = "_You can use `.letters` to view your discovered letters._"
FOOTER_LINE = f"\n\n{FOOTER}"

def welcome_msg(game: WordleGame) -> str:
    return (
        f"Welcome to Wordle, {game.player.mention}!\n\n"
        f"You currently have **{game.guesses_remaining}** guesses remaining.\n\n"
        f"{game.board_text()}\n\n"
        f"Type your word below!{FOOTER_LINE}"
    )

def guess_msg(game: WordleGame, colours: list[str]) -> str:
    found = game.new_letters_found(colours)
    header = (
        f"🎉 You revealed **{found}** letter{'s' if found != 1 else ''}! 🎉"
        if found > 0 else
        "No new letters found this time."
    )
    return (
        f"{header}\n\n"
        f"— You have **{game.guesses_remaining}** "
        f"guess{'es' if game.guesses_remaining != 1 else ''} remaining —\n\n"
        f"{game.board_text()}\n\n"
        f"Type your next word below!{FOOTER_LINE}"
    )

def win_msg(game: WordleGame) -> str:
    return (
        f"🎉 **You won, {game.player.mention}!**\n"
        f"You guessed **{game.word.upper()}** in **{len(game.guesses)}** "
        f"guess{'es' if len(game.guesses) != 1 else ''}!\n\n"
        f"{game.board_text()}{FOOTER_LINE}"
    )

def lose_msg(game: WordleGame) -> str:
    return (
        f"💀 **Game over, {game.player.mention}!**\n"
        f"The word was **{game.word.upper()}**.\n\n"
        f"{game.board_text()}{FOOTER_LINE}"
    )

def giveup_msg(game: WordleGame) -> str:
    return (
        f"🏳️ **{game.player.mention} gave up!**\n"
        f"The word was **{game.word.upper()}**.\n\n"
        f"{game.board_text()}{FOOTER_LINE}"
    )

def timeout_msg(game: WordleGame) -> str:
    return (
        f"⏰ **Timed out, {game.player.mention}!**\n"
        f"The word was **{game.word.upper()}**.{FOOTER_LINE}"
    )

def build_dm_summary(game: WordleGame, outcome: str) -> str:
    header = {
        "win":  f"🎉 You won your Wordle game!",
        "lose": f"💀 You lost this Wordle game.",
        "giveup": "🏳️ You gave up this Wordle game.",
        "timeout": "⏰ Your Wordle game timed out.",
    }.get(outcome, "Your Wordle game has finished.")
    lines = [
        header,
        "",
        f"Secret word: **{game.word.upper()}**",
        f"Guesses used: **{len(game.guesses)} / {MAX_GUESSES}**",
        "",
        "Board:",
        game.board_text(),
        "",
        "Thanks for playing! You can toggle these DMs with `.wordledmoff` / `.wordledmon` in the server.",
    ]
    return "\n".join(lines)


# ── Leaderboard view ──────────────────────────────────────────────────────────

BOARD_CATEGORIES = [
    ("🏆  Most Games Played",  "games_played",  lambda v: f"{v} games"),
    ("🥇  Most Games Won",     "games_won",     lambda v: f"{v} wins"),
    ("🎯  Best Guess Count",   "best_guesses",  lambda v: f"{v} guesses" if v else "—"),
    ("📊  Total Guesses Made", "total_guesses", lambda v: f"{v} guesses"),
    ("🔥  Best Win Streak",    "best_streak",   lambda v: f"{v} in a row"),
    ("🏳️  Most Give-Ups",     "giveups",       lambda v: f"{v} give-ups"),
    ("📈  Best Win Rate",      "__winrate__",   lambda v: f"{v}%"),
]

def _build_lb_embed(page: int) -> discord.Embed:
    title, key, fmt = BOARD_CATEGORIES[page]
    data = _load_lb()

    if not data:
        embed = discord.Embed(title=title, description="No games recorded yet!", colour=discord.Colour.gold())
        embed.set_footer(text=f"Page {page + 1} of {len(BOARD_CATEGORIES)}")
        return embed

    if key == "__winrate__":
        rows = []
        for uid, p in data.items():
            played = p.get("games_played", 0)
            if played == 0:
                continue
            rate = round(p.get("games_won", 0) / played * 100)
            rows.append((p.get("name", "Unknown"), rate, played))
        rows.sort(key=lambda r: (r[1], r[2]), reverse=True)
        lines = [f"**{i+1}.** {name} — {rate}% ({played} played)" for i, (name, rate, played) in enumerate(rows[:10])]
    else:
        rows = []
        for uid, p in data.items():
            val = p.get(key)
            if val is None:
                continue
            rows.append((p.get("name", "Unknown"), val))
        rows.sort(key=lambda r: r[1], reverse=(key != "best_guesses"))
        lines = [f"**{i+1}.** {name} — {fmt(val)}" for i, (name, val) in enumerate(rows[:10])]

    embed = discord.Embed(
        title=title,
        description="\n".join(lines) if lines else "No data yet!",
        colour=discord.Colour.gold(),
    )
    embed.set_footer(text=f"Page {page + 1} of {len(BOARD_CATEGORIES)}")
    return embed


class LeaderboardView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=120)
        self.page = 0
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= len(BOARD_CATEGORIES) - 1

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=_build_lb_embed(self.page), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=_build_lb_embed(self.page), view=self)


# ── How-to-play view ──────────────────────────────────────────────────────────

class HowToPlayView(discord.ui.View):
    PAGES = [
        (
            "📖 How to Play Wordle — Page 1 of 3",
            (
                "**Wordle** is a word-guessing game.\n\n"
                f"You have **{MAX_GUESSES} attempts** to guess a secret **{WORD_LENGTH}-letter word**.\n\n"
                "After each guess you get colour-coded feedback to help narrow down the answer.\n\n"
                "Press **Next →** to continue."
            ),
        ),
        (
            "🎨 Understanding the colours — Page 2 of 3",
            (
                "Each letter in your guess gets a colour indicator:\n\n"
                f"{GREEN} **Green** — correct letter, correct position\n"
                f"{YELLOW} **Yellow** — correct letter, wrong position\n"
                f"{RED} **Red** — letter is not in the word\n\n"
                f"**Example — guess CRANE, secret word TRAIL:**\n"
                f"{letter_emoji('C')} {letter_emoji('R')} {letter_emoji('A')} {letter_emoji('N')} {letter_emoji('E')}\n"
                f"{RED} {YELLOW} {YELLOW} {RED} {RED}\n\n"
                "R and A are in the word, just in the wrong spots.\n\n"
                "Press **Next →** to continue."
            ),
        ),
        (
            "🚀 Ready to play? — Page 3 of 3",
            (
                "**Rules:**\n"
                f"• Guesses must be exactly **{WORD_LENGTH} letters** long\n"
                "• Only letters A–Z are accepted\n"
                f"• You have **{MAX_GUESSES} guesses** — use them wisely!\n"
                "• Type `giveup` at any time to end and reveal the word\n\n"
                "Press **Start Playing** when you're ready. Good luck! 🍀"
            ),
        ),
    ]

    def __init__(self, ctx: commands.Context, word: str) -> None:
        super().__init__(timeout=120)
        self.ctx     = ctx
        self.word    = word
        self.page    = 0
        self.message: discord.Message | None = None
        self._update_buttons()

    def _build_embed(self) -> discord.Embed:
        title, body = self.PAGES[self.page]
        return discord.Embed(title=title, description=body, colour=discord.Colour.blurple())

    def _update_buttons(self) -> None:
        self.next_btn.disabled  = self.page >= len(self.PAGES) - 1
        self.start_btn.disabled = self.page < len(self.PAGES) - 1

    @discord.ui.button(label="Next →", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="Start Playing", style=discord.ButtonStyle.success, disabled=True)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        self.stop()
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            return
        await interaction.response.defer()
        self.ctx.bot.dispatch("wordle_start", self.ctx, self.word)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(
                    embed=discord.Embed(
                        title="⏰ Timed out",
                        description="Run `.wordle` again whenever you're ready!",
                        colour=discord.Colour.red(),
                    ),
                    view=self,
                )
            except discord.HTTPException:
                pass

    async def send(self, ctx: commands.Context) -> None:
        self.message = await ctx.send(embed=self._build_embed(), view=self)


# ── Summary view (DM again button) ────────────────────────────────────────────

class SummaryView(discord.ui.View):
    def __init__(self, cog: "WordleCog", user_id: int) -> None:
        super().__init__(timeout=900)  # same as message lifetime
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="📩 Send Summary to My DMs Again", style=discord.ButtonStyle.primary)
    async def send_again_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button isn't for you.", ephemeral=True)
            return

        now = time.time()
        last = self.cog.last_dm_again.get(self.user_id, 0)
        if now - last < 60:
            await interaction.response.send_message(
                "You can only resend the summary once per minute. Please wait a bit.",
                ephemeral=True,
            )
            return

        summary = self.cog.last_summaries.get(self.user_id)
        if not summary:
            await interaction.response.send_message(
                "I don't have a recent Wordle summary stored for you.",
                ephemeral=True,
            )
            return

        self.cog.last_dm_again[self.user_id] = now
        try:
            await interaction.user.send(summary)
            await interaction.response.send_message("Summary sent to your DMs again.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I couldn't DM you. Please make sure your DMs are open.",
                ephemeral=True,
            )


# ── Cog ───────────────────────────────────────────────────────────────────────

class WordleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot             = bot
        self.games:          dict[int, WordleGame]      = {}  # user_id -> game
        self.board_messages: dict[int, discord.Message] = {}  # user_id -> current board msg
        self.game_messages:  dict[int, list[discord.Message]] = {}  # user_id -> list of bot msgs to delete
        self.letters_messages: dict[int, discord.Message] = {}  # user_id -> letters msg

        # Channel-level game control
        self.channel_active: dict[int, int] = {}  # channel_id -> user_id currently playing
        self.channel_queue:  dict[int, list[commands.Context]] = {}  # channel_id -> list of ctxs

        # DM preferences and summaries
        self.dm_prefs: dict[int, bool] = {}  # user_id -> bool (default True)
        self.last_summaries: dict[int, str] = {}  # user_id -> last DM summary text
        self.last_dm_again: dict[int, float] = {}  # user_id -> last "send again" timestamp

    def dm_enabled(self, user_id: int) -> bool:
        return self.dm_prefs.get(user_id, True)

    async def _schedule_delete(self, message: discord.Message, delay: int) -> None:
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except discord.HTTPException:
            pass

    def _track_game_message(self, user_id: int, msg: discord.Message) -> None:
        self.game_messages.setdefault(user_id, []).append(msg)

    async def _start_game_for_ctx(self, ctx: commands.Context) -> None:
        word = random.choice(ANSWERS)
        view = HowToPlayView(ctx, word)
        await view.send(ctx)

    async def _advance_queue(self, channel: discord.TextChannel) -> None:
        chan_id = channel.id
        queue = self.channel_queue.get(chan_id) or []
        if not queue:
            self.channel_active.pop(chan_id, None)
            return

        next_ctx = queue.pop(0)
        self.channel_queue[chan_id] = queue

        user = next_ctx.author
        mention = user.mention
        msg = await channel.send(
            f"{mention} it's your turn to play Wordle! "
            f"You have **60 seconds** to respond in this channel or your spot will be skipped.\n"
            f"(This message will be deleted in 15 minutes.)"
        )
        asyncio.create_task(self._schedule_delete(msg, 900))

        def check(m: discord.Message) -> bool:
            return m.author.id == user.id and m.channel.id == channel.id

        try:
            reply = await self.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            # User didn't respond, move to next
            await self._advance_queue(channel)
            return

        try:
            await reply.delete()
        except discord.HTTPException:
            pass

        # Start game for this user
        self.channel_active[chan_id] = user.id
        await self._start_game_for_ctx(next_ctx)

    @commands.command(name="wordle", aliases=("wrd",))
    async def wordle_command(self, ctx: commands.Context) -> None:
        """Start a game of Wordle."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        user_id = ctx.author.id
        chan_id = ctx.channel.id

        # If user already has an active game anywhere, tell them
        if self.games.get(user_id):
            notice = await ctx.send(
                f"{ctx.author.mention} You already have an active Wordle game! Finish it first."
            )
            asyncio.create_task(self._schedule_delete(notice, 6))
            return

        # If channel already has an active game, queue this user
        active_user = self.channel_active.get(chan_id)
        if active_user is not None:
            queue = self.channel_queue.setdefault(chan_id, [])
            # Check if user already in queue
            if any(c.author.id == user_id for c in queue):
                notice = await ctx.send(
                    f"{ctx.author.mention} Please wait — you're already in the Wordle queue for this channel."
                )
                asyncio.create_task(self._schedule_delete(notice, 6))
                return

            queue.append(ctx)
            position = len(queue)
            notice = await ctx.send(
                f"{ctx.author.mention} Please wait until <@{active_user}> has finished playing Wordle.\n"
                f"Your current position in the queue is **{position}**.\n"
                f"(This message will be deleted in 15 minutes.)"
            )
            asyncio.create_task(self._schedule_delete(notice, 900))
            return

        # No active game in this channel — start immediately
        self.channel_active[chan_id] = user_id
        await self._start_game_for_ctx(ctx)

    @commands.command(name="leaderboard", aliases=("lb", "scores"))
    async def leaderboard_command(self, ctx: commands.Context) -> None:
        """View the Wordle leaderboard."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        view = LeaderboardView()
        msg = await ctx.send(embed=_build_lb_embed(0), view=view)
        # Optional: auto-delete leaderboard after some time
        asyncio.create_task(self._schedule_delete(msg, 900))

    @commands.command(name="letters")
    async def letters_command(self, ctx: commands.Context) -> None:
        """Show discovered letters for your current Wordle game."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        game = self.games.get(ctx.author.id)
        if not game:
            # No active game — silently delete
            return

        status = game.letter_status()
        # Build A–Z line with colours
        rows = []
        for ch_code in range(ord("A"), ord("Z") + 1):
            ch = chr(ch_code)
            col = status.get(ch)
            if col == GREEN:
                symbol = f"{GREEN}{letter_emoji(ch)}"
            elif col == YELLOW:
                symbol = f"{YELLOW}{letter_emoji(ch)}"
            elif col == RED:
                symbol = f"{RED}{letter_emoji(ch)}"
            else:
                symbol = f"{BLANK}{letter_emoji(ch)}"
            rows.append(symbol)

        text = (
            f"{ctx.author.mention} Here are your discovered letters so far:\n\n"
            + " ".join(rows)
            + "\n\nThis message will disappear when you send your next message in this channel."
        )
        msg = await ctx.send(text)
        # Track and overwrite any previous letters message for this user
        old = self.letters_messages.get(ctx.author.id)
        if old:
            try:
                await old.delete()
            except discord.HTTPException:
                pass
        self.letters_messages[ctx.author.id] = msg
        self._track_game_message(ctx.author.id, msg)

    @commands.command(name="wordledmoff")
    async def wordle_dm_off(self, ctx: commands.Context) -> None:
        """Turn off Wordle result DMs."""
        self.dm_prefs[ctx.author.id] = False
        msg = await ctx.send(f"{ctx.author.mention} Wordle result DMs are now **disabled**.")
        asyncio.create_task(self._schedule_delete(msg, 10))
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.command(name="wordledmon")
    async def wordle_dm_on(self, ctx: commands.Context) -> None:
        """Turn on Wordle result DMs."""
        self.dm_prefs[ctx.author.id] = True
        msg = await ctx.send(f"{ctx.author.mention} Wordle result DMs are now **enabled**.")
        asyncio.create_task(self._schedule_delete(msg, 10))
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_wordle_start(self, ctx: commands.Context, word: str) -> None:
        game = WordleGame(word, ctx.author)
        self.games[ctx.author.id] = game
        msg  = await ctx.send(welcome_msg(game))
        self.board_messages[ctx.author.id] = msg
        self._track_game_message(ctx.author.id, msg)
        await self._run_game(ctx, game)

    async def _run_game(self, ctx: commands.Context, game: WordleGame) -> None:
        user_id = ctx.author.id
        chan_id = ctx.channel.id

        def check(m: discord.Message) -> bool:
            return m.author.id == user_id and m.channel.id == chan_id

        while not game.is_over:
            try:
                msg = await self.bot.wait_for("message", timeout=120.0, check=check)
            except asyncio.TimeoutError:
                await self._finish(ctx, game, outcome="timeout")
                return

            # Delete any active letters message as soon as user sends ANY message
            letters_msg = self.letters_messages.pop(user_id, None)
            if letters_msg:
                try:
                    await letters_msg.delete()
                except discord.HTTPException:
                    pass

            # Delete the user's guess/command
            try:
                await msg.delete()
            except discord.HTTPException:
                pass

            content = msg.content.strip().lower()

            if content == "giveup":
                await self._finish(ctx, game, outcome="giveup")
                return

            # --- VALIDATION CHECKS ---
            if len(content) != WORD_LENGTH:
                err = await ctx.send(f"{ctx.author.mention} Please enter a **{WORD_LENGTH}-letter** word.{FOOTER_LINE}")
                self._track_game_message(user_id, err)
                await asyncio.sleep(4)
                try:
                    await err.delete()
                except discord.HTTPException:
                    pass
                continue

            if not content.isalpha():
                err = await ctx.send(f"{ctx.author.mention} Only letters please — no numbers or symbols.{FOOTER_LINE}")
                self._track_game_message(user_id, err)
                await asyncio.sleep(4)
                try:
                    await err.delete()
                except discord.HTTPException:
                    pass
                continue

            if content not in VALID_GUESSES:
                err = await ctx.send(f"{ctx.author.mention} **{content.upper()}** is not in the word list!{FOOTER_LINE}")
                self._track_game_message(user_id, err)
                await asyncio.sleep(4)
                try:
                    await err.delete()
                except discord.HTTPException:
                    pass
                continue
            # --- END VALIDATION ---

            colours = game.record_guess(content)
            await self._delete_board(user_id)

            if game.is_won:
                await self._finish(ctx, game, outcome="win")
                return
            elif game.guesses_remaining == 0:
                await self._finish(ctx, game, outcome="lose")
                return
            else:
                new_msg = await ctx.send(guess_msg(game, colours))
                self.board_messages[user_id] = new_msg
                self._track_game_message(user_id, new_msg)

    async def _finish(self, ctx: commands.Context, game: WordleGame, outcome: str) -> None:
        user_id = ctx.author.id
        chan_id = ctx.channel.id

        await self._delete_board(user_id)

        # DM summary if enabled
        summary_text = build_dm_summary(game, outcome)
        self.last_summaries[user_id] = summary_text
        if self.dm_enabled(user_id):
            try:
                await ctx.author.send(summary_text)
            except discord.Forbidden:
                pass

        # Record game in leaderboard
        won = outcome == "win"
        gave_up = outcome == "giveup"
        record_game(ctx.author, len(game.guesses), won=won, gave_up=gave_up)

        # Small summary in channel
        if outcome == "win":
            small = await ctx.send(
                f"{ctx.author.mention} — You solved the Wordle in **{len(game.guesses)}** guesses!\n"
                f"This message will be deleted in 15 minutes."
            )
        elif outcome == "lose":
            small = await ctx.send(
                f"{ctx.author.mention} — You lost this Wordle. The word was **{game.word.upper()}**.\n"
                f"This message will be deleted in 15 minutes."
            )
        elif outcome == "giveup":
            small = await ctx.send(
                f"{ctx.author.mention} — You gave up. The word was **{game.word.upper()}**.\n"
                f"This message will be deleted in 15 minutes."
            )
        else:  # timeout
            small = await ctx.send(
                f"{ctx.author.mention} — Your Wordle game timed out. The word was **{game.word.upper()}**.\n"
                f"This message will be deleted in 15 minutes."
            )

        view = SummaryView(self, user_id)
        # Attach button to the small summary
        await small.edit(view=view)
        asyncio.create_task(self._schedule_delete(small, 900))

        # "Check your DMs" message
        check_msg = await ctx.send(
            f"{ctx.author.mention} Check Your DM's For Your Full Results! **Make Sure To Have Your DM's Open!**\n"
            f"This message will be deleted in 15 minutes."
        )
        asyncio.create_task(self._schedule_delete(check_msg, 900))

        # Clean up all game-related messages in channel
        msgs = self.game_messages.pop(user_id, [])
        for m in msgs:
            try:
                await m.delete()
            except discord.HTTPException:
                pass

        self._cleanup(user_id)

        # Advance queue for this channel
        channel = ctx.channel
        await self._advance_queue(channel)

    async def _delete_board(self, user_id: int) -> None:
        msg = self.board_messages.pop(user_id, None)
        if msg:
            try:
                await msg.delete()
            except discord.HTTPException:
                pass

    def _cleanup(self, user_id: int) -> None:
        self.games.pop(user_id, None)
        self.board_messages.pop(user_id, None)
        self.letters_messages.pop(user_id, None)
        # Remove user from any channel_active mapping
        to_remove = []
        for chan_id, uid in self.channel_active.items():
            if uid == user_id:
                to_remove.append(chan_id)
        for chan_id in to_remove:
            self.channel_active.pop(chan_id, None)


# ── Bot ───────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print(f"Loaded {len(ANSWERS)} Wordle answers.")
    print(f"Loaded {len(VALID_GUESSES)} valid guess words.")
    print("Commands: .wordle | .leaderboard | .letters | .wordledmon | .wordledmoff")
    print("------")

async def main() -> None:
    async with bot:
        await bot.add_cog(WordleCog(bot))
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN not set — add it to your .env file")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())

