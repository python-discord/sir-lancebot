import json
import logging
import os
from asyncio import sleep as asleep
from typing import Optional, Union

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context

log = logging.getLogger(__name__)

EMOJIS = {
    'SUCCESS': u'\u2705',
    'ERROR': u'\u274C'
}


class MonsterSurvey:
    """
    Vote for your favorite monster!
    This command allows users to vote for their favorite listed monster.
    Users may change their vote, but only their current vote will be counted.
    """

    def __init__(self, bot: Bot):
        """Initializes values for the bot to use within the voting commands."""
        self.bot = bot
        self.registry_location = os.path.join(os.getcwd(), 'bot', 'resources', 'monstersurvey', 'monstersurvey.json')
        with open(self.registry_location, 'r') as jason:
            self.voter_registry = json.load(jason)

    def json_write(self):
        log.info("Saved Monster Survey Results")
        with open(self.registry_location, 'w') as jason:
            json.dump(self.voter_registry, jason, indent=2)

    @commands.group(
        name='monster',
        aliases=['ms']
    )
    async def monster_group(self, ctx: Context):
        """
        The base voting command. If nothing is called, then it will return an embed.
        """

        if ctx.invoked_subcommand is None:
            default_embed = Embed(
                title='Monster Voting',
                color=0xFF6800,
                description='Vote for your favorite monster!'
            )
            default_embed.add_field(
                name='.monster show monster_name(optional)',
                value='Show a specific monster. If none is listed, it will give you an error with valid choices.',
                inline=False)
            default_embed.add_field(
                name='.monster vote monster_name',
                value='Vote for a specific monster. You get one vote, but can change it at any time.',
                inline=False
            )
            default_embed.add_field(
                name='.monster leaderboard',
                value='Which monster has the most votes? This command will tell you.',
                inline=False
            )
            return await ctx.send(embed=default_embed)

    @monster_group.command(
        name='vote'
    )
    async def monster_vote(self, ctx: Context, name: Optional[Union[int, str]] = None):
        """Casts a vote for a particular monster, or displays a list of monsters that can be voted for
        if one is not given."""
        vote_embed = Embed(
            name='Monster Voting',
            color=0xFF6800
        )
        if isinstance(name, int):
            name = list(self.voter_registry.keys())[name]

        if name is None or name.lower() not in self.voter_registry.keys():
            if name is not None:
                vote_embed.description = f'You cannot vote for {name} because it\'s not in the running.'
            vote_embed.add_field(
                name='Use `.monster show {monster_name}` for more information on a specific monster',
                value='or use `.monster vote {monster}` to cast your vote for said monster.',
                inline=False
            )
            vote_embed.add_field(
                name='You may vote for or show the following monsters:',
                value=f"{', '.join(self.voter_registry.keys())}"
            )
            return await ctx.send(embed=vote_embed)
        for monster in self.voter_registry.keys():
            if ctx.author.id in self.voter_registry[monster]['votes']:
                if name.lower() != monster:
                    self.voter_registry[monster]['votes'].remove(ctx.author.id)
                    break
                else:
                    vote_embed.add_field(
                        name='Vote unsuccessful.',
                        value='You already voted for this monster. '
                              'If you want to change your vote, use another monster.',
                        inline=False
                    )
                    log.info(f"{ctx.author.name} Tried to vote for the same monster.")
                    await ctx.send(embed=vote_embed)
                    await asleep(.5)
                    return await ctx.invoke(self.monster_vote)
        self.voter_registry[name]['votes'].append(ctx.author.id)
        vote_embed.add_field(
            name='Vote successful!',
            value=f'You have successfully voted for {self.voter_registry[name]["full_name"]}!',
            inline=False
        )
        vote_embed.set_thumbnail(url=self.voter_registry[name]['image'])
        self.json_write()
        return await ctx.send(embed=vote_embed)

    @monster_group.command(
        name='show'
    )
    async def monster_show(self, ctx: Context, name: Optional[Union[int, str]] = None):
        """
        Shows the named monster. If one is not named, it sends the default voting embed instead.
        :param ctx:
        :param name:
        :return:
        """
        if name is None:
            monster_choices = map(lambda m: f"'{m}'", self.voter_registry.keys())
            monster_choices = ', '.join(monster_choices)
            embed = Embed(title="Uh Oh!",
                          description="I need you to provide a name for your"
                                      f" monster. Choose from {monster_choices}")
            await ctx.send(embed=embed)
            return
        if isinstance(name, int):
            m = list(self.voter_registry.values())[name]
        else:
            m = self.voter_registry.get(name.lower())
        if not m:
            await ctx.send('That monster does not exist.')
            return await ctx.invoke(self.monster_vote)
        embed = Embed(title=m['full_name'], color=0xFF6800)
        embed.add_field(name='Summary', value=m['summary'])
        embed.set_image(url=m['image'])
        embed.set_footer(text=f'To vote for this monster, type .monster vote {name}')
        return await ctx.send(embed=embed)

    @monster_group.command(
        name='leaderboard',
        aliases=['lb']
    )
    async def monster_leaderboard(self, ctx: Context):
        """
        Shows the current standings.
        :param ctx:
        :return:
        """
        vr = self.voter_registry
        top = sorted(vr.values(), key=lambda k: len(k['votes']), reverse=True)

        embed = Embed(title="Monster Survey Leader Board", color=0xFF6800)
        total_votes = sum(len(m['votes']) for m in self.voter_registry.values())
        for rank, m in enumerate(top):
            votes = len(m['votes'])
            percentage = ((votes / total_votes) * 100) if total_votes > 0 else 0
            embed.add_field(name=f"{rank+1}. {m['full_name']}",
                            value=f"{votes} votes. {percentage:.1f}%"
                                  f" of total votes.", inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MonsterSurvey(bot))
    log.debug("MonsterSurvey COG Loaded")
