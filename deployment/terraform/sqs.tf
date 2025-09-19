# SQS Queue for stock names with Dead Letter Queue (DLQ)

# Dead Letter Queue for stock names
resource "aws_sqs_queue" "stock_names_dlq" {
  name                      = "stock-names-dlq"
  delay_seconds             = 0
  max_message_size          = 256000
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 0
  
  tags = {
    Name = "Stock Names Dead Letter Queue"
    Service = "Stock Processing"
  }
}

# Main SQS Queue for stock names
resource "aws_sqs_queue" "stock_names" {
  name                      = "stock-names"
  delay_seconds             = 0
  max_message_size          = 256000
  message_retention_seconds = 345600  # 4 days
  receive_wait_time_seconds = 20
  
  # Configure Dead Letter Queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.stock_names_dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = {
    Name = "Stock Names Queue"
    Service = "Stock Processing"
  }
}

# Output the queue URLs for reference
output "stock_names_queue_url" {
  value = aws_sqs_queue.stock_names.url
}

output "stock_names_dlq_url" {
  value = aws_sqs_queue.stock_names_dlq.url
}