output "bucket_name" {
  description = "Name of the S3 bucket for raw and processed data"
  value       = aws_s3_bucket.ev_demo.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket for raw and processed data"
  value       = aws_s3_bucket.ev_demo.arn
}

output "databricks_role_arn" {
  description = "IAM role ARN that Databricks clusters can assume to access S3"
  value       = aws_iam_role.databricks_s3_access.arn
}

output "databricks_instance_profile_arn" {
  description = "IAM instance profile ARN to use in Databricks cluster config (aws_instance_profile_arn)"
  value       = aws_iam_instance_profile.databricks_s3_access.arn
}

