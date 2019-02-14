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
USER_LOVEFEST = []
JSON_FILE = open(Path('bot', 'resources', 'VALENTINES', 'bemyvalentine_valentines.json'), 'r', encoding="utf8")
VALENTINES = load(JSON_FILE)


class BeMyValentine:
    """
    A cog that sends VALENTINES to other users !
    """
    id = Lovefest.role_id

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lovefest")
    async def add_role(self, ctx):
        """
        This command adds people to the lovefest role.
        """
        user = ctx.author
        role = discord.utils.get(ctx.guild.roles, id=Lovefest.role_id)
        if id not in [role.id for role in ctx.message.author.roles]:
            USER_LOVEFEST.append(ctx.author)
            await user.add_roles(role)
            await ctx.send("The Lovefest role has been added !")
        else:
            await ctx.send("You already have the role !")

    @commands.command(name='refreshlovefest')
    async def refresh_user_lovefestlist(self, ctx):
        """
        Use this command to refresh the USER_VALENTINE list when the bot goes offline and then comes back online
        """
        USER_LOVEFEST.clear()
        for member in ctx.guild.members:
            for role in member.roles:
                if role.id == Lovefest.role_id:
                    USER_LOVEFEST.append(member)
        embed = discord.Embed(
            title="USER_LOVEFEST list updated!",
            description=f'''The USER_LOVEFEST has been refreshed,`bemyvalentine` and `bemyvalentine dm` commands can now
                            be used and there are {USER_LOVEFEST.__len__()} members having the lovefest role.''',
            color=Colours.pink
        )
        await ctx.send(embed=embed)

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
        if ctx.guild is None:
            # This command should only be used in the server
            msg = "You are supposed to use this command in the server."
            return await ctx.send(msg)

        channel = self.bot.get_channel(Lovefest.channel_id)

        if user == ctx.author:
            # Well a user cant valentine himself/herself.
            await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        elif user is None:
            # just making sure that the random does not pick up the same user(ctx.author)
            USER_LOVEFEST.remove(ctx.author)
            user = random.choice(USER_LOVEFEST)
            USER_LOVEFEST.append(ctx.author)

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
        This command DMs a valentine to be given anonymous to a user if specified or a random user having lovefest role.

        **This command should be DMed to the bot.**

        syntax : .bemyvalentine dm [user](optional) [p/poem/c/compliment/or you can type your own valentine message]
        (optional)

        example : .bemyvalentine dm (sends valentine as a poem or a compliment to a random user in DM making you
        anonymous)
        example : .bemyvalentine dm Iceman#6508 p (sends a poem to Iceman in DM making you anonymous)
        example : .bemyvalentine dm Iceman#6508 Hey I love you, wanna hang around ? (sends the custom message to Iceman
        in DM making you anonymous)
        """
        if ctx.guild is not None:
            # This command is only DM specific
            msg = "You are not supposed to use this command in the server, DM the command to the bot."
            return await ctx.send(msg)

        if user == ctx.author:
            # Well a user cant valentine himself/herself.
            await ctx.send('Come on dude, you cant send a valentine to yourself :expressionless:')

        elif user is None:
            # just making sure that the random dosent pick up the same user(ctx.author)
            USER_LOVEFEST.remove(ctx.author)
            user = random.choice(USER_LOVEFEST)
            USER_LOVEFEST.append(ctx.author)

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
            await ctx.author.send(f"Your message has been sent to {user}")
            await user.send(embed=embed)

    @staticmethod
    def random_valentine():
        """
        Grabs a random poem or a compliment (any message).
        """
        valentine_poem = random.choice(VALENTINES['valentine_poems'])
        valentine_compliment = random.choice(VALENTINES['valentine_compliments'])
        JSON_FILE.close()
        random_valentine = random.choice([valentine_compliment, valentine_poem])
        if random_valentine == valentine_poem:
            message_type = 'A poem dedicated to'
        else:
            message_type = 'A compliment for '
        return random_valentine['message'], message_type

    @staticmethod
    def valentine_poem():
        """
        Grabs a random poem.
        """
        valentine_poem = random.choice(VALENTINES['valentine_poems'])
        JSON_FILE.close()
        return valentine_poem['message']

    @staticmethod
    def valentine_compliment():
        """
        Grabs a random compliment.
        """
        valentine_compliment = random.choice(VALENTINES['valentine_compliments'])
        JSON_FILE.close()
        return valentine_compliment['message']


def setup(bot):
    bot.add_cog(BeMyValentine(bot))
    log.debug("Be My Valentine cog loaded")
