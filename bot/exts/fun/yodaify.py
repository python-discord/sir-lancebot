import re
from discord.ext import commands
from discord import AllowedMentions

from bot.bot import Bot


class Yodaify(commands.Cog):
    """Cog for the yodaify command."""

    def _yodaify_sentence(self, sentence: str) -> str:
        """Convert a single sentence to Yoda speech pattern."""
        sentence = sentence.strip().rstrip('.')
        
        # Basic pattern matching for subject-verb-object
        # Looking for patterns like "I am driving a car" -> "Driving a car, I am"
        words = sentence.split()
        if len(words) < 3: 
            return sentence + "."
            
        # Common subject-verb patterns to identify the split point
        subject_verb_patterns = [
            (r'^(i|you|he|she|it|we|they)\s+(am|are|is|was|were)\s+', 2),
            (r'^(i|you|he|she|it|we|they)\s+\w+\s+', 2),
        ]
        
        for pattern, split_index in subject_verb_patterns:
            if re.match(pattern, sentence.lower()):
                subject = ' '.join(words[:split_index])
                predicate = ' '.join(words[split_index:])
                if predicate:
                    return f"{predicate.lower()}, {subject.lower()}."
        
        # If no pattern matches, return original with message
        return None

    @commands.command(name="yoda")
    async def yodaify(self, ctx: commands.Context, *, text: str | None) -> None:
        """
        Convert the provided text into Yoda-like speech.

        The command transforms sentences from subject-verb-object format
        to object-subject-verb format, similar to how Yoda speaks.
        """
        if not text:
            return  # Help message handled by Discord.py's help system
            
        # Split into sentences (considering multiple punctuation types)
        sentences = re.split(r'[.!?]+\s*', text.strip())
        sentences = [s for s in sentences if s] 
        
        yoda_sentences = []
        any_converted = False
        
        for sentence in sentences:
            yoda_sentence = self._yodaify_sentence(sentence)
            if yoda_sentence is None:
                yoda_sentences.append(sentence + ".")
            else:
                any_converted = True
                yoda_sentences.append(yoda_sentence)
        
        if not any_converted:
            await ctx.send(
                f"Yodafication this doesn't need, {ctx.author.display_name}!\n>>> {text}",
                allowed_mentions=AllowedMentions.none()
            )
            return
        
        for i in range(len(yoda_sentences)):
            sentence = yoda_sentences[i]
            words = sentence.split()
            for j in range(len(words)):
                if words[j].lower() == "i":
                    words[j] = "I"
            sentence = ' '.join(words)
            sentence = sentence[0].upper() + sentence[1:]
            yoda_sentences[i] = sentence
        result = ' '.join(yoda_sentences)
        
        await ctx.send(
            f">>> {result}",
            allowed_mentions=AllowedMentions.none()
        )


async def setup(bot: Bot) -> None:
    """Loads the yodaify cog."""
    await bot.add_cog(Yodaify())
