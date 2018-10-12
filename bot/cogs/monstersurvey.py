from discord.ext.commands import Bot, Context
from typing import Optional, Tuple
from discord.ext import commands
from discord import Embed
import discord, logging, json, os

log = logging.getLogger(__name__)

EMOJIS = {
    'SUCCESS': u'\u2705',
    'ERROR': u'\u274C'
}


class MonsterServey:

    def __init__(self, bot: Bot):
        self.bot = bot
        self.registry_location = os.path.join(os.getcwd(), 'resources', 'monstersurvey', 'monstersurvey.json')
        with open(self.registry_location, 'r') as jason:
            self.voter_registry = json.load(jason)

    @commands.group(
        name='monster',
        aliases=['ms']
    )
    async def monster_group(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            default_embed = Embed(
                title='Monster Voting',
                color=0xFF6800,
                description='Vote for your favorite monster!'
            )
            default_embed.add_field(
                name='.monster show monster_name(optional)',
                value='Show a specific monster. If none is listed, show a brief of all.',
                inline=False)
            default_embed.add_field(
                name='.monster vote monster_name',
                value='Vote for a specific monster. You can vote more than once, but you can only vote for one monster'
                      'at a time.',
                inline=False
            )
            default_embed.add_field(
                name='.monster leaderboard',
                value='Which monster has the most votes? This command will tell you.',
                inline=False
            )
            await ctx.send(embed=default_embed)

    @monster_group.command(
        name='vote'
    )
    async def monster_vote(self, ctx: Context, name: Optional[str] = None):
        """Casts a vote for a particular monster, or displays a list of monsters that can be voted for
        if one is not given."""
        vote_embed = Embed(
            name='Monster Voting',
            color=0xFF6800
        )
        if name not in self.voter_registry.keys() and name is not None:
            vote_embed.description = f'You cannot vote for {name} because it\'s not in the running.'
            vote_embed.add_field(
                name='Use `.monster show {monster_name} for more information on a specific monster',
                value='or use `.monster vote {monster}` to cast your vote for said monster.',
                inline=False
            )
            vote_embed.add_field(
                name='You may vote for the following monsters:',
                value=f"{', '.join(self.voter_registry.keys())}"
            )
            return await ctx.send(embed=vote_embed)
        if name is None:
            pass



    @monster_group.command(name='show')
    async def monster_show(self, ctx: Context, name: str):
        m = self.voter_registry.get(name)
        if not m:
            # TODO: invoke .monster vote command to display list
            raise commands.BadArgument("Monster does not exist.")

        embed = Embed(title=m['full_name'], color=0xFF6800)
        embed.add_field(name='Summary', value=m['summary'])
        embed.set_image(url=m['image'])
        embed.set_footer(text=f'To vote for this monster, type .monster vote {name}')
        await ctx.send(embed=embed)

    @monster_group.command(name='leaderboard')
    async def monster_leaderboard(self, ctx: Context):
        vr = self.voter_registry
        top = sorted(vr.values(), key=lambda k: len(k['votes']), reverse=True)

        embed = Embed(title="Leader board", color=0xFF6800)
        total_votes = sum(len(m['votes']) for m in self.voter_registry.values())
        for rank, m in enumerate(top):
            votes = len(m['votes'])
            percentage = ((votes / total_votes) * 100) if total_votes > 0 else 0
            embed.add_field(name=f"{rank+1}. {m['full_name']}",
                            value=f"{votes} votes. {percentage:.1f}%"
                                  f" of total votes.", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(MonsterServey(bot))
