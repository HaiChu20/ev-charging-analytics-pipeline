SELECT
  *
FROM delta.`s3a://${pipeline_bucket}/gold/openchargemap/connectors_by_type`
ORDER BY connector_count DESC;

