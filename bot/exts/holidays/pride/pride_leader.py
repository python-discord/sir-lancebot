import json
import random
from pathlib import Path

import discord
from discord.ext import commands
from pydis_core.utils.logging import get_logger
from rapidfuzz import fuzz

from bot import constants
from bot.bot import Bot

log = get_logger(__name__)

PRIDE_RESOURCE = json.loads(Path("bot/resources/holidays/pride/prideleader.json").read_text("utf8"))
MINIMUM_FUZZ_RATIO = 40


class PrideLeader(commands.Cog):
    """Gives information about Pride Leaders."""

    def __init__(self, bot: Bot):
        self.bot = bot

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
        for name in PRIDE_RESOURCE:
            if fuzz.ratio(pride_leader, name) >= MINIMUM_FUZZ_RATIO:
                valid_names.append(name)

        if not valid_names:
            valid_names = ", ".join(PRIDE_RESOURCE)
            error_msg = "Sorry your input didn't match any stored names, here is a list of available names:"
        else:
            valid_names = "\n".join(valid_names)
            error_msg = "Did you mean?"

        embed.description = f"{error_msg}\n```\n{valid_names}\n```"
        embed.set_footer(text="To add more pride leaders, feel free to open a pull request!")

        return embed

    def embed_builder(self, pride_leader: dict) -> discord.Embed:
        """Generate an Embed with information about a pride leader."""
        name = next(name for name, info in PRIDE_RESOURCE.items() if info == pride_leader)

        embed = discord.Embed(
            title=name,
            description=pride_leader["About"],
            color=constants.Colours.blue
        )
        embed.add_field(
            name="Known for",
            value=pride_leader["Known for"],
            inline=False
        )
        embed.add_field(
            name="D.O.B and Birth place",
            value=pride_leader["Born"],
            inline=False
        )
        embed.add_field(
            name="Awards and honors",
            value=pride_leader["Awards"],
            inline=False
        )
        embed.add_field(
            name="For More Information",
            value=f"Do `{constants.Client.prefix}wiki {name}`"
                  f" in <#{constants.Channels.sir_lancebot_playground}>",
            inline=False
        )
        embed.set_thumbnail(url=pride_leader["url"])
        return embed

    @commands.command(aliases=("pl", "prideleader"))
    async def pride_leader(self, ctx: commands.Context, *, pride_leader_name: str | None) -> None:
        """
        Information about a Pride Leader.

        Returns information about the specified pride leader
        and if there is no pride leader given, return a random pride leader.
        """
        if not pride_leader_name:
            leader = random.choice(list(PRIDE_RESOURCE.values()))
        else:
            leader = PRIDE_RESOURCE.get(pride_leader_name.title())
            if not leader:
                log.trace(f"Got a Invalid pride leader: {pride_leader_name}")

                embed = self.invalid_embed_generate(pride_leader_name)
                await ctx.send(embed=embed)
                return

        embed = self.embed_builder(leader)
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Pride Leader Cog."""
    await bot.add_cog(PrideLeader(bot))
