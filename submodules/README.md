# sarif-toolkit - Submodules

SARIF Submodules Tool/Action.

This tools allows users to split up SARIF files that use submodules into multiple SARIF files that are then published to there appropriate repositories.

## Example / Use Case

Your repository has a submodule called "core" which is either a git submodule or pulled into your CI at runtime to build the full code base.
Your security scanning tool takes all the code present in the repository or at build time and discovers security issues that end up in "core".

Example: `SQL Injection sink in "core"`

You want to publish bad your results to the "core" team that develops that code base.


## Usage

### Actions

This Action needs to be placed in between the point of the SARIF file(s) being created and uploaded.


**Simple Usage**

```yaml
# ... SARIF file has been created
- uses: advanced-security/sarif-toolkit/submodules@main
# ... SARIF file is being uploaded
```

**Advance config**

```yaml
# 
- uses: advanced-security/sarif-toolkit/submodules@main
  with:
    # SARIF File / Directory location
    # [optional]: Default: '../results'
    sarif: 'sarif-output.json'
    # Working Directory (sub folder of the working directory)
    # [optional]: Default: '.' (current working directory)
    working: '.'
    # Mode for how detecting SARIF result locations are located and how they 
    #  should be reported.
    # 'sink': Only split on sink being in the submodule
    # 'path': If any location is in the SARIF file
    # [optional]: Default: 'sink'
    mode: 'sink'
```
