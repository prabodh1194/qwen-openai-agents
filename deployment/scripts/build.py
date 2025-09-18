"""
Build Lambda deployment package.
"""
import shutil
import tempfile
import subprocess
from pathlib import Path


def find_repo_root(start_path: Path) -> Path:
    """Find the git repository root directory by checking for .git folder."""
    current = start_path.resolve()
    while current != current.parent:  # Stop at filesystem root
        if (current / ".git").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Not in a git repository - .git directory not found")


def build_lambda_package() -> Path:
    """Build Lambda deployment package with all dependencies."""

    # Create temporary build directory
    with tempfile.TemporaryDirectory() as temp_dir:
        build_path = Path(temp_dir) / "lambda-package"
        build_path.mkdir()

        print(f"Building Lambda package in {build_path}")

        # Copy source code
        source_dir = find_repo_root(Path(__file__))

        # Copy main application files (excluding .pyc files)
        for item in source_dir.iterdir():
            if item.name in [
                "cli",
                "client",
                "services",
                "tools",
                "main.py",
                "pyproject.toml",
            ]:
                if item.is_dir():
                    shutil.copytree(
                        item,
                        build_path / item.name,
                        ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
                    )
                else:
                    shutil.copy2(item, build_path / item.name)

        # Copy deployment scripts
        deployment_scripts_dir = source_dir / "deployment" / "scripts"
        if deployment_scripts_dir.exists():
            shutil.copytree(
                deployment_scripts_dir,
                build_path / "deployment" / "scripts",
                ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
            )

        # Copy deployment lambda handlers
        lambda_dir = Path(__file__).parent.parent / "lambda"
        lambda_handlers = [
            "lambda_handler.py",
        ]
        for handler in lambda_handlers:
            handler_path = lambda_dir / handler
            if handler_path.exists():
                shutil.copy2(handler_path, build_path / handler)

        # Export and install dependencies using uv
        print("Exporting dependencies...")
        requirements_file = build_path / "requirements.txt"
        subprocess.run(
            ["uv", "export", "--frozen", "--no-dev", "-o", str(requirements_file)],
            cwd=source_dir,
            check=True,
        )

        print("Installing dependencies with Lambda platform...")
        packages_dir = build_path / "packages"
        packages_dir.mkdir()

        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--target",
                str(packages_dir),
                "--no-installer-metadata",
                "--no-compile-bytecode",
                "--python-platform",
                "x86_64-manylinux2014",
                "--python",
                "3.13",
                "-r",
                str(requirements_file),
            ],
            check=True,
        )

        # Create zip package
        zip_path = find_repo_root(Path(__file__)) / "lambda-package.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(build_path))

        print(f"Package created: {zip_path}")
        return zip_path


if __name__ == "__main__":
    build_lambda_package()
