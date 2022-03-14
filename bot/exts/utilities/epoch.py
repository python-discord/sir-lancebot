from typing import Optional, Union

import arrow
import discord
from dateutil import parser
from discord.ext import commands

from bot.bot import Bot
from bot.utils.extensions import invoke_help_command

# https://discord.com/developers/docs/reference#message-formatting-timestamp-styles
STYLES = {
    "Epoch": ("",),
    "Short Time": ("t", "h:mm A",),
    "Long Time": ("T", "h:mm:ss A"),
    "Short Date": ("d", "MM/DD/YYYY"),
    "Long Date": ("D", "MMMM D, YYYY"),
    "Short Date/Time": ("f", "MMMM D, YYYY h:mm A"),
    "Long Date/Time": ("F", "dddd, MMMM D, YYYY h:mm A"),
    "Relative Time": ("R",)
}
DROPDOWN_TIMEOUT = 60


class DateString(commands.Converter):
    """Convert a relative or absolute date/time string to an arrow.Arrow object."""

    async def convert(self, ctx: commands.Context, argument: str) -> Union[arrow.Arrow, Optional[tuple]]:
        """
        Convert a relative or absolute date/time string to an arrow.Arrow object.

        Try to interpret the date string as a relative time. If conversion fails, try to interpret it as an absolute
        time. Tokens that are not recognised are returned along with the part of the string that was successfully
        converted to an arrow object. If the date string cannot be parsed, BadArgument is raised.
        """
        try:
            return arrow.utcnow().dehumanize(argument)
        except (ValueError, OverflowError):
            try:
                dt, ignored_tokens = parser.parse(argument, fuzzy_with_tokens=True)
            except parser.ParserError:
                raise commands.BadArgument(f"`{argument}` Could not be parsed to a relative or absolute date.")
            except OverflowError:
                raise commands.BadArgument(f"`{argument}` Results in a date outside of the supported range.")
            return arrow.get(dt), ignored_tokens


class Epoch(commands.Cog):
    """Convert an entered time and date to a unix timestamp."""

    @commands.command(name="epoch")
    async def epoch(self, ctx: commands.Context, *, date_time: DateString = None) -> None:
        """
        Convert an entered date/time string to the equivalent epoch.

        **Relative time**
            Must begin with `in...` or end with `...ago`.
            Accepted units: "seconds", "minutes", "hours", "days", "weeks", "months", "years".
            eg `.epoch in a month 4 days and 2 hours`

        **Absolute time**
            eg `.epoch 2022/6/15 16:43 -04:00`
            Absolute times must be entered in descending orders of magnitude.
            If AM or PM is left unspecified, the 24-hour clock is assumed.
            Timezones are optional, and will default to UTC. The following timezone formats are accepted:
                Z (UTC)
                ±HH:MM
                ±HHMM
                ±HH

        Times in the dropdown are shown in UTC
        """
        if not date_time:
            await invoke_help_command(ctx)
            return

        if isinstance(date_time, tuple):
            # Remove empty strings. Strip extra whitespace from the remaining items
            ignored_tokens = list(map(str.strip, filter(str.strip, date_time[1])))
            date_time = date_time[0]
            if ignored_tokens:
                await ctx.send(f"Could not parse the following token(s): `{', '.join(ignored_tokens)}`")
        await ctx.send(f"Date and time parsed as: `{date_time.format(arrow.FORMAT_RSS)}`")

        epoch = int(date_time.timestamp())
        view = TimestampMenuView(ctx, self._format_dates(date_time), epoch)
        original = await ctx.send(f"`{epoch}`", view=view)
        await view.wait()  # wait until expiration before removing the dropdown
        try:
            await original.edit(view=None)
        except discord.NotFound:  # disregard the error message if the message is deleled
            pass

    @staticmethod
    def _format_dates(date: arrow.Arrow) -> list[str]:
        """
        Return a list of date strings formatted according to the discord timestamp styles.

        These are used in the description of each style in the dropdown
        """
        date = date.to('utc')
        formatted = [str(int(date.timestamp()))]
        formatted += [date.format(format[1]) for format in list(STYLES.values())[1:7]]
        formatted.append(date.humanize())
        return formatted


class TimestampMenuView(discord.ui.View):
    """View for the epoch command which contains a single `discord.ui.Select` dropdown component."""

    def __init__(self, ctx: commands.Context, formatted_times: list[str], epoch: int):
        super().__init__(timeout=DROPDOWN_TIMEOUT)
        self.ctx = ctx
        self.epoch = epoch
        self.dropdown: discord.ui.Select = self.children[0]
        for label, date_time in zip(STYLES.keys(), formatted_times):
            self.dropdown.add_option(label=label, description=date_time)

    @discord.ui.select(placeholder="Select the format of your timestamp")
    async def select_format(self, _: discord.ui.Select, interaction: discord.Interaction) -> discord.Message:
        """Drop down menu which contains a list of formats which discord timestamps can take."""
        selected = interaction.data["values"][0]
        if selected == "Epoch":
            return await interaction.response.edit_message(content=f"`{self.epoch}`")
        return await interaction.response.edit_message(content=f"`<t:{self.epoch}:{STYLES[selected][0]}>`")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description="Sorry, but this dropdown menu can only be used by the original author.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True


def setup(bot: Bot) -> None:
    """Load the Epoch cog."""
    bot.add_cog(Epoch())
