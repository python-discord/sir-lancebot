import datetime
import logging
from pathlib import Path

from bot.constants import PYTHON_GUILD
from bot.utils.cog_load import load_cogs

log = logging.getLogger()


class Season:
    name = None

    def __init__(self):
        current_year = datetime.date.today().year
        date_format = "%d/%m-%Y"
        self.start = datetime.datetime.strptime(f"{self.start_string}-{current_year}", date_format).date()
        self.end = datetime.datetime.strptime(f"{self.end_string}-{current_year}", date_format).date()

    async def load(self):
        """
        Loads in the bot name, the bot avatar,
        and the cogs that are relevant to that season.
        """

        # Change the name
        bot_member = self.bot.get_guild(PYTHON_GUILD).get_member(self.bot.user.id)
        await bot_member.edit(nick=self.bot_name)
        await self.bot.user.edit(avatar=self.bot_avatar)

        # Loads all the cogs for that season, and then the evergreen ones.
        cogs = []
        for cog_folder in (self.name, "evergreen"):
            if cog_folder:
                log.info(f'Start loading extensions from bot/cogs/{cog_folder}/')
                for file in Path('bot', 'cogs', cog_folder).glob('*.py'):
                    if not file.name.startswith("__"):
                        cogs.append(f"bot.cogs.{cog_folder}.{file.stem}")

        # Load the season handler
        cogs.append("bot.cogs.season")

        load_cogs(self.bot, cogs)
