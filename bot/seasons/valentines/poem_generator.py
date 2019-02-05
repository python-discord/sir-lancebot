import logging

from discord.ext import commands
import markovify

log = logging.getLogger(__name__)


class PoemGenerator:
    SOURCES = [
        "shakespeare corpus.txt"
    ]

    def __init__(self):
        full_corpus = ""

        for file in self.SOURCES:
            with open(f"bot/resources/valentines/{file}") as f:
                full_corpus += f.read()  # Make sure all files end with a blank newline!

        self.model = markovify.Text(full_corpus)  # Create a markov model

    def generate_poem(self):
        lines = []
        for _ in range(14):  # A sonnet has 14 lines, so generate 14
            line = None
            while line is None:  # Line can be None if it fails to be under 50, so keep looping
                line = self.model.make_short_sentence(50)
            lines.append(line)

        return "\n\n".join([  # Section dividers
            "\n".join(lines[:4]),  # 4, 4, 3, 3, like a shakespearian sonnet
            "\n".join(lines[4:8]),
            "\n".join(lines[8:11]),
            "\n".join(lines[11:])
        ])

    @commands.command()
    async def poem(self, ctx):
        await ctx.send(self.generate_poem())


def setup(bot):
    bot.add_cog(PoemGenerator())
    log.debug("PoemGenerator cog loaded")
