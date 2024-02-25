import re


def suppress_links(message: str) -> str:
    """Accepts a message that may contain links, suppresses them, and returns them."""
    for link in set(re.findall(r"https?://[^\s]+", message, re.IGNORECASE)):
        message = message.replace(link, f"<{link}>")
    return message

def neutralise_string(txt: str | None) -> list[str] | None:
    """Attempts to neutralise all punctuation and cases and returns a string of lowercase words."""
    # Return early if no text provided.
    if not txt:
        return None

    # Take out punctuation.
    txt = re.sub(r"[\W_]", " ", txt)

    words = []
    for word in txt.split():
        if word.isupper():
            words.append(word.lower())
        else:
            old_i = 0
            for i, char in enumerate(word):
                if char.isupper() and i != 0:
                    words.append(word[old_i:i].lower())
                    old_i = i
            words.append(word[old_i:].lower())

    return words
