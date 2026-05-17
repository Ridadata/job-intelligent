# Power BI DAX Measures (Star Schema)

These measures target the `powerbi` schema views created by
[powerbi/star_schema.sql](powerbi/star_schema.sql).

## Core KPI Measures

```dax
Total Offers = COUNTROWS(fact_job_offers)

Unique Companies = DISTINCTCOUNT(dim_company[company_name])

Avg Salary Max = AVERAGE(fact_job_offers[salary_max])

Median Salary Max = MEDIAN(fact_job_offers[salary_max])

Offers With Salary =
CALCULATE(
    COUNTROWS(fact_job_offers),
    NOT ISBLANK(fact_job_offers[salary_max])
)

Salary Coverage % = DIVIDE([Offers With Salary], [Total Offers], 0)
```

## Time and Trend Measures

```dax
Offers Last 7 Days =
CALCULATE(
    [Total Offers],
    DATESINPERIOD(dim_date[date_day], MAX(dim_date[date_day]), -7, DAY)
)

Offers Previous 7 Days =
CALCULATE(
    [Total Offers],
    DATESINPERIOD(dim_date[date_day], MAX(dim_date[date_day]) - 7, -7, DAY)
)

WoW Offer Growth % =
DIVIDE([Offers Last 7 Days] - [Offers Previous 7 Days], [Offers Previous 7 Days], 0)
```

## Skill Demand Measures

```dax
Skill Demand Count = COUNTROWS(fact_skill_demand)

Top Skill =
MAXX(
    TOPN(
        1,
        VALUES(dim_skill[skill_name]),
        CALCULATE(COUNTROWS(fact_skill_demand)),
        DESC
    ),
    dim_skill[skill_name]
)
```

## Recommendation and Conversion Measures

```dax
Recommendations Shown =
CALCULATE(
    COUNTROWS(fact_recommendation_events),
    fact_recommendation_events[action] = "shown"
)

Recommendations Saved =
CALCULATE(
    COUNTROWS(fact_recommendation_events),
    fact_recommendation_events[action] = "saved"
)

Recommendation Save Rate % = DIVIDE([Recommendations Saved], [Recommendations Shown], 0)

Avg Recommendation Score = AVERAGE(fact_recommendation_events[similarity_score])
```

## Pipeline Reliability Measures

```dax
Pipeline Runs = COUNTROWS(fact_pipeline_runs)

Pipeline Success Runs =
CALCULATE(
    COUNTROWS(fact_pipeline_runs),
    fact_pipeline_runs[status] = "success"
)

Pipeline Failure Runs =
CALCULATE(
    COUNTROWS(fact_pipeline_runs),
    fact_pipeline_runs[status] = "failed"
)

Pipeline Success Rate % = DIVIDE([Pipeline Success Runs], [Pipeline Runs], 0)

Avg Pipeline Duration (ms) = AVERAGE(fact_pipeline_runs[duration_ms])
```

## Skill Gap Parameter Measures (Optional)

Use a disconnected table `SelectedSkills` (column `Skill`) created in Power BI.

```dax
Selected Skill Count = COUNTROWS(VALUES(SelectedSkills[Skill]))

Matched Selected Skills =
COUNTROWS(
    INTERSECT(
        VALUES(SelectedSkills[Skill]),
        VALUES(dim_skill[skill_name])
    )
)

Profile Match Score % = DIVIDE([Matched Selected Skills], [Selected Skill Count], 0)

Skill Gap Count = [Selected Skill Count] - [Matched Selected Skills]
```
