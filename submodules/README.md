# sarif-toolkit - Submodules

SARIF Submodules Tool/Action.

This tools allows users to split up SARIF files that use submodules for the SARIF files to be pushed to the appropriate repositories.

## Example / Use Case

Your repository has a submodule called "core" which is pulled into your CI for building or publishing code.
Your security scanning tool takes all the code present in the repository or at build time and discovers security issues that end up in "core".

Example: `SQL Injection sink in "core"`

You want to publish bad your results to the "core" team that develops that code base.


## Usage

### Actions

This Action needs to be placed in between the point of the SARIF file(s) being created and uploaded.


**Simple Usage**

```yaml
# ... SARIF file has been created
- uses: GeekMasher/sarif-toolkit/submodules@main
# ... SARIF file is being uploaded
```

**Advance config**

```yaml
# 
- uses: GeekMasher/sarif-toolkit/submodules@main
  with:
    # SARIF File / Directory location
    # [optional]: Default: '../results'
    sarif: 'sarif-output.json'
    # Working Directory (sub folder of the working directory)
    # [optional]: Default: '.' (current working directory)
    working: '.'
```
