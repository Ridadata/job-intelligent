# Power BI - Supabase Live Connection Guide (Latest Schema)

This guide fixes the common misalignment issue between exported CSV snapshots and
the current Supabase schema. The recommended setup is to connect Power BI directly
to Supabase so dashboards always read the latest data.

## 1) Prerequisites

- Power BI Desktop (latest)
- Access to Supabase project database credentials
- SQL Editor access in Supabase

## 2) Prepare the analytical star schema (one-time)

1. Open Supabase SQL Editor.
2. Run [powerbi/star_schema.sql](powerbi/star_schema.sql).
3. Verify these views exist under schema `powerbi`:
   - dim_date, dim_source, dim_contract, dim_company, dim_location, dim_role, dim_skill
   - fact_job_offers, fact_skill_demand, fact_recommendation_events, fact_pipeline_runs

This ensures Power BI model tables stay aligned with the latest project schema.

## 3) Connection details from Supabase

From Supabase Dashboard -> Settings -> Database:
- Host: db.<project-ref>.supabase.co
- Port: 5432 (direct) or 6543 (pooler)
- Database: postgres
- User: postgres
- Password: <your-db-password>

## 4) Connect Power BI (recommended: DirectQuery)

1. Power BI Desktop -> Get Data -> PostgreSQL database.
2. Server: db.<project-ref>.supabase.co:5432
3. Database: postgres
4. Data Connectivity mode: DirectQuery
5. Advanced options (optional but recommended):
   - SQL statement: `set statement_timeout = '120s';`
6. Authentication:
   - Username: postgres
   - Password: <your-db-password>
7. Ensure SSL is required by connector settings.

If direct 5432 has networking issues, retry with 6543.

## 5) Tables to select in Navigator

Select the `powerbi` schema views:
- powerbi.dim_date
- powerbi.dim_source
- powerbi.dim_contract
- powerbi.dim_company
- powerbi.dim_location
- powerbi.dim_role
- powerbi.dim_skill
- powerbi.fact_job_offers
- powerbi.fact_skill_demand
- powerbi.fact_recommendation_events
- powerbi.fact_pipeline_runs

Then create relationships from [powerbi/star_schema.md](powerbi/star_schema.md).

## 6) Keeping data always up-to-date

## Preferred (live)
- Use DirectQuery to Supabase.
- Dashboard reflects latest ETL writes without CSV re-export.

## Import mode (if required)
- Use scheduled refresh in Power BI Service (every 6 hours).
- Keep refresh aligned with Airflow `job_etl` schedule.

## CSV fallback (offline only)
- Use [powerbi/export_to_csv.py](powerbi/export_to_csv.py), now aligned with current schema.
- Example:
  - `python powerbi/export_to_csv.py --clean`
  - `python powerbi/export_to_csv.py --since 2026-01-01T00:00:00Z`

## 7) Troubleshooting

| Issue | Resolution |
|---|---|
| Connection timeout | Validate Supabase project status; try port 6543 |
| SSL error | Force SSL mode in connector |
| Permission denied on `powerbi` views | Re-run [powerbi/star_schema.sql](powerbi/star_schema.sql) to grant SELECT |
| Dashboard not updating | Confirm DirectQuery mode or refresh schedule |
| Data mismatch with app | Use `powerbi` schema views, not legacy `candidates`/`recommendations` tables |

## 8) Validation checklist

After connecting:
- `fact_job_offers` row count > 0
- `fact_pipeline_runs` contains recent stages
- `fact_recommendation_events` contains actions (`shown`, `saved`, etc.)
- `dim_source` contains expected providers (adzuna, jsearch, rekrute, emploi_ma, etc.)
