output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.bse_news_analyzer.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.bse_news_analyzer.arn
}

output "lambda_function_url" {
  description = "URL of the Lambda function"
  value       = aws_lambda_function_url.bse_news_analyzer.function_url
}

output "lambda_creds_refresh_function_name" {
  description = "Name of the credentials refresh Lambda function"
  value       = aws_lambda_function.creds_refresh.function_name
}

output "lambda_scheduled_invoke_function_name" {
  description = "Name of the scheduled invoke Lambda function"
  value       = aws_lambda_function.scheduled_invoke.function_name
}

output "s3_bucket_name" {
  description = "Name of the S3 data bucket"
  value       = aws_s3_bucket.data_bucket.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 data bucket"
  value       = aws_s3_bucket.data_bucket.arn
}