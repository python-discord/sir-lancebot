import json
import logging
import random
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from bot import bot
from bot import constants

log = logging.getLogger(__name__)

PRIDE_LEADERS_RESOURCE = Path("bot/resources/pride/prideleader.json")
MINIMUM_FUZZ_RATIO = 40


class PrideLeader(commands.Cog):
    """Gives information about Pride Leaders."""

    def __init__(self, bot: bot.Bot):
        self.bot = bot

        self.pride = json.loads(PRIDE_LEADERS_RESOURCE.read_text("utf8"))

    def invalid_embed_generate(self, pride_leader: str) -> discord.Embed:
        """
        Generates Invalid Embed.

        The invalid embed contains a list of closely matched names of the invalid pride
        leader the user gave. If no closely matched names are found it would list all
        the available pride leader names.

        Wikipedia is a useful place to learn about pride leaders and we don't have all
        the pride leaders, so the bot would add a field containing the wikipedia
        command to execute.
        """
        embed = discord.Embed(
            color=constants.Colours.soft_red
        )
        valid_names = []
        pride_leader = pride_leader.title()
        for name in self.pride:
            if fuzz.ratio(pride_leader, name) >= MINIMUM_FUZZ_RATIO:
                valid_names.append(name)

        if not valid_names:
            valid_names = ", ".join(self.pride)
            error_msg = "Sorry your input didn't match any stored names, here is a list of available names:"
        else:
            valid_names = "\n".join(valid_names)
            error_msg = "Did you mean?"

        embed.description = f"{error_msg}\n```{valid_names}```"
        embed.add_field(
            name="You can get information about the Pride Leader on the Wikipedia command",
            value=f"Do `{constants.Client.prefix}wiki {pride_leader}`"
                  f" in <#{constants.Channels.community_bot_commands}>",
            inline=False
        )

        return embed

    def embed_builder(self, leader_name: str) -> discord.Embed:
        """Generate an Embed with information about a pride leader."""
        embed = discord.Embed(
            title=leader_name,
            description=self.pride[leader_name]["About"],
            color=constants.Colours.blue
        )
        embed.add_field(
            name="Known for",
            value=self.pride[leader_name]["Known for"],
            inline=False
        )
        embed.add_field(
            name="D.O.B and Birth place",
            value=self.pride[leader_name]["Born"],
            inline=False
        )
        embed.add_field(
            name="Awards and honors",
            value=self.pride[leader_name]["Awards"],
            inline=False
        )
        embed.add_field(
            name="For More Information",
            value=f"Do `{constants.Client.prefix}wiki {leader_name}`"
                  f" in <#{constants.Channels.community_bot_commands}>",
            inline=False
        )
        embed.set_thumbnail(url=self.pride[leader_name]["url"])
        return embed

    @commands.command(aliases=("pl", "prideleader"))
    async def pride_leader(self, ctx: commands.Context, *, pride_leader_name: Optional[str]) -> None:
        """
        Information about a Pride Leader.

        Returns information about the specified pride leader
        and if there is no pride leader given, return a random pride leader.
        """
        if not pride_leader_name:
            leader = random.choice(list(self.pride))
        else:
            leader = self.pride.get(pride_leader_name.title())
            if not leader:
                log.trace(f"Got a Invalid pride leader: {pride_leader_name}")

                embed = self.invalid_embed_generate(pride_leader_name)
                await ctx.send(embed=embed)
                return

        embed = self.embed_builder(leader)
        await ctx.send(embed=embed)


def setup(bot: bot.Bot) -> None:
    """Load the Pride Leader Cog."""
    bot.add_cog(PrideLeader(bot))
