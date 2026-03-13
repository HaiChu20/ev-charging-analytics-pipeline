SELECT
  *
FROM delta.`s3a://${pipeline_bucket}/gold/openchargemap/operator_connector_summary`
ORDER BY operator_name, connector_count DESC;

