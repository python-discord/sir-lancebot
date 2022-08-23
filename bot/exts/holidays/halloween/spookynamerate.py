import asyncio
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from pathlib import Path
from typing import Optional

from async_rediscache import RedisCache
from discord import Embed, Reaction, TextChannel, User
from discord.colour import Colour
from discord.ext import tasks
from discord.ext.commands import Cog, Context, group

from bot.bot import Bot
from bot.constants import Channels, Client, Colours, Month
from bot.utils.decorators import InMonthCheckFailure

logger = getLogger(__name__)

EMOJIS_VAL = {
    "\N{Jack-O-Lantern}": 1,
    "\N{Ghost}": 2,
    "\N{Skull and Crossbones}": 3,
    "\N{Zombie}": 4,
    "\N{Face Screaming In Fear}": 5,
}
ADDED_MESSAGES = [
    "Let's see if you win?",
    ":jack_o_lantern: SPOOKY :jack_o_lantern:",
    "If you got it, haunt it.",
    "TIME TO GET YOUR SPOOKY ON! :skull:",
]
PING = "<@{id}>"

EMOJI_MESSAGE = "\n".join(f"- {emoji} {val}" for emoji, val in EMOJIS_VAL.items())
HELP_MESSAGE_DICT = {
    "title": "Spooky Name Rate",
    "description": f"Help for the `{Client.prefix}spookynamerate` command",
    "color": Colours.soft_orange,
    "fields": [
        {
            "name": "How to play",
            "value": (
                "Everyday, the bot will post a random name, which you will need to spookify using your creativity.\n"
                "You can rate each message according to how scary it is.\n"
                "At the end of the day, the author of the message with most reactions will be the winner of the day.\n"
                f"On a scale of 1 to {len(EMOJIS_VAL)}, the reactions order:\n"
                f"{EMOJI_MESSAGE}"
            ),
            "inline": False,
        },
        {
            "name": "How do I add my spookified name?",
            "value": f"Simply type `{Client.prefix}spookynamerate add my name`",
            "inline": False,
        },
        {
            "name": "How do I *delete* my spookified name?",
            "value": f"Simply type `{Client.prefix}spookynamerate delete`",
            "inline": False,
        },
    ],
}

# The names are from https://www.mockaroo.com/
NAMES = json.loads(Path("bot/resources/holidays/halloween/spookynamerate_names.json").read_text("utf8"))
FIRST_NAMES = NAMES["first_names"]
LAST_NAMES = NAMES["last_names"]


