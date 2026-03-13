"""
Basic configuration for the EV charging pipeline.

Uses a medallion layout: bronze (raw), silver (cleaned/enriched), gold (aggregates).
S3 paths are under the same bucket with layer prefixes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date


# Medallion layer names (used in paths and docs)
BRONZE_LAYER = "bronze"
SILVER_LAYER = "silver"
GOLD_LAYER = "gold"


@dataclass(frozen=True)
class S3Config:
    bucket_name: str
    bronze_prefix: str = "bronze/openchargemap"
    silver_prefix: str = "silver/openchargemap"
    gold_prefix: str = "gold/openchargemap"

    def build_bronze_key(self, run_date: date | None = None, filename: str | None = None) -> str:
        """
        Build an S3 key for bronze (raw) OpenChargeMap data.
        Example: bronze/openchargemap/date=YYYY-MM-DD/openchargemap_poi_fi_xxx.json
        """
        if run_date is None:
            run_date = date.today()
        date_part = run_date.isoformat()
        prefix = self.bronze_prefix.rstrip("/")
        if filename is None:
            filename = "openchargemap_poi.json"
        return f"{prefix}/date={date_part}/{filename}"

    def build_raw_key(self, run_date: date | None = None, filename: str | None = None) -> str:
        """Alias for build_bronze_key for backward compatibility."""
        return self.build_bronze_key(run_date=run_date, filename=filename)


def get_s3_config() -> S3Config:
    """
    Create S3Config from environment variables.

    Required:
    - EV_PIPELINE_S3_BUCKET: Name of the S3 bucket.

    Optional (medallion prefixes under the bucket):
    - EV_PIPELINE_BRONZE_PREFIX: Bronze (raw) data prefix (default bronze/openchargemap).
    - EV_PIPELINE_SILVER_PREFIX: Silver (cleaned) tables prefix (default silver/openchargemap).
    - EV_PIPELINE_GOLD_PREFIX: Gold (aggregates) prefix (default gold/openchargemap).
    """
    bucket = os.getenv("EV_PIPELINE_S3_BUCKET")
    if not bucket:
        raise RuntimeError(
            "Environment variable EV_PIPELINE_S3_BUCKET is required for S3 uploads."
        )

    bronze_prefix = os.getenv("EV_PIPELINE_BRONZE_PREFIX", "bronze/openchargemap")
    silver_prefix = os.getenv("EV_PIPELINE_SILVER_PREFIX", "silver/openchargemap")
    gold_prefix = os.getenv("EV_PIPELINE_GOLD_PREFIX", "gold/openchargemap")
    return S3Config(
        bucket_name=bucket,
        bronze_prefix=bronze_prefix,
        silver_prefix=silver_prefix,
        gold_prefix=gold_prefix,
    )


