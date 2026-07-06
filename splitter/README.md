# sarif-toolkit - Splitter

SARIF File Splitter Plugin for categorizing alerts into separate SARIF files.

This plugin allows you to split large SARIF files into smaller, categorized files based on file paths or security severity levels. This can help with:
- Overcoming upload size restrictions in GitHub Advanced Security 
- Organizing alerts by application areas (tests, frontend, backend, etc.)
- Prioritizing security reviews by severity levels
- Improving dashboard search and filtering capabilities

## Features

- **Path-based splitting**: Split alerts by file path patterns using glob matching
- **Severity-based splitting**: Split alerts by security severity levels (critical, high, medium, low)
- **GitHub Advanced Security integration**: Automatically sets `runAutomationDetails.id` for proper categorization
- **No alert loss**: Unmatched alerts are preserved in fallback categories
- **Configurable rules**: Support for JSON configuration files or sensible defaults
- **Flexible naming**: Category names follow GitHub Advanced Security conventions

## Usage

### Actions

This Action needs to be placed in between the point where SARIF file(s) are created and where they are uploaded.

**Simple Path-based Usage**

```yaml
# ... SARIF file has been created
- uses: advanced-security/sarif-toolkit/splitter@main
  with:
    sarif: 'results.sarif'
    split-by-path: true
    language: 'javascript'
# ... Split SARIF files are being uploaded
```

**Simple Severity-based Usage**

```yaml
# ... SARIF file has been created  
- uses: advanced-security/sarif-toolkit/splitter@main
  with:
    sarif: 'results.sarif'
    split-by-severity: true
    language: 'python'
# ... Split SARIF files are being uploaded
```

**Advanced Configuration**

```yaml
- uses: advanced-security/sarif-toolkit/splitter@main
  with:
    # SARIF File / Directory location
    sarif: 'sarif-output.json'
    # Output directory for split files
    output: './split-results'
    # Split by file paths
    split-by-path: true
    # Split by security severity
    split-by-severity: true  
    # Programming language for categories
    language: 'java'
    # Custom path configuration
    path-config: 'path-rules.json'
    # Custom severity configuration  
    severity-config: 'severity-rules.json'
```

### Command Line

**Basic usage:**

```bash
# Split by file paths
python -m sariftoolkit --enable-splitter --split-by-path --language python --sarif results.sarif

# Split by severity levels
python -m sariftoolkit --enable-splitter --split-by-severity --language javascript --sarif results.sarif

# Split by both methods
python -m sariftoolkit --enable-splitter --split-by-path --split-by-severity --language java --sarif results.sarif --output ./split-output
```

**With custom configuration:**

```bash
python -m sariftoolkit --enable-splitter \
  --split-by-path \
  --split-by-severity \
  --language csharp \
  --sarif results.sarif \
  --path-config examples/splitter-configs/path-rules.json \
  --severity-config examples/splitter-configs/severity-rules.json \
  --output ./categorized-results
```

## Configuration

### Path Rules Configuration

Path rules use glob patterns to match file paths. Example `path-rules.json`:

```json
{
  "path_rules": [
    {
      "name": "Tests",
      "patterns": [
        "**/test/**",
        "**/tests/**", 
        "**/*test*"
      ]
    },
    {
      "name": "Frontend",
      "patterns": [
        "**/web/**",
        "**/client/**",
        "**/*.js",
        "**/*.jsx"
      ]
    },
    {
      "name": "Backend", 
      "patterns": [
        "**/api/**",
        "**/server/**",
        "**/*.py",
        "**/*.java"
      ]
    }
  ]
}
```

### Severity Rules Configuration

Severity rules group security severity levels. Example `severity-rules.json`:

```json
{
  "severity_rules": [
    {
      "name": "Critical",
      "severities": ["critical"]
    },
    {
      "name": "High-Medium",
      "severities": ["high", "medium"]
    },
    {
      "name": "Others",
      "severities": ["*"]
    }
  ]
}
```

### Default Rules

**Default Path Rules:**
- `Tests`: `**/test/**`, `**/tests/**`, `**/*test*`
- `App`: `**/web/**`, `**/api/**`, `**/src/**`, `**/app/**`

**Default Severity Rules:**
- `Critical`: security-severity ≥ 9.0
- `High-Medium`: security-severity 4.0-8.9  
- `Others`: All remaining (catch-all)

## Output Categories

### Path-based Categories
- `/language:<language>/category:<category-name>` - For matched path patterns
- `/language:<language>/filter:none` - For unmatched files

### Severity-based Categories  
- `/language:<language>/severity:<severity-name>` - For matched severity levels
- `/language:<language>/severity:Others` - For unmatched severities

These category names are compatible with GitHub Advanced Security's `runAutomationDetails.id` field for proper dashboard organization.

## Example Use Cases

### Large Repository Splitting
```bash
# Split a large SARIF file by application areas
python -m sariftoolkit --enable-splitter \
  --split-by-path \
  --language typescript \
  --sarif large-codeql-results.sarif \
  --output ./team-specific-results
```

### Security Triage Workflow
```bash
# Split by severity for security team triage
python -m sariftoolkit --enable-splitter \
  --split-by-severity \
  --language csharp \
  --sarif security-scan.sarif \
  --output ./security-triage
```

### Multi-dimensional Splitting
```bash
# Create both path and severity splits
python -m sariftoolkit --enable-splitter \
  --split-by-path \
  --split-by-severity \
  --language python \
  --sarif comprehensive-scan.sarif \
  --output ./organized-results
```

## Notes

- The splitter preserves all SARIF metadata including tool information, rules, and notifications
- No alerts are ever dropped - unmatched alerts go to fallback categories
- Multiple splitting methods can be used simultaneously
- Output filenames follow the pattern: `{original-name}-{method}-{category}.sarif`
- Categories are URL-safe and compatible with GitHub Advanced Security requirements