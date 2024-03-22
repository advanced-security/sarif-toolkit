import os
import copy
import gzip
import base64
import subprocess
import urllib.parse
import yaml 
from typing import List
from dataclasses import dataclass
from argparse import ArgumentParser

import requests

from sariftoolkit.plugin import Plugin
from sariftoolkit.sarif.sarif import exportSarif
from sariftoolkit.sarif.models import SarifModel


@dataclass
class SubfolderModel:
    name: str = None
    url: str = None
    path: str = None
    token: str = None


@dataclass
class Subfolders(Plugin):
    name: str = "Subfolders"
    version: str = "1.0.0"
    description: str = "Git Subfolder Splitter"

    token: str = None
    cleanup: bool = False
    # of type SubfolderModel
    config_file = [] 

    mode: str = "sink"

    def arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--config-file",
            help="The relative path to the configuration file",
        )

        parser.add_argument(
            "--subfolder-disable-cleanup",
            action="store_false",
            help="Disable clean up newly created SARIF files",
        )
        parser.add_argument(
            "--subfolder-mode",
            default="sink",
            help="Subfolder plugin mode ('sink' or 'path')",
        )

    def run(self, arguments, **kargvs):
        workspace = os.path.abspath(arguments.github_workspace)
        working = os.path.abspath(arguments.working)

        self.token = arguments.github_token
        self.cleanup = arguments.subfolder_disable_cleanup
        self.mode = arguments.subfolder_mode
        self.config_file = arguments.config_file
        self.sarif_path = arguments.sarif

        #  Load the configuration file
        with open(self.config_file) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        self.logger.debug(f"Git Workspace :: {workspace}")
        self.logger.debug(f"Working :: {working}")
        self.logger.info(f"config :: {config}")

        
        for sarif, sarif_file in self.loadSarif(self.sarif_path):
            self.processSarif(config, sarif, sarif_file)

    def processSarif(
        self,
        subfolder_structured: List[SubfolderModel],
        sarif: SarifModel,
        sarif_file: str,
    ):
        self.logger.info(f"Processing SARIF file: {sarif_file}")

        subfolder_sarifs = {}
        for sub in subfolder_structured:
            subfolder_sarifs[sub["name"]] = {}

        for run in sarif.runs:
            print("-----------SARIF -----------")
            tool = run.tool.driver
            self.logger.info(f"Processing tool: {tool.name} ({tool.semanticVersion})")

            for result in run.results:
                self.logger.debug(f"Rule('{result.ruleId}')")

                # Modes
                if self.mode == "sink":
                    #  Get the sink of the query
                    location = result.locations[len(result.locations) - 1]

                    uri = location.physicalLocation.artifactLocation.uri

                    subfolder, new_location_uri = self.isFileInSubfolder(
                        subfolder_structured, uri
                    )

                    if subfolder:
                        location.physicalLocation.artifactLocation.uri = (
                            new_location_uri
                        )
                        
                        if not subfolder_sarifs[subfolder['name']].get(result.ruleId):
                            subfolder_sarifs[subfolder['name']][result.ruleId] = []

                        subfolder_sarifs[subfolder['name']][result.ruleId].append(result)

                elif self.mode == "path":
                    #  If any of the locations in the path are in the subfolder
                    for location in result.locations:
                        uri = location.physicalLocation.artifactLocation.uri
                        self.logger.debug(f"Location('{uri}')")

                        subfolder, new_location_uri = self.isFileInSubfolder(
                            subfolder_structured, uri
                        )

                        if subfolder:
                            location.physicalLocation.artifactLocation.uri = (
                                new_location_uri
                            )

                            if not subfolder_sarifs[subfolder['name']].get(result.ruleId):
                                subfolder_sarifs[subfolder['name']][result.ruleId] = []

                            subfolder_sarifs[subfolder['name']][result.ruleId].append(
                                result
                            )

                        #  TODO: Pop result if --subfolders-disable-autoremove is true
                else:
                    raise Exception(f"Unknown Mode: {self.mode}")

        for name, subfolder_locations in subfolder_sarifs.items():
            if not subfolder_locations:
                continue

            self.logger.info(f"Subfolder: {name} || {subfolder}")
            subfolder = next((x for x in subfolder_structured if x['name'] == name), None)

            self.logger.info(f"Creating SARIF file for: {name}")
            # Create a deep copy of the SARIF file
            subfolder_sarif: SarifModel = copy.copy(sarif)

            for run in subfolder_sarif.runs:
                #  Clear the existing results
                run.results.clear()

                for rule_id, results in subfolder_locations.items():
                    self.logger.debug(
                        f"New subfolder Result :: {rule_id} ({len(results)})"
                    )

                    run.results.extend(results)

            submod_file = self.createsubfolderFileName(name, sarif_file)
            exportSarif(submod_file, subfolder_sarif)

            self.publishSarifFile(subfolder, subfolder_sarif, sarif_file=submod_file)

            if self.cleanup:
                self.logger.info(f"Cleaning up SARIF file: {submod_file}")
                os.remove(submod_file)

    def createsubfolderFileName(self, name: str, sarif_file: str):
        file_name, file_ext = os.path.splitext(sarif_file)

        return f"{file_name}-{name}{file_ext}"

    def isFileInSubfolder(self, structure: List[SubfolderModel], file: str):
        for sub in structure:
            path = sub["path"]
            if file.startswith(sub["path"]):
                new_path = file.replace(path + "/", "", 1)
                return (sub, new_path)
        return (None, None)

    def getsubfolders(self, workspace: str):
        subs = []
        command = ["git", "subfolder", "status", "--recursive"]
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

            subfolder = SubfolderModel(
                name=name,
                url=giturl,
                path=path,
                branch="refs/" + status.replace("(", "").replace(")", ""),
                commit=sha,
            )

            subs.append(subfolder)

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
        subfolder: SubfolderModel,
        sarif: SarifModel,
        sarif_file: str,
        instance: str = "https://github.com",
    ):
        if not self.token:
            self.logger.warning("Failed to find access token, skipping publishing...")
            return

        self.logger.info(f"Publishing SARIF to subfolder: {subfolder.name}")
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token " + self.token,
        }
        owner, repo = subfolder.url.split("/")
        if instance == "https://github.com":
            api_instance = "https://api.github.com"
        else:
            api_instance = instance + "/api"

        url = f"{api_instance}/repos/{owner}/{repo}/code-scanning/sarifs"
        self.logger.debug(f"Publishing SARIF file to endpoint: {url}")

        data = {
            "commit_sha": subfolder.commit,
            "ref": subfolder.branch,
            "sarif": self.packageSarif(sarif_file),
            "tool_name": sarif.runs[0].tool.driver.name,
        }

        res = requests.post(url, json=data, headers=headers)

        self.logger.info("Uploaded SARIF file to subfolder")
