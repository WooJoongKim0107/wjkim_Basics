__all__ = ['substr', 'subpath', 's', 'ss', 'p', 'o', 'rename', 'copy', 'Quick']

import os
import re
import sys
import pickle
from shutil import copy as _copy
from pathlib import Path as _Path
from datetime import datetime

_sentinel_dict = {}


def s(x: str, **kwargs):
    sp = subpath(x)
    return sp.s(**kwargs)


def ss(x: str, **kwargs):
    sp = subpath(x)
    return sp.ss(**kwargs)


def p(x: str, **kwargs):
    sp = subpath(x)
    return sp.p(**kwargs)


def o(x, *args, **kwargs):
    sp = subpath(x)
    return sp.o(*args, **kwargs)


def rename(base, pattern, old, new, skip=False, verbose=True):
    """
    files = subpath(base).s().glob(pattern)
    <rename files by replacing "old" to "new">
    """
    def search():
        qs = s(base).glob(pattern)
        fs = []
        bfs = []
        afs = []
        for q in qs:
            if q.is_file() and (old in q.as_posix()):
                fs.append(q)
                bfs.append(q.as_posix())
                x = q.as_posix().split(old)
                x.insert(1, new)
                afs.append(''.join(x))
        return fs, bfs, afs

    def announce(bfs, afs):
        for b, a in zip(bfs, afs):
            print(b, '->', a)

    def agreed():
        answer = input('Proceed? [y]/n: ')
        return answer in ['', 'y', 'yes', 'Yes', 'YES', '1']

    def proceed(fs, afs):
        for f, a in zip(fs, afs):
            f.rename(a)

    files, before, after = search()
    if verbose:
        announce(before, after)
    if skip:
        proceed(files, after)
    elif agreed():
        print('Rename agreed')
        proceed(files, after)


def copy(base, pattern, old, new, skip=False, verbose=True):
    """
    files = subpath(base).s().glob(pattern)
    <rename files by replacing "old" to "new">
    """
    def search():
        qs = s(base).glob(pattern)
        fs = []
        bfs = []
        afs = []
        for q in qs:
            if q.is_file() and (old in q.as_posix()):
                fs.append(q)
                bfs.append(q.as_posix())
                x = q.as_posix().split(old)
                x.insert(1, new)
                afs.append(''.join(x))
        return fs, bfs, afs

    def announce(bfs, afs):
        for b, a in zip(bfs, afs):
            print('Copy: ', b, '->', a)

    def agreed():
        answer = input('Proceed? [y]/n: ')
        return answer in ['', 'y', 'yes', 'Yes', 'YES', '1']

    def proceed(bfs, afs):
        for b, a in zip(bfs, afs):
            _copy(b, a)

    files, before, after = search()
    if verbose:
        announce(before, after)
    if skip:
        proceed(before, after)
    elif agreed():
        print('Copy agreed')
        proceed(before, after)


