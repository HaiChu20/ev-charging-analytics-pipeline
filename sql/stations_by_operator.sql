SELECT
  *
FROM delta.`s3a://${pipeline_bucket}/gold/openchargemap/stations_by_operator`
ORDER BY station_count DESC;

