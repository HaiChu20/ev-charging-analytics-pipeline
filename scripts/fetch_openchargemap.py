import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root on path so "from src.xxx" works when run as: python scripts/fetch_openchargemap.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import requests


POI_URL = "https://api.openchargemap.io/v3/poi"
REFERENCE_URL = "https://api.openchargemap.io/v3/referencedata/"


def fetch_referencedata(api_key: str) -> Dict[str, Any]:
    """
    Fetch reference data (connection types, operators, countries, usage/status types).
    Used to enrich POI/connections with human-readable labels in the pipeline.
    """
    params = {"key": api_key}
    resp = requests.get(REFERENCE_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("Expected object response from OpenChargeMap /referencedata endpoint")
    return data


def fetch_poi(
    api_key: str,
    country_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    distance_km: Optional[float] = None,
    max_results: int = 500,
) -> List[Dict[str, Any]]:
    """
    Fetch points of interest (charging stations) from OpenChargeMap.

    This uses a single request with a limit (max_results). For a portfolio project
    this is usually enough; for larger coverage you would implement simple
    pagination or multiple bounding-box queries.
    """
    params: Dict[str, Any] = {
        "output": "json",
        "maxresults": max_results,
        "key": api_key,
        "compact": True,
        "verbose": False,
    }

    if country_code:
        params["countrycode"] = country_code

    if latitude is not None and longitude is not None and distance_km is not None:
        params["latitude"] = latitude
        params["longitude"] = longitude
        params["distance"] = distance_km
        params["distanceunit"] = "KM"

    resp = requests.get(POI_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not isinstance(data, list):
        raise ValueError("Expected list response from OpenChargeMap /poi endpoint")

    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch charging station data from OpenChargeMap /poi endpoint."
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="OCM_API_KEY",
        help="Name of the environment variable containing the OpenChargeMap API key.",
    )
    parser.add_argument(
        "--country-code",
        type=str,
        default=None,
        help="Filter by ISO country code (e.g. FI, SE).",
    )
    parser.add_argument(
        "--latitude",
        type=float,
        default=None,
        help="Latitude for radius-based search.",
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=None,
        help="Longitude for radius-based search.",
    )
    parser.add_argument(
        "--distance-km",
        type=float,
        default=None,
        help="Radius distance in kilometers for radius-based search.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=500,
        help="Maximum number of POIs to fetch in a single call.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join("data", "raw"),
        help="Directory to write the raw OpenChargeMap JSON file into.",
    )
    parser.add_argument(
        "--reference-only",
        action="store_true",
        help="Fetch only reference data (connection types, operators, countries, etc.) and write to openchargemap_reference_<timestamp>.json.",
    )

    args = parser.parse_args()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(
            f"Environment variable {args.api_key_env} is not set. "
            "Set it to your OpenChargeMap API key."
        )

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    if args.reference_only:
        ref = fetch_referencedata(api_key)
        filename = f"openchargemap_reference_{timestamp}.json"
        output_path = os.path.join(args.output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(ref, f, ensure_ascii=False, indent=2)
        print(f"Fetched reference data and wrote to {output_path}")
        return

    pois = fetch_poi(
        api_key=api_key,
        country_code=args.country_code,
        latitude=args.latitude,
        longitude=args.longitude,
        distance_km=args.distance_km,
        max_results=args.max_results,
    )

    filename_parts = ["openchargemap_poi"]
    if args.country_code:
        filename_parts.append(args.country_code.lower())
    filename_parts.append(timestamp)
    filename = "_".join(filename_parts) + ".json"
    output_path = os.path.join(args.output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pois, f, ensure_ascii=False, indent=2)

    print(f"Fetched {len(pois)} POIs and wrote to {output_path}")


if __name__ == "__main__":
    main()

