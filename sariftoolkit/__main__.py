import os
import logging
import argparse

from sariftoolkit.plugin import loadPlugins
from sariftoolkit.config import Config, load

parser = argparse.ArgumentParser(__name__)
parser.add_argument("--debug", action="store_true")
parser.add_argument("-c", "--config", help="Configuration path")
parser.add_argument("-l", "--list", action="store_true", help="List Plugins")
parser.add_argument("-w", "--working", default=os.getcwd(), help="Working Directory")

parser_sarif = parser.add_argument_group("SARIF")
parser_sarif.add_argument("-s", "--sarif", help="Sarif file or folder")
parser_sarif.add_argument("-o", "--output", help="Output SARIF file or folder")

parser_github = parser.add_argument_group("GitHub")
parser_github.add_argument(
    "--github-workspace",
    default=os.environ.get("GITHUB_WORKSPACE", "./"),
    help="Root GitHub Directory (default: $GITHUB_WORKSPACE)",
)


if __name__ == "__main__":
    plugins = loadPlugins()

    for plugin in plugins:
        parse_group = parser.add_argument_group(f"Plugin - {plugin.name}")
        parse_group.add_argument(f"--enable-{plugin.name.lower()}", action="store_true")

        plugin.arguments(parse_group)

    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if arguments.list:
        print(" ===== Plugins =====")
        for plugin in plugins:
            print(f" >> {plugin}")
        exit(0)

    config = load(arguments.config)

    for plugin in plugins:
        plugin.config.enabled = getattr(arguments, f"enable_{plugin.name.lower()}")

        logging.info(f"Plugin :: {plugin.name} ({plugin.config})")

        if plugin.config.enabled:
            plugin.logger.info(f"Plugin :: {plugin.name} starting...")
            #  Run the plugin
            plugin.run(
                # Arguments
                arguments=arguments,
            )
            plugin.logger.info(f"Plugin :: {plugin.name} finished.")
