# Databricks notebook source
# MAGIC %md
# MAGIC # 04 – Build gold (aggregates)
# MAGIC
# MAGIC Reads **silver** Delta tables, builds aggregate tables for dashboards, and writes to gold. Can run after 03_build_silver (same session) or standalone (reads silver from S3).

# COMMAND ----------

bucket = dbutils.widgets.get("bucket_name")

stations_path = f"s3a://{bucket}/silver/openchargemap/stations"
connections_path = f"s3a://{bucket}/silver/openchargemap/connections"
gold_prefix = f"s3a://{bucket}/gold/openchargemap"
gold_stations_by_region_path = f"{gold_prefix}/stations_by_region"
gold_connectors_by_type_path = f"{gold_prefix}/connectors_by_type"
gold_kpi_path = f"{gold_prefix}/kpi_summary"
# Reference-data–driven gold tables (when silver is enriched from reference API)
gold_stations_by_operator_path = f"{gold_prefix}/stations_by_operator"
gold_stations_by_usage_type_path = f"{gold_prefix}/stations_by_usage_type"
gold_operator_connector_summary_path = f"{gold_prefix}/operator_connector_summary"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load silver (in case this notebook runs standalone)

# COMMAND ----------

from pyspark.sql import functions as F

# If running after 03_build_silver, stations_df and connections_df may already exist; else read from S3
try:
    _ = stations_df
    _ = connections_df
except NameError:
    stations_df = spark.read.format("delta").load(stations_path)
    connections_df = spark.read.format("delta").load(connections_path)
    print("Loaded silver from S3.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: stations by region

# COMMAND ----------

region_col = "country_name" if "country_name" in stations_df.columns else "town"
gold_stations_by_region = (
    stations_df.groupBy(region_col)
    .agg(F.count("*").alias("station_count"))
    .orderBy(F.desc("station_count"))
)
gold_stations_by_region.write.format("delta").mode("overwrite").save(gold_stations_by_region_path)
print(f"Wrote: {gold_stations_by_region_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: connectors by type

# COMMAND ----------

conn_type_col = "connection_type_name" if "connection_type_name" in connections_df.columns else "connection_type_id"
gold_connectors_by_type = (
    connections_df.groupBy(conn_type_col)
    .agg(
        F.count("*").alias("connector_count"),
        F.round(F.avg("power_kw"), 1).alias("avg_power_kw"),
    )
    .orderBy(F.desc("connector_count"))
)
gold_connectors_by_type.write.format("delta").mode("overwrite").save(gold_connectors_by_type_path)
print(f"Wrote: {gold_connectors_by_type_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: KPI summary

# COMMAND ----------

from pyspark.sql import types as T

total_stations = stations_df.count()
total_connections = connections_df.count()

# Safely handle nulls from aggregations
raw_points = connections_df.agg(F.sum("quantity")).collect()[0][0]
raw_avg_power = (
    connections_df.filter(F.col("power_kw").isNotNull())
    .agg(F.avg("power_kw"))
    .collect()[0][0]
)

gold_kpi_data = [
    ("total_stations", float(total_stations)),
    ("total_connectors", float(total_connections)),
    ("total_charging_points", float(raw_points) if raw_points is not None else 0.0),
    (
        "avg_power_kw",
        float(round(float(raw_avg_power), 1)) if raw_avg_power is not None else None,
    ),
]

gold_kpi_schema = T.StructType(
    [
        T.StructField("metric", T.StringType(), False),
        T.StructField("value", T.DoubleType(), True),
    ]
)

gold_kpi = spark.createDataFrame(gold_kpi_data, schema=gold_kpi_schema)
gold_kpi.write.format("delta").mode("overwrite").save(gold_kpi_path)
print(f"Wrote: {gold_kpi_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: stations by operator (from reference data)

# COMMAND ----------

if "operator_name" in stations_df.columns:
    gold_stations_by_operator = (
        stations_df.filter(F.col("operator_name").isNotNull())
        .groupBy("operator_name")
        .agg(F.count("*").alias("station_count"))
        .orderBy(F.desc("station_count"))
        .limit(50)
    )
    gold_stations_by_operator.write.format("delta").mode("overwrite").save(gold_stations_by_operator_path)
    print(f"Wrote: {gold_stations_by_operator_path}")
else:
    print("Skip stations_by_operator (no operator_name; run with reference data).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: stations by usage type (from reference data)

# COMMAND ----------

if "usage_type_name" in stations_df.columns:
    gold_stations_by_usage_type = (
        stations_df.filter(F.col("usage_type_name").isNotNull())
        .groupBy("usage_type_name")
        .agg(F.count("*").alias("station_count"))
        .orderBy(F.desc("station_count"))
    )
    gold_stations_by_usage_type.write.format("delta").mode("overwrite").save(gold_stations_by_usage_type_path)
    print(f"Wrote: {gold_stations_by_usage_type_path}")
else:
    print("Skip stations_by_usage_type (no usage_type_name; run with reference data).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: operator × connector type summary (from reference data)

# COMMAND ----------

if "operator_name" in stations_df.columns and "connection_type_name" in connections_df.columns:
    operator_connector = (
        stations_df.select("station_id", "operator_name")
        .join(connections_df.select("station_id", "connection_type_name"), "station_id")
        .groupBy("operator_name", "connection_type_name")
        .agg(F.count("*").alias("connector_count"))
        .orderBy("operator_name", F.desc("connector_count"))
    )
    operator_connector.write.format("delta").mode("overwrite").save(gold_operator_connector_summary_path)
    print(f"Wrote: {gold_operator_connector_summary_path}")
else:
    print("Skip operator_connector_summary (need operator_name and connection_type_name; run with reference data).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify

# COMMAND ----------

print("Gold tables: stations_by_region, connectors_by_type, kpi_summary; + stations_by_operator, stations_by_usage_type, operator_connector_summary (when reference data used).")
