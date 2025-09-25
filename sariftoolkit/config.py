from dataclasses import dataclass, field


@dataclass
class PluginConfig:
    name: str
    path: str = None
    enabled: bool = False


@dataclass
class Plugins:
    relativepaths: PluginConfig = field(default_factory=lambda: PluginConfig(
        "RelativePaths", "sariftoolkit.plugins.relativepaths"
    ))

    submodules: PluginConfig = field(default_factory=lambda: PluginConfig(
        "Submodules", "sariftoolkit.plugins.submodules"
    ))

    splitter: PluginConfig = field(default_factory=lambda: PluginConfig(
        "Splitter", "sariftoolkit.plugins.splitter"
    ))


@dataclass
class Config:
    name: str = "Default Configuration"
    version: str = "0.0.0"

    plugins: Plugins = field(default_factory=Plugins)


def load(path: str) -> Config:
    config = Config()

    return config
