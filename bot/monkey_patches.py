import logging
from datetime import datetime, timedelta

from discord import Forbidden, http
from discord.ext import commands

log = logging.getLogger(__name__)


class Command(commands.Command):
    """
    A `discord.ext.commands.Command` subclass which supports root aliases.

    A `root_aliases` keyword argument is added, which is a sequence of alias names that will act as
    top-level commands rather than being aliases of the command's group. It's stored as an attribute
    also named `root_aliases`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_aliases = kwargs.get("root_aliases", [])

        if not isinstance(self.root_aliases, (list, tuple)):
            raise TypeError("Root aliases of a command must be a list or a tuple of strings.")


class Group(commands.Group):
    """
    A `discord.ext.commands.Group` subclass which supports root aliases.

    A `root_aliases` keyword argument is added, which is a sequence of alias names that will act as
    top-level groups rather than being aliases of the command's group. It's stored as an attribute
    also named `root_aliases`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_aliases = kwargs.get("root_aliases", [])

        if not isinstance(self.root_aliases, (list, tuple)):
            raise TypeError("Root aliases of a group must be a list or a tuple of strings.")


def patch_typing() -> None:
    """
    Sometimes discord turns off typing events by throwing 403's.

    Handle those issues by patching the trigger_typing method so it ignores 403's in general.
    """
    log.debug("Patching send_typing, which should fix things breaking when discord disables typing events. Stay safe!")

    original = http.HTTPClient.send_typing
    last_403 = None

    async def honeybadger_type(self, channel_id: int) -> None:  # noqa: ANN001
        nonlocal last_403
        if last_403 and (datetime.utcnow() - last_403) < timedelta(minutes=5):
            log.warning("Not sending typing event, we got a 403 less than 5 minutes ago.")
            return
        try:
            await original(self, channel_id)
        except Forbidden:
            last_403 = datetime.utcnow()
            log.warning("Got a 403 from typing event!")
            pass

    http.HTTPClient.send_typing = honeybadger_type
