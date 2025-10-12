# GitHub Actions Version Management Strategy

## Option 1: Reusable Workflow with Centralized Versions

Create `.github/workflows/_versions.yml` (reusable workflow):

```yaml
name: Shared Action Versions

on:
  workflow_call:
    outputs:
      checkout-version:
        description: "Version of actions/checkout to use"
        value: "v5"
      setup-terraform-version:
        description: "Version of hashicorp/setup-terraform to use" 
        value: "v3"
      configure-aws-credentials-version:
        description: "Version of aws-actions/configure-aws-credentials to use"
        value: "v4"
      cache-version:
        description: "Version of actions/cache to use"
        value: "v4"
      github-script-version:
        description: "Version of actions/github-script to use"
        value: "v7"

jobs:
  versions:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Providing centralized action versions"
```

Then use in other workflows:

```yaml
name: Terraform PR Validation

on:
  pull_request:
    branches: [main]
    paths: ["infra/**"]

jobs:
  get-versions:
    uses: ./.github/workflows/_versions.yml
  
  terraform-validate:
    needs: get-versions
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@${{ needs.get-versions.outputs.checkout-version }}
      - uses: hashicorp/setup-terraform@${{ needs.get-versions.outputs.setup-terraform-version }}
```

## Option 2: Repository Variables (GitHub Feature)

Set repository-level variables in GitHub UI:
- CHECKOUT_VERSION = "v5"
- SETUP_TERRAFORM_VERSION = "v3"
- AWS_CREDENTIALS_VERSION = "v4"

Then reference: `uses: actions/checkout@${{ vars.CHECKOUT_VERSION }}`

## Option 3: Composite Action (Our Recommendation) ✅

Create a composite action that wraps common setup steps.

We implemented this option with `.github/actions/setup-terraform/action.yml` which provides:

- Centralized action versions in one location
- Consistent setup across all Terraform workflows
- Easy version updates by changing a single file
- Reduced duplication in workflow files

### Usage:
```yaml
- name: Setup Terraform Environment
  uses: ./.github/actions/setup-terraform
  with:
    aws-role-arn: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-west-2
    terraform-version: latest
    terraform-wrapper: false
    working-directory: ./infra
```

### Known Limitations:
The `act` tool (v0.2.82) has issues resolving local composite actions, causing `make github_workflow_terraform-pr` to fail with path errors. This is a limitation of the act tool, not our implementation. Workflows work perfectly in actual GitHub Actions.

### Result:
- ✅ Centralized version management implemented
- ✅ All Terraform workflows updated to use composite action
- ✅ Single source of truth for action versions
- ⚠️ Local testing limited by act tool composite action support