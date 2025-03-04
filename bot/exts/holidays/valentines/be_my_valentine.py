import random
from json import loads
from pathlib import Path

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Channels, Colours, Month, PYTHON_PREFIX, Roles
from bot.utils.decorators import in_month
from bot.utils.exceptions import MovedCommandError

log = get_logger(__name__)

HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]

MOVED_COMMAND = f"{PYTHON_PREFIX}subscribe"


class BeMyValentine(commands.Cog):
    """A cog that sends Valentines to other users!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.valentines = self.load_json()

    @staticmethod
    def load_json() -> dict:
        """Load Valentines messages from the static resources."""
        p = Path("bot/resources/holidays/valentines/bemyvalentine_valentines.json")
        return loads(p.read_text("utf8"))

    @in_month(Month.FEBRUARY)
    @commands.command(name="lovefest", help=f"NOTE: This command has been moved to {MOVED_COMMAND}")
    async def lovefest_role(self, ctx: commands.Context) -> None:
        """
        Deprecated lovefest role command.

        This command has been moved to bot, and will be removed in the future.
        """
        raise MovedCommandError(MOVED_COMMAND)

    # @commands.cooldown(1, 1800, commands.BucketType.user)
    @commands.group(name="bemyvalentine", invoke_without_command=True)
    async def send_valentine(
        self, ctx: commands.Context, user: discord.Member, privacy_type: str | None = None, anon: str | None = None, valentine_type: str | None = None
    ) -> None:
        """
        Send a valentine to a specified user with the lovefest role.

        syntax: .bemyvalentine [user] [public/private] [p/poem/c/compliment/or you can type your own valentine message]
        (optional)

        example: .bemyvalentine private Iceman#6508 p (sends a private poem to Iceman)
        example: .bemyvalentine public Iceman Hey I love you, wanna hang around ? (sends the custom message publicly to Iceman)
        NOTE : AVOID TAGGING THE USER MOST OF THE TIMES.JUST TRIM THE '@' when using this command.
        """


        if anon.lower() == "anon":
            # Delete the message containing the command right after it was sent to enforce anonymity.
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                await ctx.send("I can't delete your message! Please check my permissions.")
            

        if anon not in ["anon", "signed"]:
            # Anonymity type wrongfully specified.
            raise commands.UserInputError(
                f"Specify if you want the message to be anonymous or not!"
            )



        if ctx.guild is None:
            # This command should only be used in the server
            raise commands.UserInputError("You are supposed to use this command in the server.")

        if Roles.lovefest not in [role.id for role in user.roles]:
            raise commands.UserInputError(
                f"You cannot send a valentine to {user} as they do not have the lovefest role!"
            )
        
        if privacy_type not in ["public", "private"]:
            # Privacy type wrongfully specified.
            raise commands.UserInputError(
                f"Specify if you want the message to be sent privately or publicly!"
            )
        
        # COMMENTED FOR TESTING PURPOSES

        # if user == ctx.author:
        #     # Well a user can't valentine himself/herself.
        #     raise commands.UserInputError("Come on, you can't send a valentine to yourself :expressionless:")

        emoji_1, emoji_2 = self.random_emoji()
        channel = self.bot.get_channel(Channels.sir_lancebot_playground)
        valentine, title = self.valentine_check(valentine_type)

        if anon.lower() == "anon":
            embed = discord.Embed(
                title=f"{emoji_1} {title} {user.display_name} {emoji_2}",
                description=f"{valentine} \n **{emoji_2}From an anonymous admirer{emoji_1}**",
                color=Colours.pink
            )
        
        else:
            embed = discord.Embed(
                title=f"{emoji_1} {title} {user.display_name} {emoji_2}",
                description=f"{valentine} \n **{emoji_2}From {ctx.author}{emoji_1}**",
                color=Colours.pink
            )

        if privacy_type.lower() == "private":
            # Send the message privately if "private" was speicified
            try:
                await user.send(embed=embed)
                await ctx.author.send(f"Your valentine has been **privately** delivered to {user.display_name}!")
            except discord.Forbidden:
                await ctx.send(f"I couldn't send a private message to {user.display_name}. They may have DMs disabled.")
        else:
            # Send the message publicly if "public" was speicified
            try:
                await ctx.send(user.mention, embed=embed)
            except discord.Forbidden:
                await ctx.send(f"I couldn't send a private message to {user.display_name}. They may have DMs disabled.")

    @commands.cooldown(1, 1800, commands.BucketType.user)
    @send_valentine.command(name="secret")
    async def anonymous(
        self, ctx: commands.Context, user: discord.Member, *, valentine_type: str | None = None
    ) -> None:
        """
        Send an anonymous Valentine via DM to to a specified user with the lovefest role.

        syntax : .bemyvalentine secret [user] [p/poem/c/compliment/or you can type your own valentine message]
        (optional)

        example : .bemyvalentine secret Iceman#6508 p (sends a poem to Iceman in DM making you anonymous)
        example : .bemyvalentine secret Iceman#6508 Hey I love you, wanna hang around ? (sends the custom message to
        Iceman in DM making you anonymous)
        """
        if Roles.lovefest not in [role.id for role in user.roles]:
            await ctx.message.delete()
            raise commands.UserInputError(
                f"You cannot send a valentine to {user} as they do not have the lovefest role!"
            )

        if user == ctx.author:
            # Well a user cant valentine himself/herself.
            raise commands.UserInputError("Come on, you can't send a valentine to yourself :expressionless:")

        emoji_1, emoji_2 = self.random_emoji()
        valentine, title = self.valentine_check(valentine_type)

        embed = discord.Embed(
            title=f"{emoji_1}{title} {user.display_name}{emoji_2}",
            description=f"{valentine} \n **{emoji_2}From anonymous{emoji_1}**",
            color=Colours.pink
        )
        await ctx.message.delete()
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            raise commands.UserInputError(f"{user} has DMs disabled, so I couldn't send the message. Sorry!")
        else:
            await ctx.author.send(f"Your message has been sent to {user}")

    def valentine_check(self, valentine_type: str) -> tuple[str, str]:
        """Return the appropriate Valentine type & title based on the invoking user's input."""
        if valentine_type is None:
            return self.random_valentine()

        if valentine_type.lower() in ["p", "poem"]:
            return self.valentine_poem(), "A poem dedicated to"

        if valentine_type.lower() in ["c", "compliment"]:
            return self.valentine_compliment(), "A compliment for"

        # in this case, the user decides to type his own valentine.
        return valentine_type, "A message for"

    @staticmethod
    def random_emoji() -> tuple[str, str]:
        """Return two random emoji from the module-defined constants."""
        emoji_1 = random.choice(HEART_EMOJIS)
        emoji_2 = random.choice(HEART_EMOJIS)
        return emoji_1, emoji_2

    def random_valentine(self) -> tuple[str, str]:
        """Grabs a random poem or a compliment (any message)."""
        valentine_poem = random.choice(self.valentines["valentine_poems"])
        valentine_compliment = random.choice(self.valentines["valentine_compliments"])
        random_valentine = random.choice([valentine_compliment, valentine_poem])
        title = "A poem dedicated to" if random_valentine == valentine_poem else "A compliment for "
        return random_valentine, title

    def valentine_poem(self) -> str:
        """Grabs a random poem."""
        return random.choice(self.valentines["valentine_poems"])

    def valentine_compliment(self) -> str:
        """Grabs a random compliment."""
        return random.choice(self.valentines["valentine_compliments"])


async def setup(bot: Bot) -> None:
    """Load the Be my Valentine Cog."""
    await bot.add_cog(BeMyValentine(bot))
