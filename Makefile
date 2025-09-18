# Define phony targets
.PHONY: build deploy setup-s3 help

# Build Lambda deployment package
build:
	AWS_PROFILE=personal-aws uv run deployment/scripts/build.py

# Deploy Lambda infrastructure to AWS with S3 storage
deploy: build
	tofu -chdir=deployment/terraform init  -input=false
	tofu -chdir=deployment/terraform apply -auto-approve -input=false

# Upload credentials and setup S3 bucket for mountpoint
setup-s3:
	uv run deployment/scripts/upload_creds.py --bucket bse-news-analyzer-data

# Help target
help:
	@echo "Available targets:"
	@echo "  build     - Build Lambda deployment package"
	@echo "  deploy    - Deploy Lambda infrastructure to AWS with S3 storage"
	@echo "  setup-s3  - Upload credentials and setup S3 bucket for mountpoint"
	@echo "  help      - Show this help message"