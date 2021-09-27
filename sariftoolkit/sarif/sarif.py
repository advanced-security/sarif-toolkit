import os
import json
from dataclasses import dataclass, field, asdict
import logging
from typing import List, Any

from sariftoolkit.utils.dataclasses import _dataclass_from_dict
from sariftoolkit.sarif.models import *


logger = logging.getLogger("sarif")


def loadSarif(path: str):
    path = os.path.abspath(path)
    logger.info(f"Loading SARIF File: '{path}'")
    with open(path, "r") as handle:
        sarif_dict = json.load(handle)

    return _dataclass_from_dict(SarifModel, sarif_dict)


def exportSarif(path: str, sarif: SarifModel):
    def _exportAsDict(obj):
        data = asdict(obj)

        if hasattr(obj, "__holders__"):
            for key, value in obj.__holders__.items():
                if value in data:
                    data[key] = data[value]
                    data.pop(value)

        return data

    path = os.path.abspath(path)
    logger.info(f"Exporting SARIF File: '{path}'")

    with open(path, "w") as handle:
        json.dump(_exportAsDict(sarif), handle, indent=4)
