# sarif-toolkit - RelativePaths

SARIF Relative Path Patching Tool/Action.

This tools allows users to update broken SARIF files that have relative paths that aren't based on the root GitHub Repository folder.

## Example / Use Case

You have a tool that you using for security scanning and point it to a sub folder of the repository.
This SARIF uploaded in this state will cause an issue rendering in the GitHub Advanced Security Code Scanning UI (file not found).

This sub folder path needs to be updates to add the relative path from the GitHub Actions workspace path.


## Usage

### Actions

This Action needs to be placed in between the point of the SARIF file(s) being created and uploaded.


**Simple Usage**

```yaml
# ... SARIF file has been created
- uses: advanced-security/sarif-toolkit/relativepaths@main
# ... SARIF file is being uploaded
```

**Advance config**

```yaml
# 
- uses: advanced-security/sarif-toolkit/relativepaths@main
  with:
    # SARIF File / Directory location
    # [optional]: Default: '../results'
    sarif: 'sarif-output.json'
    # Working Directory (sub folder of the working directory)
    # [optional]: Default: '.' (current working directory)
    working: '.'
```
