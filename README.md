<div align="center">
<h1>SARIF Toolkit</h1>

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/advanced-security/sarif-toolkit)
[![GitHub Issues](https://img.shields.io/github/issues/advanced-security/sarif-toolkit?style=for-the-badge)](https://github.com/advanced-security/sarif-toolkit/issues)
[![GitHub Stars](https://img.shields.io/github/stars/advanced-security/sarif-toolkit?style=for-the-badge)](https://github.com/advanced-security/sarif-toolkit)
[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

</div>

All things SARIF, as an Action

## ⚡️ Requirements

- [Python][python] >= `3.9`

## Plugins

Plugins are simple utilities built into the toolkit to provide functionality.

### [Relative Path Patcher](./relativepaths/README.md)

Patches SARIF result files from the relative working directory path to the Actions / root workspace of the repository.

### [Submodules Splitter](./submodules/README.md)

This tools allows users to split up SARIF files that use submodules into multiple SARIF files that are then published to there appropriate repository.

## Support

Please create issues for any feature requests, bugs, or documentation problems.

## Acknowledgement

- @GeekMasher - Author and Maintainer

## License

This project is licensed under the terms of the MIT open source license.
Please refer to [MIT](./LICENSE.md) for the full terms.

<!-- resources / references -->

[python]: https://www.python.org/