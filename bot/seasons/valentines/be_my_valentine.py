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
EMOJI_1 = random.choice(HEART_EMOJIS)
EMOJI_2 = random.choice(HEART_EMOJIS)


class BeMyValentine:
    """
    A cog that sends valentines to other users !
    """
    id = Lovefest.role_id

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lovefest")
    async def add_role(self, ctx):
        """
            This command adds people to the lovefest role
        """
        user = ctx.author
        role = discord.utils.get(ctx.guild.roles, id=Lovefest.role_id)
        if id not in [role.id for role in ctx.message.author.roles]:
            await user.add_roles(role)
            await ctx.send("The Lovefest role has been added !")
        else:
            await ctx.send("You already have the role !")

    @commands.cooldown(1, 1800, BucketType.user)
    @commands.group(
        name='bemyvalentine',
        invoke_without_command=True
    )
    async def send_valentine(self, ctx, user: typing.Optional[discord.Member] = None, *, valentine_type=None):
        """
        This command sends valentine to user if specified or a random user having lovefest role.


        syntax: .bemyvalentine [user](optional) [p/poem/c/compliment/or you can type your own valentine message]
        (optional)

        example: .bemyvalentine (sends valentine as a poem or a compliment to a random user)

        example: .bemyvalentine @Iceman#6508 p (sends a poem to Iceman)

        example: .bemyvalentine @Iceman#6508 Hey I love you, wanna hang around ? (sends the custom message to Iceman)
        """
        channel = self.bot.get_channel(Lovefest.channel_id)
        random_user = []

        if user == ctx.author:
            await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        elif user is None:
            for member in ctx.guild.members:
                for role in member.roles:
                    if role.id == Lovefest.role_id:
                        random_user.append(member)
                        user = random.choice(random_user)

            if valentine_type is None:
                # grabs a random valentine -can be a poem or a good message
                valentine, title = self.random_valentine()
                embed = discord.Embed(
                    title=f"{EMOJI_1} {title} {user.display_name}{EMOJI_2}",
                    color=Colours.pink
                )

            elif valentine_type in ['p', 'poem']:
                valentine = self.valentine_poem()
                embed = discord.Embed(
                    title=f"{EMOJI_1} A poem dedicated to {user.display_name}{EMOJI_2}",
                    color=Colours.pink
                )

            elif valentine_type in ['c', 'compliment']:
                valentine = self.valentine_compliment()
                embed = discord.Embed(
                    title=f"{EMOJI_1} A compliment for {user.display_name}{EMOJI_2}",
                    color=Colours.pink
                )
            else:
                # in this case, the user decides to type his own valentine.
                valentine = valentine_type
                embed = discord.Embed(
                    title=f'{EMOJI_1}A message for {user.display_name}{EMOJI_2}',
                    color=Colours.pink
                )

            embed.description = f'{valentine} \n **{EMOJI_2}From {ctx.author}{EMOJI_1}**'
            await channel.send(user.mention, embed=embed)

    @commands.cooldown(1, 1800, BucketType.user)
    @send_valentine.command(name='dm')
    async def anonymous(self, ctx, user: typing.Optional[discord.Member] = None, *, valentine_type=None):
        """
    - This command DMs a valentine to be given anonymous to a user if specified or a random user having lovefest role.


    **This command should be DMed to the bot.**


    syntax : .bemyvalentine dm [user](optional) [p/poem/c/compliment/or you can type your own valentine message]
    (optional)

    example : .bemyvalentine dm (sends valentine as a poem or a compliment to a random user in DM making you anonymous)

    example : .bemyvalentine dm Iceman#6508 p (sends a poem to Iceman in DM making you anonymous)

    example : .bemyvalentine dm Iceman#6508 Hey I love you, wanna hang around ? (sends the custom message to Iceman in
    DM making you anonymous)
        """
        random_user = []

        if user == ctx.author:
            await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        elif user is None:
            for member in ctx.guild.members:
                for role in member.roles:
                    if role.id == Lovefest.role_id:
                        random_user.append(member)
                        user = random.choice(random_user)

            if valentine_type is None:
                valentine, title = self.random_valentine()
                embed = discord.Embed(
                    title=f"{EMOJI_1} {title} {user.display_name}{EMOJI_2}",
                    color=Colours.pink
                )

            elif valentine_type in ['p', 'poem']:
                valentine = self.valentine_poem()
                embed = discord.Embed(
                    title=f"{EMOJI_1} A poem dedicated to {user.display_name}{EMOJI_2}",
                    color=Colours.pink
                )

            elif valentine_type in ['c', 'compliment']:
                valentine = self.valentine_compliment()
                embed = discord.Embed(
                    title=f"{EMOJI_1} A compliment for {user.display_name}{EMOJI_1}",
                    color=Colours.pink
                )
            else:
                # in this case, the user decides to type his own valentine.
                valentine = valentine_type
                embed = discord.Embed(
                    title=f'{EMOJI_1}A message for {user.display_name}{EMOJI_2}',
                    color=Colours.pink
                )

            embed.description = f'{valentine} \n **{EMOJI_2}From anonymous{EMOJI_1}**'
            await user.send(embed=embed)

    @staticmethod
    def random_valentine():
        """
            grabs a random poem or a compliment (any message)
        """
        with open(Path('bot', 'resources', 'valentines', 'bemyvalentine_valentines.json'), 'r', encoding="utf8") as f:
            valentines = load(f)
            valentine_poem = random.choice(valentines['valentine_poems'])
            valentine_compliment = random.choice(valentines['valentine_compliments'])
            random_valentine = random.choice([valentine_compliment, valentine_poem])
            if random_valentine == valentine_poem:
                message_type = 'A poem dedicated to'
            else:
                message_type = 'A compliment for '
            return random_valentine['message'], message_type

    @staticmethod
    def valentine_poem():
        """
            grabs a random poem
        """
        with open(Path('bot', 'resources', 'valentines', 'bemyvalentine_valentines.json'), 'r', encoding="utf8") as f:
            valentines = load(f)
            valentine_poem = random.choice(valentines['valentine_poems'])
            return valentine_poem['message']

    @staticmethod
    def valentine_compliment():
        """
            grabs a random compliment
        """
        with open(Path('bot', 'resources', 'valentines', 'bemyvalentine_valentines.json'), 'r', encoding="utf8") as f:
            valentines = load(f)
            valentine_compliment = random.choice(valentines['valentine_compliments'])
            return valentine_compliment['message']


def setup(bot):
    bot.add_cog(BeMyValentine(bot))
    log.debug("Be My Valentine cog loaded")
