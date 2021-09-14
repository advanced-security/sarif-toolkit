import os
import json
import logging
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Tuple

from sariftoolkit.config import Plugins
from sariftoolkit.sarif.sarif import loadSarif


def _dynamic_import(path: str, class_name: str):
    paths = path.split(".")
    try:
        module = __import__(paths[0])
        for p in paths[1:]:
            module = getattr(module, p)
        return getattr(module, class_name)

    except Exception as err:
        logging.error(f"Failed to import {path}")


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

    def loadSarif(self, path: str):
        if not os.path.exists(path):
            raise Exception(f"{path} doesn't exist")

        sarif_files = []

        if os.path.isdir(path):
            for file in os.listdir(path):
                file_path = os.path.abspath(os.path.join(path, file))
                _, extention = os.path.splitext(file)

                if extention in [".json", ".sarif"]:

                    sarif_model = loadSarif(file_path)

                    sarif_files.append((sarif_model, file_path))
        else:

            _, extention = os.path.splitext(path)
            if extention in [".json", ".sarif"]:

                sarif_model = loadSarif(path)

                sarif_files.append((sarif_model, path))

        return sarif_files
