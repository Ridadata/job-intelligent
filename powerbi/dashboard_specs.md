# Power BI Dashboard — Design Specification

## Overview
3-page dashboard connected to Supabase PostgreSQL, refreshing from materialized views.

---

## Page 1: Market Overview

### KPI Cards (top row)
| Card               | Source View           | Measure                  |
|--------------------|-----------------------|--------------------------|
| Total Active Offers| mv_market_trends      | SUM(offer_count)         |
| Unique Companies   | mv_top_companies      | COUNT(company_name)      |
| Avg Salary (€)     | mv_salary_by_role     | AVG(salary_avg)          |
| Top Skill          | mv_offers_by_skill    | TOPN(1, skill_name)      |

### Visuals
1. **Line Chart — Weekly Offer Trends**
   - Source: `mv_market_trends`
   - X-axis: `week_date`
   - Y-axis: `offer_count`
   - Legend: `source_name`
   - Last 12 weeks

2. **Map — Offers by Location (France)**
   - Source: `mv_offers_by_location`
   - Location: `city`
   - Bubble size: `offer_count`
   - Tooltip: `avg_salary`
   - Filter: France only

3. **Horizontal Bar Chart — Top 15 Skills**
   - Source: `mv_offers_by_skill`
   - Y-axis: `skill_name` (sorted by count)
   - X-axis: `offer_count`
   - Filter: current week only

4. **Donut Chart — Offers by Source**
   - Source: `mv_market_trends`
   - Values: `SUM(offer_count)` per `source_name`

---

## Page 2: Salary Analysis

### Visuals
1. **Clustered Bar Chart — Salary Range by Role**
   - Source: `mv_salary_by_role`
   - X-axis: `job_title`
   - Y-axis: `salary_min`, `salary_avg`, `salary_max` (stacked ranges)
   - Sort by `salary_avg` DESC

2. **Matrix — Contract Type × Role**
   - Source: `mv_salary_by_role`
   - Rows: `job_title`
   - Columns: `contract_type`
   - Values: `salary_avg`, `offer_count`
   - Conditional formatting: heat map on salary_avg

3. **Scatter Plot — Salary vs. Offer Count**
   - Source: `mv_salary_by_role`
   - X-axis: `offer_count`
   - Y-axis: `salary_avg`
   - Size: `offer_count`
   - Color: `contract_type`
   - Labels: `job_title`

4. **Card — DAX Measures**
   - Median Salary (see DAX below)
   - Salary Growth YoY %
   - Top Paying Role

---

## Page 3: Skill Matching (Interactive)

### Visuals
1. **What-If Parameter — Candidate Skills**
   - Multi-select slicer for skills (from `mv_offers_by_skill.skill_name`)
   - Creates a virtual "candidate profile"

2. **Gauge — Profile Match Score %**
   - DAX measure: count of selected skills appearing in each offer's `tech_stack`
   - Percentage = matched / total required skills
   - Red < 40%, Yellow 40-70%, Green > 70%

3. **Table — Top Matching Offers**
   - Columns: Title, Company, Location, Contract, Match %, Salary Range
   - Sorted by Match % DESC
   - Top 20 rows
   - Conditional formatting on Match %

4. **Bar Chart — Skill Gap Analysis**
   - Shows top skills required by matching offers NOT in candidate's selection
   - "Skills you should learn"

---

## Filters (Global)
- Date range slicer (published_at)
- Contract type slicer
- Location slicer
- Source slicer

## Refresh
- Scheduled refresh: every 6 hours (aligned with Airflow DAG)
- Connection: DirectQuery to Supabase PostgreSQL (MVs are pre-aggregated)
