import random
from contextlib import suppress
from typing import Optional

from discord import AllowedMentions, Embed, Forbidden
from discord.ext import commands

from bot.constants import Cats, Colours, NEGATIVE_REPLIES


class Catify(commands.Cog):
    """Cog for the catify command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["ᓚᘏᗢify", "ᓚᘏᗢ"])
    async def catify(self, ctx: commands.Context, *, text: Optional[str]) -> None:
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

            else:
                display_name += f" | {random.choice(Cats.cats)}"

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
                        string_list[index] = name.replace("cat", f"**{random.choice(Cats.cats)}**")
                    else:
                        string_list[index] = name.replace("cat", random.choice(Cats.cats))
                for element in Cats.cats:
                    if element in name:
                        string_list[index] = name.replace(element, "cat")

            string_len = len(string_list) // 3 or len(string_list)

            for _ in range(random.randint(1, string_len)):
                # insert cat at random index
                if random.randint(0, 5) == 5:
                    string_list.insert(random.randint(0, len(string_list)), f"**{random.choice(Cats.cats)}**")
                else:
                    string_list.insert(random.randint(0, len(string_list)), random.choice(Cats.cats))

            text = " ".join(string_list)
            await ctx.send(
                f">>> {text}",
                allowed_mentions=AllowedMentions.none()
            )


def setup(bot: commands.Bot) -> None:
    """Loads the catify cog."""
    bot.add_cog(Catify(bot))
