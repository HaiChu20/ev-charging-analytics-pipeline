# Databricks notebooks

## Medallion layout (bronze → silver → gold)

- **Bronze:** Raw JSON in `s3://bucket/bronze/openchargemap/date=YYYY-MM-DD/` — **two sources:** POI (`/v3/poi`) and **reference** (`/v3/referencedata/`).
- **Silver:** Delta tables `stations`, `connections` in `s3://bucket/silver/openchargemap/` (enriched with reference labels when available).
- **Gold:** `kpi_summary`, `stations_by_region`, `connectors_by_type`; plus **reference-driven:** `stations_by_operator`, `stations_by_usage_type`, `operator_connector_summary` in `s3://bucket/gold/openchargemap/`.

---

## Ingest pipeline (split into four notebooks)

The ingest is split so no single file is too long. Run **01_ingest_orchestrator** (it %run’s the others in order).

| Notebook | Purpose |
|----------|---------|
| **01_ingest_orchestrator** | Widgets `bucket_name`, `partition_date`; runs 02 → 03 → 04. **Job entry point.** |
| **02_read_bronze** | Read bronze POI and reference JSON; build `raw_df` and ref lookup tables. |
| **03_build_silver** | Build stations and connections from `raw_df`, enrich with ref, write silver Delta. |
| **04_build_gold** | Read silver, build aggregate tables (including reference-driven: stations by operator, by usage type, operator–connector summary), write gold Delta. |

All four must live in the same workspace folder (e.g. `/Shared/ev-charging/`) so `%run ./02_read_bronze` etc. resolve. The job runs **01_ingest_orchestrator** with `bucket_name` and `partition_date`; the orchestrator passes the same Spark session to 02, 03, 04.

### Running

Run **01_ingest_orchestrator** (or trigger the job). It will read bronze, write silver, then write gold.

---

## 05_analytics_dashboard.py

**Purpose:** Dashboard over **silver** and **gold** Delta tables: gold KPIs, stations by region, connectors by type; silver detail, power buckets, top stations, map.

**Widget:** **bucket_name** – same S3 bucket. Attach the cluster and Run all; use each cell’s chart type (bar, pie, map) for visualizations.

---

## 01_ingest_openchargemap.py (legacy single-file)

A single-file version of the full ingest (bronze → silver → gold) is kept for reference. Prefer the orchestrator + 02/03/04 for maintenance.