class Quick:
    """
    Basic purpose:
        if (file exist):
            return (load from file)
        else:
            obj = (gen from input)
            (dump obj as file)
            return obj

    Design:
        (file): specified by .__new__(<file_name>) and .__init__(<file_name>)
                Assume subpath(<file_name>).s(**<kwargs>) points the actual file (, say <exact_file_name>)
        (load): specified by .register('load')(<load>)
                If not given, pickle.load() with mode='rb' will be used.
                Assume <load>(<exact_file_name>, **kwargs) as its signature
         (gen): specified by .register('gen')(<gen>)
                Must be given
                Assume <gen>(**<kwargs>) as its signature
        (dump): specified by .dump('dump')(<dump>)
                If not given, pickle.dump() with mode='wb' will be used.
                Assume <dump>(<obj>, <exact_file_name>, **kwargs) as its signature

    Step 1. initiate: Same as subpath - It will use cache, so don't need to store the instance
    Step 2. register: by wrapping a function to register its .gen, (optional) .load and (optional) .dump
    Step 3.      get: Initiate again (loaded from cache), and call .get(**kwargs)

    Upon self.get(**kwargs), each method will take the following as its input
        self.gen(.) <- **kwargs
        self.load(.) <- self.fname.s(**kwargs), **kwargs
        self.dump(.) <- (self.gen(**kwargs), self.fname.s(**kwargs), **kwargs)

    Usage 1 - The simplest - real "Quick" version
        q = Quick('$rsrc/lite/trial17/BA_0.50.pkl').load()
        Quick('$rsrc/lite/trial17/BA_0.50.pkl~').dump(q)

    Usage 2 - The most probable case
        @Quick('$rsrc/${ntype}_${cost}.pkl').register('gen')
        def gen(ntype, cost):
            # Create obj
            return obj

        if __name__ == '__main__':
            my_obj =  Quick('$rsrc/${ntype}_${cost}.pkl').get(ntype='BA', cost=0.5)

    Usage 3 - With custom "load" and "dump" method, e.g. using gzip.open
        @Quick('$rsrc/${ntype}_${cost}.pkl').register('gen')
        def gen(ntype, cost):
            # Create obj
            return obj

        @Quick('$rsrc/${ntype}_${cost}.pkl').register('load')
        def load(fname, **kwargs):
            with gzip.open(fname, 'rb') as file:
                obj = pickle.load(file)
            return obj

        @Quick('$rsrc/${ntype}_${cost}.pkl').register('dump')
        def dump(obj, fname, **kwargs):
            with gzip.open(fname, 'wb') as file:
                pickle.dump(obj, file)

        if __name__ == '__main__':
            my_obj = Quick('$rsrc/${ntype}_${cost}.pkl').get(ntype='BA', cost=0.5)
    """
    __cache__ = {}

    def __new__(cls, fname):
        if fname in cls.__cache__:
            return cls.__cache__[fname]
        return super().__new__(cls)

    def __init__(self, fname: str):
        if fname in self.__cache__:
            return
        else:
            self.__cache__[fname] = self
        self.fname: subpath = subpath(fname)
        self._exist = None
        self._load = None
        self._dump = None
        self._gen = None

    def s(self, **kwargs):
        return self.fname.s(**kwargs)

    def register(self, ftype):
        if ftype == 'exist':
            return self._register_exist
        elif ftype == 'load':
            return self._register_load
        elif ftype == 'gen':
            return self._register_gen
        elif ftype == 'dump':
            return self._register_dump

    def _register_exist(self, func):
        self._exist = func
        return func

    def _register_load(self, func):
        self._load = func
        return func

    def _register_gen(self, func):
        self._gen = func
        return func

    def _register_dump(self, func):
        self._dump = func
        return func

    def exist(self, **kwargs):
        if self._exist is None:
            return self.s(**kwargs).is_file()
        elif callable(self._exist):
            return self._exist(self.s(**kwargs), **kwargs)
        else:
            raise ValueError(f'Quick.exist not prepared')

    def load(self, **kwargs):
        if self._load is None:
            with open(self.s(**kwargs), 'rb') as file:
                return pickle.load(file)
        elif callable(self._load):
            return self._load(self.s(**kwargs), **kwargs)
        else:
            raise ValueError(f'Quick.load not prepared')

    def gen(self, **kwargs):
        if not callable(self._gen):
            raise ValueError(f'Quick.gen not prepared')
        else:
            return self._gen(**kwargs)

    def dump(self, res, **kwargs):
        if self._dump is None:
            with open(self.s(**kwargs), 'wb') as file:
                pickle.dump(res, file)
        elif callable(self._dump):
            self._dump(res, self.s(**kwargs), **kwargs)
        else:
            raise ValueError(f'Quick.dump not prepared')

    def get(self, **kwargs):
        try:
            assert self.exist(**kwargs)
            return self.load(**kwargs)
        except (AssertionError, EOFError):
            res = self.gen(**kwargs)
            self.dump(res, **kwargs)
            return res


