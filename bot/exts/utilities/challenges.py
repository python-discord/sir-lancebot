import logging
from asyncio import to_thread
from random import choice
from typing import Union

from bs4 import BeautifulSoup
from discord import Embed, Interaction, SelectOption, ui
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Emojis, NEGATIVE_REPLIES

log = logging.getLogger(__name__)
API_ROOT = "https://www.codewars.com/api/v1/code-challenges/{kata_id}"

# Map difficulty for the kata to color we want to display in the embed.
# These colors are representative of the colors that each kyu's level represents on codewars.com
MAPPING_OF_KYU = {
    8: 0xdddbda, 7: 0xdddbda, 6: 0xecb613, 5: 0xecb613,
    4: 0x3c7ebb, 3: 0x3c7ebb, 2: 0x866cc7, 1: 0x866cc7
}

# Supported languages for a kata on codewars.com
SUPPORTED_LANGUAGES = {
    "stable": [
        "c", "c#", "c++", "clojure", "coffeescript", "coq", "crystal", "dart", "elixir",
        "f#", "go", "groovy", "haskell", "java", "javascript", "kotlin", "lean", "lua", "nasm",
        "php", "python", "racket", "ruby", "rust", "scala", "shell", "sql", "swift", "typescript"
    ],
    "beta": [
        "agda", "bf", "cfml", "cobol", "commonlisp", "elm", "erlang", "factor",
        "forth", "fortran", "haxe", "idris", "julia", "nim", "objective-c", "ocaml",
        "pascal", "perl", "powershell", "prolog", "purescript", "r", "raku", "reason", "solidity", "vb.net"
    ]
}


class InformationDropdown(ui.Select):
    """A dropdown inheriting from ui.Select that allows finding out other information about the kata."""

    def __init__(self, language_embed: Embed, tags_embed: Embed, other_info_embed: Embed, main_embed: Embed):
        options = [
            SelectOption(
                label="Main Information",
                description="See the kata's difficulty, description, etc.",
                emoji="🌎"
            ),
            SelectOption(
                label="Languages",
                description="See what languages this kata supports!",
                emoji=Emojis.reddit_post_text
            ),
            SelectOption(
                label="Tags",
                description="See what categories this kata falls under!",
                emoji=Emojis.stackoverflow_tag
            ),
            SelectOption(
                label="Other Information",
                description="See how other people performed on this kata and more!",
                emoji="ℹ"
            )
        ]

        # We map the option label to the embed instance so that it can be easily looked up later in O(1)
        self.mapping_of_embeds = {
            "Main Information": main_embed,
            "Languages": language_embed,
            "Tags": tags_embed,
            "Other Information": other_info_embed,
        }

        super().__init__(
            placeholder="See more information regarding this kata",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction) -> None:
        """Callback for when someone clicks on a dropdown."""
        # Edit the message to the embed selected in the option
        # The `original_message` attribute is set just after the message is sent with the view.
        # The attribute is not set during initialization.
        result_embed = self.mapping_of_embeds[self.values[0]]
        await self.original_message.edit(embed=result_embed)


