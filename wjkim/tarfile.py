import tarfile as _tarfile
from collections.abc import Iterable
from functools import cached_property
from pathlib import Path
from .pathlib import s


def tar(tar_name, mode='r', keep=False):
    assert mode in ['r', 'w', 'a']
    tar_path = s(tar_name)
    if mode == 'r':
        return TarRead(tar_path, mode=mode)
    return TarWrite(tar_path, mode=mode, keep=keep)


class TarWrite:
    def __init__(self, tar_path: Path, mode='w', keep=False):
        assert mode in ['w', 'a']
        self.tar_path = tar_path
        self.mode = mode
        self.keep = keep
        self.tar_file: None | _tarfile.TarFile = None
        self._mem_paths = []  # list[Path]

    def extend(self, mem_paths: Iterable[Path]):
        for path in mem_paths:
            self.append(path)

    def append(self, mem_path: Path):
        self.tar_file.add(mem_path, arcname=mem_path.name)
        self._mem_paths.append(mem_path)

    def _unlink(self):
        for path in self._mem_paths:
            path.unlink()
        self._mem_paths.clear()

    def _close(self):
        self.tar_file.close()
        self.tar_file = None

    def __enter__(self):
        self.tar_file = _tarfile.open(self.tar_path, mode=self.mode)
        return self

    def __exit__(self, typ, value, trace_back):
        self._close()
        if (typ is None) and (value is None) and (trace_back is None):
            if not self.keep:
                self._unlink()
            else:
                self._mem_paths.clear()


class TarRead:
    def __init__(self, tar_path, mode='r'):
        self.tar_path = tar_path
        self.mode = mode
        self.tar_file: None | _tarfile.TarFile = None
        self._mem_files = []

    def get(self, mem_name: str):  # -> File
        member = self.tar_file.getmember(mem_name)
        f = self.tar_file.extractfile(member)
        self._mem_files.append(f)
        return f

    def __iter__(self):  # -> Iterator[File]
        return (self.get(member) for member in self.tar_file.getnames())

    def __getitem__(self, item):  # -> File or list[File]
        if isinstance(item, slice):
            return [self.get(name) for name in self.mem_names[item]]
        else:
            return self.get(self.mem_names[item])

    @cached_property
    def mem_names(self):  # list[str]
        return self.tar_file.getnames()

    @property
    def mem_paths(self):
        return [self.tar_path.parent / name for name in self.mem_names]

    def _close(self):
        self.tar_file.close()
        self.tar_file = None
        for file in self._mem_files:
            file.close()
        self._mem_files.clear()

    def __enter__(self):
        self.tar_file = _tarfile.open(self.tar_path, mode=self.mode)
        _ = self.mem_names
        return self

    def __exit__(self, typ, value, trace_back):
        self._close()


if __name__ == '__main__':
    import pickle
    import wjkim as wj
    """
    Writing 
        1. Make individual files first
        2. Tar later
            2.A. mode='w'  : Create new tar file
            2.B. mode='a'  : Append to existing tar file (create new if not exist)
            
            2.a. keep=False: individual files will be lost (default)
            2.b. keep=True : individual files will be kept
    """
    # 1. Make individual files
    for n in range(10):
        with wj.o(f'$rsrc/test_{n}.pkl', 'wb') as file:
            pickle.dump(list(range(n)), file)

    # 2.A.b. Create new tar file while keeping individual files
    with tar('$rsrc/Test_alpha.tar', 'w', keep=True) as tf:
        for n in range(10):
            tf.append(wj.s(f'$rsrc/test_{n}.pkl'))

    # 2.B.a. Append to existing tar file and erase individual files
    with tar('$rsrc/Test_alpha.tar', 'a', keep=False) as tf:
        for n in range(10, 20):
            with wj.o(f'$rsrc/test_{n}.pkl', 'wb') as file:
                pickle.dump(list(range(n)), file)
            tf.append(wj.s(f'$rsrc/test_{n}.pkl'))

    # 2.A.b. Archive while loosing individual files (default)
    with tar('$rsrc/Test_bravo.tar', 'w', keep=False) as tf:
        paths = [wj.s(f'$rsrc/test_{n}.pkl') for n in range(10)]
        tf.extend(paths)

    """
    Reading
        a. tf.__iter__()       :  Iterate over all files
        b. tf.__getitem__(item):  Access by index or slice
        c. tf.get(name)        :  Access by file name
        
        d. tf.mem_names        :  List of all file names
        e. tf.mem_paths        :  List of all file paths
    """
    with tar('$rsrc/Test_alpha.tar', 'r') as tf:
        for file in tf:
            print(pickle.load(file))
        print()
        for file in tf[::2]:
            print(pickle.load(file))
        print()
        print(pickle.load(tf[13]))
        print()

    with tar('$rsrc/Test_bravo.tar', 'r') as tf:
        print(tf.mem_names)
        print(tf.mem_paths)
        print(pickle.load(tf.get('test_3.pkl')))
