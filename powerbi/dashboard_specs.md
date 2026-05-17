# Power BI Dashboard - Design Specification (Star Schema)

## Overview
3-page dashboard connected to Supabase PostgreSQL using the `powerbi` star-schema views
defined in [powerbi/star_schema.sql](powerbi/star_schema.sql).

---

## Page 1: Market Overview

### KPI Cards (top row)
| Card | Source | Measure |
|---|---|---|
| Total Active Offers | powerbi.fact_job_offers | COUNTROWS(fact_job_offers) |
| Unique Companies | powerbi.dim_company | DISTINCTCOUNT(dim_company[company_name]) |
| Avg Salary (EUR) | powerbi.fact_job_offers | AVERAGE(fact_job_offers[salary_max]) |
| Top Skill | powerbi.fact_skill_demand | TOPN by COUNT(offer_id) |

### Visuals
1. **Line Chart - Weekly Offer Trends**
   - Source: `powerbi.fact_job_offers` + `powerbi.dim_date`
   - X-axis: `dim_date.date_day`
   - Y-axis: count of `fact_job_offers.offer_id`
   - Legend: `powerbi.dim_source.source_name`
   - Filter: last 12 weeks

2. **Map - Offers by Location (France)**
   - Source: `powerbi.fact_job_offers` + `powerbi.dim_location`
   - Location: `dim_location.location_name`
   - Bubble size: count of `fact_job_offers.offer_id`
   - Tooltip: average `salary_max`
   - Filter: France only

3. **Horizontal Bar Chart - Top 15 Skills**
   - Source: `powerbi.fact_skill_demand`
   - Y-axis: `skill_name` (sorted by count)
   - X-axis: count of `offer_id`
   - Filter: current week

4. **Donut Chart - Offers by Source**
   - Source: `powerbi.fact_job_offers` + `powerbi.dim_source`
   - Values: count of `offer_id` per `source_name`

---

## Page 2: Salary Analysis

### Visuals
1. **Clustered Bar Chart - Salary Range by Role**
   - Source: `powerbi.fact_job_offers`
   - X-axis: `normalized_title`
   - Y-axis: `salary_min`, average salary, `salary_max`
   - Sort by average salary DESC

2. **Matrix - Contract Type x Role**
   - Source: `powerbi.fact_job_offers`
   - Rows: `normalized_title`
   - Columns: `contract_type`
   - Values: average salary, offer count
   - Conditional formatting: heat map on average salary

3. **Scatter Plot - Salary vs Offer Count**
   - Source: `powerbi.fact_job_offers`
   - X-axis: offer count (by role)
   - Y-axis: average salary
   - Size: offer count
   - Color: contract_type
   - Labels: normalized_title

4. **Card - DAX Measures**
   - Median Salary (see DAX below)
   - Salary Growth YoY %
   - Top Paying Role

---

## Page 3: Skill Matching (Interactive)

### Visuals
1. **What-If Parameter - Candidate Skills**
   - Multi-select slicer from `powerbi.dim_skill.skill_name`
   - Creates a virtual candidate profile

2. **Gauge - Profile Match Score %**
   - DAX measure: count of selected skills appearing in each offer's `tech_stack`
   - Percentage = matched / total required skills
   - Red < 40%, Yellow 40-70%, Green > 70%

3. **Table - Top Matching Offers**
   - Columns: Title, Company, Location, Contract, Match %, Salary Range
   - Sorted by Match % DESC
   - Top 20 rows
   - Conditional formatting on Match %

4. **Bar Chart - Skill Gap Analysis**
   - Shows top skills required by matching offers NOT in candidate's selection
   - "Skills you should learn"

---

## Filters (Global)
- Date range slicer (published_at)
- Contract type slicer
- Location slicer
- Source slicer

## Refresh
- Preferred: DirectQuery to Supabase PostgreSQL (`powerbi` views)
- Import fallback: scheduled refresh every 6 hours (aligned with Airflow DAG)
