import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# Project root on path so "from src.xxx" works when run as: python scripts/upload_sample_data.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import boto3
from botocore.exceptions import ClientError

from src.config import get_s3_config


def upload_file_to_s3(
    local_path: str,
    bucket: str,
    key: str,
    extra_args: Optional[dict] = None,
) -> str:
    """
    Upload a local file to S3 and return the s3:// URI.
    """
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    s3_client = boto3.client("s3")

    try:
        s3_client.upload_file(local_path, bucket, key, ExtraArgs=extra_args or {})
    except ClientError as exc:
        raise RuntimeError(f"Failed to upload {local_path} to s3://{bucket}/{key}") from exc

    return f"s3://{bucket}/{key}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload raw OpenChargeMap JSON file to S3."
    )
    parser.add_argument(
        "--input-path",
        type=str,
        default=None,
        help=(
            "Path to the local raw OpenChargeMap JSON file. "
            "If not provided, will look for the newest file under data/raw/."
        ),
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help=(
            "Run date in YYYY-MM-DD format for partitioning in S3. "
            "Defaults to today if not provided."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all JSON files from data/raw to the same date partition (use after fetching both POI and reference data).",
    )

    args = parser.parse_args()

    s3_cfg = get_s3_config()
    run_date = date.today()
    if args.date:
        try:
            run_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise SystemExit("Invalid --date format. Use YYYY-MM-DD.") from exc

    raw_dir = os.path.join("data", "raw")

    if args.input_path:
        local_path = args.input_path
        filename = os.path.basename(local_path)
        key = s3_cfg.build_bronze_key(run_date=run_date, filename=filename)
        uri = upload_file_to_s3(local_path=local_path, bucket=s3_cfg.bucket_name, key=key, extra_args={"ContentType": "application/json"})
        print(f"Uploaded {local_path} to {uri}")
    elif args.all:
        if not os.path.isdir(raw_dir):
            raise SystemExit(f"Raw dir does not exist: {raw_dir}")
        candidates = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(".json")]
        if not candidates:
            raise SystemExit("No JSON files in data/raw. Run fetch_openchargemap.py (and --reference-only) first.")
        for local_path in candidates:
            filename = os.path.basename(local_path)
            key = s3_cfg.build_bronze_key(run_date=run_date, filename=filename)
            uri = upload_file_to_s3(local_path=local_path, bucket=s3_cfg.bucket_name, key=key, extra_args={"ContentType": "application/json"})
            print(f"Uploaded {local_path} to {uri}")
    else:
        if not os.path.isdir(raw_dir):
            raise SystemExit(f"No --input-path and raw dir does not exist: {raw_dir}")
        candidates = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(".json")]
        if not candidates:
            raise SystemExit("No JSON files in data/raw. Run fetch_openchargemap.py first or use --input-path.")
        local_path = max(candidates, key=os.path.getmtime)
        filename = os.path.basename(local_path)
        key = s3_cfg.build_bronze_key(run_date=run_date, filename=filename)
        uri = upload_file_to_s3(local_path=local_path, bucket=s3_cfg.bucket_name, key=key, extra_args={"ContentType": "application/json"})
        print(f"Uploaded {local_path} to {uri}")


if __name__ == "__main__":
    main()

