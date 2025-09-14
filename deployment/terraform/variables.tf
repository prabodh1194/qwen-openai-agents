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
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "scheduled_invoke_schedule" {
  description = "Schedule expression for scheduled invoke Lambda"
  type        = string
  default     = "cron(30 2 ? * * *)"
}

variable "scheduled_invoke_timeout" {
  description = "Timeout for scheduled invoke Lambda function in seconds"
  type        = number
  default     = 900
}