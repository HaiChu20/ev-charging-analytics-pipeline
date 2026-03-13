terraform {
  required_version = ">= 1.6.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.60.0"
    }
  }
}

provider "databricks" {
}

data "databricks_spark_version" "latest_lts" {
  long_term_support = true
}

data "databricks_node_type" "smallest" {
  local_disk = false
}

locals {
  notebook_ingest_orchestrator = "${path.module}/../../databricks/notebooks/01_ingest_orchestrator.py"
  notebook_read_bronze         = "${path.module}/../../databricks/notebooks/02_read_bronze.py"
  notebook_build_silver        = "${path.module}/../../databricks/notebooks/03_build_silver.py"
  notebook_build_gold          = "${path.module}/../../databricks/notebooks/04_build_gold.py"
  notebook_dashboard           = "${path.module}/../../databricks/notebooks/05_analytics_dashboard.py"
}

resource "databricks_sql_endpoint" "ev_charging_warehouse" {
  name                     = "ev-charging-sql-warehouse"
  cluster_size             = "2X-Small"
  max_num_clusters         = 1
  auto_stop_mins           = 30
  enable_serverless_compute = false
  enable_photon            = true
  warehouse_type           = "PRO"
}

resource "databricks_cluster" "ev_charging_dev" {
  cluster_name            = var.cluster_name
  spark_version           = data.databricks_spark_version.latest_lts.id
  node_type_id            = "r5d.large"
  autotermination_minutes = var.cluster_autotermination_minutes
  num_workers             = var.cluster_num_workers

  aws_attributes {
    availability         = "ON_DEMAND"
    instance_profile_arn = var.aws_instance_profile_arn

  }
}

resource "databricks_notebook" "ingest_orchestrator" {
  path     = var.notebook_ingest_orchestrator_path
  language = "PYTHON"
  source   = local.notebook_ingest_orchestrator
}

resource "databricks_notebook" "read_bronze" {
  path     = var.notebook_read_bronze_path
  language = "PYTHON"
  source   = local.notebook_read_bronze
}

resource "databricks_notebook" "build_silver" {
  path     = var.notebook_build_silver_path
  language = "PYTHON"
  source   = local.notebook_build_silver
}

resource "databricks_notebook" "build_gold" {
  path     = var.notebook_build_gold_path
  language = "PYTHON"
  source   = local.notebook_build_gold
}

resource "databricks_job" "openchargemap_pipeline" {
  name = var.job_name

  schedule {
    quartz_cron_expression = var.job_quartz_cron
    timezone_id            = var.job_timezone
  }

  task {
    task_key = "run_ingest_pipeline"

    notebook_task {
      notebook_path = databricks_notebook.ingest_orchestrator.path
      base_parameters = {
        bucket_name     = var.pipeline_bucket_name
        partition_date  = var.pipeline_partition_date
      }
    }

    existing_cluster_id = databricks_cluster.ev_charging_dev.cluster_id
  }
}

resource "databricks_sql_query" "gold_kpi" {
  name           = "EV charging – KPI summary"
  data_source_id = databricks_sql_endpoint.ev_charging_warehouse.data_source_id

  query = replace(
    file("${path.module}/../../sql/gold_kpi.sql"),
    "$${pipeline_bucket}",
    var.pipeline_bucket_name,
  )
}

resource "databricks_sql_query" "stations_by_region" {
  name           = "EV charging – Stations by region"
  data_source_id = databricks_sql_endpoint.ev_charging_warehouse.data_source_id

  query = replace(
    file("${path.module}/../../sql/stations_by_region.sql"),
    "$${pipeline_bucket}",
    var.pipeline_bucket_name,
  )
}

resource "databricks_sql_query" "connectors_by_type" {
  name           = "EV charging – Connectors by type"
  data_source_id = databricks_sql_endpoint.ev_charging_warehouse.data_source_id

  query = replace(
    file("${path.module}/../../sql/connectors_by_type.sql"),
    "$${pipeline_bucket}",
    var.pipeline_bucket_name,
  )
}

resource "databricks_sql_query" "stations_by_operator" {
  name           = "EV charging – Stations by operator"
  data_source_id = databricks_sql_endpoint.ev_charging_warehouse.data_source_id

  query = replace(
    file("${path.module}/../../sql/stations_by_operator.sql"),
    "$${pipeline_bucket}",
    var.pipeline_bucket_name,
  )
}

resource "databricks_sql_query" "stations_by_usage_type" {
  name           = "EV charging – Stations by usage type"
  data_source_id = databricks_sql_endpoint.ev_charging_warehouse.data_source_id

  query = replace(
    file("${path.module}/../../sql/stations_by_usage_type.sql"),
    "$${pipeline_bucket}",
    var.pipeline_bucket_name,
  )
}

resource "databricks_sql_query" "operator_connector_summary" {
  name           = "EV charging – Operator connector mix"
  data_source_id = databricks_sql_endpoint.ev_charging_warehouse.data_source_id

  query = replace(
    file("${path.module}/../../sql/operator_connector_summary.sql"),
    "$${pipeline_bucket}",
    var.pipeline_bucket_name,
  )
}

