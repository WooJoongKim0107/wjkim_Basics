from sys import argv
from os import cpu_count


def next_to(targets):
    for i, x in enumerate(argv):
        if x in targets:
            return argv[i+1]
    raise ValueError(f"{targets} Not found")


def get_workers(strict=True):
    targets = {'-p', '--workers'}
    workers = int(next_to(targets))
    if workers > cpu_count():
        raise ValueError("Number of workers exceed that of CPU's ({workers} > {cpu_count()})")
    elif workers is None and strict:
        raise ValueError("Number of workers not given")
    else:
        return workers
