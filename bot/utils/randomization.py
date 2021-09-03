import itertools
import random
from collections.abc import Iterable
from typing import Any


class RandomCycle:
    """
    Cycles through elements from a randomly shuffled iterable, repeating indefinitely.

    The iterable is reshuffled after each full cycle.
    """

    def __init__(self, iterable: Iterable):
        self.iterable = list(iterable)
        self.index = itertools.cycle(range(len(iterable)))

    def __next__(self) -> Any:
        idx = next(self.index)

        if idx == 0:
            random.shuffle(self.iterable)

        return self.iterable[idx]
