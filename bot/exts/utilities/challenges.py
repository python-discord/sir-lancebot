import logging
from random import choice
from typing import Union

from bs4 import BeautifulSoup
from discord import Color, Embed, Interaction, SelectOption, ui
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Emojis, NEGATIVE_REPLIES

logger = logging.getLogger(__name__)
API_ROOT = "https://www.codewars.com/api/v1/code-challenges/{kata_id}"
# Map difficulty for the kata to color we want to display in the embed.
# These colors are representative of the colors that each 'kyu' level represents on codewars.com
MAPPING_OF_KYU = {
    8: (221, 219, 218), 7: (221, 219, 218), 6: (236, 182, 19), 5: (236, 182, 19),
    4: (60, 126, 187), 3: (60, 126, 187), 2: (134, 108, 199), 1: (134, 108, 199),
}


class InformationDropdown(ui.Select):
    """A dropdown inheriting from ui.Select that allows finding out other information about the kata."""

    def __init__(
            self,
            language_embed: Embed,
            tags_embed: Embed,
            other_info_embed: Embed,
            main_embed: Embed,
    ):
        options = [
            SelectOption(
                label="Main Information",
                description="See the kata's difficulty, description, etc.",
                emoji='🌎',
            ),
            SelectOption(
                label='Languages',
                description='See what languages this kata supports!',
                emoji=Emojis.reddit_post_text,
            ),
            SelectOption(
                label='Tags',
                description='See what categories this kata falls under!',
                emoji=Emojis.stackoverflow_tag,
            ),
            SelectOption(
                label='Other Information',
                description='See how other people performed on this kata and more!',
                emoji='ℹ',
            ),
        ]

        # We map the option label to the embed instance so that it can be easily looked up later in O(1)
        self.mapping_of_embeds = {
            "Main Information": main_embed,
            "Languages": language_embed,
            "Tags": tags_embed,
            "Other Information": other_info_embed,
        }

        super().__init__(
            placeholder='See more information regarding this kata',
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction) -> None:
        """Callback for when someone clicks on a dropdown."""
        # Edit the message to the embed selected in the option
        result_embed = self.mapping_of_embeds[self.values[0]]
        await self.original_message.edit(embed=result_embed)


