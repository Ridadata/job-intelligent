# Power BI Starter Star Schema (Job Intelligent)

This file defines the recommended semantic model for Power BI using analytical views created in [powerbi/star_schema.sql](powerbi/star_schema.sql).

## 1) Why this schema

The star schema isolates dimensions (filters) from facts (metrics/events) and gives:
- Better performance in Power BI.
- Cleaner DAX measures.
- Stable model aligned with latest Supabase tables.

## 2) Objects to load in Power BI

## Dimensions
- powerbi.dim_date
- powerbi.dim_source
- powerbi.dim_contract
- powerbi.dim_company
- powerbi.dim_location
- powerbi.dim_role
- powerbi.dim_skill

## Facts
- powerbi.fact_job_offers
- powerbi.fact_skill_demand
- powerbi.fact_recommendation_events
- powerbi.fact_pipeline_runs

## 3) Relationship blueprint

Create these relationships in Model view:

1. dim_date[date_key] (1) -> fact_job_offers[published_date_key] (*)
2. dim_source[source_id] (1) -> fact_job_offers[source_id] (*)
3. dim_company[company_key] (1) -> fact_job_offers[company_key] (*)
4. dim_location[location_key] (1) -> fact_job_offers[location_key] (*)
5. dim_contract[contract_type] (1) -> fact_job_offers[contract_type] (*)
6. dim_skill[skill_name] (1) -> fact_skill_demand[skill_name] (*)
7. fact_job_offers[offer_id] (1) -> fact_skill_demand[offer_id] (*)
8. fact_job_offers[offer_id] (1) -> fact_recommendation_events[offer_id] (*)
9. dim_date[date_key] (1) -> fact_recommendation_events[event_date_key] (*)
10. dim_date[date_key] (1) -> fact_pipeline_runs[started_date_key] (*)

Use single-direction filter flow from dimension to fact.

## 4) Grain definition (important)

- fact_job_offers: one row per job offer.
- fact_skill_demand: one row per (job offer, skill).
- fact_recommendation_events: one row per recommendation action event.
- fact_pipeline_runs: one row per ETL stage run.

## 5) Recommended measures

- Total Offers = COUNTROWS(fact_job_offers)
- Avg Salary = AVERAGE(fact_job_offers[salary_max])
- Recommendation Events = COUNTROWS(fact_recommendation_events)
- Save Rate = DIVIDE(
    CALCULATE(COUNTROWS(fact_recommendation_events), fact_recommendation_events[action] = "saved"),
    CALCULATE(COUNTROWS(fact_recommendation_events), fact_recommendation_events[action] = "shown"),
    0
  )
- ETL Success Rate = DIVIDE(
    CALCULATE(COUNTROWS(fact_pipeline_runs), fact_pipeline_runs[status] = "success"),
    COUNTROWS(fact_pipeline_runs),
    0
  )

## 6) Refresh strategy

- Preferred: DirectQuery to Supabase PostgreSQL for near-real-time analysis.
- Alternative: Import mode + scheduled refresh every 6 hours.
- If using CSV export fallback, regenerate snapshot with [powerbi/export_to_csv.py](powerbi/export_to_csv.py).
