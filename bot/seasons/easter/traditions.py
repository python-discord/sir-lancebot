import logging
import random

from discord.ext import commands

log = logging.getLogger(__name__)


class Traditions(commands.Cog):
    """A cog which allows users to get a random easter tradition or custom from a random country."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="easter_tradition")
    async def easter_tradition(self, ctx):
        """Responds with a random tradition or custom"""

        traditions = {
            "England": (
                "Easter in England is celebrated through the exchange of Easter Eggs and other gifts like clothes, "
                "chocolates or holidays packages. Easter bonnets or baskets are also made that have fillings like daffodils in them."
                ),
            "Haiti": (
                "In Haiti, kids have the freedom to spend Good Friday playing outdoors. "
                "On this day colourful kites fill the sky and children run long distances, often barefoot, "
                "trying to get their kite higher than their friends."
                ),
            "Indonesia": "Slightly unconventional, but kids in Indonesia celebrate Easter with a tooth brushing competition!",
            "Ethipoia": (
                "In Ethiopia, Easter is called Fasika and marks the end of a 55-day fast during which Christians "
                "have only eaten one vegetarian meal a day. Ethiopians will often break their fast after church by eating injera "
                "(a type of bread) or teff pancakes, made from grass flour."
                ),
            "El Salvador": (
                "On Good Friday communities make rug-like paintings on the streets with sand and sawdust. "
                "These later become the path for processions and main avenues and streets are closed"
                ),
            "Ghana": (
                "Ghanaians dress in certain colours to mark the different days of Easter. "
                "On Good Friday, depending on the church denomination, men and women will either dress in dark mourning "
                "clothes or bright colours. On Easter Sunday everyone wears white."
                ),
            "Kenya": (
                "On Easter Sunday, kids in Kenya look forward to a sumptuous Easter meal after church "
                "(Easter services are known to last for three hours!). "
                "Children share Nyama Choma (roasted meat) and have a soft drink with their meal!"
                ),
            "Guatemala": (
                "In Guatemala, Easter customs include a large, colourful celebration marked by countless processions. "
                "The main roads are closed, and the sound of music rings through the streets. "
                "Special food is prepared such as curtido (a diced vegetable mix which is cooked in vinegar to achieve a sour taste), "
                "fish, eggs, chickpeas, fruit mix, pumpkin, pacaya palm and spondias fruit (a Spanish version of a plum.)"
                ),
            "Germany": (
                "In Germany, Easter is known by the name of Ostern. "
                "Easter holidays for children last for about three weeks. "
                "Good Friday, Easter Saturday and Easter Sunday are the days when people do not work at all."
                ),
            "Mexico": (
                "Semana Santa and Pascua (two separate observances) form a part of Easter celebrations in Mexico. "
                "Semana Santa stands for the entire Holy Week, from Palm Sunday to Easter Saturday, "
                "whereas the Pascua is the observance of the period from the Resurrection Sunday to the following Saturday."
                ),
            "Poland": (
                "They shape the Easter Butter Lamg (Baranek Wielkanocyny) from a chunk of butter. "
                "They attempt to make it look like a fluffy sheep!"),
            "Greece": (
                "They burn an effigy of Judas Iscariot, they betrayer of Jesus, "
                "sometimes is done as part of a Passion Play! It is hung by the neck and then burnt."
                ),
            "Philippines": (
                "Some Christians put themselves through the same pain that Christ endured, "
                "they have someone naile them to a cross and put a crown of thornes on their head."
                ),
        }

        random_country = random.choice(list(traditions))

        await ctx.send(f"{random_country}:\n{traditions[random_country]}")


def setup(bot):
    """Traditions Cog load."""

    bot.add_cog(Traditions(bot))
    log.info("Traditions cog loaded")
