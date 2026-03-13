variable "aws_instance_profile_arn" {
  description = "Optional: AWS instance profile ARN to allow the Databricks cluster to access S3 (recommended). Example: arn:aws:iam::<acct>:instance-profile/<name>."
  type        = string
  default     = null
}

variable "cluster_name" {
  description = "Name of the Databricks cluster created by Terraform."
  type        = string
  default     = "ev-charging-dev"
}

variable "cluster_num_workers" {
  description = "Number of workers for the cluster (small to control cost)."
  type        = number
  default     = 1
}

variable "cluster_autotermination_minutes" {
  description = "Auto-terminate cluster after this many minutes of inactivity."
  type        = number
  default     = 30
}

variable "job_name" {
  description = "Name of the Databricks job that runs the pipeline notebook."
  type        = string
  default     = "ev-charging-openchargemap-pipeline"
}

variable "notebook_ingest_orchestrator_path" {
  description = "Workspace path of the ingest orchestrator notebook (entry point for the pipeline)."
  type        = string
  default     = "/Shared/ev-charging/01_ingest_orchestrator"
}

variable "notebook_read_bronze_path" {
  description = "Workspace path of the read_bronze notebook."
  type        = string
  default     = "/Shared/ev-charging/02_read_bronze"
}

variable "notebook_build_silver_path" {
  description = "Workspace path of the build_silver notebook."
  type        = string
  default     = "/Shared/ev-charging/03_build_silver"
}

variable "notebook_build_gold_path" {
  description = "Workspace path of the build_gold notebook."
  type        = string
  default     = "/Shared/ev-charging/04_build_gold"
}

variable "job_timezone" {
  description = "Timezone for the job schedule."
  type        = string
  default     = "Europe/Helsinki"
}

variable "job_quartz_cron" {
  description = "Quartz cron expression for scheduling the job. Default runs daily at 06:00."
  type        = string
  default     = "0 0 6 * * ?"
}

variable "pipeline_bucket_name" {
  description = "S3 bucket name passed into the notebook (widget bucket_name)."
  type        = string
}

variable "pipeline_partition_date" {
  description = "Partition date passed into the notebook (widget partition_date), format YYYY-MM-DD or 'auto' for today's date."
  type        = string
}