class Challenges(commands.Cog):
    """
    Cog for a challenge command.

    The challenge command pulls a random kata from codewars.com.
    A kata is the name for a challenge, specific to `codewars.com`.

    The challenge command also has filters to customize the kata that is given.
    You can specify the language the kata should be from, the difficulty of the kata.
    Lastly, you can customize the topic you want the kata to be about!
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def kata_id(self, search_link: str, params: dict) -> Union[str, Embed]:
        """
        Uses bs4 to get the HTML code for the page of katas, where the page is the link of the formatted `search_link`.

        This will webscrape the search page with `search_link` and then get the ID of a kata for the
        codewars.com API to use.
        """
        async with self.bot.http_session.get(search_link, params=params) as response:
            if response.status != 200:
                error_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="We ran into an error with getting the kata from codewars.com, try again later.",
                    color=Colours.soft_red,
                )
                return error_embed

            soup = BeautifulSoup(await response.text(), features="lxml")
            first_kata_div = soup.find_all("div", class_="item-title px-0")

            if not first_kata_div:
                raise commands.BadArgument("No katas could be found with the filters provided.")
            elif len(first_kata_div) >= 3:
                first_kata_div = choice(first_kata_div[:3])
            elif 'q=' not in search_link:
                first_kata_div = choice(first_kata_div)
            else:
                first_kata_div = first_kata_div[0]

            # there are numerous divs before arriving at the id of the kata, which can be used for the link.
            first_kata_id = first_kata_div.a["href"].split("/")[-1]
            return first_kata_id

    async def kata_information(self, kata_id: str) -> Union[dict, Embed]:
        """
        Returns the information about the Kata.

        Uses the codewars.com API to get information about the kata using the kata's ID.
        """
        async with self.bot.http_session.get(API_ROOT.format(kata_id=kata_id)) as response:
            if response.status != 200:
                error_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="We ran into an error with getting the kata information, try again later.",
                    color=Colours.soft_red,
                )
                return error_embed

            return await response.json()

    @staticmethod
    def main_embed(kata_information: dict) -> Embed:
        """Creates the main embed which displays the description of the kata and the difficulty, along with the name."""
        kata_description = kata_information["description"]
        kata_url = f"https://codewars.com/kata/{kata_information['id']}"

        # ensuring it isn't over the length 1024
        if len(kata_description) > 1024:
            kata_description = "\n".join(kata_description[:1000].split("\n")[:-1])
            kata_description += f"\n[Read more...]({kata_url})"

        kata_embed = Embed(
            title=f"[{kata_information['name']}]({kata_url})",
            description=kata_description,
            color=Color.from_rgb(
                *MAPPING_OF_KYU[int(kata_information['rank']['name'].replace(' kyu', ''))]
            ),
        )
        kata_embed.add_field(name="Difficulty", value=kata_information['rank']['name'], inline=False)
        return kata_embed

    @staticmethod
    def language_embed(kata_information: dict) -> Embed:
        """Creates the 'language embed' which displays all languages the kata supports."""
        languages = '\n'.join(map(str.title, kata_information['languages']))
        language_embed = Embed(
            title="Languages Supported",
            description=f"```nim\n{languages}```",
            color=Colours.python_blue,
        )
        return language_embed

    @staticmethod
    def tags_embed(kata_information: dict) -> Embed:
        """
        Creates the 'tags embed' which displays all the tags of the Kata.

        Tags explain what the Kata is about, this is what codewars.com calls categories.
        """
        tags = '\n'.join(kata_information['tags'])
        tags_embed = Embed(
            title="Tags",
            description=f"```nim\n{tags}```",
            color=Colours.grass_green,
        )
        return tags_embed

    @staticmethod
    def miscellaneous_embed(kata_information: dict) -> Embed:
        """
        Creates the 'other information embed' which displays miscellaneous information about the kata.

        This embed shows statistics like the total number of people who completed the kata,
        the total number of stars of the Kata, etc.
        """
        miscellaneous_embed = Embed(
            title="Other Information",
            color=Colours.grass_green,
        )
        miscellaneous_embed.add_field(
            name="`Total Score`",
            value=f"**{kata_information['voteScore']}**",
            inline=False,
        )
        miscellaneous_embed.add_field(
            name="`Total Stars`",
            value=f"**{kata_information['totalStars']}**",
            inline=False,
        )
        miscellaneous_embed.add_field(
            name="`Total Completed`",
            value=f"**{kata_information['totalCompleted']}**",
            inline=False,
        )
        miscellaneous_embed.add_field(
            name="`Total Attempts`",
            value=f"**{kata_information['totalAttempts']}**",
            inline=False,
        )
        return miscellaneous_embed

    @staticmethod
    def create_view(dropdown: InformationDropdown, link: str) -> ui.View:
        """
        Creates the discord.py View for the Discord message components (dropdowns and buttons).

        The discord UI is implemented onto the embed, where the user can choose what information about the kata they
        want, along with a link button to the kata itself.
        """
        view = ui.View()
        view.add_item(dropdown)
        view.add_item(ui.Button(label="View the Kata", url=link))
        return view

    @commands.command(aliases=["kata"])
    async def challenge(self, ctx: commands.Context, language: str = "python", *, query: str = None) -> None:
        """
        The challenge command pulls a random kata (challenge) from codewars.com.

        The different ways to use this command are:
        `.challenge <language>` - Pulls a random challenge within that language's scope.
        `.challenge <language> <difficulty>` - The difficulty can be from 1-8,
        1 being the hardest, 8 being the easiest. This pulls a random challenge within that difficulty & language.
        `.challenge <language> <query>` - Pulls a random challenge with the query provided under the language
        `.challenge <language> <query>, <difficulty>` - Pulls a random challenge with the query provided,
        under that difficulty within the language's scope.
        """
        get_kata_link = f"https://codewars.com/kata/search/{language}"

        if language and not query:
            level = f"-{choice([1, 2, 3, 4, 5, 6, 7, 8])}"
        elif "," in query:
            query_splitted = query.split("," if ", " not in query else ", ")

            if len(query_splitted) > 2:
                raise commands.BadArgument(
                    "There can only be one comma within the query, separating the difficulty and the query itself."
                )

            query, level = query_splitted
            level = f"-{level}"
        elif query.isnumeric():
            level, query = f"-{query}", None
        else:
            level = None

        params = {}
        if query:
            params["q"] = query
        if level:
            params["r[]"] = level

        params["beta"] = "false"

        first_kata_id = await self.kata_id(get_kata_link, params)
        if isinstance(first_kata_id, Embed):
            # ran into an error with retrieving the website link
            await ctx.send(embed=first_kata_id)
            return

        kata_information = await self.kata_information(first_kata_id)
        if isinstance(kata_information, Embed):
            # ran into an error with the codewars api, getting the kata information
            await ctx.send(embed=kata_information)
            return

        kata_embed = self.main_embed(kata_information)
        language_embed = self.language_embed(kata_information)
        tags_embed = self.tags_embed(kata_information)
        miscellaneous_embed = self.miscellaneous_embed(kata_information)

        dropdown = InformationDropdown(
            main_embed=kata_embed,
            language_embed=language_embed,
            tags_embed=tags_embed,
            other_info_embed=miscellaneous_embed,
        )
        kata_view = self.create_view(dropdown, f'https://codewars.com/kata/{first_kata_id}')
        original_message = await ctx.send(embed=kata_embed, view=kata_view)
        dropdown.original_message = original_message


def setup(bot: Bot) -> None:
    """Load the Challenges cog."""
    bot.add_cog(Challenges(bot))
