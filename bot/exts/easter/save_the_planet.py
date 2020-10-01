from discord.ext import commands
from pathlib import Path
from discord import Embed
import random
import json

embeds = []

# cog
class SaveThePlanet(commands.Cog):
    """A cog that teaches users how they can help our planet."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def get_response(self) -> Embed:
        return random.choice(embeds)

    @commands.command(aliases=('save_the_earth',))
    async def save_the_planet(self, ctx: commands.Context) -> None:
        """Responds with a random tip on how to be ecofriendly and help our planet."""
        await ctx.send(embed=self.get_response())

def setup(bot: commands.Bot) -> None:
    """save_the_planet Cog load."""
        
    with open(Path("bot/resources/easter/save_the_planet.json"), 'r', encoding="utf8") as f:
        responses = json.load(f)

    # convert what's in the json to discord embed objects https://discord.com/developers/docs/resources/channel#embed-object
    for response in responses["embeds"]:
        response["title"] = f"Save the Planet: {response['topic']}"
        response["footer"] = {"text": "The best thing you can do is sharing this information!"}
        response["image"] = {
            "url": response["image_url"]
        }
        response["fields"] = [
            {
                "name": "The Problem",
                "value": response["problem"],
                "inline": False
            },
            {
                "name": "What you can do",
                "value": response["solution"]
            }
        ]

        embeds.append(Embed.from_dict(response))
    bot.add_cog(SaveThePlanet(bot))