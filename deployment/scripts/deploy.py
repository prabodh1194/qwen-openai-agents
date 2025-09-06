"""
Deploy Lambda infrastructure using Terraform.
"""
import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)


def run_terraform(command: str, terraform_dir: Path):
    """Run terraform command in specified directory."""

    original_dir = os.getcwd()
    try:
        os.chdir(terraform_dir)

        if command == "init":
            result = subprocess.run(
                ["tofu", "init", "-input=false"], capture_output=True, text=True
            )
        elif command == "apply":
            result = subprocess.run(
                ["tofu", "apply", "-auto-approve", "-input=false"],
                capture_output=True,
                text=True,
            )
        elif command == "destroy":
            result = subprocess.run(
                ["tofu", "destroy", "-auto-approve", "-input=false"],
                capture_output=True,
                text=True,
            )
        else:
            raise ValueError(f"Unknown terraform command: {command}")

        logger.info(f"Terraform {command} output:")
        logger.info(result.stdout)
        if result.stderr:
            logger.error(f"Errors: {result.stderr}")

        return result.returncode == 0

    finally:
        os.chdir(original_dir)


def deploy_infrastructure():
    """Deploy complete infrastructure."""

    terraform_dir = Path(__file__).parent.parent / "terraform"

    logger.info(f"Initializing Terraform... {terraform_dir}")
    if not run_terraform("init", terraform_dir):
        logger.error("Terraform init failed")
        return False

    logger.info("Applying Terraform configuration...")
    if not run_terraform("apply", terraform_dir):
        logger.error("Terraform apply failed")
        return False

    logger.info("Deployment completed successfully!")
    return True


def destroy_infrastructure():
    """Destroy deployed infrastructure."""

    terraform_dir = Path(__file__).parent.parent / "terraform"

    logger.info("Destroying infrastructure...")
    return run_terraform("destroy", terraform_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Lambda infrastructure")
    parser.add_argument(
        "--destroy",
        action="store_true",
        help="Destroy infrastructure instead of deploying",
    )

    args = parser.parse_args()

    if args.destroy:
        destroy_infrastructure()
    else:
        deploy_infrastructure()
