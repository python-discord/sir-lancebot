from bot.bot import Bot


def setup(bot: Bot) -> None:
    """Load Music cog."""
    from bot.exts.evergreen.music.app.cog import Music
    bot.add_cog(Music(bot))
