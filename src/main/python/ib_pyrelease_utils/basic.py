#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


def read_properties_file(file_path: Path) -> dict:
    """Read a properties file and return a dictionary of its contents.
    Prints error but returns empty dict if file not found or error occurs."""
    properties = {}

    if not file_path.exists():
        print(
            f"❌ Error: Properties file '{file_path}' does not exist", file=sys.stderr
        )
        return properties

    try:
        with open(file_path, encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#") or line.startswith("!"):
                    continue

                # Split on first '=' to handle values with '=' in them
                if "=" in line:
                    key, value = line.split("=", 1)
                    properties[key.strip()] = value.strip()
    except Exception as e:
        print(f"❌ Error reading properties file '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

    return properties


def check_for_release(directory_path: str) -> None:
    """Check if release.properties file exists in the given directory."""
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist", file=sys.stderr)
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory", file=sys.stderr)
        sys.exit(1)

    release_properties_file = directory / "release.properties"

    if release_properties_file.exists():
        print(
            "❌ Error: release.properties file already exists. "
            "Please remove it before proceeding or perform make release-perform.",
            file=sys.stderr,
        )
        sys.exit(1)


def ensure_empty_directory(directory_path: str) -> None:
    """Ensure the given directory is empty, creating it if necessary."""
    directory = Path(directory_path)

    if directory.exists():
        if not directory.is_dir():
            print(
                f"❌ Error: '{directory}' exists and is not a directory",
                file=sys.stderr,
            )
            sys.exit(1)

        # Remove all contents of the directory
        for item in directory.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        directory.mkdir(parents=True, exist_ok=True)


def ensure_no_changed_files(directory: Path) -> None:
    """Ensure there are no modified files in the given git repo.
    Exits with error if there are any."""
    print(f"🔍 Checking for uncommitted changes in {directory}...")
    if not directory.exists() or not directory.is_dir():
        print(
            f"❌ Error: '{directory}' does not exist or is not a directory",
            file=sys.stderr,
        )
        sys.exit(1)

    result = git(["status", "--porcelain"], directory)
    if result:
        print(
            f"❌ Error: There are modified files in '{directory}'. "
            "Please commit or stash them before proceeding.",
            file=sys.stderr,
        )
        sys.exit(1)


def run_command_or_fail(
    command: str,
    args: list,
    cwd: Path = Path("."),
    errmsg: str = None,
    secrets: list = [],
) -> str:
    """Run a command with the given arguments and return its output.
    If the command fails, print an error message and exit.

    Args:
        command (str): Command to run (must be in PATH or an absolute path).
        args (list): list of arguments to pass to the command.
        cwd (Path, optional): Directory to run command out of. Defaults to ".".
        secrets (list, optional): strings to redact from error msg. Defaults to [].
        errmsg (str, optional): Addl error msg to display on failure. Defaults to None.

    Returns:
        str: The standard output of the command.
    """
    try:
        result = subprocess.run(
            [command] + args, capture_output=True, cwd=cwd, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = f"❌ Error running {command} {' '.join(args)}: {e}"
        for secret in secrets:
            error_message = error_message.replace(secret, "****")
        print(error_message)
        if errmsg:
            print(errmsg)
        # print("\tSTDOUT:", e.stdout)
        # print("\tSTDERR:", e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Error: '{command}' command not found. ")
        if errmsg:
            print(errmsg)
        sys.exit(1)


def uv(args: list, cwd: Path = Path(".")) -> str:
    """Run uv with the given arguments and return the CompletedProcess."""
    return run_command_or_fail("uv", args, cwd)


def git(args: list, cwd: Path = Path("."), errmsg: str = None) -> str:
    """Run git with the given arguments."""
    return run_command_or_fail("git", args, cwd, errmsg, [])


def bmv(args: list, cwd: Path = Path(".")) -> str:
    """Run bump-my-version with the given arguments and return the CompletedProcess."""
    return uv(["run", "bump-my-version"] + args, cwd)


def get_next_version(cwd: Path = Path(".")) -> str:
    """Get the next version string after a bump patch."""
    return bmv(["--increment", "patch", "show"], cwd)


def get_current_version(cwd: Path = Path(".")) -> str:
    """Get the current version string."""
    return bmv(["show", "current_version"], cwd)


def ensure_release_tag_does_not_exist(release_tag: str, cwd: Path = Path(".")) -> None:
    """Ensure the given release tag does not already exist locally or remotely."""
    local_result = git(["tag", "-l", release_tag], cwd)

    # Check if tag exists locally
    if local_result.strip():
        print(
            f"❌ Error: Tag {release_tag} already exists locally. "
            "Please delete the existing tag or use a different version:\n"
            f"   git tag -d {release_tag}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if tag exists remotely
    remote_result = git(["ls-remote", "--tags", "origin"], cwd)
    reftag = f"refs/tags/{release_tag}"
    if any(line.endswith(reftag) for line in remote_result.splitlines()):
        print(
            f"❌ Error: Tag {release_tag} already exists at origin. "
            "Please use a different version. "
            "Do not delete or modify the remote tag.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ Tag {release_tag} does not exist locally or at origin")


def bump_sync_commit(
    current_version: str,
    next_version: str,
    cwd: Path = Path("."),
    files_to_commit: list = ["pyproject.toml", "uv.lock"],
) -> None:
    """Bump the version to the next version, sync, and commit the changes."""
    print(f"🔢 Bumping version for next release to {next_version}...")
    bmv(
        [
            "bump",
            "--no-commit",
            "--no-tag",
            "--allow-dirty",
            "--new-version",
            next_version,
        ],
        cwd,
    )
    print(f"✅ Version bumped to {next_version}")
    print("🔄 Syncing...")
    uv(["sync"], cwd)
    git(["add"] + files_to_commit, cwd)
    git(["commit", "-m", f"Bump version: {current_version} → {next_version}"], cwd)


def create_release_properties_file(
    release_tag: str, next_version: str, cwd: Path = Path(".")
) -> Path:
    """Create the release.properties file with the given tag and next version."""
    props = cwd / "release.properties"
    with open(props, "w", encoding="utf-8") as file:
        file.write(f"scm.tag={release_tag}\n")
        file.write(f"scm.next_version={next_version}\n")
        file.write("\n")
    print("✅ release.properties file created successfully")
    return props


def create_tag_for_version(next_version: str, cwd: Path = Path(".")) -> str:
    """Create a git tag for the current version and prepare for the next version."""
    ensure_no_changed_files(cwd)
    current_version = get_current_version()
    release_tag = f"v{current_version}"
    print(f"📋 Current version: {current_version}")
    print(f"🔍 Checking if tag '{release_tag}' already exists...")
    ensure_release_tag_does_not_exist(release_tag)
    print(f"🏷️  Creating tag: {release_tag}...")
    git(["tag", "-a", "-m", f"Tag for release {current_version}", release_tag], cwd)
    print(f"✅ Tag {release_tag} created successfully")
    bump_sync_commit(current_version, next_version, cwd)
    ensure_no_changed_files(cwd)
    create_release_properties_file(release_tag, next_version, cwd)
    return release_tag


def release_prepare(next_version: str = None) -> None:
    """Prepare the release checkout."""

    print("📦 Preparing release checkout...")
    print("===============================")
    repo_dir = Path.cwd()

    if next_version:
        print(f"🔢 Next version specified: {next_version}")
    else:
        next_version = get_next_version()
        print(f"ℹ️🔢 Will use {next_version} as a patch increment")

    props = create_tag_for_version(next_version, repo_dir)
    pf = read_properties_file(props)
    release_tag = pf.get("scm.tag", "MISSING")
    if release_tag == "MISSING":
        print("❌ Error: 'scm.tag' not found in release.properties", file=sys.stderr)
        sys.exit(1)


def release_perform(
    checkout_path: Path = Path("target/checkout"),
    publish_index: str = None,
    token: str = None,
) -> None:
    """Perform the release checkout."""

    print("📦 Performing release checkout...")
    print("===============================")
    checkout_path = checkout_path.absolute()
    ensure_empty_directory(checkout_path)
    if not checkout_path.exists():
        print(
            f"❌ Error: Checkout directory '{checkout_path}' does not exist. "
            "Please run release-prepare first.",
            file=sys.stderr,
        )
        sys.exit(1)
    pf = read_properties_file("release.properties")
    release_tag = pf.get("scm.tag", "MISSING")
    if release_tag == "MISSING" or release_tag == "":
        print("❌ Error: 'scm.tag' not found in release.properties", file=sys.stderr)
        sys.exit(1)
    print(f"🏷️  Found release tag defined in release.properties: {release_tag}")
    git(["clone", "--depth", "1", "--branch", release_tag, ".", checkout_path])
    print(f"✅ Repository successfully checked out to {checkout_path}")
    print("🔧 Checking for .envrc file...")
    if Path(".envrc").exists():
        print("📋 Found .envrc file, copying to checkout directory...")
        run_command_or_fail("cp", [".envrc", checkout_path])
        print(f"✅ .envrc copied to {checkout_path}")
    else:
        print("ℹ️  No .envrc file found, skipping direnv setup")

    previous_dir = Path.cwd().absolute()

    print("🚀 Preparing release to PyPI...")
    print("===============================")
    print("")
    print(f"📦 Changing to {checkout_path} directory...")
    os.chdir(checkout_path)
    if Path(".envrc").exists():
        print("🔐 Running direnv allow...")
        run_command_or_fail("direnv", ["allow"], checkout_path)
        print("✅ direnv allow executed")

    print(f"✅ Changed to {checkout_path} directory")
    print("")
    print(f"🧪 Running validation in checkout directory {checkout_path}...")
    print("==============================================")
    print("")
    print("🧹 📦 Running make clean build...")
    run_command_or_fail("make", ["clean", "build"])
    print("")
    ensure_no_changed_files(checkout_path)
    print("✅ All validation steps completed successfully!")
    if publish_index:
        print(f"✅ PUBLISH_INDEX : {publish_index}")
    print("🔐 Checking for PyPI token...")
    if token:
        print("✅ UV_PUBLISH_TOKEN found")
    else:
        print(
            "❌ Error: Token not found. "
            "Probably UV_PUBLISH_TOKEN environment variable is not set"
        )
        print("📝 Please set your token")
        print(" and re-run make release-perform")
        print("   export UV_PUBLISH_TOKEN=your_token_here")
        sys.exit(1)

    print("")
    print("📦 Uploading to PyPI...")
    print("----------------------")
    uv(
        ["publish", "--token", token]
        + (["--index", publish_index] if publish_index else []),
        secrets=[token],
    )
    print("✅ Package uploaded to PyPI successfully")
    print("")
    print("🔄 Returning to original directory...")
    os.chdir(previous_dir)
    print("📤 Pushing tag to source control...")
    git(["push", "--tags", "origin", release_tag], cwd=previous_dir)
    print(f"✅ Tag {release_tag} pushed successfully")
    print("📥 Pulling latest changes from remote...")
    emsg = (
        "⚠️  Warning: Failed to pull latest changes from remote\n"
        + "⚠️  Version was incremented locally but not pushed"
    )
    git(["pull", "origin", "HEAD"], errmsg=emsg)
    print("✅ Successfully pulled latest changes from remote")
    print("✅ Release process completed successfully!")


# Leftover stuff from Makefile
# @echo "📥 Pulling latest changes from remote..."
# @echo "======================================="
# @git fetch --all && git pull || { \
# 	echo "⚠️  Warning: Failed to pull latest changes from remote"; \
# 	echo "📋 This is not critical but you may want to manually sync"; \
# 	echo "✅ Release process still completed successfully"; \
# } && \
# echo "✅ Successfully pulled latest changes from remote"
# @echo ""


def main():
    """Main entry point for command line usage."""
    command = sys.argv[0]
    if command.endswith("ib-prepare"):
        if len(sys.argv) == 2:
            next_version = sys.argv[1]
            release_prepare(next_version)
        else:
            release_prepare()
    elif command.endswith("ib-perform"):
        if len(sys.argv) == 2:
            checkout_path = Path(sys.argv[1])
        else:
            checkout_path = Path("target/checkout")
        token = os.environ.get("UV_PUBLISH_TOKEN")
        publish_index = (
            os.environ.get("UV_PUBLISH_INDEX")
            if os.environ.get("UV_PUBLISH_INDEX")
            else None
        )
        release_perform(
            checkout_path=checkout_path, publish_index=publish_index, token=token
        )
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
