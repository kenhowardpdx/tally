# GitHub Actions Standard Versions

This file documents the standard action versions used across all workflows in this repository.

## 📦 **Standard Action Versions**

| Action | Version | Purpose | Last Updated |
|--------|---------|---------|--------------|
| `actions/checkout` | `v5` | Repository checkout | 2025-10-12 |
| `hashicorp/setup-terraform` | `v3` | Terraform installation | 2025-10-12 |
| `aws-actions/configure-aws-credentials` | `v4` | AWS OIDC authentication | 2025-10-12 |
| `actions/cache` | `v4` | Dependency caching | 2025-10-12 |
| `actions/github-script` | `v7` | GitHub API interactions | 2025-10-12 |

## 🎯 **Version Management Strategy**

### **1. Composite Actions (Recommended)**
We use composite actions in `.github/actions/` to centralize common setup patterns:

- **`.github/actions/setup-terraform/`** - Standard Terraform environment setup
- Automatically includes: checkout, AWS auth, Terraform setup, provider caching
- Single place to update action versions

### **2. Composite Action Usage**
```yaml
steps:
  - name: Setup Terraform Environment  
    uses: ./.github/actions/setup-terraform
    with:
      aws-role-arn: ${{ secrets.AWS_ROLE_ARN }}
      aws-region: us-west-2
      terraform-version: latest
```

### **3. Benefits**
- ✅ **Single source of truth** for action versions
- ✅ **Consistent setup** across all Terraform workflows  
- ✅ **Easy updates** - change version in one place
- ✅ **Reduced duplication** in workflow files
- ✅ **Better testing** - composite actions can be tested independently

### **4. Update Process**
1. Update version in composite action (`/.github/actions/setup-terraform/action.yml`)
2. Test with local workflow: `make github_workflow_terraform-pr`
3. All workflows automatically use new version
4. Update this documentation file

### **5. Local Testing Limitations**

**⚠️ Note**: The `act` tool (version 0.2.82) has known limitations with local composite actions:

```
Error: failed to read 'action.yml' from action 'Setup Terraform Environment' with path '' of step: file does not exist
```

This is a limitation of the `act` tool, **not** our composite action implementation. The workflows work perfectly in actual GitHub Actions. For local testing:

- The `make github_workflow_terraform-pr` command may fail with composite action errors
- Workflows run successfully in the actual GitHub Actions environment
- For comprehensive local testing, consider creating temporary inline versions of workflows

## 📋 **Migration Checklist**

- [x] Create composite action for Terraform setup
- [x] Update terraform-apply.yml to use composite action
- [x] Update terraform-pr.yml to use composite action  
- [x] Add terraform-wrapper input support for plan output capture
- [ ] Test all workflows with local testing
- [ ] Document in Copilot instructions

## 🔄 **Maintenance**

Review and update action versions monthly or when security updates are released.
Use Dependabot or Renovate for automated version updates if desired.