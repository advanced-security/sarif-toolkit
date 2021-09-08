from dataclasses import dataclass


@dataclass
class PluginConfig:
    name: str
    path: str = None
    enabled: bool = False


@dataclass
class Plugins:
    relativepaths: PluginConfig = PluginConfig(
        "RelativePaths", "sariftoolkit.plugins.relativepaths"
    )


@dataclass
class Config:
    name: str = "Default Configuration"
    version: str = "0.0.0"

    plugins: Plugins = Plugins()


def load(path: str) -> Config:
    config = Config()

    return config
