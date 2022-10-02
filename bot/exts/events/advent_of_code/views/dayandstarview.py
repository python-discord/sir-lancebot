from datetime import datetime

import discord

AOC_DAY_AND_STAR_TEMPLATE = "{rank: >4} | {name:25.25} | {completion_time: >10}"


class AoCDropdownView(discord.ui.View):
    """Interactive view to filter AoC stats by Day and Star."""

    def __init__(self, original_author: discord.Member, day_and_star_data: dict[str: dict], maximum_scorers: int):
        super().__init__()
        self.day = 0
        self.star = 0
        self.data = day_and_star_data
        self.maximum_scorers = maximum_scorers
        self.original_author = original_author

    def generate_output(self) -> str:
        """
        Generates a formatted codeblock with AoC statistics based on the currently selected day and star.

        Optionally, when the requested day and star data does not exist yet it returns an error message.
        """
        header = AOC_DAY_AND_STAR_TEMPLATE.format(
            rank="Rank",
            name="Name", completion_time="Completion time (UTC)"
        )
        lines = [f"{header}\n{'-' * (len(header) + 2)}"]
        if not (day_and_star_data := self.data.get(f"{self.day}-{self.star}")):
            return ":x: The requested data for the specified day and star does not exist yet."
        for rank, scorer in enumerate(day_and_star_data[:self.maximum_scorers]):
            time_data = datetime.fromtimestamp(scorer['completion_time']).strftime("%I:%M:%S %p")
            lines.append(AOC_DAY_AND_STAR_TEMPLATE.format(
                datastamp="",
                rank=rank + 1,
                name=scorer['member_name'],
                completion_time=time_data)
            )
        joined_lines = "\n".join(lines)
        return f"Statistics for Day: {self.day}, Star: {self.star}.\n ```\n{joined_lines}\n```"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Global check to ensure that the interacting user is the user who invoked the command originally."""
        if interaction.user != self.original_author:
            await interaction.response.send_message(
                ":x: You can't interact with someone else's response. Please run the command yourself!",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.select(
        placeholder="Day",
        options=[discord.SelectOption(label=str(i)) for i in range(1, 26)],
        custom_id="day_select"
    )
    async def day_select(self, _: discord.Interaction, select: discord.ui.Select) -> None:
        """Dropdown to choose a Day of the AoC."""
        self.day = select.values[0]

    @discord.ui.select(
        placeholder="Star",
        options=[discord.SelectOption(label=str(i)) for i in range(1, 3)],
        custom_id="star_select"
    )
    async def star_select(self, _: discord.Interaction, select: discord.ui.Select) -> None:
        """Dropdown to choose either the first or the second star."""
        self.star = select.values[0]

    @discord.ui.button(label="Fetch", style=discord.ButtonStyle.blurple)
    async def fetch(self, _: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Button that fetches the statistics based on the dropdown values."""
        if self.day == 0 or self.star == 0:
            await interaction.response.send_message(
                "You have to select a value from both of the dropdowns!",
                ephemeral=True
            )
        else:
            await interaction.response.edit_message(content=self.generate_output())
            self.day = 0
            self.star = 0
