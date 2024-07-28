from typing import IO
from itertools import zip_longest
from collections.abc import Iterable
from more_itertools import roundrobin


Readable = Iterable[str] | IO[str]


def read_commented(x: Readable, mark='#'):
    lines = (line.partition(mark)[0].rstrip() for line in x)  # remove comments
    yield from (line for line in lines if line)  # remove empty lines


def filled(x, size, fillvalue=''):
    y = [0]*size
    return [xx for xx, _ in zip_longest(x, y, fillvalue=fillvalue)]


def joins(x: Iterable[str], y: Iterable):
    return ''.join(roundrobin(y, x))  # ''.join([3, '| ', 0.17, ' ', 2e-5, ' ', 0.55])


def col_wrap(*cols,
             header: Iterable = (), seps: Iterable = (),
             filler: Iterable = (), location: Iterable = (), fmt: Iterable = ()):
    def_sep = ' '
    def_filler = ''
    def_location = '>'

    seps = filled(seps, size=len(cols)-1, fillvalue=def_sep)
    filler = filled(filler, size=len(cols), fillvalue=def_filler)
    location = filled(location, size=len(cols), fillvalue=def_location)

    hf_cols = [(h,) + tuple(f'{x:{f}}' for x in col) for h, col, f in zip_longest(header, cols, fmt, fillvalue='')]
    size = [max(len(str(x)) for x in col) for col in hf_cols]
    rows = [joins(seps, (f'{x:{f}{l}{s}}' for x, f, l, s in zip(row, filler, location, size))) for row in zip(*hf_cols)]
    return '\n'.join(rows)
