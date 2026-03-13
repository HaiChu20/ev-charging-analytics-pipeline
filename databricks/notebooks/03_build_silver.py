# Databricks notebook source
# MAGIC %md
# MAGIC # 03 – Build silver (stations + connections)
# MAGIC
# MAGIC Builds **stations** and **connections** from `raw_df` (from 02_read_bronze), enriches with reference lookups, and writes Delta to silver. Expects `raw_df` and ref_* in the session.

# COMMAND ----------

bucket = dbutils.widgets.get("bucket_name")

stations_path = f"s3a://{bucket}/silver/openchargemap/stations"
connections_path = f"s3a://{bucket}/silver/openchargemap/connections"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build stations table

# COMMAND ----------

from pyspark.sql import functions as F

stations_df = (
    raw_df
    .select(
        F.col("ID").alias("station_id"),
        F.col("UUID").alias("station_uuid"),
        F.col("AddressInfo.Title").alias("title"),
        F.col("AddressInfo.AddressLine1").alias("address_line1"),
        F.col("AddressInfo.Town").alias("town"),
        F.col("AddressInfo.StateOrProvince").alias("state_or_province"),
        F.col("AddressInfo.Postcode").alias("postcode"),
        F.col("AddressInfo.CountryID").alias("country_id"),
        F.col("AddressInfo.Latitude").alias("latitude"),
        F.col("AddressInfo.Longitude").alias("longitude"),
        F.col("OperatorID").alias("operator_id"),
        F.col("UsageTypeID").alias("usage_type_id"),
        F.col("StatusTypeID").alias("status_type_id"),
        F.col("NumberOfPoints").alias("number_of_points"),
        F.col("DateLastStatusUpdate").alias("date_last_status_update"),
        F.col("DateCreated").alias("date_created"),
        F.col("DataQualityLevel").alias("data_quality_level"),
    )
    .dropDuplicates(["station_id"])
)
stations_df.cache()
print(f"Stations count: {stations_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build connections table

# COMMAND ----------

connections_df = (
    raw_df
    .select(
        F.col("ID").alias("station_id"),
        F.explode("Connections").alias("conn"),
    )
    .select(
        "station_id",
        F.col("conn.ID").alias("connection_id"),
        F.col("conn.ConnectionTypeID").alias("connection_type_id"),
        F.col("conn.CurrentTypeID").alias("current_type_id"),
        F.col("conn.LevelID").alias("level_id"),
        F.col("conn.PowerKW").alias("power_kw"),
        F.col("conn.Quantity").alias("quantity"),
        F.col("conn.StatusTypeID").alias("status_type_id"),
    )
)
print(f"Connections count: {connections_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enrich with reference labels

# COMMAND ----------

if has_reference and ref_operators is not None and ref_countries is not None and ref_usage_types is not None and ref_status_types is not None:
    stations_df = stations_df.join(ref_operators, stations_df.operator_id == ref_operators.id, "left").select(
        stations_df["*"], ref_operators.title.alias("operator_name")
    )
    stations_df = stations_df.join(ref_countries, stations_df.country_id == ref_countries.id, "left").select(
        stations_df["*"], ref_countries.title.alias("country_name")
    )
    stations_df = stations_df.join(ref_usage_types, stations_df.usage_type_id == ref_usage_types.id, "left").select(
        stations_df["*"], ref_usage_types.title.alias("usage_type_name")
    )
    stations_df = stations_df.join(ref_status_types, stations_df.status_type_id == ref_status_types.id, "left").select(
        stations_df["*"], ref_status_types.title.alias("status_type_name")
    )
    if ref_connection_types is not None:
        connections_df = connections_df.join(ref_connection_types, connections_df.connection_type_id == ref_connection_types.id, "left").select(
            connections_df["*"], ref_connection_types.title.alias("connection_type_name")
        )
    print("Enrichment applied.")
else:
    print("Skipping enrichment (reference data not available).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write silver Delta

# COMMAND ----------

stations_df.write.format("delta").mode("overwrite").save(stations_path)
connections_df.write.format("delta").mode("overwrite").save(connections_path)
print(f"Wrote silver: {stations_path}, {connections_path}")
