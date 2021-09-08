import logging
from argparse import ArgumentParser
from dataclasses import dataclass

from sariftoolkit.config import Plugins


def _dynamic_import(path: str, class_name: str):
    paths = path.split(".")
    module = __import__(paths[0])
    for p in paths[1:]:
        module = getattr(module, p)
    return getattr(module, class_name)


def loadPlugins():
    plugins = Plugins()

    retval = []
    for key, _ in plugins.__annotations__.items():
        value = plugins.__getattribute__(key)

        clss = _dynamic_import(value.path, value.name)()

        clss.config = getattr(plugins, key)
        # print(f" >> {key} - {clss}")

        retval.append(clss)
    return retval


@dataclass
class Plugin:
    name: str = None
    description: str = None
    version: str = None

    config = None

    logging = None

    def __post_init__(self):
        self.logger = logging.getLogger(f"Plugin-{self.name}")

    def arguments(self, parser: ArgumentParser):
        pass

    def run(self, **kargvs):
        raise Exception("Plugin Sub Class doesn't support a run function...")