class SpookyNameRate(Cog):
    """
    A game that asks the user to spookify or halloweenify a name that is given everyday.

    It sends a random name everyday. The user needs to try and spookify it to his best ability and
    send that name back using the `spookynamerate add entry` command
    """

    # This cache stores the message id of each added word along with a dictionary which contains the name the author
    # added, the author's id, and the author's score (which is 0 by default)
    messages = RedisCache()

    # The data cache stores small information such as the current name that is going on and whether it is the first time
    # the bot is running
    data = RedisCache()
    debug = getenv("SPOOKYNAMERATE_DEBUG", False)  # Enable if you do not want to limit the commands to October or if
    # you do not want to wait till 12 UTC. Note: if debug is enabled and you run `.cogs reload spookynamerate`, it
    # will automatically start the scoring and announcing the result (without waiting for 12, so do not expect it to.).
    # Also, it won't wait for the two hours (when the poll closes).

    def __init__(self, bot: Bot):
        self.bot = bot
        self.name = None

        self.bot.loop.create_task(self.load_vars())

        self.first_time = None
        self.poll = False
        self.announce_name.start()
        self.checking_messages = asyncio.Lock()
        # Define an asyncio.Lock() to make sure the dictionary isn't changed
        # when checking the messages for duplicate emojis'

    async def load_vars(self) -> None:
        """Loads the variables that couldn't be loaded in __init__."""
        self.first_time = await self.data.get("first_time", True)
        self.name = await self.data.get("name")

    @group(name="spookynamerate", invoke_without_command=True)
    async def spooky_name_rate(self, ctx: Context) -> None:
        """Get help on the Spooky Name Rate game."""
        await ctx.send(embed=Embed.from_dict(HELP_MESSAGE_DICT))

    @spooky_name_rate.command(name="list", aliases=("all", "entries"))
    async def list_entries(self, ctx: Context) -> None:
        """Send all the entries up till now in a single embed."""
        await ctx.send(embed=await self.get_responses_list(final=False))

    @spooky_name_rate.command(name="name")
    async def tell_name(self, ctx: Context) -> None:
        """Tell the current random name."""
        if not self.poll:
            await ctx.send(f"The name is **{self.name}**")
            return

        await ctx.send(
            f"The name ~~is~~ was **{self.name}**. The poll has already started, so you cannot "
            "add an entry."
        )

    @spooky_name_rate.command(name="add", aliases=("register",))
    async def add_name(self, ctx: Context, *, name: str) -> None:
        """Use this command to add/register your spookified name."""
        if self.poll:
            logger.info(f"{ctx.author} tried to add a name, but the poll had already started.")
            await ctx.send("Sorry, the poll has started! You can try and participate in the next round though!")
            return

        for data in (json.loads(user_data) for _, user_data in await self.messages.items()):
            if data["author"] == ctx.author.id:
                await ctx.send(
                    "But you have already added an entry! Type "
                    f"`{Client.prefix}spookynamerate "
                    "delete` to delete it, and then you can add it again"
                )
                return

            elif data["name"] == name:
                await ctx.send("TOO LATE. Someone has already added this name.")
                return

        msg = await (await self.get_channel()).send(f"{ctx.author.mention} added the name {name!r}!")

        await self.messages.set(
            msg.id,
            json.dumps(
                {
                    "name": name,
                    "author": ctx.author.id,
                    "score": 0,
                }
            ),
        )

        for emoji in EMOJIS_VAL:
            await msg.add_reaction(emoji)

        logger.info(f"{ctx.author} added the name {name!r}")

    @spooky_name_rate.command(name="delete")
    async def delete_name(self, ctx: Context) -> None:
        """Delete the user's name."""
        if self.poll:
            await ctx.send("You can't delete your name since the poll has already started!")
            return
        for message_id, data in await self.messages.items():
            data = json.loads(data)

            if ctx.author.id == data["author"]:
                await self.messages.delete(message_id)
                await ctx.send(f"Name deleted successfully ({data['name']!r})!")
                return

        await ctx.send(
            f"But you don't have an entry... :eyes: Type `{Client.prefix}spookynamerate add your entry`"
        )

    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
        """Ensures that each user adds maximum one reaction."""
        if user.bot or not await self.messages.contains(reaction.message.id):
            return

        async with self.checking_messages:  # Acquire the lock so that the dictionary isn't reset while iterating.
            if reaction.emoji in EMOJIS_VAL:
                # create a custom counter
                reaction_counter = defaultdict(int)
                for msg_reaction in reaction.message.reactions:
                    async for reaction_user in msg_reaction.users():
                        if reaction_user == self.bot.user:
                            continue
                        reaction_counter[reaction_user] += 1

                if reaction_counter[user] > 1:
                    await user.send(
                        "Sorry, you have already added a reaction, "
                        "please remove your reaction and try again."
                    )
                    await reaction.remove(user)
                    return

    @tasks.loop(hours=24.0)
    async def announce_name(self) -> None:
        """Announces the name needed to spookify every 24 hours and the winner of the previous game."""
        if not self.in_allowed_month():
            return

        channel = await self.get_channel()

        if self.first_time:
            await channel.send(
                "Okkey... Welcome to the **Spooky Name Rate Game**! It's a relatively simple game.\n"
                f"Everyday, a random name will be sent in <#{Channels.sir_lancebot_playground}> "
                "and you need to try and spookify it!\nRegister your name using "
                f"`{Client.prefix}spookynamerate add spookified name`"
            )

            await self.data.set("first_time", False)
            self.first_time = False

        else:
            if await self.messages.items():
                await channel.send(embed=await self.get_responses_list(final=True))
                self.poll = True
                if not SpookyNameRate.debug:
                    await asyncio.sleep(2 * 60 * 60)  # sleep for two hours

            logger.info("Calculating score")
            for message_id, data in await self.messages.items():
                data = json.loads(data)

                msg = await channel.fetch_message(message_id)
                score = 0
                for reaction in msg.reactions:
                    reaction_value = EMOJIS_VAL.get(reaction.emoji, 0)  # get the value of the emoji else 0
                    score += reaction_value * (reaction.count - 1)  # multiply by the num of reactions
                    # subtract one, since one reaction was done by the bot

                logger.debug(f"{self.bot.get_user(data['author'])} got a score of {score}")
                data["score"] = score
                await self.messages.set(message_id, json.dumps(data))

            # Sort the winner messages
            winner_messages = sorted(
                ((msg_id, json.loads(usr_data)) for msg_id, usr_data in await self.messages.items()),
                key=lambda x: x[1]["score"],
                reverse=True,
            )

            winners = []
            for i, winner in enumerate(winner_messages):
                winners.append(winner)
                if len(winner_messages) > i + 1:
                    if winner_messages[i + 1][1]["score"] != winner[1]["score"]:
                        break
                elif len(winner_messages) == (i + 1) + 1:  # The next element is the last element
                    if winner_messages[i + 1][1]["score"] != winner[1]["score"]:
                        break

            # one iteration is complete
            await channel.send("Today's Spooky Name Rate Game ends now, and the winner(s) is(are)...")

            async with channel.typing():
                await asyncio.sleep(1)  # give the drum roll feel

                if not winners:  # There are no winners (no participants)
                    await channel.send("Hmm... Looks like no one participated! :cry:")
                    return

                score = winners[0][1]["score"]
                congratulations = "to all" if len(winners) > 1 else PING.format(id=winners[0][1]["author"])
                names = ", ".join(f'{win[1]["name"]} ({PING.format(id=win[1]["author"])})' for win in winners)

                # display winners, their names and scores
                await channel.send(
                    f"Congratulations {congratulations}!\n"
                    f"You have a score of {score}!\n"
                    f"Your name{ 's were' if len(winners) > 1 else 'was'}:\n{names}"
                )

                # Send random party emojis
                party = (random.choice([":partying_face:", ":tada:"]) for _ in range(random.randint(1, 10)))
                await channel.send(" ".join(party))

            async with self.checking_messages:  # Acquire the lock to delete the messages
                await self.messages.clear()  # reset the messages

        # send the next name
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        await self.data.set("name", self.name)

        await channel.send(
            "Let's move on to the next name!\nAnd the next name is...\n"
            f"**{self.name}**!\nTry to spookify that... :smirk:"
        )

        self.poll = False  # accepting responses

    @announce_name.before_loop
    async def wait_till_scheduled_time(self) -> None:
        """Waits till the next day's 12PM if crossed it, otherwise waits till the same day's 12PM."""
        if SpookyNameRate.debug:
            return

        now = datetime.utcnow()
        if now.hour < 12:
            twelve_pm = now.replace(hour=12, minute=0, second=0, microsecond=0)
            time_left = twelve_pm - now
            await asyncio.sleep(time_left.seconds)
            return

        tomorrow_12pm = now + timedelta(days=1)
        tomorrow_12pm = tomorrow_12pm.replace(hour=12, minute=0, second=0, microsecond=0)
        await asyncio.sleep((tomorrow_12pm - now).seconds)

    async def get_responses_list(self, final: bool = False) -> Embed:
        """Returns an embed containing the responses of the people."""
        channel = await self.get_channel()

        embed = Embed(color=Colour.red())

        if await self.messages.items():
            if final:
                embed.title = "Spooky Name Rate is about to end!"
                embed.description = (
                    "This Spooky Name Rate round is about to end in 2 hours! You can review "
                    "the entries below! Have you rated other's names?"
                )
            else:
                embed.title = "All the spookified names!"
                embed.description = "See a list of all the entries entered by everyone!"
        else:
            embed.title = "No one has added an entry yet..."

        for message_id, data in await self.messages.items():
            data = json.loads(data)

            embed.add_field(
                name=(self.bot.get_user(data["author"]) or await self.bot.fetch_user(data["author"])).name,
                value=f"[{(data)['name']}](https://discord.com/channels/{Client.guild}/{channel.id}/{message_id})",
            )

        return embed

    async def get_channel(self) -> Optional[TextChannel]:
        """Gets the sir-lancebot-channel after waiting until ready."""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(
            Channels.sir_lancebot_playground
        ) or await self.bot.fetch_channel(Channels.sir_lancebot_playground)
        if not channel:
            logger.warning("Bot is unable to get the #sir-lancebot-playground channel. Please check the channel ID.")
        return channel

    @staticmethod
    def in_allowed_month() -> bool:
        """Returns whether running in the limited month."""
        if SpookyNameRate.debug:
            return True

        if not Client.month_override:
            return datetime.utcnow().month == Month.OCTOBER
        return Client.month_override == Month.OCTOBER

    def cog_check(self, ctx: Context) -> bool:
        """A command to check whether the command is being called in October."""
        if not self.in_allowed_month():
            raise InMonthCheckFailure("You can only use these commands in October!")
        return True

    def cog_unload(self) -> None:
        """Stops the announce_name task."""
        self.announce_name.cancel()


async def setup(bot: Bot) -> None:
    """Load the SpookyNameRate Cog."""
    await bot.add_cog(SpookyNameRate(bot))
