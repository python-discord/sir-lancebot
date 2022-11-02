import json
import logging
import pathlib

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context

log = logging.getLogger(__name__)

EMOJIS = {
    "SUCCESS": u"\u2705",
    "ERROR": u"\u274C"
}


class MonsterSurvey(Cog):
    """
    Vote for your favorite monster.

    This Cog allows users to vote for their favorite listed monster.

    Users may change their vote, but only their current vote will be counted.
    """

    def __init__(self):
        """Initializes values for the bot to use within the voting commands."""
        self.registry_path = pathlib.Path("bot", "resources", "holidays", "halloween", "monstersurvey.json")
        self.voter_registry = json.loads(self.registry_path.read_text("utf8"))

    def json_write(self) -> None:
        """Write voting results to a local JSON file."""
        log.info("Saved Monster Survey Results")
        self.registry_path.write_text(json.dumps(self.voter_registry, indent=2))

    def cast_vote(self, id: int, monster: str) -> None:
        """
        Cast a user's vote for the specified monster.

        If the user has already voted, their existing vote is removed.
        """
        vr = self.voter_registry
        for m in vr:
            if id not in vr[m]["votes"] and m == monster:
                vr[m]["votes"].append(id)
            else:
                if id in vr[m]["votes"] and m != monster:
                    vr[m]["votes"].remove(id)

    def get_name_by_leaderboard_index(self, n: int) -> str:
        """Return the monster at the specified leaderboard index."""
        n = n - 1
        vr = self.voter_registry
        top = sorted(vr, key=lambda k: len(vr[k]["votes"]), reverse=True)
        name = top[n] if n >= 0 else None
        return name

    @commands.group(
        name="monster",
        aliases=("mon",)
    )
    async def monster_group(self, ctx: Context) -> None:
        """The base voting command. If nothing is called, then it will return an embed."""
        if ctx.invoked_subcommand is None:
            async with ctx.typing():
                default_embed = Embed(
                    title="Monster Voting",
                    color=0xFF6800,
                    description="Vote for your favorite monster!"
                )
                default_embed.add_field(
                    name=".monster show monster_name(optional)",
                    value="Show a specific monster. If none is listed, it will give you an error with valid choices.",
                    inline=False
                )
                default_embed.add_field(
                    name=".monster vote monster_name",
                    value="Vote for a specific monster. You get one vote, but can change it at any time.",
                    inline=False
                )
                default_embed.add_field(
                    name=".monster leaderboard",
                    value="Which monster has the most votes? This command will tell you.",
                    inline=False
                )
                default_embed.set_footer(text=f"Monsters choices are: {', '.join(self.voter_registry)}")

            await ctx.send(embed=default_embed)

    @monster_group.command(
        name="vote"
    )
    async def monster_vote(self, ctx: Context, name: str = None) -> None:
        """
        Cast a vote for a particular monster.

        Displays a list of monsters that can be voted for if one is not specified.
        """
        if name is None:
            await ctx.invoke(self.monster_leaderboard)
            return

        async with ctx.typing():
            # Check to see if user used a numeric (leaderboard) index to vote
            try:
                idx = int(name)
                name = self.get_name_by_leaderboard_index(idx)
            except ValueError:
                name = name.lower()

            vote_embed = Embed(
                name="Monster Voting",
                color=0xFF6800
            )

            m = self.voter_registry.get(name)
            if m is None:
                vote_embed.description = f"You cannot vote for {name} because it's not in the running."
                vote_embed.add_field(
                    name="Use `.monster show {monster_name}` for more information on a specific monster",
                    value="or use `.monster vote {monster}` to cast your vote for said monster.",
                    inline=False
                )
                vote_embed.add_field(
                    name="You may vote for or show the following monsters:",
                    value=", ".join(self.voter_registry.keys())
                )
            else:
                self.cast_vote(ctx.author.id, name)
                vote_embed.add_field(
                    name="Vote successful!",
                    value=f"You have successfully voted for {m['full_name']}!",
                    inline=False
                )
                vote_embed.set_thumbnail(url=m["image"])
                vote_embed.set_footer(text="Please note that any previous votes have been removed.")
                self.json_write()

        await ctx.send(embed=vote_embed)

    @monster_group.command(
        name="show"
    )
    async def monster_show(self, ctx: Context, name: str = None) -> None:
        """Shows the named monster. If one is not named, it sends the default voting embed instead."""
        if name is None:
            await ctx.invoke(self.monster_leaderboard)
            return

        async with ctx.typing():
            # Check to see if user used a numeric (leaderboard) index to vote
            try:
                idx = int(name)
                name = self.get_name_by_leaderboard_index(idx)
            except ValueError:
                name = name.lower()

            m = self.voter_registry.get(name)
            if not m:
                await ctx.send("That monster does not exist.")
                await ctx.invoke(self.monster_vote)
                return

            embed = Embed(title=m["full_name"], color=0xFF6800)
            embed.add_field(name="Summary", value=m["summary"])
            embed.set_image(url=m["image"])
            embed.set_footer(text=f"To vote for this monster, type .monster vote {name}")

        await ctx.send(embed=embed)

    @monster_group.command(
        name="leaderboard",
        aliases=("lb",)
    )
    async def monster_leaderboard(self, ctx: Context) -> None:
        """Shows the current standings."""
        async with ctx.typing():
            vr = self.voter_registry
            top = sorted(vr, key=lambda k: len(vr[k]["votes"]), reverse=True)
            total_votes = sum(len(m["votes"]) for m in self.voter_registry.values())

            embed = Embed(title="Monster Survey Leader Board", color=0xFF6800)
            for rank, m in enumerate(top):
                votes = len(vr[m]["votes"])
                percentage = ((votes / total_votes) * 100) if total_votes > 0 else 0
                embed.add_field(
                    name=f"{rank+1}. {vr[m]['full_name']}",
                    value=(
                        f"{votes} votes. {percentage:.1f}% of total votes.\n"
                        f"Vote for this monster by typing "
                        f"'.monster vote {m}'\n"
                        f"Get more information on this monster by typing "
                        f"'.monster show {m}'"
                    ),
                    inline=False
                )

            embed.set_footer(text="You can also vote by their rank number. '.monster vote {number}' ")

        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the Monster Survey Cog."""
    await bot.add_cog(MonsterSurvey())