class substr:
    base_cls = str
    _magic = dict(
        strftime=None,
        cwd=None,
    )
    a = re.compile(r'\$(?P<key>[_a-z][_a-z0-9]*)', flags=re.I)  # $key
    b = re.compile(r'\$?{(?P<key>[_a-z][_a-z0-9]*)}', flags=re.I)  # {key} or ${key}
    c = re.compile(r'\$?{(?P<key>[_a-z][_a-z0-9]*):(?P<fmt>.*?)}', flags=re.I)  # {key:fmt} or ${key:fmt}

    def __init__(self, template):
        self.template = template
        self.a_keys = tuple(self.a.findall(template))
        self.b_keys = tuple(self.b.findall(template))
        self.c_keys, self.c_fmts = zip(*x) if (x := self.c.findall(template)) else ((), ())
        self.c_dict = {key: fmt for key, fmt in zip(self.c_keys, self.c_fmts)}
        self.keys = {*self.a_keys, *self.b_keys, *self.c_keys}

    def __repr__(self):
        return f"{type(self).__name__}('{self.template}')"

    def ss(self, **kwargs):
        def ab_convert(x):
            key = x.group('key')
            val = kwargs.get(key, x.group())
            return str(val)

        def c_convert(x):
            key, fmt = x.groups()
            if key in kwargs:
                val = kwargs[key]
                return f'{val:{fmt}}'
            else:
                return x.group()

        template = self.a.sub(ab_convert, self.template)
        template = self.b.sub(ab_convert, template)
        template = self.c.sub(c_convert, template)
        if self.keys.issubset(kwargs):
            return self.base_cls(template)
        return type(self)(template)

    def magic_substitute(self):
        def ab_convert(x):
            key = x.group('key')
            if key == 'strftime':
                return datetime.now().strftime('%Y-%m-%d %X')
            elif key == 'cwd':
                return os.getcwd()
            val = self._magic.get(key, x.group())
            return str(val)

        def c_convert(x):
            key, fmt = x.groups()
            if key not in self._magic:
                return x.group()
            elif key == 'strftime':
                return datetime.now().strftime(fmt)
            else:
                val = self._magic[key]
                return f'{val:{fmt}}'

        template = self.a.sub(ab_convert, self.template)
        template = self.b.sub(ab_convert, template)
        template = self.c.sub(c_convert, template)
        if self.keys.issubset(self._magic):
            return self.base_cls(template)
        return type(self)(template)

    def s(self, **kwargs):
        full = kwargs | self._magic
        if not self.keys.issubset(full):
            raise KeyError(f'{self.keys.difference(full)} not provided.\nUse .ss() if necessary.')
        x = self.ss(**kwargs)
        if isinstance(x, type(self)):
            x = x.magic_substitute()
        if isinstance(x, self.base_cls):
            return x
        else:
            raise KeyError(f'Something went wrong! This supposed to be never triggered...\n{x}')

    def p(self, **kwargs):
        print(self.s(**kwargs))

    def o(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None, **kwargs):
        open_kwargs = dict(mode=mode, buffering=buffering, encoding=encoding,
                           errors=errors, newline=newline, closefd=closefd, opener=opener)
        return open(self.s(**kwargs), **open_kwargs)


def _find_base_dir():
    if res := os.environ.get('PROJ_DIR', ''):
        return _Path(res)
    pathes = list(map(_Path, sys.path))
    for path in pathes:
        if (path.stem == 'src') and any(path.parent == x for x in pathes):
            return path.parent  # ~/project_dir
    else:
        raise ValueError('Project directory not found.')


class subpath(substr):
    base_cls = _Path
    _base = _find_base_dir()
    _rsrc = _base / 'rsrc'
    _constants = dict(
        base=_base,
        rsrc=_rsrc,
        data=_rsrc/'data',
        pdata=_rsrc/'pdata',
        lite=_rsrc/'lite',
    )

    def s(self, **kwargs):
        kwargs = self._constants | kwargs
        return super().s(**kwargs)
