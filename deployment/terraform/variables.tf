variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "bse-news-analyzer"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for mountpoint"
  type        = string
  default     = "bse-news-analyzer-data"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "batch_invoke_lambda_function_name" {
  description = "Name of the batch invoke Lambda function"
  type        = string
  default     = "bse-news-batch-invoke"
}

variable "batch_invoke_lambda_timeout" {
  description = "Batch invoke Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "batch_invoke_lambda_memory_size" {
  description = "Batch invoke Lambda function memory size in MB"
  type        = number
  default     = 512
}

