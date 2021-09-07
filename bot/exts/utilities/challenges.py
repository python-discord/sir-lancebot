import logging
from random import choice

from bs4 import BeautifulSoup
from discord import Color, Embed, Interaction, Message, SelectOption, ui
from discord.ext import commands

from bot.bot import Bot
from bot.constants import Colours, Emojis, NEGATIVE_REPLIES

logger = logging.getLogger(__name__)
API_ROOT = "https://www.codewars.com/api/v1/code-challenges/{kata_id}"


class Challenges(commands.Cog):
    """
    Cog for a challenge command.

    Pulls a random kata from codewars.com, and can be filtered through.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

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
            level = f"-{choice(['1', '2', '3', '4', '5', '6', '7', '8'])}"
        elif "," in query or ", " in query:
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

        params = {name: value for name, value in zip(["q", "r[]"], [query, level]) if value}
        params = {**params, "beta": "false"}
        async with self.bot.http_session.get(get_kata_link, params=params) as response:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from codewars.com"
                )
            soup = BeautifulSoup(await response.text(), features="lxml")
            first_kata_div = soup.find_all("div", class_="item-title px-0")

            if not first_kata_div:
                no_results_embed = Embed(
                    title=choice(NEGATIVE_REPLIES),
                    description="No results could be found with the filters provided.",
                    color=Colours.soft_red,
                )
                await ctx.send(embed=no_results_embed)
                return
            elif not query:
                first_kata_div = choice(first_kata_div)
            elif len(first_kata_div) >= 3:
                first_kata_div = choice(first_kata_div[:3])
            else:
                first_kata_div = first_kata_div[0]

            # there are numerous divs before arriving at the id of the kata, which can be used for the link.
            first_kata_id = first_kata_div.a["href"].split("/")[-1]

        async with self.bot.http_session.get(API_ROOT.format(kata_id=first_kata_id)) as kata_information:
            if response.status != 200:
                logger.error(
                    f"Unexpected status code {response.status} from codewars.com/api/v1"
                )
            kata_information = await kata_information.json()
            # maps specific rgb codes to kyu (difficulty) of kata
            mapping_of_kyu = {
                -8: (221, 219, 218), -7: (221, 219, 218), -6: (236, 182, 19), -5: (236, 182, 19),
                -4: (60, 126, 187), -3: (60, 126, 187), -2: (134, 108, 199), -1: (134, 108, 199)
            }

            kata_description = kata_information["description"]

            # ensuring it isn't over the length 1024
            if len(kata_description) > 1024:
                kata_description = "\n".join(kata_description[:1000].split("\n")[:-1])
                kata_description += f"\n[Read more]({f'https://codewars.com/kata/{first_kata_id}'})"

            # creating the main kata embed
            kata_embed = Embed(
                title=kata_information['name'],
                description=kata_description,
                color=Color.from_rgb(*mapping_of_kyu[kata_information['rank']['id']]),
            )
            kata_embed.add_field(name="Difficulty", value=kata_information['rank']['name'], inline=False)

            # creating the language embed
            languages = '\n'.join(map(str.title, kata_information['languages']))
            language_embed = Embed(
                title="Languages Supported",
                description=f"```nim\n{languages}```",
                color=Colours.grass_green,
            )

            # creating the tags embed
            tags = '\n'.join(kata_information['tags'])
            tags_embed = Embed(
                title="Tags",
                description=f"```nim\n{tags}```",
                color=Colours.grass_green,
            )

            # creating the miscellaneous embed
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

            # sending then editing so the dropdown can access the original message
            original_message = await ctx.send(embed=kata_embed)
            dropdown = InformationDropdown(
                original_message=original_message,
                main_embed=kata_embed,
                language_embed=language_embed,
                tags_embed=tags_embed,
                other_info_embed=miscellaneous_embed,
            )
            await original_message.edit(
                embed=kata_embed,
                view=KataView(f'https://codewars.com/kata/{first_kata_id}', dropdown)
            )


# creates the information dropdown
class InformationDropdown(ui.Select):
    """A dropdown inheriting from ui.Select that allows finding out other information about the kata."""

    def __init__(
            self,
            original_message: Message,
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

        self.original_message = original_message
        # maps embeds to item chosen
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
        # option chosen will retrieve the embed for that specific option then the message will be edited
        result_embed = self.mapping_of_embeds[self.values[0]]
        await self.original_message.edit(embed=result_embed)


# creating the discord.ui.View subclass for the UI in the challenges command.
class KataView(ui.View):
    """The view for the InformationDropdown and the link to the Kata."""

    def __init__(self, link: str, dropdown: InformationDropdown):
        super().__init__()

        # adding the dropdown
        self.add_item(dropdown)
        # manually creating the button as it is a link button and has no decorator
        self.add_item(ui.Button(label="View the Kata", url=link))


def setup(bot: Bot) -> None:
    """Sets up Challenges cog."""
    bot.add_cog(Challenges(bot))
