"""
Deploy Lambda infrastructure using Terraform.
"""
import os
import subprocess
from pathlib import Path


def run_terraform(command: str, terraform_dir: Path):
    """Run terraform command in specified directory."""

    original_dir = os.getcwd()
    try:
        os.chdir(terraform_dir)

        if command == "init":
            result = subprocess.run(["tofu", "init"], capture_output=True, text=True)
        elif command == "apply":
            result = subprocess.run(
                ["tofu", "apply", "-auto-approve"], capture_output=True, text=True
            )
        elif command == "destroy":
            result = subprocess.run(
                ["tofu", "destroy", "-auto-approve"],
                capture_output=True,
                text=True,
            )
        else:
            raise ValueError(f"Unknown terraform command: {command}")

        print(f"Terraform {command} output:")
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")

        return result.returncode == 0

    finally:
        os.chdir(original_dir)


def deploy_infrastructure():
    """Deploy complete infrastructure."""

    terraform_dir = Path(__file__).parent.parent / "terraform"

    print(f"Initializing Terraform... {terraform_dir}")
    if not run_terraform("init", terraform_dir):
        print("Terraform init failed")
        return False

    print("Applying Terraform configuration...")
    if not run_terraform("apply", terraform_dir):
        print("Terraform apply failed")
        return False

    print("Deployment completed successfully!")
    return True


def destroy_infrastructure():
    """Destroy deployed infrastructure."""

    terraform_dir = Path(__file__).parent.parent / "terraform"

    print("Destroying infrastructure...")
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
