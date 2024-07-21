__all__ = ['substr', 'subpath', 's', 'ss', 'p', 'o', 'glob', 'explore', 'rename', 'copy']

import os
import re
import sys
import json
import pickle
from glob import glob as _glob
from shutil import copy as _copy
from pathlib import Path as _Path
from datetime import datetime

_sentinel_dict = {}


def s(x: str, *, mkdir=False, **kwargs):
    sp = subpath(x)
    return sp.s(mkdir=mkdir, **kwargs)


def ss(x: str, **kwargs):
    sp = subpath(x)
    return sp.ss(**kwargs)


def p(x: str, **kwargs):
    sp = subpath(x)
    return sp.p(**kwargs)


def o(x, *args, mkdir=False, **kwargs):
    sp = subpath(x)
    return sp.o(*args, mkdir=mkdir, **kwargs)


def glob(x, **excludes):
    """Caution: If keys are not seperated, e.g. $tau$beta,
    they will be translated as `**`, which means `any subdirectories`."""
    sp = subpath(x)
    return sp.glob(**excludes)


def explore(x, *targets):
    sp = subpath(x)
    return sp.explore(*targets)


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


class substr:
    base_cls = str
    _magic = dict(
        strftime=None,
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


def _mkdir_parent(sp):
    if not sp.parent.is_dir() and sp != sp.parent:  # sp == sp.parent if sp is '/'
        print(f'wjkim_Warning: Directory {sp.parent.absolute()} not found.')
        print(f'  Creating {sp.parent.absolute()}  - by mkdir=True')
        sp.parent.mkdir(parents=True)


def _resolve_env_vars(x):
    s = substr(x)
    kwargs = {}
    for key in s.keys:
        kwargs[key] = os.environ.get(key, '')
    return s.s(**kwargs)


def _find_json_path():
    # Find `.wjkim_config.json` -- via `WJKIM_CONFIG_PATH`
    json_dir = os.environ.get('WJKIM_CONFIG_PATH', None)
    if json_dir is not None:
        json_path = _Path(json_dir)
        if json_dir == '':
            print('Warning: `WJKIM_CONFIG_PATH` is an empty string.')
        elif json_path.exists():
            print(f'Warning: `WJKIM_CONFIG_PATH`={json_dir} does not exist.')
        elif json_path.is_dir():
            print('Warning: `WJKIM_CONFIG_PATH` must point to `.wjkim_config.json` file, not its parent directory.')
        elif json_path.is_file():
            print(f'Warning: `WJKIM_CONFIG_PATH`={json_dir} is not a file.')
        else:
            return _Path(json_dir)

    # Find `.wjkim_config.json` -- via `$HOME/bin/others/.wjkim_config.json`
    default_path = _Path.home() / 'bin/others/.wjkim_config.json'
    if default_path.is_file():
        return default_path


def _fillout_constants():
    # Find `.wjkim_config.json`
    if json_path := _find_json_path():
        with open(json_path, 'r') as file:
            dct = json.load(file)
        res_dct = {k: _resolve_env_vars(v) for k, v in dct.items()}
        print(f'{json_path} used for wjkim.pathlib')
        return res_dct    

    # Find `PROJ_DIR` environment variable
    base_dir = os.environ.get('PROJ_DIR', None)
    if not base_dir:
        print('Warning: `wjkim.pathlib` not available.')
        print('  Option 1. Generate `.wjkim_config.json` and save its location to `WJKIM_CONFIG_PATH` environment variable.')
        print('  Option 2. Make `PROJ_DIR` to indicate the location of your project directory.')
        print('For more information, see https://github.com/WooJoongKim0107/wjkim_Basics')
        return {}

    print('Using environment variable `PROJ_DIR` for `wjkim.pathlib`')
    base_path = _Path(base_dir)
    default = dict(
        base=base_path,
        src=base_path/'src',
        log=base_path/'log',
        rsrc=base_path/'rsrc',
        data=base_path/'rsrc'/'data',
        pdata=base_path/'rsrc'/'pdata',
        lite=base_path/'rsrc'/'lite',
    )
    return default


class subpath(substr):
    base_cls = _Path
    _constants = _fillout_constants()
    _restricted = {'mkdir', 'mode', 'buffering', 'encoding', 'errors', 'newline', 'closefd', 'opener'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.keys.isdisjoint(self._restricted):
            msg = f'{self.keys.intersection(self._restricted)} cannot be used. Followings are not allowed:\n'
            msg += f'  {self._restricted}'
            raise ValueError(msg)

    def s(self, *, mkdir=False, **kwargs):
        kwargs = self._constants | kwargs
        sp = super().s(**kwargs)
        if mkdir:
            _mkdir_parent(sp)
        return sp

    def ss(self, **kwargs):
        kwargs = self._constants | kwargs
        return super().ss(**kwargs)

    def o(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None, *, mkdir=False, **kwargs):
        open_kwargs = dict(mode=mode, buffering=buffering, encoding=encoding,
                           errors=errors, newline=newline, closefd=closefd, opener=opener)
        # if self.keys intersects with open_kwargs // or include mkdir, raise error
        x = self.s(**kwargs)
        if mkdir and 'w' in mode:
            _mkdir_parent(x)
        return open(x, **open_kwargs)

    def glob(self, **excludes):
        cls = type(self)
        new = self.ss(**excludes)
        if isinstance(new, self.base_cls):
            res = cls((super().c.sub('*', new.as_posix())))
        elif isinstance(new, cls):
            res = cls((super().c.sub('*', new.template)))
        else:
            raise ValueError(f'Unexpected type from subpath.glob(): {type(new)}')
        kwargs = {key: '*' for key in res.keys}
        return _glob(str(res.s(**kwargs)))

    def explore(self, *targets):
        new = self.ss()
        kwargs = {key: fr'(?P<{key}>[\w.-]+)' for key in new.keys}
        pattern = str(new.s(**kwargs))
        pattern = pattern.replace('*', r'([\w.-]+)')
        pattern = re.sub(r'(?<!\()\?(?!P)', r'([\\w.-])', pattern)  # replace `?` except `(?P<`
        names = new.glob()
        res = {}
        for name in names:
            for key, v in re.match(pattern, name).groupdict().items():
                res.setdefault(key, []).append(v)

        if not targets:
            return res
        if len(targets) == 1:
            return res[targets[0]]
        return {target: res[target] for target in targets}
