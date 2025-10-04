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

# DynamoDB Table for tracking BSE news scrape results
resource "aws_dynamodb_table" "bse_news_scrape_tracker" {
  name         = "${var.lambda_function_name}-tracker"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.lambda_function_name}-tracker"
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
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.bse_news_scrape_tracker.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.stock_names.arn
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
      S3_BUCKET_NAME      = var.s3_bucket_name,
      PYTHONPATH          = "/var/task/packages",
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.bse_news_scrape_tracker.name
      SQS_QUEUE_URL       = aws_sqs_queue.stock_names.url
      OPENAI_BASE_URL     = "https://api.deepseek.com"
      MODEL               = "deepseek-chat"
      OPENAI_API_KEY      = ""
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy
  ]
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

# Event Source Mapping for SQS to Lambda
resource "aws_lambda_event_source_mapping" "stock_names_sqs_trigger" {
  event_source_arn = aws_sqs_queue.stock_names.arn
  function_name    = aws_lambda_function.bse_news_analyzer.arn
  batch_size       = 1
}