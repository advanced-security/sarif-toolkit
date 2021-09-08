# sarif-toolkit - RelativePaths

SARIF Relative Path Patching Tool/Action

## Usage

### Actions

This Action needs to be placed in between the point of the SARIF file(s) being created and uploaded.


**Simple Usage**

```yaml
# ... SARIF file has been created
- uses: GeekMasher/sarif-toolkit/relativepaths@main
# ... SARIF file is being uploaded
```

**Advance config**

```yaml
# 
- uses: GeekMasher/sarif-toolkit/relativepaths@main
  with:
    # Set the Root directory 
    # [optional]: Default: '../results'
    root: '..'
    # SARIF File / Directory location
    # [optional]: Default: Replace input file
    sarif: 'sarif-output.json'
```