from dataclasses import dataclass
import os
import json
from sariftoolkit.plugin import Plugin


@dataclass
class RelativePaths(Plugin):
    name: str = "RelativePaths"
    version: str = "1.0.0"
    description: str = "Patching Relative SARIF paths"

    def run(self, arguments, **kargvs):
        workspace = os.path.abspath(arguments.github_workspace)
        working = os.path.abspath(arguments.working)

        if workspace and not os.path.exists(workspace):
            raise Exception(f"Root path provided does not exist: {workspace}")

        self.logger.info(f"Root Path    :: {workspace}")
        self.logger.info(f"Working Path :: {working}")
        self.logger.info(f"Sarif Path   :: {arguments.sarif}")

        if working == workspace:
            self.logger.warning(
                f"Working path is the same as root path. This is not recommended."
            )
            return

        difference = os.path.relpath(working, workspace)
        self.logger.info(f"Difference in paths :: {difference}")

        if os.path.isdir(arguments.sarif):
            for file in os.listdir(arguments.sarif):
                file_path = os.path.abspath(os.path.join(arguments.sarif, file))
                _, extention = os.path.splitext(file)

                if extention in [".json", ".sarif"]:

                    sarif = self.processSarifFile(
                        difference, os.path.join(arguments.sarif, file)
                    )

                    if arguments.output and arguments.output != "":
                        output = os.path.join(arguments.output, file)
                    else:
                        self.logger.info("Replacing existing SARIF file")
                        output = file_path

                    self.writeSarif(output, sarif)
        else:
            if arguments.output and arguments.output != "":
                output = os.path.abspath(arguments.output)
            else:
                self.logger.info("Replacing existing SARIF file")
                output = arguments.sarif

            sarif = self.processSarifFile(difference, arguments.sarif)

            self.writeSarif(output, sarif)

    def writeSarif(self, path: str, data: dict):
        self.logger.info(f"Writing SARIF File: {path}")
        with open(path, "w") as handle:
            json.dump(data, handle, indent=2)

    def updateLocation(self, location, root) -> dict:
        uri = (
            location.get("physicalLocation", {}).get("artifactLocation", {}).get("uri")
        )

        new_location = location.copy()

        if uri:
            new_uri = f"{root}/{uri}"

            self.logger.debug(f"Update: {uri} => {new_uri}")

            new_location["physicalLocation"]["artifactLocation"]["uri"] = new_uri
        return new_location

    def processSarifFile(self, root: str, path: str):
        self.logger.info(f"Processing SARIF File: {path}")
        if not os.path.exists(path):
            raise Exception("Sarif file does not exist")

        with open(path) as handle:
            sarif = json.load(handle)

        for run in sarif.get("runs", []):
            tool = run.get("tool", {}).get("driver", {})
            self.logger.info(
                "Processing tool: {name} ({version})".format(
                    name=tool.get("name"), version=tool.get("semanticVersion", "NA")
                )
            )

            new_results = []

            for result in run.get("results", []):
                self.logger.debug(f"Rule({result.get('ruleId')})")

                # Locations
                new_locations = []
                for location in result.get("locations", []):
                    #  https://github.com/microsoft/sarif-tutorials/blob/main/docs/2-Basics.md#-linking-results-to-artifacts
                    new_location = self.updateLocation(location, root)
                    new_locations.append(new_location)

                if new_locations:
                    result["locations"] = new_locations
                    new_results.append(result)

                # Code Flows
                for flow in result.get("codeFlows", []):
                    for flow_step in flow.get("threadFlows", []):
                        new_locations = []
                        for location in flow_step.get("locations", []):
                            new_location = self.updateLocation(
                                location.get("location"), root
                            )

                            new_locations.append({"location": new_location})

                        if new_locations:
                            flow_step["locations"] = new_locations

            if new_results:
                run["results"] = new_results

        return sarif
