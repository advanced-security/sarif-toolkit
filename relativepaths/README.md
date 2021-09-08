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
    # SARIF File / Directory location
    # [optional]: Default: '../results'
    sarif: 'sarif-output.json'
```
