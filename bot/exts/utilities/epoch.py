import discord
from discord.ext import commands
from discord.ext.commands import Converter
from bot.bot import Bot
from typing import Union

import dateutil
from dateutil import parser
import arrow
from bot.exts.core.extensions import invoke_help_command

# https://discord.com/developers/docs/reference#message-formatting-timestamp-styles
TIMESTAMP_FORMATS = ["h:mm A", "h:mm:ss A", "MM/DD/YYYY", "MMMM D, YYYY", "MMMM D, YYYY h:mm A",
                     "dddd, MMMM D, YYYY h:mm A "]
STYLES = {"Epoch": "", "Short Time": "t", "Long Time": "T", "Short Date": "d", "Long Date": "D", "Short Date/Time": "f",
          "Long Date/Time": "F", "Relative Time": "R"}


class RelativeDate(Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> arrow.Arrow:
        return arrow.utcnow().dehumanize(argument)


class AbsoluteDate(Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> arrow.Arrow:
        return arrow.get(dateutil.parser.parse(argument))


class Epoch(commands.Cog):

    @commands.command(name="epoch")
    async def epoch(self, ctx: commands.Context, *, date_time: Union[RelativeDate, AbsoluteDate] = None) -> None:
        """Converts an entered time and date to a unix timestamp. Both relative and absolute times are accepted.
        Eg ".epoch in 5 months 4 days and 2 hours"
        or ".epoch 2022/6/15 16:43 -04:00"

        Absolute times must be entered in descending orders of magnitude.
        Times in the dropdown are show in UTC

        Timezones may take the following forms:
            Z (UTC)
            ±HH:MM
            ±HHMM
            ±HH
        """

        if not date_time:
            await invoke_help_command(ctx)
            return

        epoch = int(date_time.timestamp())
        dropdown = TimeStampDropdown(self._format_dates(date_time), epoch)
        view = TimeStampMenuView(ctx, dropdown)
        original = await ctx.send(f"`{epoch}`", view=view)
        if await view.wait():  # wait until expiration and remove the dropdown
            await original.edit(view=None)

    def _format_dates(self, date: arrow.Arrow) -> list[str]:
        """returns a list of dates formatted according to the discord timestamp styles.
        These are used in the description of each option in the dropdown"""
        date = date.to('utc')
        formatted = [str(int(date.timestamp()))]
        formatted += [date.format(d_format) for d_format in TIMESTAMP_FORMATS]
        formatted.append(date.humanize())
        return formatted


class TimeStampDropdown(discord.ui.Select):
    def __init__(self, formatted_times, epoch: int):
        self.epoch: int = epoch
        super().__init__(
            placeholder="Format this epoch as a discord timestamp",
            options=[discord.SelectOption(label=label, description=date_time) for label, date_time in
                     zip(STYLES.keys(), formatted_times)]
        )

    async def callback(self, interaction: discord.Interaction):
        selected = interaction.data["values"][0]
        if selected == "Epoch":
            return await interaction.message.edit(content=f"`{self.epoch}`")
        else:
            return await interaction.message.edit(content=fr"\<t:{self.epoch}:{STYLES[selected]}>")


class TimeStampMenuView(discord.ui.View):
    def __init__(self, ctx, dropdown: TimeStampDropdown):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.add_item(dropdown)

    async def interaction_check(self, interaction: discord.Interaction):
        """Check to ensure that the interacting user is the user who invoked the command."""
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description=f"Sorry, but this interaction can only be used by the original author.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        else:
            return True


def setup(bot: Bot) -> None:
    bot.add_cog(Epoch())
