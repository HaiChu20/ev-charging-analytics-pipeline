# Databricks notebook source
# MAGIC %md
# MAGIC # EV Charging Analytics Dashboard
# MAGIC
# MAGIC Each section answers a specific question for EV charging strategy, coverage, and competition. Uses POI + reference data. Set **bucket_name** to your S3 bucket.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Config & load data

# COMMAND ----------

dbutils.widgets.text("bucket_name", "ev-charging-pipeline-mhchu-demo", "S3 bucket name")

bucket = dbutils.widgets.get("bucket_name")
silver_prefix = f"s3a://{bucket}/silver/openchargemap"
gold_prefix = f"s3a://{bucket}/gold/openchargemap"

stations = spark.read.format("delta").load(f"{silver_prefix}/stations")
connections = spark.read.format("delta").load(f"{silver_prefix}/connections")
kpi_df = spark.read.format("delta").load(f"{gold_prefix}/kpi_summary")
stations_by_region = spark.read.format("delta").load(f"{gold_prefix}/stations_by_region")
connectors_by_type = spark.read.format("delta").load(f"{gold_prefix}/connectors_by_type")

def _load_if_exists(path):
    try:
        return spark.read.format("delta").load(path)
    except Exception:
        return None

stations_by_operator = _load_if_exists(f"{gold_prefix}/stations_by_operator")
stations_by_usage_type = _load_if_exists(f"{gold_prefix}/stations_by_usage_type")
operator_connector_summary = _load_if_exists(f"{gold_prefix}/operator_connector_summary")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 2. What is the scale of infrastructure in this dataset?

# COMMAND ----------

display(kpi_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Where is coverage? (Which regions have the most or least stations?)

# COMMAND ----------

display(stations_by_region)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 4. What connector types and power levels are deployed? (Interoperability & fast vs AC)

# COMMAND ----------

display(connectors_by_type)

# COMMAND ----------

from pyspark.sql import functions as F

power_buckets = (
    connections.filter(F.col("power_kw").isNotNull())
    .withColumn(
        "power_bucket",
        F.when(F.col("power_kw") < 7, "0–7 kW (AC)")
        .when(F.col("power_kw") < 50, "7–50 kW")
        .when(F.col("power_kw") < 150, "50–150 kW (fast)")
        .otherwise("150+ kW (ultra-fast)"),
    )
    .groupBy("power_bucket")
    .agg(F.count("*").alias("connector_count"))
    .orderBy("power_bucket")
)
display(power_buckets)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 5. Who are the main players? (Which operators have the largest footprint?)

# COMMAND ----------

if stations_by_operator is not None:
    display(stations_by_operator)
else:
    print("Run ingest with reference data to see stations by operator.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 6. Which operators focus on fast charging? (Share of connectors ≥50 kW per operator)

# COMMAND ----------

if "operator_name" in stations.columns:
    fast = F.when(F.col("power_kw") >= 50, 1).otherwise(0)
    conn_with_op = (
        connections
        .join(stations.select("station_id", "operator_name"), "station_id")
        .filter(F.col("operator_name").isNotNull())
    )
    operator_fast_share = (
        conn_with_op
        .groupBy("operator_name")
        .agg(
            F.count("*").alias("total_connectors"),
            F.sum(fast).alias("fast_connectors"),
            F.round(F.avg("power_kw"), 1).alias("avg_power_kw"),
        )
        .withColumn("fast_share_pct", F.round(F.col("fast_connectors") / F.col("total_connectors") * 100, 1))
        .orderBy(F.desc("total_connectors"))
        .limit(25)
    )
    display(operator_fast_share)
else:
    print("Run ingest with reference data to see operator fast-charging share.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 7. What do operators offer? (Operator × connector type – who bets on CCS, CHAdeMO, etc.)

# COMMAND ----------

if operator_connector_summary is not None:
    display(operator_connector_summary)
else:
    print("Run ingest with reference data to see operator–connector mix.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 8. How much is public vs restricted? (Stations by usage type – accessibility)

# COMMAND ----------

if stations_by_usage_type is not None:
    display(stations_by_usage_type)
else:
    print("Run ingest with reference data to see public vs other usage types.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 9. Where are the high-capacity sites? (Top stations by connector count – key assets)

# COMMAND ----------

station_conn_counts = connections.groupBy("station_id").agg(
    F.count("*").alias("connector_count"),
    F.sum("quantity").alias("total_points"),
    F.round(F.avg("power_kw"), 1).alias("avg_power_kw"),
)
top_stations = (
    stations.join(station_conn_counts, "station_id")
    .select(
        stations.station_id,
        stations.title,
        stations.town,
        station_conn_counts.connector_count,
        station_conn_counts.total_points,
        station_conn_counts.avg_power_kw,
    )
    .orderBy(F.desc("connector_count"))
    .limit(20)
)
if "operator_name" in stations.columns:
    top_stations = top_stations.join(
        stations.select("station_id", "operator_name"), "station_id"
    ).select("station_id", "title", "town", "operator_name", "connector_count", "total_points", "avg_power_kw")
display(top_stations)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 10. Where are stations on the map?

# COMMAND ----------

map_df = (
    stations.select("station_id", "title", "latitude", "longitude", "town")
    .filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull())
    .limit(500)
)
display(map_df)
