import os
import logging
import subprocess
import urllib.parse
from typing import List
from dataclasses import dataclass

from sariftoolkit.plugin import Plugin
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

    def run(self, arguments, **kargvs):
        workspace = os.path.abspath(arguments.github_workspace)
        working = os.path.abspath(arguments.working)

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
        self, submodules: List[SubmoduleModel], sarif: SarifModel, sarif_file: str
    ):
        self.logger.info(f"Processing SARIF file: {sarif_file}")

        submodule_sarif = {}
        for sub in submodules:
            submodule_sarif[sub.name] = []

        for run in sarif.runs:
            tool = run.tool.driver
            self.logger.info(f"Processing tool: {tool.name} ({tool.semanticVersion})")

            for result in run.results:
                self.logger.debug(f"Rule('{result.ruleId}')")

                for location in result.locations:
                    uri = location.physicalLocation.artifactLocation.uri
                    self.logger.debug(f"Location('{uri}')")

                    submodule = self.isFileinSubmodule(submodules, uri)
                    if submodule:
                        self.logger.debug(f"Result is in Submodule: {submodule}")

                        #  TODO: add result to submodule_sarif

        return

    def isFileinSubmodule(self, submodules: List[SubmoduleModel], file: str):
        for sub in submodules:
            if file.startswith(sub.path):
                return sub
        return None

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
