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
