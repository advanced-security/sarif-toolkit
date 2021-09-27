# sarif-toolkit
All things SARIF, as an Action


## Plugins

Plugins are simple utilities built into the toolkit to provide functionality.

### [Relative Path Patcher](./relativepaths/README.md)

Patches SARIF result files from the relative working directory path to the Actions / root workspace of the repository.

### [Submodules Splitter](./submodules/README.md)

This tools allows users to split up SARIF files that use submodules into multiple SARIF files that are then published to there appropriate repositories.
