output "cluster_id" {
  description = "ID of the Databricks cluster created by Terraform"
  value       = databricks_cluster.ev_charging_dev.cluster_id
}

output "job_id" {
  description = "ID of the Databricks job created by Terraform"
  value       = databricks_job.openchargemap_pipeline.id
}

output "notebook_ingest_orchestrator_path" {
  description = "Workspace path of the ingest orchestrator (pipeline entry point)"
  value       = databricks_notebook.ingest_orchestrator.path
}

