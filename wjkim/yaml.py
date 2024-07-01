from omegaconf import OmegaConf, DictConfig
from .pathlib import subpath

Config = DictConfig | dict | list | str


def manager(filepath):
    filepath = subpath.s(filepath)
    directory = filepath.parents[0]
    q = OmegaConf.load(filepath)
    confs = [OmegaConf.create({key: OmegaConf.load(directory/key/target)}) for key, target in q.items()]
    return OmegaConf.merge(*confs)


def print_conf(conf: Config):
    conf = OmegaConf.create(conf)
    print(OmegaConf.to_yaml(conf))
