# imports
import re
from string import punctuation


def suppress_links(message: str) -> str:
    """Accepts a message that may contain links, suppresses them, and returns them."""
    for link in set(re.findall(r"https?://[^\s]+", message, re.IGNORECASE)):
        message = message.replace(link, f"<{link}>")
    return message

def neutralise_string(txt: str) -> str:
    """Attempts to neutralise all punctuation and cases and returns a string of lowercase words"""
    # take out punctuation

    for c in punctuation:
        words = txt.split(c)
        txt = " ".join(words)

    words = txt.split()
    # full caps words
    words = [word.lower() if word.isupper() else word for word in words]
    txt = " ".join(words)

    words = []
    old_i = 0
    for i, char in enumerate(txt):
        if char.isupper():
            words.append(txt[old_i:i])
            old_i = i
    words.append(txt[old_i:])

    # strip white spaces
    words = [word.strip() for word in words]
    txt = " ".join(words)
    # return everything lower case
    return " ".join(word.lower() for word in txt.split())