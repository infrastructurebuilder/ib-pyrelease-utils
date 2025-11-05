# INCOMPLETE Makefile originally from ibdata_pymerkle project

.PHONY: help install test test-simple test-full lint format type-check build clean dev-install \
		check-uv release-perform test-quiet set-version pre-release release-prepare release \
		local-install .tag_this_version bump-patch bump-minor show-commands clean-venv test-all check \
		.pre-release .bump .read-release-properties .check-for-release-properties .push_release_tag

_UNCOMMITTED_CHANGED := $$(git status --porcelain)

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) |  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check-uv:  ## Check if uv is installed
	@command -v uv >/dev/null 2>&1 || { echo "❌ Error: uv is not installed"; echo "📦 Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

dev-install: check-uv  ## Install with development dependencies
	@uv sync --group dev

test-cov: dev-install  ## Run tests with coverage
	@echo "📊 Running tests with coverage..."
	@echo "---------------------------------"
	@uv run pytest src/test/python --cov=src/main/python --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "📈 Showing coverage report for src/ directory only:"
	@echo "---------------------------------------------------"
	@uv run coverage report --include="src/main/python/*"

lint: format ## Run linter (ruff)
	@uv run ruff check src/main/python src/test/python

lint-fix: dev-install  ## Fix linting issues with ruff --fix
	@uv run ruff check --fix src/main/python src/test/python

format: dev-install  ## Format code with black and ruff
	@uv run black src/main/python src/test/python

type-check: dev-install  ## Run type checker (mypy)
	@uv run mypy src/main/python

check: dev-install lint format type-check  ## Run all checks (lint, format, type-check)


build: check-uv lint format test-all ## Build the package
	@uv build

local-install: check-uv build  ## Install the package into local environment using uv tool install
	@echo "📦 Installing package into local environment..."
	@echo "=============================================="
	@uv tool install --force dist/ibdata_pymerkle-*.whl
	@echo ""
	@echo "✅ Package installed successfully!"
	@echo "💡 To verify installation, run: ibdatapy --help"

.bump:
	@uv tool run bump-my-version bump $(COMMAND) $(FLAGS)

# Bump patch version
bump-patch:
	$(MAKE) .bump COMMAND=patch FLAGS="--no-tag --no-commit --allow-dirty"

# Bump minor version
bump-minor:
	$(MAKE) .bump COMMAND=minor	FLAGS="--no-tag --no-commit --allow-dirty"


set-version: check-uv  ## Set version to a specific semantic version (usage: make set-version VERSION=x.y.z)
	@echo "🔢 Setting version to $(VERSION)..."
	@echo "-----------------------------------"
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Error: VERSION parameter is required"; \
		echo "📝 Usage: make set-version VERSION=x.y.z"; \
		echo "📋 Example: make set-version VERSION=1.2.3"; \
		exit 1; \
	fi
	@uv run bump-my-version bump --new-version $(VERSION)
	@echo "✅ Version successfully set to $(VERSION)"

test: dev-install  ## Run tests quietly for release validation
	@uv run pytest src/test/python --tb=no 

test-quiet: dev-install  ## Run tests quietly for release validation
	@uv run pytest src/test/python --tb=no -q

clean:  ## Clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf target/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-venv: clean ## Clean virtual environment artifacts
	rm -rf .venv/

# Default target
all: dev-install check test  ## Install deps, run checks, and test

# Additional helpful targets
test-all: test-cov  ## Run relevant test variants (coverage gets everything)

