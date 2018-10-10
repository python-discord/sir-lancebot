import asyncio
import random
from datetime import timedelta

import discord
from discord.ext import commands

HALLOWEEN_FACTS = [
    "Halloween or Hallowe'en is also known as Allhalloween, All Hallows' Eve and  All Saints' Eve.",
    ("It is widely believed that many Halloween traditions originated from ancient Celtic harvest festivals, "
     "particularly the Gaelic festival Samhain, which means \"summer's end\"."),
    ("It is believed that the custom of making jack-o'-lanterns at Halloween began in Ireland. In the 19th century, "
     "turnips or mangel wurzels, hollowed out to act as lanterns and often carved with grotesque faces, were used at "
     "Halloween in parts of Ireland and the Scottish Highlands."),
    "Halloween is the second highest grossing commercial holiday after Christmas.",
    ("The word \"witch\" comes from the Old English *wicce*, meaning \"wise woman\". In fact, *wiccan* were highly "
     "respected people at one time. According to popular belief, witches held one of their two main meetings, or "
     "*sabbats*, on Halloween night."),
    "Samhainophobia is the fear of Halloween.",
    ("The owl is a popular Halloween image. In Medieval Europe, owls were thought to be witches, and to hear an owl's "
     "call meant someone was about to die."),
    ("An Irish legend about jack-o'-lanterns goes as follows:\n"
     "*On route home after a night's drinking, Jack encounters the Devil and tricks him into climbing a tree. A "
     "quick-thinking Jack etches the sign of the cross into the bark, thus trapping the Devil. Jack strikes a bargain "
     "that Satan can never claim his soul. After a life of sin, drink, and mendacity, Jack is refused entry to heaven "
     "when he dies. Keeping his promise, the Devil refuses to let Jack into hell and throws a live coal straight from "
     "the fires of hell at him. It was a cold night, so Jack places the coal in a hollowed out turnip to stop it from "
     "going out, since which time Jack and his lantern have been roaming looking for a place to rest.*"),
    ("Trick-or-treating evolved from the ancient Celtic tradition of putting out treats and food to placate spirits "
     "who roamed the streets at Samhain, a sacred festival that marked the end of the Celtic calendar year."),
    ("Comedian John Evans once quipped: \"What do you get if you divide the circumference of a jack-o’-lantern by its "
     "diameter? Pumpkin π.\""),
    ("Dressing up as ghouls and other spooks originated from the ancient Celtic tradition of townspeople disguising "
     "themselves as demons and spirits. The Celts believed that disguising themselves this way would allow them to "
     "escape the notice of the real spirits wandering the streets during Samhain."),
    ("In Western history, black cats have typically been looked upon as a symbol of evil omens, specifically being "
     "suspected of being the familiars of witches, or actually shape-shifting witches themselves. They are, however, "
     "too cute to be evil."),
]
SPOOKY_EMOJIS = [
    "\N{BAT}",
    "\N{DERELICT HOUSE BUILDING}",
    "\N{EXTRATERRESTRIAL ALIEN}",
    "\N{GHOST}",
    "\N{JACK-O-LANTERN}",
    "\N{SKULL}",
    "\N{SKULL AND CROSSBONES}",
    "\N{SPIDER WEB}",
]
PUMPKIN_ORANGE = discord.Color(0xFF7518)
HACKTOBERFEST_CHANNEL_ID = 101010  # Replace with actual channel ID.
INTERVAL = timedelta(hours=6).total_seconds()


class HalloweenFacts:

    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.last_fact = None

    async def on_ready(self):
        self.channel = self.bot.get_channel(HACKTOBERFEST_CHANNEL_ID)
        self.bot.loop.create_task(self._fact_publisher_task())

    async def _fact_publisher_task(self):
        """
        A background task that runs forever, sending Halloween facts at random to the Discord channel with id equal to
        HACKTOBERFEST_CHANNEL_ID every INTERVAL seconds.
        """
        facts = list(enumerate(HALLOWEEN_FACTS))
        while True:
            # Avoid choosing each fact at random to reduce chances of facts being reposted soon.
            random.shuffle(facts)
            for index, fact in facts:
                embed = self._build_embed(index, fact)
                await self.channel.send("Your regular serving of random Halloween facts", embed=embed)
                self.last_fact = (index, fact)
                await asyncio.sleep(INTERVAL)

    @commands.command(name="hallofact", aliases=["hallofacts"], brief="Get the most recent Halloween fact")
    async def get_last_fact(self, ctx):
        """
        Reply with the most recent Halloween fact.
        """
        if ctx.channel != self.channel:
            return
        index, fact = self.last_fact
        embed = self._build_embed(index, fact)
        await ctx.send("Halloween fact recap", embed=embed)

    @staticmethod
    def _build_embed(index, fact):
        """
        Builds a Discord embed from the given fact and its index.
        """
        emoji = random.choice(SPOOKY_EMOJIS)
        title = f"{emoji} Halloween Fact #{index + 1}"
        return discord.Embed(title=title, description=fact, color=PUMPKIN_ORANGE)


def setup(bot):
    bot.add_cog(HalloweenFacts(bot))
