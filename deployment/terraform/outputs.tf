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

output "s3_bucket_name" {
  description = "Name of the S3 data bucket"
  value       = aws_s3_bucket.data_bucket.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 data bucket"
  value       = aws_s3_bucket.data_bucket.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for tracking BSE news scrape results"
  value       = aws_dynamodb_table.bse_news_scrape_tracker.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for tracking BSE news scrape results"
  value       = aws_dynamodb_table.bse_news_scrape_tracker.arn
}