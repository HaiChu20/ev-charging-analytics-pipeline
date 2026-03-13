SELECT
  metric,
  value
FROM delta.`s3a://${pipeline_bucket}/gold/openchargemap/kpi_summary`;

