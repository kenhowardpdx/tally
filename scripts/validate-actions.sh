#!/bin/bash
# Git Hooks - GitHub Actions Version Validator
# Simple shell-based hook system for validating GitHub Actions versions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_FILE=".github/action-versions.conf"
WORKFLOWS_DIR=".github/workflows"
TEMP_FILE="/tmp/approved-versions-$$"

print_header() {
    echo -e "${BLUE}🔍 GitHub Actions Version Validator${NC}"
    echo "=================================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

load_approved_versions() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file $CONFIG_FILE not found"
        return 1
    fi
    
    # Clean and process the config file into a temp file
    > "$TEMP_FILE"
    local count=0
    
    while IFS=':' read -r action version || [[ -n "$action" ]]; do
        # Skip comments and empty lines
        if [[ "$action" =~ ^[[:space:]]*# ]] || [[ -z "$action" ]]; then
            continue
        fi
        
        # Clean up whitespace
        action=$(echo "$action" | xargs)
        version=$(echo "$version" | xargs)
        
        if [[ -n "$action" && -n "$version" ]]; then
            echo "$action:$version" >> "$TEMP_FILE"
            ((count++))
        fi
    done < "$CONFIG_FILE"
    
    print_info "Loaded $count approved action versions"
}

get_approved_version() {
    local action="$1"
    grep "^$action:" "$TEMP_FILE" 2>/dev/null | cut -d':' -f2
}

cleanup() {
    rm -f "$TEMP_FILE"
}

validate_workflow_file() {
    local workflow_file="$1"
    local errors=0
    
    print_info "Validating $workflow_file"
    
    # Find all 'uses:' statements with regex
    while IFS= read -r line; do
        if [[ "$line" =~ uses:[[:space:]]*([^@[:space:]]+)@([^[:space:]]+) ]]; then
            local action="${BASH_REMATCH[1]}"
            local version="${BASH_REMATCH[2]}"
            
            # Clean up any quotes
            action=$(echo "$action" | tr -d '"'"'"'')
            version=$(echo "$version" | tr -d '"'"'"'')
            
            local expected_version
            expected_version=$(get_approved_version "$action")
            
            if [[ -n "$expected_version" ]]; then
                if [[ "$version" != "$expected_version" ]]; then
                    print_error "$workflow_file: Action '$action' uses version '$version' but expected '$expected_version'"
                    ((errors++))
                else
                    print_success "$workflow_file: Action '$action@$version' ✓"
                fi
            else
                print_warning "$workflow_file: Unknown action '$action@$version' (not in approved list)"
            fi
        fi
    done < "$workflow_file"
    
    return $errors
}

validate_all_workflows() {
    if [[ ! -d "$WORKFLOWS_DIR" ]]; then
        print_error "Workflows directory $WORKFLOWS_DIR not found"
        return 1
    fi
    
    local total_errors=0
    local workflow_count=0
    
    # Find all workflow files
    for workflow_file in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
        if [[ -f "$workflow_file" ]]; then
            validate_workflow_file "$workflow_file"
            local file_errors=$?
            ((total_errors += file_errors))
            ((workflow_count++))
        fi
    done
    
    if [[ $workflow_count -eq 0 ]]; then
        print_error "No workflow files found in $WORKFLOWS_DIR"
        return 1
    fi
    
    echo "=================================================="
    if [[ $total_errors -eq 0 ]]; then
        print_success "All $workflow_count workflow files passed validation! 🎉"
        echo ""
        print_info "To update approved versions, edit: $CONFIG_FILE"
        return 0
    else
        print_error "Found $total_errors version violations in $workflow_count workflow files"
        echo ""
        echo "💡 To fix these issues:"
        echo "   1. Update the workflow files to use approved versions"
        echo "   2. Or update $CONFIG_FILE if new versions are approved"
        echo "   3. Run 'make validate-actions' to re-check"
        return 1
    fi
}

check_yaml_syntax() {
    print_info "Checking YAML syntax..."
    local errors=0
    
    for workflow_file in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
        if [[ -f "$workflow_file" ]]; then
            if command -v yq >/dev/null 2>&1; then
                if ! yq eval '.' "$workflow_file" >/dev/null 2>&1; then
                    print_error "YAML syntax error in $workflow_file"
                    ((errors++))
                else
                    print_success "YAML syntax valid: $workflow_file"
                fi
            else
                print_warning "No YAML validator found (yq), skipping syntax check"
                print_info "Install yq with: brew install yq"
                break
            fi
        fi
    done
    
    return $errors
}

main() {
    # Set up cleanup trap
    trap cleanup EXIT
    
    print_header
    
    # Load approved versions
    if ! load_approved_versions; then
        exit 1
    fi
    
    # Check YAML syntax first
    if ! check_yaml_syntax; then
        print_error "YAML syntax errors found. Fix these before validating action versions."
        exit 1
    fi
    
    # Validate action versions
    if validate_all_workflows; then
        exit 0
    else
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi