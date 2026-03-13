terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  # No profile: Terraform uses env vars (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION) from .env when you load them into the shell.
}

resource "aws_s3_bucket" "ev_demo" {
  bucket = var.bucket_name

  tags = {
    Project     = "ev-charging-pipeline"
    Environment = var.environment
  }
}

resource "aws_iam_role" "databricks_s3_access" {
  name = "databricks-ev-charging-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project     = "ev-charging-pipeline"
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "databricks_s3_policy_doc" {
  statement {
    sid    = "DatabricksS3Access"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:DeleteObject",
    ]

    resources = [
      aws_s3_bucket.ev_demo.arn,
      "${aws_s3_bucket.ev_demo.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "databricks_s3_policy" {
  name   = "databricks-ev-charging-s3-policy"
  policy = data.aws_iam_policy_document.databricks_s3_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "databricks_s3_attachment" {
  role       = aws_iam_role.databricks_s3_access.name
  policy_arn = aws_iam_policy.databricks_s3_policy.arn
}

resource "aws_iam_instance_profile" "databricks_s3_access" {
  name = aws_iam_role.databricks_s3_access.name
  role = aws_iam_role.databricks_s3_access.name
}

