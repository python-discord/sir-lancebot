import logging
import random
import typing
from json import load
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from bot.constants import Colours, Lovefest

log = logging.getLogger(__name__)

HEART_EMOJIS = [":heart:", ":gift_heart:", ":revolving_hearts:", ":sparkling_heart:", ":two_hearts:"]


class BeMyValentine:
    """
    A cog that sends valentines to other users !
    """
    id = Lovefest.role_id

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
        By using this command, you can have yourself the lovefest role or remove it.
        The lovefest role makes you eligible to receive anonymous valentines from other users.
        """
        message = """```
You can have the lovefest role or get rid of it by using one of the commands shown below:
1) use the command \".lovefest sub\" to get the lovefest role.
2) use the command \".lovefest unsub\" to get rid of the lovefest role.
            ```"""
        await ctx.send(message)

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
        example: .bemyvalentine @Iceman#6508 p (sends a poem to Iceman)
        example: .bemyvalentine @Iceman#6508 Hey I love you, wanna hang around ? (sends the custom message to Iceman)
        """
        emoji_1, emoji_2 = self.random_emoji()

        if ctx.guild is None:
            # This command should only be used in the server
            msg = "You are supposed to use this command in the server."
            return await ctx.send(msg)

        channel = self.bot.get_channel(Lovefest.channel_id)

        if user == ctx.author:
            # Well a user cant valentine himself/herself.
            await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        elif user is None:
            author = ctx.author
            members = ctx.guild.members
            user = self.random_user(author, members)
            # just making sure that the random does not pick up the same user(ctx.author)

        if valentine_type is None:
            # grabs a random valentine -can be a poem or a good message
            valentine, title = self.random_valentine()

        elif valentine_type.lower() in ['p', 'poem']:
            valentine = self.valentine_poem()
            title = f'A poem dedicated to'

        elif valentine_type.lower() in ['c', 'compliment']:
            valentine = self.valentine_compliment()
            title = f'A compliment for'

        else:
            # in this case, the user decides to type his own valentine.
            valentine = valentine_type
            title = f'A message for'

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
        emoji_1, emoji_2 = self.random_emoji()
        if ctx.guild is not None:
            # This command is only DM specific
            msg = "You are not supposed to use this command in the server, DM the command to the bot."
            return await ctx.send(msg)

        if user == ctx.author:
            # Well a user cant valentine himself/herself.
            await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        if user is None:
            author = ctx.author
            members = ctx.guild.members
            user = self.random_user(author, members)
            # just making sure that the random does not pick up the same user(ctx.author)

        if valentine_type is None:
            valentine, title = self.random_valentine()

        elif valentine_type.lower() in ['p', 'poem']:
            valentine = self.valentine_poem()
            title = f'A poem dedicated to'

        elif valentine_type.lower() in ['c', 'compliment']:
            valentine = self.valentine_compliment()
            title = f'A compliment for'

        else:
            # in this case, the user decides to type his own valentine.
            valentine = valentine_type
            title = f'A message for'

        embed = discord.Embed(
            title=f'{emoji_1}{title} {user.display_name}{emoji_2}',
            description=f'{valentine} \n **{emoji_2}From anonymous{emoji_1}**',
            color=Colours.pink
        )
        await ctx.author.send(f"Your message has been sent to {user}")
        await user.send(embed=embed)

    @staticmethod
    def random_user(author, members):
        USER_LOVEFEST = []
        for member in members:
            for role in member.roles:
                if role.id == Lovefest.role_id:
                    USER_LOVEFEST.append(member)

        USER_LOVEFEST.remove(author)
        user = random.choice(USER_LOVEFEST)
        USER_LOVEFEST.append(author)
        return user

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
        return random_valentine['message'], title

    def valentine_poem(self):
        """
        Grabs a random poem.
        """
        valentine_poem = random.choice(self.valentines['valentine_poems'])
        return valentine_poem['message']

    def valentine_compliment(self):
        """
        Grabs a random compliment.
        """
        valentine_compliment = random.choice(self.valentines['valentine_compliments'])
        return valentine_compliment['message']


def setup(bot):
    bot.add_cog(BeMyValentine(bot))
    log.debug("Be My Valentine cog loaded")
