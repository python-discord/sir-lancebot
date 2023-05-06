import random
from contextlib import suppress

from discord import AllowedMentions, Embed, Forbidden
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, NEGATIVE_REPLIES
from bot.utils import helpers

CATS = ["ᓚᘏᗢ", "ᘡᘏᗢ", "🐈", "ᓕᘏᗢ", "ᓇᘏᗢ", "ᓂᘏᗢ", "ᘣᘏᗢ", "ᕦᘏᗢ", "ᕂᘏᗢ"]


class Catify(commands.Cog):
    """Cog for the catify command."""

    @commands.command(aliases=("ᓚᘏᗢify", "ᓚᘏᗢ"))
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def catify(self, ctx: commands.Context, *, text: str | None) -> None:
        """
        Convert the provided text into a cat themed sentence by interspercing cats throughout text.

        If no text is given then the users nickname is edited.
        """
        if not text:
            display_name = ctx.author.display_name

            if len(display_name) > 26:
                embed = Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description=(
                        "Your display name is too long to be catified! "
                        "Please change it to be under 26 characters."
                    ),
                    color=Colours.soft_red
                )
                await ctx.send(embed=embed)
                return

            display_name += f" | {random.choice(CATS)}"

            await ctx.send(f"Your catified nickname is: `{display_name}`", allowed_mentions=AllowedMentions.none())

            with suppress(Forbidden):
                await ctx.author.edit(nick=display_name)
        else:
            if len(text) >= 1500:
                embed = Embed(
                    title=random.choice(NEGATIVE_REPLIES),
                    description="Submitted text was too large! Please submit something under 1500 characters.",
                    color=Colours.soft_red
                )
                await ctx.send(embed=embed)
                return

            string_list = text.split()
            for index, name in enumerate(string_list):
                name = name.lower()
                if "cat" in name:
                    if random.randint(0, 5) == 5:
                        string_list[index] = name.replace("cat", f"**{random.choice(CATS)}**")
                    else:
                        string_list[index] = name.replace("cat", random.choice(CATS))
                for cat in CATS:
                    if cat in name:
                        string_list[index] = name.replace(cat, "cat")

            string_len = len(string_list) // 3 or len(string_list)

            for _ in range(random.randint(1, string_len)):
                # insert cat at random index
                if random.randint(0, 5) == 5:
                    string_list.insert(random.randint(0, len(string_list)), f"**{random.choice(CATS)}**")
                else:
                    string_list.insert(random.randint(0, len(string_list)), random.choice(CATS))

            text = helpers.suppress_links(" ".join(string_list))
            await ctx.send(
                f">>> {text}",
                allowed_mentions=AllowedMentions.none()
            )


async def setup(bot: Bot) -> None:
    """Loads the catify cog."""
    await bot.add_cog(Catify())
