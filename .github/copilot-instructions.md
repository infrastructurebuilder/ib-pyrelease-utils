---
applyTo: "**"
---

Ensure that any python commands are performed using the `uv` virtual environment tool.

When creating python code, keep line length within the limit defined in the project's configuration (usually 88 characters for `black`).

When working on this project, ensure that linting, formatting, and testing are performed before calling the work done.
Use `make lint` for linting, `make lint-fix` for fixing linting issues, `make format` for formatting, and `make test` for testing.

If `make lint` detects issues, try running `make lint-fix`  to automatically fix them before attempting other changes.

When working on this project, ensure that linting, formatting, and testing are performed before calling the work done.

If the file is a Python file, ensure that it is formatted with `black` and linted with `ruff`.

If the file is a JavaScript or TypeScript file, ensure that it is formatted with `prettier` and linted with `eslint`.

When making changes to the code, ensure that you do not delete any existing code unless it is necessary for the functionality of the code.

If you do delete code, ensure that you add a comment explaining why the code was deleted.

If the file is a Python file, ensure that it is tested with `pytest` and that the tests are run before committing the changes.

If the file is a JavaScript or TypeScript file, ensure that it is tested with `jest` and that the tests are run before committing the changes

When adding new features or making changes to the code, ensure that you document the changes in the code comments and in the project's documentation if necessary.

When adding new features or making changes to the code, ensure that you do not break existing functionality. If you do break existing functionality, ensure that you add tests to cover the new functionality and that you run the tests before committing the changes.

When making changes to the code, ensure that you do not introduce any new dependencies unless they are necessary for the functionality of the code. If you do introduce new dependencies, ensure that they are documented in the project's documentation and that they are tested before committing the changes.

When adding new features or changing existing code, write new tests that test the functionality added.
Make sure code coverage requirements are met as noted by `make test-cov` and the associated project configuration for test coverage.
