# Power BI DAX Measures

## Market Overview Measures

```dax
// Total Active Offers
Total Offers = SUM(mv_market_trends[offer_count])

// Unique Companies
Unique Companies = DISTINCTCOUNT(mv_top_companies[company_name])

// Average Salary
Avg Salary = AVERAGE(mv_salary_by_role[salary_avg])

// Top Skill by Demand
Top Skill =
FIRSTNONBLANK(
    TOPN(1,
        VALUES(mv_offers_by_skill[skill_name]),
        CALCULATE(SUM(mv_offers_by_skill[offer_count]))
    ),
    1
)

// Week-over-Week Growth %
WoW Growth =
VAR CurrentWeek = SUM(mv_market_trends[offer_count])
VAR PreviousWeek =
    CALCULATE(
        SUM(mv_market_trends[offer_count]),
        DATEADD(mv_market_trends[week_date], -7, DAY)
    )
RETURN
    DIVIDE(CurrentWeek - PreviousWeek, PreviousWeek, 0)
```

## Salary Analysis Measures

```dax
// Median Salary (approximation using PERCENTILE)
Median Salary =
PERCENTILE.INC(mv_salary_by_role[salary_avg], 0.5)

// Salary Range Spread
Salary Spread =
AVERAGE(mv_salary_by_role[salary_max]) - AVERAGE(mv_salary_by_role[salary_min])

// Top Paying Role
Top Paying Role =
FIRSTNONBLANK(
    TOPN(1,
        VALUES(mv_salary_by_role[job_title]),
        CALCULATE(MAX(mv_salary_by_role[salary_max]))
    ),
    1
)

// Offers with Salary Info %
Salary Coverage =
DIVIDE(
    COUNTROWS(FILTER(mv_salary_by_role, mv_salary_by_role[salary_avg] > 0)),
    COUNTROWS(mv_salary_by_role),
    0
)
```

## Skill Matching Measures

```dax
// Profile Match Score %
// Requires a What-If parameter table "SelectedSkills"
Profile Match Score =
VAR SelectedSkills = VALUES(SelectedSkills[Skill])
VAR MatchedCount =
    COUNTROWS(
        FILTER(
            SelectedSkills,
            CONTAINSSTRING(
                CONCATENATEX(
                    RELATEDTABLE(mv_offers_by_skill),
                    mv_offers_by_skill[skill_name],
                    ","
                ),
                SelectedSkills[Skill]
            )
        )
    )
VAR TotalSelected = COUNTROWS(SelectedSkills)
RETURN DIVIDE(MatchedCount, TotalSelected, 0)

// Skill Gap — skills in demand but NOT selected by candidate
Skill Gap Count =
VAR SelectedSkills = VALUES(SelectedSkills[Skill])
RETURN
    COUNTROWS(
        FILTER(
            VALUES(mv_offers_by_skill[skill_name]),
            NOT(mv_offers_by_skill[skill_name] IN SelectedSkills)
        )
    )
```
