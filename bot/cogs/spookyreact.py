SPOOKY_TRIGGERS = {
    'spooky': "\U0001F47B",
    'skeleton': "\U0001F480",
    'doot': "\U0001F480",
    'pumpkin': "\U0001F383",
    'halloween': "\U0001F383",
    'jack-o-lantern': "\U0001F383",
    'danger': "\U00002620"
}


class SpookyReact:

    """
    A cog that makes the bot react to message triggers.
    """

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, ctx):
        """
        React on message if contains a spooky trigger.
        """
        for trigger in SPOOKY_TRIGGERS.keys():
            if trigger in ctx.content.lower():
                await ctx.add_reaction(SPOOKY_TRIGGERS[trigger])


def setup(bot):
    bot.add_cog(SpookyReact(bot))
