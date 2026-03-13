# Databricks notebook source
# MAGIC %md
# MAGIC # 02 – Read bronze (POI + reference)
# MAGIC
# MAGIC Reads raw POI and reference JSON from bronze S3 path. Builds `raw_df` and reference lookup DataFrames for the next step. Expects widgets `bucket_name` and `partition_date` from the orchestrator.

# COMMAND ----------

bucket = dbutils.widgets.get("bucket_name")
partition_date = dbutils.widgets.get("partition_date")

bronze_prefix = f"s3a://{bucket}/bronze/openchargemap/date={partition_date}/"
raw_poi_glob = f"{bronze_prefix}openchargemap_poi*.json"
raw_ref_glob = f"{bronze_prefix}openchargemap_reference*.json"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read POI JSON

# COMMAND ----------

raw_df = spark.read.json(raw_poi_glob)
raw_df.cache()
print(f"Raw POI count: {raw_df.count()}")
raw_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read reference data and build lookups

# COMMAND ----------

from pyspark.sql import functions as F

has_reference = False
ref_connection_types = None
ref_operators = None
ref_countries = None
ref_usage_types = None
ref_status_types = None

try:
    ref_df = spark.read.json(raw_ref_glob)
    if ref_df.count() > 0:
        def to_lookup(df, col_name):
            if col_name not in df.columns:
                return None
            return df.select(F.explode(F.col(col_name)).alias("_ref")).select(
                F.col("_ref.ID").alias("id"), F.col("_ref.Title").alias("title")
            ).dropDuplicates(["id"])

        ref_connection_types = to_lookup(ref_df, "ConnectionTypes")
        ref_operators = to_lookup(ref_df, "Operators")
        ref_countries = to_lookup(ref_df, "Countries")
        ref_usage_types = to_lookup(ref_df, "UsageTypes")
        ref_status_types = to_lookup(ref_df, "StatusTypes")
        if ref_connection_types is not None:
            has_reference = True
            print("Reference data loaded; enrichment will be applied in build_silver.")
except Exception as e:
    print(f"No reference data or error (ID-only tables): {e}")
