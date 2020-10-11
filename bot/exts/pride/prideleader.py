import json
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from bot.constants import Colours
log = logging.getLogger(__name__)


class PrideLeader(commands.Cog):
    """Gives information about Pride Leaders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pride = self.load_pride_leader_json()

    @staticmethod
    def load_pride_leader_json() -> dict:
        """Loads pride leader information from static json resource."""
        explanation_file = Path("bot/resources/pride/prideleader.json")
        with explanation_file.open(encoding="utf8") as json_data:
            pride = json.load(json_data)

        return pride

    def name_verifier(self, leader_name: str) -> str:
        """Verify leader name whether it is present in json or not."""
        leader_name = leader_name.title()
        if leader_name in self.pride:
            log.trace("Got Valid name.")
            return leader_name

    def invalid_embed_generate(self, pride_leader: str) -> discord.Embed:
        """Generates Invalid Embed."""
        embed = discord.Embed()
        embed.color = Colours.soft_red
        valid_name = []
        pride_leader = pride_leader.title()
        for name in self.pride:
            if fuzz.ratio(pride_leader, name) >= 40:
                valid_name.append(name)

        if not valid_name:
            valid_name = ", ".join(name for name in self.pride.keys())
            error_msg = "Sorry your input didn't match any stored name, here is a list of available names"
        else:
            valid_name = "\n".join(name for name in valid_name)
            error_msg = "Did you mean?"

        embed.description = f"{error_msg}\n```{valid_name}```"
        return embed

    def embed_builder(self, leader_name: str) -> discord.Embed:
        """Genrate Embed with pride leader info."""
        embed = discord.Embed()
        embed.color = Colours.blue
        embed.title = f'__{leader_name}__'
        embed.description = self.pride[leader_name]["About"]
        embed.add_field(name="__Known for__", value=self.pride[leader_name]["Known for"], inline=False)
        embed.add_field(name="__D.O.B and Birth place__", value=self.pride[leader_name]["Born"], inline=False)
        embed.add_field(name="__Awards and honors__", value=self.pride[leader_name]["Awards"], inline=False)
        embed.set_thumbnail(url=self.pride[leader_name]["url"])
        return embed

    @commands.command(name="prideleader", aliases=['pl'])
    async def pride_leader(self, ctx: commands.Context, *, pride_leader_name: str) -> None:
        """Provides info about pride leader by taking name as input or randomly without input."""
        leader = self.name_verifier(pride_leader_name)
        if leader is None:
            log.trace("Got invalid name.")
            final_embed = self.invalid_embed_generate(pride_leader_name)
        else:
            final_embed = self.embed_builder(leader)
        await ctx.send(embed=final_embed)

    @pride_leader.error
    async def pride_leader_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Error handler of pride leader command."""
        if isinstance(error, commands.MissingRequiredArgument):
            log.trace("Name not provided by the user so selecting random from json.")
            name_list = [name for name in self.pride]
            leader = random.choice(name_list)
            final_embed = self.embed_builder(leader)
            await ctx.send(embed=final_embed)
        else:
            raise error


def setup(bot: commands.Bot) -> None:
    """Loads Pride leader cog."""
    bot.add_cog(PrideLeader(bot))
