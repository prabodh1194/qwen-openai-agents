"""
Build Lambda deployment package.
"""
import shutil
import tempfile
from pathlib import Path


def find_repo_root(start_path: Path) -> Path:
    """Find the git repository root directory by checking for .git folder."""
    current = start_path.resolve()
    while current != current.parent:  # Stop at filesystem root
        if (current / ".git").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Not in a git repository - .git directory not found")


def build_lambda_package():
    """Build Lambda deployment package with all dependencies."""

    # Create temporary build directory
    with tempfile.TemporaryDirectory() as temp_dir:
        build_path = Path(temp_dir) / "lambda-package"
        build_path.mkdir()

        print(f"Building Lambda package in {build_path}")

        # Copy source code
        source_dir = find_repo_root(Path(__file__))

        # Copy main application files
        for item in source_dir.iterdir():
            if item.name in ["cli", "client", "tools", "main.py", "pyproject.toml"]:
                if item.is_dir():
                    shutil.copytree(item, build_path / item.name)
                else:
                    shutil.copy2(item, build_path / item.name)

        # Copy deployment lambda handler
        lambda_handler = Path(__file__).parent.parent / "lambda" / "lambda_handler.py"
        if lambda_handler.exists():
            shutil.copy2(lambda_handler, build_path / "lambda_handler.py")

        # Create zip package
        zip_path = find_repo_root(Path(__file__)) / "lambda-package.zip"
        shutil.make_archive(zip_path.with_suffix(""), "zip", build_path)

        print(f"Package created: {zip_path}")
        return zip_path


if __name__ == "__main__":
    build_lambda_package()
