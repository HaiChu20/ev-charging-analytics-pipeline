SELECT
  *
FROM delta.`s3a://${pipeline_bucket}/gold/openchargemap/stations_by_usage_type`
ORDER BY station_count DESC;

