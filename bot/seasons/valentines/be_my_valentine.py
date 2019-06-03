import logging
import random
import typing
from json import load
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from bot.constants import Client, Colours, Lovefest

log = logging.getLogger(__name__)

HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]


class BeMyValentine:
    """
    A cog that sends valentines to other users !
    """

    def __init__(self, bot):
        self.bot = bot
        self.valentines = self.load_json()

    @staticmethod
    def load_json():
        p = Path('bot', 'resources', 'valentines', 'bemyvalentine_valentines.json')
        with p.open() as json_data:
            valentines = load(json_data)
            return valentines

    @commands.group(name="lovefest", invoke_without_command=True)
    async def lovefest_role(self, ctx):
        """
        You can have yourself the lovefest role or remove it.
        The lovefest role makes you eligible to receive anonymous valentines from other users.

        1) use the command \".lovefest sub\" to get the lovefest role.
        2) use the command \".lovefest unsub\" to get rid of the lovefest role.
        """
        await ctx.invoke(self.bot.get_command("help"), "lovefest")

    @lovefest_role.command(name="sub")
    async def add_role(self, ctx):
        """
        This command adds the lovefest role.
        """
        user = ctx.author
        role = discord.utils.get(ctx.guild.roles, id=Lovefest.role_id)
        if Lovefest.role_id not in [role.id for role in ctx.message.author.roles]:
            await user.add_roles(role)
            await ctx.send("The Lovefest role has been added !")
        else:
            await ctx.send("You already have the role !")

    @lovefest_role.command(name="unsub")
    async def remove_role(self, ctx):
        """
        This command removes the lovefest role.
        """
        user = ctx.author
        role = discord.utils.get(ctx.guild.roles, id=Lovefest.role_id)
        if Lovefest.role_id not in [role.id for role in ctx.message.author.roles]:
            await ctx.send("You dont have the lovefest role.")
        else:
            await user.remove_roles(role)
            await ctx.send("The lovefest role has been successfully removed !")

    @commands.cooldown(1, 1800, BucketType.user)
    @commands.group(name='bemyvalentine', invoke_without_command=True)
    async def send_valentine(self, ctx, user: typing.Optional[discord.Member] = None, *, valentine_type=None):
        """
        This command sends valentine to user if specified or a random user having lovefest role.

        syntax: .bemyvalentine [user](optional) [p/poem/c/compliment/or you can type your own valentine message]
        (optional)

        example: .bemyvalentine (sends valentine as a poem or a compliment to a random user)
        example: .bemyvalentine Iceman#6508 p (sends a poem to Iceman)
        example: .bemyvalentine Iceman Hey I love you, wanna hang around ? (sends the custom message to Iceman)
        NOTE : AVOID TAGGING THE USER MOST OF THE TIMES.JUST TRIM THE '@' when using this command.
        """

        if ctx.guild is None:
            # This command should only be used in the server
            msg = "You are supposed to use this command in the server."
            return await ctx.send(msg)

        if user:
            if Lovefest.role_id not in [role.id for role in user.roles]:
                message = f"You cannot send a valentine to {user} as he/she does not have the lovefest role!"
                return await ctx.send(message)

        if user == ctx.author:
            # Well a user can't valentine himself/herself.
            return await ctx.send("Come on dude, you can't send a valentine to yourself :expressionless:")

        emoji_1, emoji_2 = self.random_emoji()
        lovefest_role = discord.utils.get(ctx.guild.roles, id=Lovefest.role_id)
        channel = self.bot.get_channel(Lovefest.channel_id)
        valentine, title = self.valentine_check(valentine_type)

        if user is None:
            author = ctx.author
            user = self.random_user(author, lovefest_role.members)
            if user is None:
                return await ctx.send("There are no users avilable to whome your valentine can be sent.")

        embed = discord.Embed(
            title=f'{emoji_1} {title} {user.display_name} {emoji_2}',
            description=f'{valentine} \n **{emoji_2}From {ctx.author}{emoji_1}**',
            color=Colours.pink
        )
        await channel.send(user.mention, embed=embed)

    @commands.cooldown(1, 1800, BucketType.user)
    @send_valentine.command(name='secret')
    async def anonymous(self, ctx, user: typing.Optional[discord.Member] = None, *, valentine_type=None):
        """
        This command DMs a valentine to be given anonymous to a user if specified or a random user having lovefest role.

        **This command should be DMed to the bot.**

        syntax : .bemyvalentine secret [user](optional) [p/poem/c/compliment/or you can type your own valentine message]
        (optional)

        example : .bemyvalentine secret (sends valentine as a poem or a compliment to a random user in DM making you
        anonymous)
        example : .bemyvalentine secret Iceman#6508 p (sends a poem to Iceman in DM making you anonymous)
        example : .bemyvalentine secret Iceman#6508 Hey I love you, wanna hang around ? (sends the custom message to
        Iceman in DM making you anonymous)
        """

        if ctx.guild is not None:
            # This command is only DM specific
            msg = "You are not supposed to use this command in the server, DM the command to the bot."
            return await ctx.send(msg)

        if user:
            if Lovefest.role_id not in [role.id for role in user.roles]:
                message = f"You cannot send a valentine to {user} as he/she does not have the lovefest role!"
                return await ctx.send(message)

        if user == ctx.author:
            # Well a user cant valentine himself/herself.
            return await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        guild = self.bot.get_guild(id=Client.guild)
        emoji_1, emoji_2 = self.random_emoji()
        lovefest_role = discord.utils.get(guild.roles, id=Lovefest.role_id)
        valentine, title = self.valentine_check(valentine_type)

        if user is None:
            author = ctx.author
            user = self.random_user(author, lovefest_role.members)
            if user is None:
                return await ctx.send("There are no users avilable to whome your valentine can be sent.")

        embed = discord.Embed(
            title=f'{emoji_1}{title} {user.display_name}{emoji_2}',
            description=f'{valentine} \n **{emoji_2}From anonymous{emoji_1}**',
            color=Colours.pink
        )
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            await ctx.author.send(f"{user} has DMs disabled, so I couldn't send the message. Sorry!")
        else:
            await ctx.author.send(f"Your message has been sent to {user}")

    def valentine_check(self, valentine_type):
        if valentine_type is None:
            valentine, title = self.random_valentine()

        elif valentine_type.lower() in ['p', 'poem']:
            valentine = self.valentine_poem()
            title = 'A poem dedicated to'

        elif valentine_type.lower() in ['c', 'compliment']:
            valentine = self.valentine_compliment()
            title = 'A compliment for'

        else:
            # in this case, the user decides to type his own valentine.
            valentine = valentine_type
            title = 'A message for'
        return valentine, title

    @staticmethod
    def random_user(author, members):
        """
        Picks a random member from the list provided in `members`, ensuring
        the author is not one of the options.

        :param author: member who invoked the command
        :param members: list of discord.Member objects
        """
        if author in members:
            members.remove(author)

        return random.choice(members) if members else None

    @staticmethod
    def random_emoji():
        EMOJI_1 = random.choice(HEART_EMOJIS)
        EMOJI_2 = random.choice(HEART_EMOJIS)
        return EMOJI_1, EMOJI_2

    def random_valentine(self):
        """
        Grabs a random poem or a compliment (any message).
        """
        valentine_poem = random.choice(self.valentines['valentine_poems'])
        valentine_compliment = random.choice(self.valentines['valentine_compliments'])
        random_valentine = random.choice([valentine_compliment, valentine_poem])
        if random_valentine == valentine_poem:
            title = 'A poem dedicated to'
        else:
            title = 'A compliment for '
        return random_valentine, title

    def valentine_poem(self):
        """
        Grabs a random poem.
        """
        valentine_poem = random.choice(self.valentines['valentine_poems'])
        return valentine_poem

    def valentine_compliment(self):
        """
        Grabs a random compliment.
        """
        valentine_compliment = random.choice(self.valentines['valentine_compliments'])
        return valentine_compliment


def setup(bot):
    bot.add_cog(BeMyValentine(bot))
    log.debug("Be My Valentine cog loaded")
