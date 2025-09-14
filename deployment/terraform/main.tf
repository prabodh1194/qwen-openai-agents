
# S3 Bucket for mountpoint
resource "aws_s3_bucket" "data_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_versioning" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.lambda_function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          "${aws_s3_bucket.data_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:*:*:function:${var.lambda_function_name}*"
        ]
      }
    ]
  })
}

# Lambda Function - BSE News Analyzer
resource "aws_lambda_function" "bse_news_analyzer" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.13"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  filename         = "${path.module}/../../lambda-package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../lambda-package.zip")

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name,
      PYTHONPATH     = "/var/task/packages"
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy
  ]
}

# Lambda Function - Credentials Refresh
resource "aws_lambda_function" "creds_refresh" {
  function_name = "${var.lambda_function_name}-creds-refresh"
  role          = aws_iam_role.lambda_role.arn
  handler       = "refresh_creds_handler.lambda_handler"
  runtime       = "python3.13"
  timeout       = 300 # 5 minutes
  memory_size   = 128

  filename         = "${path.module}/../../lambda-package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../lambda-package.zip")

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name,
      PYTHONPATH     = "/var/task/packages"
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy
  ]
}

# Lambda Function - Scheduled Invoke
resource "aws_lambda_function" "scheduled_invoke" {
  function_name = "${var.lambda_function_name}-scheduled-invoke"
  role          = aws_iam_role.lambda_role.arn
  handler       = "scheduled_invoke_handler.lambda_handler"
  runtime       = "python3.13"
  timeout       = var.scheduled_invoke_timeout
  memory_size   = 512

  filename         = "${path.module}/../../lambda-package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../lambda-package.zip")

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name,
      PYTHONPATH     = "/var/task/packages"
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy
  ]
}

# EventBridge Rule for 5-hour credential refresh
resource "aws_cloudwatch_event_rule" "creds_refresh_schedule" {
  name                = "${var.lambda_function_name}-creds-refresh-5h"
  description         = "Trigger credentials refresh every 5 hours"
  schedule_expression = "rate(5 hours)"
}

# EventBridge Rule for scheduled invoke
resource "aws_cloudwatch_event_rule" "scheduled_invoke" {
  name                = "${var.lambda_function_name}-scheduled-invoke-daily"
  description         = "Trigger scheduled invoke of BSE news analysis daily at 8:00 AM IST"
  schedule_expression = var.scheduled_invoke_schedule
}

# EventBridge Target for credentials refresh Lambda
resource "aws_cloudwatch_event_target" "creds_refresh_target" {
  rule = aws_cloudwatch_event_rule.creds_refresh_schedule.name
  arn  = aws_lambda_function.creds_refresh.arn
}

# EventBridge Target for scheduled invoke Lambda
resource "aws_cloudwatch_event_target" "scheduled_invoke_target" {
  rule = aws_cloudwatch_event_rule.scheduled_invoke.name
  arn  = aws_lambda_function.scheduled_invoke.arn
}

# Lambda Permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge_creds_refresh" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.creds_refresh.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.creds_refresh_schedule.arn
}

# Lambda Permission for EventBridge scheduled invoke
resource "aws_lambda_permission" "allow_eventbridge_scheduled_invoke" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduled_invoke.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_invoke.arn
}

# Lambda Function URL
resource "aws_lambda_function_url" "bse_news_analyzer" {
  function_name      = aws_lambda_function.bse_news_analyzer.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["POST", "GET"]
    allow_headers     = ["*"]
    expose_headers    = ["keep-alive", "date"]
  }
}