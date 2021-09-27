import os
import copy
import gzip
import base64
import subprocess
import urllib.parse
from typing import List
from dataclasses import dataclass
from argparse import ArgumentParser

import requests

from sariftoolkit.plugin import Plugin
from sariftoolkit.sarif.sarif import exportSarif
from sariftoolkit.sarif.models import SarifModel


@dataclass
class SubmoduleModel:
    name: str = None
    url: str = None
    path: str = None
    branch: str = None
    commit: str = None


@dataclass
class Submodules(Plugin):
    name: str = "Submodules"
    version: str = "1.0.0"
    description: str = "Git Submodules Splitter"

    token: str = None
    cleanup: bool = False

    mode: str = "sink"

    def arguments(self, parser: ArgumentParser):
        # parser.add_argument("--submodules-disable-autoremove", action="store_false")
        parser.add_argument(
            "--submodules-disable-cleanup",
            action="store_false",
            help="Disable clean up newly created SARIF files",
        )
        parser.add_argument(
            "--submodules-mode",
            default="sink",
            help="Submodule plugin mode ('sink' or 'path')",
        )

    def run(self, arguments, **kargvs):
        workspace = os.path.abspath(arguments.github_workspace)
        working = os.path.abspath(arguments.working)

        self.token = arguments.github_token
        self.cleanup = arguments.submodules_disable_cleanup
        self.mode = arguments.submodules_mode

        self.logger.debug(f"Git Workspace :: {workspace}")
        self.logger.debug(f"Working :: {working}")

        submodules = self.getSubmodules(workspace)

        if len(submodules) == 0:
            self.logger.warning("No submodules found.")
            return

        self.logger.info("Submodules found:")
        for sub in submodules:
            self.logger.info(f" >> {sub}")

        for sarif, sarif_file in self.loadSarif(arguments.sarif):
            self.processSarif(submodules, sarif, sarif_file)

    def processSarif(
        self,
        submodules: List[SubmoduleModel],
        sarif: SarifModel,
        sarif_file: str,
    ):
        self.logger.info(f"Processing SARIF file: {sarif_file}")

        submodule_sarifs = {}
        for sub in submodules:
            submodule_sarifs[sub.name] = {}

        for run in sarif.runs:
            tool = run.tool.driver
            self.logger.info(f"Processing tool: {tool.name} ({tool.semanticVersion})")

            for result in run.results:
                self.logger.debug(f"Rule('{result.ruleId}')")

                # Modes
                if self.mode == "sink":
                    #  Get the sink of the query
                    location = result.locations[len(result.locations) - 1]

                    uri = location.physicalLocation.artifactLocation.uri
                    self.logger.debug(f"Location('{uri}')")

                    submodule, new_location_uri = self.isFileInSubmodule(
                        submodules, uri
                    )

                    if submodule:
                        self.logger.info(f"Result is in Submodule: {submodule.name}")

                        location.physicalLocation.artifactLocation.uri = (
                            new_location_uri
                        )

                        if not submodule_sarifs[submodule.name].get(result.ruleId):
                            submodule_sarifs[submodule.name][result.ruleId] = []

                        submodule_sarifs[submodule.name][result.ruleId].append(result)

                elif self.mode == "path":
                    #  If any of the locations in the path are in the submodule
                    for location in result.locations:
                        uri = location.physicalLocation.artifactLocation.uri
                        self.logger.debug(f"Location('{uri}')")

                        submodule, new_location_uri = self.isFileInSubmodule(
                            submodules, uri
                        )

                        if submodule:
                            self.logger.info(
                                f"Result is in Submodule: {submodule.name}"
                            )

                            location.physicalLocation.artifactLocation.uri = (
                                new_location_uri
                            )

                            if not submodule_sarifs[submodule.name].get(result.ruleId):
                                submodule_sarifs[submodule.name][result.ruleId] = []

                            submodule_sarifs[submodule.name][result.ruleId].append(
                                result
                            )

                        #  TODO: Pop result if --submodules-disable-autoremove is true
                else:
                    raise Exception(f"Unknown Mode: {self.mode}")

        for name, submodule_locations in submodule_sarifs.items():
            if not submodule_locations:
                continue

            submodule = next((x for x in submodules if x.name == name), None)

            self.logger.info(f"Creating SARIF file for: {name}")
            # Create a deep copy of the SARIF file
            submodule_sarif: SarifModel = copy.copy(sarif)

            for run in submodule_sarif.runs:
                #  Clear the existing results
                run.results.clear()

                for rule_id, results in submodule_locations.items():
                    self.logger.debug(
                        f"New Submodule Result :: {rule_id} ({len(results)})"
                    )

                    run.results.extend(results)

            submod_file = self.createSubmoduleFileName(name, sarif_file)
            exportSarif(submod_file, submodule_sarif)

            self.publishSarifFile(submodule, submodule_sarif, sarif_file=submod_file)

            if self.cleanup:
                self.logger.info(f"Cleaning up SARIF file: {submod_file}")
                os.remove(submod_file)

    def createSubmoduleFileName(self, name: str, sarif_file: str):
        file_name, file_ext = os.path.splitext(sarif_file)

        return f"{file_name}-{name}{file_ext}"

    def isFileInSubmodule(self, submodules: List[SubmoduleModel], file: str):
        for sub in submodules:
            if file.startswith(sub.path):
                new_path = file.replace(sub.path + "/", "", 1)
                return (sub, new_path)
        return (None, None)

    def getSubmodules(self, workspace: str):
        subs = []
        command = ["git", "submodule", "status", "--recursive"]
        result = subprocess.run(command, stdout=subprocess.PIPE, cwd=workspace)
        data = result.stdout.decode().split("\n")

        for line in data:
            line = line.strip()
            if line == "" or line.startswith("-") or line.startswith("+"):
                continue

            sha, path, status = line.split(" ")
            name = os.path.basename(path)
            full_path = os.path.join(workspace, path)
            url = self.getGitRemoteUrl(full_path)

            if not url.scheme and not url.netloc:
                #  Assume SSH like URL...
                _, giturl = url.path.split(":")
            else:
                giturl = url.path.replace("/", "", 1)

            giturl = giturl.replace(".git", "")

            submodule = SubmoduleModel(
                name=name,
                url=giturl,
                path=path,
                branch="refs/" + status.replace("(", "").replace(")", ""),
                commit=sha,
            )

            subs.append(submodule)

        return subs

    def getGitRemoteUrl(self, path: str):
        self.logger.debug(f"Git Remote Path :: {path}")

        command = ["git", "config", "--get", "remote.origin.url"]
        result = subprocess.run(command, stdout=subprocess.PIPE, cwd=path)
        url = result.stdout.decode().strip()

        return urllib.parse.urlparse(url)

    def packageSarif(self, path: str):
        if os.path.exists(path):
            with open(path, "rb") as handle:
                content = gzip.compress(handle.read())
            return base64.b64encode(content).decode()

    def publishSarifFile(
        self,
        submodule: SubmoduleModel,
        sarif: SarifModel,
        sarif_file: str,
        instance: str = "https://github.com",
    ):
        if not self.token:
            self.logger.warning("Failed to find access token, skipping publishing...")
            return

        self.logger.info(f"Publishing SARIF to submodule: {submodule.name}")
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token " + self.token,
        }
        owner, repo = submodule.url.split("/")
        if instance == "https://github.com":
            api_instance = "https://api.github.com"
        else:
            api_instance = instance + "/api"

        url = f"{api_instance}/repos/{owner}/{repo}/code-scanning/sarifs"
        self.logger.debug(f"Publishing SARIF file to endpoint: {url}")

        data = {
            "commit_sha": submodule.commit,
            "ref": submodule.branch,
            "sarif": self.packageSarif(sarif_file),
            "tool_name": sarif.runs[0].tool.driver.name,
        }

        res = requests.post(url, json=data, headers=headers)

        self.logger.info("Uploaded SARIF file to submodule")
