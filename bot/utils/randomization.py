import itertools
import random
import typing as t


class RandomCycle:
    """
    Cycles through elements from a randomly shuffled iterable, repeating indefinitely.

    The iterable is reshuffled after each full cycle.
    """

    def __init__(self, iterable: t.Iterable) -> None:
        self.iterable = list(iterable)
        self.index = itertools.cycle(range(len(iterable)))

    def __next__(self) -> t.Any:
        idx = next(self.index)

        if idx == 0:
            random.shuffle(self.iterable)

        return self.iterable[idx]
