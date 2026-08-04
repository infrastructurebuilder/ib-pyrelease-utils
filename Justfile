# Justfile for ib-pyrelease-utils, driven by uv.
#
# Run `just` (or `just help`) for the recipe list.

set shell := ["bash", "-euo", "pipefail", "-c"]

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
# Source and test roots

src := "src"
tests := "tests"

# Build outputs

dist_dir := "dist"
wheel_glob := dist_dir / "ib_pyrelease_utils-*.whl"

# Isolated checkout used by the release recipes

checkout_dir := "target/checkout"

# Tool run as `<tool> clean build` inside the release checkout. Any command
# exposing those two targets works (just, make, task, ...).

build_tool := env_var_or_default("IB_BUILD_TOOL", "just")

# Flags shared by every bump-my-version invocation that must not tag or commit

bump_flags := "--no-tag --no-commit --allow-dirty"

# Coverage reporting targets

cov_reports := "--cov-report=term-missing --cov-report=html"

# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

alias t := test
alias c := check
alias b := build
alias fmt := format

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

# Show this help message
help:
    @just --list --unsorted

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Check if uv is installed
[private]
check-uv:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v uv >/dev/null 2>&1; then
        echo "❌ Error: uv is not installed"
        echo "📦 Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

# Install with development dependencies
dev-install: check-uv
    @uv sync --group dev

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

# Format code with black
format: dev-install
    @uv run black {{ src }} {{ tests }}

# Run linter (ruff)
lint: format
    @uv run ruff check {{ src }} {{ tests }}

# Fix linting issues with ruff --fix
lint-fix: dev-install
    @uv run ruff check --fix {{ src }} {{ tests }}

# Run type checker (mypy)
type-check: dev-install
    @uv run mypy {{ src }}

# Run all checks (lint, format, type-check)
check: dev-install lint format type-check

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# Run the test suite
test: dev-install
    @uv run pytest {{ tests }} --tb=no

# Run the test suite quietly for release validation
test-quiet: dev-install
    @uv run pytest {{ tests }} --tb=no -q

# Run tests with coverage
test-cov: dev-install
    @echo "📊 Running tests with coverage..."
    @echo "---------------------------------"
    @uv run pytest {{ tests }} --cov={{ src }} {{ cov_reports }}
    @echo ""
    @echo "📈 Showing coverage report for {{ src }}/ directory only:"
    @echo "---------------------------------------------------"
    @uv run coverage report --include="{{ src }}/*"

# Run relevant test variants (coverage gets everything)
test-all: test-cov

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

# Build the package
build: check-uv lint format test-all
    @uv build

# Install the package into the local environment using uv tool install
local-install: build
    @echo "📦 Installing package into local environment..."
    @echo "=============================================="
    @uv tool install --force {{ wheel_glob }}
    @echo ""
    @echo "✅ Package installed successfully!"
    @echo "💡 Installed commands: ib-prepare, ib-perform, ib-check-release"

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

# Bump the version without tagging or committing (level: major, minor, patch)
bump level="patch": check-uv
    @uv tool run bump-my-version bump {{ level }} {{ bump_flags }}

# Bump the patch version
bump-patch: (bump "patch")

# Bump the minor version
bump-minor: (bump "minor")

# Set version to a specific semantic version (e.g. just set-version 1.2.3)
set-version version: check-uv
    @echo "🔢 Setting version to {{ version }}..."
    @echo "-----------------------------------"
    @uv run bump-my-version bump --new-version {{ version }}
    @echo "✅ Version successfully set to {{ version }}"

# Show the current version
show-version: check-uv
    @uv run bump-my-version show current_version

# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------

# Check that there are no uncommitted files in the repository
[private]
pre-release:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔍 Checking for uncommitted changes..."
    echo "======================================"
    echo ""
    if [ -n "$(git status --porcelain)" ]; then
        echo "❌ Error: There are uncommitted changes in the repository"
        echo "📋 Uncommitted files:"
        echo ""
        git status --porcelain
        echo ""
        echo "🔧 Please commit or stash your changes before releasing:"
        echo "   git add ."
        echo "   git commit -m \"Your commit message\""
        echo "   or"
        echo "   git stash"
        exit 1
    fi
    echo "✅ Repository is clean - no uncommitted changes"
    echo ""

# Check that release.properties does not already exist
[private]
check-for-release-properties: pre-release
    @uv run ib-check-release .

# Show the release tag recorded in release.properties
[private]
read-release-properties:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📋 Reading release.properties file..."
    if [ ! -f release.properties ]; then
        echo "❌ Error: release.properties file not found"
        exit 1
    fi
    RELEASE_TAG="$(grep '^scm.tag=' release.properties | cut -d'=' -f2)"
    echo "🏷️  Found release tag: ${RELEASE_TAG}"

# Tag the current version and bump to the next one (default: patch increment)
release-prepare next_version="": check-for-release-properties
    @uv run ib-prepare {{ next_version }}

# Release to PyPI (requires UV_PUBLISH_TOKEN; honors UV_PUBLISH_INDEX)
release-perform checkout=checkout_dir tool=build_tool: pre-release
    @uv run ib-perform {{ checkout }} --build-tool {{ tool }}

# Complete release workflow (release-prepare then release-perform)
release: release-prepare release-perform
    @echo "🎉 Complete release workflow finished!"

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

# Clean build artifacts
clean:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🧹 Cleaning build artifacts..."
    rm -rf {{ dist_dir }}/ build/ *.egg-info/ .pytest_cache/ htmlcov/ target/
    find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true

# Clean virtual environment artifacts
clean-venv: clean
    @rm -rf .venv/

# Install deps, run checks, and test
all: dev-install check test

