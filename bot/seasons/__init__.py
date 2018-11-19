from bot.seasons.season import SeasonBase, SeasonManager, get_season

__all__ = ("SeasonBase", "get_season")


def setup(bot):
    bot.add_cog(SeasonManager(bot))
