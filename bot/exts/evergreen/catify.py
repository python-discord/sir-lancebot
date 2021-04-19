import random
from typing import Optional

from discord.ext import commands

from bot.constants import Cats


class Catify(commands.Cog):
    """Cog for the catify command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["ᓚᘏᗢify", "ᓚᘏᗢ"])
    async def catify(self, ctx: commands.Context, *, text: Optional[str]) -> None:
        """Catifies your nickname or a given string."""
        if text == ():
            display_name = ctx.author.display_name
            if len(display_name) >= 28:
                await ctx.send("Your username is too long to be catified! Please change it.")
            else:
                display_name += f" | {random.choice(Cats.cats)}"
                await ctx.send(f"Your catified username is: `{display_name}`")
                await ctx.author.edit(nick=display_name)
        else:
            string_list = text.split()
            for index, name in enumerate(string_list):
                if "cat" in name:
                    string_list[index] = string_list[index].replace("cat", random.choice(Cats.cats))

            for _i in range(random.randint(1, len(string_list)//2)):
                # insert cat at random index
                string_list.insert(random.randint(0, len(string_list)-1), random.choice(Cats.cats))

                text = " ".join(string_list)

            await ctx.channel.send(text)


def setup(bot: commands.Bot) -> None:
    """Loads the catify cog."""
    bot.add_cog(Catify(bot))
