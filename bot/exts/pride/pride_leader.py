import json
import logging
import random
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from bot import constants

log = logging.getLogger(__name__)

PRIDE_LEADERS_RESOURCE = Path("bot/resources/pride/prideleader.json")
MINIMUM_FUZZ_RATIO = 40


class PrideLeader(commands.Cog):
    """Gives information about Pride Leaders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        with PRIDE_LEADERS_RESOURCE.open(encoding="utf8") as data:
            self.pride = json.load(data)

    def name_verifier(self, leader_name: str) -> Optional[str]:
        """Verify leader name whether it is present in resources or not."""
        leader_name = leader_name.title()
        if leader_name in self.pride:
            return leader_name
        log.trace(f"Got a Invalid pride leader: {leader_name}")

    def invalid_embed_generate(self, pride_leader: str) -> discord.Embed:
        """Generates Invalid Embed."""
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
            error_msg = "Sorry your input didn't match any stored name, here is a list of available names:"
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
            leader = random.choice([name for name in self.pride])
        else:
            leader = self.name_verifier(pride_leader_name)
            if not leader:
                embed = self.invalid_embed_generate(pride_leader_name)
                await ctx.send(embed=embed)
                return

        embed = self.embed_builder(leader)
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Loads Pride leader cog."""
    bot.add_cog(PrideLeader(bot))
