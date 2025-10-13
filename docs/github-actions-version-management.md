# GitHub Actions Version Management

This project uses a simple shell-based approach to enforce consistent GitHub Actions versions across all workflow files.

## How It Works

### 1. Version Configuration
All approved action versions are defined in `.github/action-versions.conf`:

```
actions/checkout: v5
aws-actions/configure-aws-credentials: v4  
hashicorp/setup-terraform: v3
actions/cache: v4
actions/github-script: v7
actions/setup-node: v4
actions/setup-python: v5
```

### 2. Validation Script
The `scripts/validate-actions.sh` script:
- ✅ Reads the approved versions from the config file
- ✅ Scans all workflow files in `.github/workflows/`
- ✅ Validates that each `uses:` statement matches the approved version
- ✅ Provides clear error messages for version mismatches
- ✅ Optionally checks YAML syntax (if `yq` is installed)

### 3. Make Targets
Convenient commands available:

```bash
# Validate all workflow files
make validate-actions

# Install git pre-commit hooks
make install-git-hooks

# Remove git hooks
make uninstall-git-hooks
```

## Usage

### Manual Validation
```bash
# Check all workflow files
make validate-actions

# Direct script usage
./scripts/validate-actions.sh
```

### Automatic Validation with Git Hooks
```bash
# Install pre-commit hook
make install-git-hooks

# Now every commit will validate action versions
git commit -m "update workflow"
```

### Example Output

**✅ Success:**
```
🔍 GitHub Actions Version Validator
==================================================
ℹ️  Loaded 7 approved action versions  
ℹ️  Validating .github/workflows/ci.yml
✅ .github/workflows/ci.yml: Action 'actions/checkout@v5' ✓
✅ All 2 workflow files passed validation! 🎉
```

**❌ Version Mismatch:**
```
❌ .github/workflows/ci.yml: Action 'actions/checkout' uses version 'v4' but expected 'v5'
❌ Found 1 version violations in 2 workflow files

💡 To fix these issues:
   1. Update the workflow files to use approved versions
   2. Or update .github/action-versions.conf if new versions are approved
   3. Run 'make validate-actions' to re-check
```

## Updating Approved Versions

1. Edit `.github/action-versions.conf`
2. Add or update action versions using the format: `action/name: version`
3. Run `make validate-actions` to verify all workflows comply
4. Commit the changes

## Benefits

- 🚀 **Simple**: No external dependencies (just bash)
- ⚡ **Fast**: Quick validation using regex parsing
- 🔒 **Enforced**: Pre-commit hooks prevent inconsistent versions
- 📋 **Clear**: Easy-to-read configuration file
- 🛠️ **Maintainable**: Single source of truth for all action versions
- 🎯 **Focused**: Purpose-built for action version management

## Installation Requirements

- Bash shell
- `yq` (optional, for YAML syntax validation): `brew install yq`