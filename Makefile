# Makefile for ibdata_pymerkle project using uv

.PHONY: help install test test-simple test-full lint format type-check build clean dev-install \
		check-uv release-perform test-quiet set-version pre-release release-prepare release \
		local-install .tag_this_version bump-patch bump-minor show-commands clean-venv test-all check \
		.pre-release .bump .read-release-properties .check-for-release-properties .push_release_tag

_UNCOMMITTED_CHANGED := $$(git status --porcelain)

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check-uv:  ## Check if uv is installed
	@command -v uv >/dev/null 2>&1 || { echo "❌ Error: uv is not installed"; echo "📦 Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

dev-install: check-uv  ## Install with development dependencies
	@uv sync --group dev

test-simple: check-uv  ## Run simple tests (no dependencies)
	@echo "📋 Running simple tests (no dependencies required)..."
	@echo "----------------------------------------------------"
	@echo "✅ No simple tests found, skipping"

test-simple-quiet: check-uv  ## Run simple tests quietly (internal target)
	@echo "✅ No simple tests found, skipping"

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

.pre-release:   ## Check that there are no uncommitted files in the repository
	@echo "🔍 Checking for uncommitted changes..."
	@echo "======================================"
	@echo ""
	@if [ -n "$(_UNCOMMITTED_CHANGED)" ]; then \
		echo "❌ Error: There are uncommitted changes in the repository"; \
		echo "📋 Uncommitted files:"; \
		echo ""; \
		git status --porcelain; \
		echo ""; \
		echo "🔧 Please commit or stash your changes before releasing:"; \
		echo "   git add ."; \
		echo "   git commit -m \"Your commit message\""; \
		echo "   or"; \
		echo "   git stash"; \
		exit 1; \
	else \
		echo "✅ Repository is clean - no uncommitted changes"; \
	fi
	@echo ""

.tag_this_version: .pre-release	## Tag the current version in git
	@echo "🏷️  Tagging current version..."
	@echo "============================"
	@export _RELEASE_VERSION=$$(uv run bump-my-version show current_version) && \
	export RELEASE_TAG="v$$_RELEASE_VERSION" && \
	echo "📋 Current version: $$RELEASE_TAG" && \
	echo "🔍 Checking if tag $$RELEASE_TAG already exists..." && \
		if git tag -l | grep -q "^$$RELEASE_TAG$$"; then \
			echo "❌ Error: Tag $$RELEASE_TAG already exists locally"; \
			echo "🔧 Please delete the existing tag or use a different version:"; \
			echo "   git tag -d $$RELEASE_TAG"; \
			exit 1; \
		fi && \
		if git ls-remote --tags origin | grep -q "refs/tags/$$RELEASE_TAG$$"; then \
			echo "❌ Error: Tag $$RELEASE_TAG already exists at origin"; \
			echo "🔧 Please use a different version.  Do not delete or modify the remote tag"; \
			exit 1; \
		fi && \
	echo "✅ Tag $$RELEASE_TAG does not exist locally or at origin" && \
	echo "🏷️  Creating tag: $$RELEASE_TAG" && \
	git tag -a -m "Tag for release $$_RELEASE_VERSION" "$$RELEASE_TAG" && \
	if [ -n "$(NEXT_VERSION)" ]; then \
		export _NEXT_VERSION="$(NEXT_VERSION)" && \
		echo "🔢 Incrementing version for next release from $$_RELEASE_VERSION to $(NEXT_VERSION)..." && \
		uv run bump-my-version bump --no-commit --no-tag --allow-dirty --new-version $(NEXT_VERSION); \
	else \
				echo "ℹ️  No NEXT_VERSION specified, incrementing patch version" && \
				uv run bump-my-version bump patch --no-commit --no-tag --allow-dirty && \
				export _NEXT_VERSION=$$(uv run bump-my-version show current_version); \
	fi && \
	echo "✅ Version incremented from $${RELEASE_TAG} to $${_NEXT_VERSION}" && \
	uv sync && \
	git add pyproject.toml uv.lock && \
	git commit -m "Bump version: $${_RELEASE_VERSION} → $${_NEXT_VERSION}" && \
	echo "scm.tag=$$RELEASE_TAG" > release.properties && \
	echo "scm.next_version=$(NEXT_VERSION)" >> release.properties && \
	echo "" >> release.properties
	@echo "✅ Release tagging completed successfully!"


.push_release_tag:
	echo "📤 Pushing tag to source control..." && \
	git push --tags origin "$$RELEASE_TAG" || { \
		echo "❌ Error: Failed to push tag to source control"; \
		exit 1; \
	} && \
	echo "✅ Tag $$RELEASE_TAG created and pushed successfully"

.read-release-properties:
	@echo "📋 Reading release.properties file..." && \
	if [ ! -f "release.properties" ]; then \
		echo "❌ Error: release.properties file not found"; \
		exit 1; \
	fi && \
	export RELEASE_TAG=$$(grep "^scm.tag=" release.properties | cut -d'=' -f2) && \
	echo "🏷️  Found release tag: $${RELEASE_TAG}"
# 

.check-for-release-properties: .pre-release	## Check that release.properties file does not already exist
	@uv run ./.scripts/check-for-release-properties.py "."

release-prepare: .check-for-release-properties # clean test-all .pre-release  ## Tag then check out the current repository into target/checkout directory and run validation
	@export __PREVIOUS_DIR=$$(pwd)

	@echo "📦 Preparing release checkout..."
	@echo "==============================="
	@echo ""
	@echo "🧹 Cleaning target directory..."
	@mkdir -p target/checkout && rm -rf target/checkout && mkdir -p target/checkout
	@echo "🧹 Checking NEXT_VERSION $(NEXT_VERSION)..."
	@export _NEXT_VERSION="$(NEXT_VERSION)"
	@if [ -n "$${_NEXT_VERSION}" ]; then \
		echo "🔢 NEXT_VERSION specified: $${_NEXT_VERSION}"; \
		$(MAKE) .tag_this_version NEXT_VERSION=$${_NEXT_VERSION}; \
	else \
		echo "ℹ️  No NEXT_VERSION specified, will increment patch version after release"; \
		$(MAKE) .tag_this_version; \
	fi
	$(MAKE) .read-release-properties && \
	@echo "📋 Reading release.properties file..." && \
	if [ ! -f "release.properties" ]; then \
		echo "❌ Error: release.properties file not found"; \
		exit 1; \
	fi && \
	export RELEASE_TAG=$$(grep "^scm.tag=" release.properties | cut -d'=' -f2) && \
	echo "🏷️  Found release tag: $${RELEASE_TAG}"

	echo "🔄 Checking out $$RELEASE_TAG to target/checkout..." && \
	git clone --depth 1 --branch $$RELEASE_TAG . target/checkout
	@echo ""
	@echo "✅ Repository successfully checked out to target/checkout"
	@echo ""
	@echo "🔧 Checking for .envrc file..."
	@if [ -f ".envrc" ]; then \
		echo "📋 Found .envrc file, copying to checkout directory..."; \
		cp .envrc target/checkout/; \
		echo "🔐 Running direnv allow in checkout directory..."; \
		cd target/checkout && direnv allow; \
		echo "✅ .envrc copied and direnv allow executed"; \
	else \
		echo "ℹ️  No .envrc file found, skipping direnv setup"; \
	fi
	@echo ""
	@echo "🔄 Returning to original directory..."&& \
	@echo cd ${__PREVIOUS_DIR} 
	cd ${__PREVIOUS_DIR}

release-perform: .pre-release  ## Release to PyPI (requires UV_PUBLISH_TOKEN or PYPI_TOKEN env var)
	@echo "🚀 Preparing release to PyPI..."
	@echo "==============================="
	@echo ""
	@echo "� Changing to target/checkout directory..."
	@export __PREVIOUS_DIR=$$(pwd)
	@cd target/checkout
	@echo ""
	@echo "🧪 Running validation in checkout directory..."
	@echo "=============================================="
	@echo ""
	@echo "📂 Changing to target/checkout directory..."
	@export __PREVIOUS_DIR=$$(pwd)
	@cd target/checkout && \
	echo "🧹 Running make clean..." && \
	make clean && \
	echo "" && \
	echo "📦 Running make build..." && \
	make build && \
	echo "" && \
	echo "✅ All validation steps completed successfully!"
	@echo "" && \
	echo "�🔐 Checking for PyPI token..." && \
	if [ -n "$$PUBLISH_INDEX" ]; then \
		echo "✅ PUBLISH_INDEX found: $$PUBLISH_INDEX"; \
	else \
		echo "ℹ️  No PUBLISH_INDEX specified, defaulting to PyPI"; \
		export PUBLISH_INDEX="pypi"; \
	fi && \
	if [ -n "$$UV_PUBLISH_TOKEN" ]; then \
		echo "✅ UV_PUBLISH_TOKEN found"; \
	else \
		if [ -n "$$PUBLISH_INDEX" ]; then \`
			export _PIX=PUBLISH_INDEX=$$PUBLISH_INDEX"
		else \
			export _PIX=""
		fi; \
		echo "❌ Error: UV_PUBLISH_TOKEN environment variable is set"; \
		echo "📝 Please set your PyPI token"; \
			echo " and re-run make release-perform $$_PIX"
		echo "   export UV_PUBLISH_TOKEN=your_token_here"; \
		exit 1; \
	fi

	@echo "🧹 Running make clean..." && \
	make clean && \
	echo "" && \
	echo "📦 Running make build..." && \
	make build && \
	echo "" && \
	echo "🔍 Checking for uncommitted changes after build..." && \
	$(MAKE) .pre-release && \
	echo "" && \
	echo "�📦 Uploading to PyPI..." && \
	echo "----------------------" && \
	if [ -n "$$UV_PUBLISH_TOKEN" ]; then \
		uv publish --index $${PUBLISH_INDEX}; \
	else \
		uv publish --token $$PYPI_TOKEN --index $${PUBLISH_INDEX}; \
	fi && \
	echo "" && \
	echo "� Pushing release tag..." && \
	echo "==========================" && \
	$(MAKE) .read-release-properties && \
	git push --tags origin "$$RELEASE_TAG" || { \
		echo "❌ Error: Failed to push tag to source control"; \
		exit 1; \
	} && \
	echo "✅ Tag $$RELEASE_TAG pushed successfully"
	@echo "📥 Pulling latest changes from remote..."
	@echo "======================================="
	@git pull origin HEAD || { \
		echo "❌ Error: Failed to pull origin HEAD"; \
		echo "⚠️  Version was incremented locally but not pushed"; \
		exit 1; \
	} && \
	echo "" && \
	echo "🎉 Release completed successfully!" && \
	echo "📋 Package is now available on PyPI and tag $$RELEASE_TAG pushed to origin" && \
	echo ""
	@cd ${__PREVIOUS_DIR}
	@echo "🔄 Returning to original directory..." && \
	echo "✅ Release process completed successfully!" &&  \
	echo ""
	@echo "📥 Pulling latest changes from remote..."
	@echo "======================================="
	@git fetch --all && git pull || { \
		echo "⚠️  Warning: Failed to pull latest changes from remote"; \
		echo "📋 This is not critical but you may want to manually sync"; \
		echo "✅ Release process still completed successfully"; \
	} && \
	echo "✅ Successfully pulled latest changes from remote"
	@echo ""

release: release-prepare release-perform  ## Complete release workflow (release-prepare release-perform)
	@echo "🎉 Complete release workflow finished!"

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

show-commands:  ## Show useful uv commands
	@echo ""
	@echo "🔧 Useful uv commands:"
	@echo "  make dev-install         # Install all dev dependencies"
	@echo "  make test               # Run comprehensive test suite"
	@echo "  make test-simple        # Run simple tests only"
	@echo "  make test-cov           # Run tests with coverage"
	@echo "  make lint               # Lint code"
	@echo "  make format             # Format code"
	@echo "  make type-check         # Type check code"
	@echo "  make set-version VERSION=x.y.z  # Set version to specific semantic version"
	@echo "  make build              # Build the package"
	@echo "  make release-prepare    # Prepare release in isolated checkout"
	@echo "  make release-perform    # Release to PyPI (requires UV_PUBLISH_TOKEN or PYPI_TOKEN)"
	@echo "  make release            # Complete release workflow (prepare + perform)"
	@echo "  make clean              # Clean build artifacts"
	@echo "  uv build               # Build the package directly"
	@echo "  uv pip install .       # Install the package directly"
