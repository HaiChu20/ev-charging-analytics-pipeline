# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest pipeline (orchestrator)
# MAGIC
# MAGIC Entry point for the Bronze → Silver → Gold pipeline. Defines widgets and runs the steps in order.
# MAGIC - **02_read_bronze:** Read POI and reference JSON from bronze, build lookup tables.
# MAGIC - **03_build_silver:** Build stations and connections, enrich, write silver Delta.
# MAGIC - **04_build_gold:** Read silver, build aggregates, write gold Delta.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Config (widgets + auto date)

# COMMAND ----------
from datetime import date

# Bucket name always comes from the job (Terraform), but we keep a widget so you
# can override it when running interactively.
dbutils.widgets.text("bucket_name", "ev-charging-pipeline-mhchu-demo", "S3 bucket name")

# For scheduled runs, set pipeline_partition_date = "auto" (or leave empty) in Terraform.
# Then this notebook will use today's date. For backfills, pass an explicit YYYY-MM-DD.
dbutils.widgets.text("partition_date", "", "Partition date (YYYY-MM-DD) or 'auto' (today)")

bucket = dbutils.widgets.get("bucket_name")
raw_partition = dbutils.widgets.get("partition_date")

if (not raw_partition) or (raw_partition.lower() == "auto"):
    partition_date = date.today().isoformat()
else:
    partition_date = raw_partition

print(f"Bucket: {bucket}, partition_date: {partition_date}")


# MAGIC %md
# MAGIC ## 2. Run pipeline steps (02–04)

# COMMAND ----------

# MAGIC %run ./02_read_bronze

# COMMAND ----------

# MAGIC %run ./03_build_silver

# COMMAND ----------

# MAGIC %run ./04_build_gold

# COMMAND ----------

# MAGIC %md
# MAGIC Pipeline complete. Silver (stations, connections) and gold aggregates are written to S3.
