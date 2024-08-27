from sys import argv


def get_workers(strict=True):
    targets = {'-p', '--workers'}
    for i, x in enumerate(argv):
        if x in targets:
            return int(argv[i+1])
    if strict:
        raise ValueError("Number of workers not given")
