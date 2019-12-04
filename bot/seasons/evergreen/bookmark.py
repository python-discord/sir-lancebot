import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class Bookmark(commands.Cog):
    """A cog for Bookmarking a message."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="bookmark", aliases=("bm", "pin"))
    async def bookmark(self, ctx: commands.Context, jump_url: str = None, *args) -> None:
        """Bookmarks a message."""
        if jump_url is not None and jump_url != "*":
            if "discordapp.com/channels" not in jump_url:
                await ctx.send("I can't find the associated message,"
                               " the command support the following syntax:\n"
                               " `.bm [message url] (bookmark name)`")
                return
        if jump_url is None or jump_url == "*":
            channel = ctx.channel
            async for x in channel.history(limit=2):
                message_id = x.id
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                await ctx.send(">>> Message not in this"
                               " channel\n"
                               "Or\n"
                               "You are trying to Pin"
                               " your own message,\n"
                               "Please use the channel"
                               " where message is.")
                return
            jump_url = f"https://discordapp.com/channels/" \
                       f"{ctx.guild.id}/{channel.id}/{message.id}"

        embed = discord.Embed(
            title="Your bookmark",
            description=None,
            colour=0x2ecc71
        )
        x = args
        hint = ""
        for word in x:
            hint = hint + " " + word
        if hint == "":
            hint = "No hint provided"

        embed.set_footer(text="Why everything so heavy ?")
        embed.set_thumbnail(url="https://emojipedia-us.s3."
                                "dualstack.us-west-1.amazonaws.com"
                                "/thumbs/240/twitter/"
                                "233/incoming-envelope_1f4e8.png")
        embed.set_author(name=ctx.author)
        embed.add_field(name='Hints', value=hint, inline=False)
        embed.add_field(name='Link', value=jump_url, inline=False)
        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Something is not right,"
                           " you have either blocked me or"
                           " you have disabled direct messages "
                           "from this server.")
            return
        await ctx.send("Sent you that DM")


def setup(bot: commands.Bot) -> None:
    """Uptime Cog load."""
    bot.add_cog(Bookmark(bot))
    log.info("Bookmark cog loaded")