class Challenges(commands.Cog):
    """
    Cog for the challenge command.

    The challenge command pulls a random kata from codewars.com.
    A kata is the name for a challenge, specific to codewars.com.

    The challenge command also has filters to customize the kata that is given.
    You can specify the language the kata should be from, difficulty and topic of the kata.
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
                    description="We ran into an error when getting the kata from codewars.com, try again later.",
                    color=Colours.soft_red
                )
                log.error(f"Unexpected response from codewars.com, status code: {response.status}")
                return error_embed

            soup = BeautifulSoup(await response.text(), features="lxml")
            first_kata_div = await to_thread(soup.find_all, "div", class_="item-title px-0")

            if not first_kata_div:
                raise commands.BadArgument("No katas could be found with the filters provided.")
            elif len(first_kata_div) >= 3:
                first_kata_div = choice(first_kata_div[:3])
            elif "q=" not in search_link:
                first_kata_div = choice(first_kata_div)
            else:
                first_kata_div = first_kata_div[0]

            # There are numerous divs before arriving at the id of the kata, which can be used for the link.
            first_kata_id = first_kata_div.a["href"].split("/")[-1]
            return first_kata_id

    async def kata_information(self, kata_id: str) -> Union[dict, Embed]:
        """
        Returns the information about the Kata.

        Uses the codewars.com API to get information about the kata using `kata_id`.
        """
        async with self.bot.http_session.get(API_ROOT.format(kata_id=kata_id)) as response:
            if response.status != 200:
                error_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="We ran into an error when getting the kata information, try again later.",
                    color=Colours.soft_red
                )
                log.error(f"Unexpected response from codewars.com/api/v1, status code: {response.status}")
                return error_embed

            return await response.json()

    @staticmethod
    def main_embed(kata_information: dict) -> Embed:
        """Creates the main embed which displays the name, difficulty and description of the kata."""
        kata_description = kata_information["description"]
        kata_url = f"https://codewars.com/kata/{kata_information['id']}"

        # Ensuring it isn't over the length 1024
        if len(kata_description) > 1024:
            kata_description = "\n".join(kata_description[:1000].split("\n")[:-1]) + "..."
            kata_description += f" [continue reading]({kata_url})"

        if kata_information["rank"]["name"] is None:
            embed_color = 8
            kata_difficulty = "Unable to retrieve difficulty for beta languages."
        else:
            embed_color = int(kata_information["rank"]["name"].replace(" kyu", ""))
            kata_difficulty = kata_information["rank"]["name"]

        kata_embed = Embed(
            title=kata_information["name"],
            description=kata_description,
            color=MAPPING_OF_KYU[embed_color],
            url=kata_url
        )
        kata_embed.add_field(name="Difficulty", value=kata_difficulty, inline=False)
        return kata_embed

    @staticmethod
    def language_embed(kata_information: dict) -> Embed:
        """Creates the 'language embed' which displays all languages the kata supports."""
        kata_url = f"https://codewars.com/kata/{kata_information['id']}"

        languages = "\n".join(map(str.title, kata_information["languages"]))
        language_embed = Embed(
            title=kata_information["name"],
            description=f"```yaml\nSupported Languages:\n{languages}\n```",
            color=Colours.python_blue,
            url=kata_url
        )
        return language_embed

    @staticmethod
    def tags_embed(kata_information: dict) -> Embed:
        """
        Creates the 'tags embed' which displays all the tags of the Kata.

        Tags explain what the kata is about, this is what codewars.com calls categories.
        """
        kata_url = f"https://codewars.com/kata/{kata_information['id']}"

        tags = "\n".join(kata_information["tags"])
        tags_embed = Embed(
            title=kata_information["name"],
            description=f"```yaml\nTags:\n{tags}\n```",
            color=Colours.grass_green,
            url=kata_url
        )
        return tags_embed

    @staticmethod
    def miscellaneous_embed(kata_information: dict) -> Embed:
        """
        Creates the 'other information embed' which displays miscellaneous information about the kata.

        This embed shows statistics such as the total number of people who completed the kata,
        the total number of stars of the kata, etc.
        """
        kata_url = f"https://codewars.com/kata/{kata_information['id']}"

        embed = Embed(
            title=kata_information["name"],
            description="```nim\nOther Information\n```",
            color=Colours.grass_green,
            url=kata_url
        )
        embed.add_field(
            name="`Total Score`",
            value=f"```css\n{kata_information['voteScore']}\n```",
            inline=False
        )
        embed.add_field(
            name="`Total Stars`",
            value=f"```css\n{kata_information['totalStars']}\n```",
            inline=False
        )
        embed.add_field(
            name="`Total Completed`",
            value=f"```css\n{kata_information['totalCompleted']}\n```",
            inline=False
        )
        embed.add_field(
            name="`Total Attempts`",
            value=f"```css\n{kata_information['totalAttempts']}\n```",
            inline=False
        )
        return embed

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
    @commands.cooldown(1, 5, commands.BucketType.user)
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
        language = language.lower()
        if language not in SUPPORTED_LANGUAGES["stable"] + SUPPORTED_LANGUAGES["beta"]:
            raise commands.BadArgument("This is not a recognized language on codewars.com!")

        get_kata_link = f"https://codewars.com/kata/search/{language}"
        params = {}

        if query is not None:
            if "," in query:
                query_splitted = query.split("," if ", " not in query else ", ")

                if len(query_splitted) > 2:
                    raise commands.BadArgument(
                        "There can only be one comma within the query, separating the difficulty and the query itself."
                    )

                query, level = query_splitted
                params["q"] = query
                params["r[]"] = f"-{level}"
            elif query.isnumeric():
                params["r[]"] = f"-{query}"
            else:
                params["q"] = query

        params["beta"] = str(language in SUPPORTED_LANGUAGES["beta"]).lower()

        first_kata_id = await self.kata_id(get_kata_link, params)
        if isinstance(first_kata_id, Embed):
            # We ran into an error when retrieving the website link
            await ctx.send(embed=first_kata_id)
            return

        kata_information = await self.kata_information(first_kata_id)
        if isinstance(kata_information, Embed):
            # Something went wrong when trying to fetch the kata information
            await ctx.d(embed=kata_information)
            return

        kata_embed = self.main_embed(kata_information)
        language_embed = self.language_embed(kata_information)
        tags_embed = self.tags_embed(kata_information)
        miscellaneous_embed = self.miscellaneous_embed(kata_information)

        dropdown = InformationDropdown(
            main_embed=kata_embed,
            language_embed=language_embed,
            tags_embed=tags_embed,
            other_info_embed=miscellaneous_embed
        )
        kata_view = self.create_view(dropdown, f"https://codewars.com/kata/{first_kata_id}")
        original_message = await ctx.send(
            embed=kata_embed,
            view=kata_view
        )
        dropdown.original_message = original_message

        wait_for_kata = await kata_view.wait()
        if wait_for_kata:
            await original_message.edit(embed=kata_embed, view=None)


def setup(bot: Bot) -> None:
    """Load the Challenges cog."""
    bot.add_cog(Challenges(bot))
