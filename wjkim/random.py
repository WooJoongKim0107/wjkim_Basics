from random import randrange
from more_itertools import nth
from collections.abc import Iterable


def choice_from_iterable(x: Iterable, size: int):
    return nth(x, randrange(size))


def choice_from_set(x: set):
    """As set is iterable, use choice_from_iterable() instead"""
    return nth(x, randrange(len(x)))
