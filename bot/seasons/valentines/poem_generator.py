import random

import aiohttp
import logging
from typing import List, Dict

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

        self.model = markovify.Text(full_corpus, state_size=1)  # Create a markov model
        self.rhymes: Dict[str, List[str]] = {}

    async def get_rhyming_words(self, word: str) -> List[str]:
        word = word.replace("'", "e")  # Sometimes e is replaced with '

        if word in self.rhymes:
            return self.rhymes[word]

        async with aiohttp.ClientSession() as client:
            async with client.get("https://api.datamuse.com/words?rel_rhy=" + word) as response:  # Exact rhymes
                exact = [x["word"] for x in await response.json()]
                if not exact:
                    print(word)
            async with client.get("https://api.datamuse.com/words?rel_nry=" + word) as response:  # Close rhymes
                close = [x["word"] for x in await response.json() if x.get("score", 0) > 2000]

        words = exact + close

        self.rhymes[word] = words
        return words

    @staticmethod
    def last_word(line: str) -> str:
        return line.strip("?.,!").split()[-1]

    async def generate_poem(self) -> str:
        lines = []
        for i in range(1, 15):  # A sonnet has 14 lines, so generate 14
            line = None
            while line is None:  # Line can be None if it fails to be under 50, so keep looping
                line = self.model.make_short_sentence(random.randint(50, 120))
                if line is not None and i in (3, 4, 7, 8, 11, 12, 13, 14):
                    previous = lines[i-3]
                    last_word = self.last_word(previous)
                    words = await self.get_rhyming_words(last_word)
                    current_last_word = self.last_word(line)

                    if words and current_last_word not in [*words, last_word]:
                        line = None
            lines.append(line)

        return "\n\n".join([  # Section dividers
            "\n".join(lines[:4]),  # 4, 4, 3, 3, like a shakespearian sonnet
            "\n".join(lines[4:8]),
            "\n".join(lines[8:11]),
            "\n".join(lines[11:])
        ])

    @commands.command()
    async def poem(self, ctx):
        await ctx.send(await self.generate_poem())


def setup(bot):
    bot.add_cog(PoemGenerator())
    log.debug("PoemGenerator cog loaded")


if __name__ == "__main__":
    import asyncio
    print(asyncio.get_event_loop().run_until_complete(PoemGenerator().generate_poem()))
