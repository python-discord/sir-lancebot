from typing import Optional, Union

import arrow
import discord
from dateutil import parser
from discord.ext import commands

from bot.bot import Bot
from bot.exts.core.extensions import invoke_help_command

# https://discord.com/developers/docs/reference#message-formatting-timestamp-styles
STYLES = {"Epoch": ("",),
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
        except OverflowError:
            raise commands.BadArgument(f"`{argument}` Could not be parsed to a relative or absolute date")
        except ValueError:
            try:
                dt, ignored_tokens = parser.parse(argument, fuzzy_with_tokens=True)
                return arrow.get(dt), ignored_tokens
            except parser.ParserError:
                raise commands.BadArgument(f"`{argument}` Could not be parsed to a relative or absolute date")


class Epoch(commands.Cog):
    """Convert an entered time and date to a unix timestamp."""

    @commands.command(name="epoch")
    async def epoch(self, ctx: commands.Context, *, date_time: DateString = None) -> None:
        """
        Convert an entered date/time string to the equivalent epoch.

        **Relative time**
            accepted units: "seconds", "minutes", "hours", "days", "weeks", "months", "years"
            Eg ".epoch in a month 4 days and 2 hours"

        **Absolute time**
            eg ".epoch 2022/6/15 16:43 -04:00"
            Absolute times must be entered in descending orders of magnitude.
            Timezones may take the following forms:
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
            ignored_tokens, date_time = list(a.strip() for a in date_time[1] if a.strip()), date_time[0]
            if ignored_tokens:
                await ctx.send(f"Could not parse the following token(s): `{', '.join(ignored_tokens)}`")
                await ctx.send(f"The resulting date and time is: `{date_time.format(arrow.FORMAT_RSS)}`")

        epoch = int(date_time.timestamp())
        dropdown = _TimestampDropdown(self._format_dates(date_time), epoch)
        view = _TimestampMenuView(ctx, dropdown)
        original = await ctx.send(f"`{epoch}`", view=view)
        if await view.wait():  # wait until expiration and remove the dropdown
            await original.edit(view=None)

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


class _TimestampDropdown(discord.ui.Select):
    def __init__(self, formatted_times: list[str], epoch: int):
        self.epoch: int = epoch
        super().__init__(
            placeholder="Select the format of your timestamp",
            options=[discord.SelectOption(label=label, description=date_time) for label, date_time in
                     zip(STYLES.keys(), formatted_times)]
        )

    async def callback(self, interaction: discord.Interaction) -> discord.Message:
        selected = interaction.data["values"][0]
        if selected == "Epoch":
            return await interaction.message.edit(content=f"`{self.epoch}`")
        else:
            return await interaction.message.edit(content=f"`<t:{self.epoch}:{STYLES[selected][0]}>`")


class _TimestampMenuView(discord.ui.View):
    def __init__(self, ctx: commands.Context, dropdown: _TimestampDropdown):
        super().__init__(timeout=DROPDOWN_TIMEOUT)
        self.ctx = ctx
        self.add_item(dropdown)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description="Sorry, but this interaction can only be used by the original author.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        else:
            return True


def setup(bot: Bot) -> None:
    """Load the Epoch cog."""
    bot.add_cog(Epoch())
