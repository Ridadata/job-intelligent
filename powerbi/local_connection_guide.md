# Power BI ↔ Local Supabase — Step-by-Step Connection Guide

This guide connects **Power BI Desktop (Windows host)** to the **local self-hosted Supabase stack** running in Docker on this machine, using the dedicated `powerbi.*` star-schema views.

> **Status of the local DB**: 2,800 rows migrated from cloud · 10 star-schema views created · `powerbi_reader` read-only role provisioned · validated end-to-end from the Windows host.

---

## 0) What's already done (verified)

| Item | Status |
|---|---|
| Local Supabase stack running | ✅ ([docker-compose.yml](../docker-compose.yml)) |
| Star-schema views applied | ✅ ([powerbi/star_schema.sql](star_schema.sql)) |
| `role_key` added to `fact_job_offers` | ✅ |
| Read-only role `powerbi_reader` | ✅ |
| Host-side connection tested via Supavisor (`localhost:54322`) | ✅ |

Row counts (verified):

| View | Rows |
|---|---|
| `powerbi.dim_date` | 1222 |
| `powerbi.dim_source` | 9 |
| `powerbi.dim_contract` | 4 |
| `powerbi.dim_company` | 198 |
| `powerbi.dim_location` | 110 |
| `powerbi.dim_role` | 165 |
| `powerbi.dim_skill` | 61 |
| `powerbi.fact_job_offers` | 1256 |
| `powerbi.fact_skill_demand` | 2709 |
| `powerbi.fact_recommendation_events` | 93 |
| `powerbi.fact_pipeline_runs` | 0 *(no ETL runs yet)* |

---

## 1) Connection credentials (local)

| Setting | Value |
|---|---|
| **Server** | `localhost:54322` |
| **Database** | `postgres` |
| **Username** | `powerbi_reader.aqualocal` |
| **Password** | _set via `POWERBI_READER_PASSWORD` in your `.env` (see step 2 below)_ |
| **Encryption** | OFF (no TLS on local pooler) |
| **Schema** | `powerbi` |

> The `.aqualocal` suffix is **required** — it's the Supavisor tenant identifier. Plain `powerbi_reader` will fail authentication.

> Alternative super-user (admin only): `postgres.aqualocal` / `your-super-secret-and-long-postgres-password`.

---

## 2) Install prerequisites (one-time)

### 2.1 Power BI Desktop
Install the latest **Power BI Desktop** from the Microsoft Store or [powerbi.microsoft.com/desktop](https://powerbi.microsoft.com/desktop/).

### 2.2 Npgsql .NET data provider (required by the PostgreSQL connector)
1. Download the **Npgsql MSI** from [github.com/npgsql/npgsql/releases](https://github.com/npgsql/npgsql/releases) (latest 4.x — choose `Npgsql-4.0.x.msi` which registers in the GAC).
2. During install, check **"Npgsql GAC Installation"**.
3. **Close Power BI Desktop** completely and reopen.

> If you skip this step, Power BI's PostgreSQL connector throws *"the 'Npgsql' provider is not installed"*.

---

## 3) Connect Power BI to Supabase

1. Power BI Desktop → **Home → Get Data → More → PostgreSQL database → Connect**.
2. Fill the dialog:
   - **Server**: `localhost:54322`
   - **Database**: `postgres`
   - **Data Connectivity mode**: **Import** *(recommended)*
   - Leave SQL statement empty.
3. Click **OK**.
4. In the credentials prompt, switch to the **Database** tab (NOT Windows):
   - **User name**: `powerbi_reader.aqualocal`
   - **Password**: the value of `POWERBI_READER_PASSWORD` from your `.env`
   - **Apply settings to**: `localhost:54322`
   - Click **Connect**.
5. If you see a TLS/SSL warning, click the link to **disable encryption for this server** (local stack has no TLS on the pooler).
6. In **Navigator**, expand the `powerbi` schema and **tick these 10 views**:
   - `dim_date`, `dim_source`, `dim_contract`, `dim_company`, `dim_location`, `dim_role`, `dim_skill`
   - `fact_job_offers`, `fact_skill_demand`, `fact_recommendation_events`, `fact_pipeline_runs`
7. Click **Transform Data** (NOT Load yet).

---

## 4) Power Query — sanity-check column types

In the Power Query editor, click each table and verify the column data types in the header row. Power BI usually auto-detects correctly; if not, fix:

| Column pattern | Expected type |
|---|---|
| `*_key` (e.g., `date_key`, `company_key`) | Whole Number (for `date_key`) / Text (for hash keys) |
| `date_day`, `published_date`, `event_date`, `started_date` | Date |
| `salary_min`, `salary_max`, `demand_score`, `similarity_score`, `score_*` | Decimal Number |
| `required_skill_count`, `tech_stack_count`, `rows_*`, `duration_ms` | Whole Number |
| Everything else under `status`, `action`, `category`, `seniority_level`, `contract_type`, names | Text |

Click **Close & Apply**. The first load takes a few seconds.

---

## 5) Build the star-schema model

Switch to **Model view** (left rail, 3rd icon). Power BI auto-creates some relationships — **delete all auto-detected relationships first** (right-click each line → Delete), then create these **11 relationships** manually:

| # | From (dim) | → To (fact) | Cardinality | Cross-filter |
|---|---|---|---|---|
| 1 | `dim_date[date_key]` | `fact_job_offers[published_date_key]` | 1 ↔ * | Single |
| 2 | `dim_source[source_id]` | `fact_job_offers[source_id]` | 1 ↔ * | Single |
| 3 | `dim_company[company_key]` | `fact_job_offers[company_key]` | 1 ↔ * | Single |
| 4 | `dim_location[location_key]` | `fact_job_offers[location_key]` | 1 ↔ * | Single |
| 5 | `dim_contract[contract_type]` | `fact_job_offers[contract_type]` | 1 ↔ * | Single |
| 6 | `dim_role[role_key]` | `fact_job_offers[role_key]` | 1 ↔ * | Single |
| 7 | `dim_skill[skill_name]` | `fact_skill_demand[skill_name]` | 1 ↔ * | Single |
| 8 | `fact_job_offers[offer_id]` | `fact_skill_demand[offer_id]` | 1 ↔ * | Single |
| 9 | `fact_job_offers[offer_id]` | `fact_recommendation_events[offer_id]` | 1 ↔ * | Single |
| 10 | `dim_date[date_key]` | `fact_recommendation_events[event_date_key]` | 1 ↔ * | Single |
| 11 | `dim_date[date_key]` | `fact_pipeline_runs[started_date_key]` | 1 ↔ * | Single |

**To create a relationship**: drag the field from the dimension table onto the matching field in the fact table. In the dialog, confirm cardinality and cross-filter direction.

### Mark `dim_date` as a Date table
1. Right-click `dim_date` in the Fields pane → **Mark as date table**.
2. Choose `date_day` as the date column → **OK**.

### Hide foreign keys from report view
On each `fact_*` table, right-click each `*_key` / `*_id` column → **Hide in report view**. Keeps the field list clean.

### Set sort-by columns
- `dim_date[month_name]` → Column tools → **Sort by column** → `month`.
- `dim_date[day_name]` → Sort by column → `day_of_week`.

---

## 6) Add DAX measures

1. In **Report view**, click **Home → Enter Data**.
2. Name the table `_Measures`. Leave one empty column. Click **Load**.
3. Right-click `_Measures` → **New measure**. Add each measure from [powerbi/dax_measures.md](dax_measures.md). Recommended starting set:

```dax
Total Offers = COUNTROWS(fact_job_offers)
Unique Companies = DISTINCTCOUNT(dim_company[company_name])
Avg Salary Max = AVERAGE(fact_job_offers[salary_max])
Median Salary Max = MEDIAN(fact_job_offers[salary_max])

Offers Last 7 Days =
CALCULATE(
    [Total Offers],
    DATESINPERIOD(dim_date[date_day], MAX(dim_date[date_day]), -7, DAY)
)

Recommendations Shown =
CALCULATE(COUNTROWS(fact_recommendation_events), fact_recommendation_events[action] = "shown")

Recommendations Saved =
CALCULATE(COUNTROWS(fact_recommendation_events), fact_recommendation_events[action] = "saved")

Save Rate % = DIVIDE([Recommendations Saved], [Recommendations Shown], 0)

Pipeline Success Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(fact_pipeline_runs), fact_pipeline_runs[status] = "success"),
    COUNTROWS(fact_pipeline_runs), 0
)
```

4. After creating each measure, set its format (Measure tools → Format): `%` for ratios, `0` decimals for salary.
5. Hide the placeholder `Column1` on `_Measures` from report view so only measures appear.

---

## 7) Validation checklist

Place a few visuals on a temporary page to confirm everything is wired correctly:

| Visual | Expected result |
|---|---|
| Card `Total Offers` | **1256** |
| Card `Recommendations Shown` + `Recommendations Saved` (sum) | **93** |
| Bar chart: `Total Offers` by `dim_source[source_name]` | bars for adzuna, jsearch, rekrute, etc. |
| Line chart: `Total Offers` by `dim_date[date_day]` (last 12 weeks) | trend renders |
| Slicer: `dim_contract[contract_type]` | filters all visuals |

In **Model view**:
- Diagram looks like a clean star (dims on the outside, facts in the center).
- No yellow ⚠️ "ambiguous relationship" badges.
- All relationship lines show **single-direction** arrows (►).

---

## 8) Save & version

Save the file as `powerbi/job_intelligent.pbix` in the repo. The `.pbix` is binary — it is excluded from git automatically (or add to `.gitignore` if not). Treat the **DAX measures** and **star schema SQL** as the source of truth; the `.pbix` is a build artifact you can regenerate.

---

## 9) Refresh strategy

### Local dev (single user)
After each Airflow `job_etl` run, hit **Home → Refresh** in Power BI Desktop. Refresh takes <10 seconds for the current dataset size.

### Power BI Service (if you publish)
1. Publish from Desktop → **Home → Publish**.
2. Install the **[On-premises data gateway (Personal mode)](https://learn.microsoft.com/power-bi/connect-data/service-gateway-personal-mode)** on this Windows machine.
3. In Power BI Service → Dataset settings → **Gateway connection** → map the PostgreSQL data source to `localhost:54322` with `powerbi_reader.aqualocal`.
4. Schedule refresh every 6 hours aligned with the Airflow DAG.

---

## 10) Troubleshooting

| Symptom | Fix |
|---|---|
| `"The Npgsql provider is not installed"` | Install Npgsql MSI (step 2.2), restart Power BI. |
| `"could not translate host name 'db' to address"` | You used the internal Docker hostname. From the host, use **`localhost:54322`**. |
| Authentication failure on `powerbi_reader` | Make sure the username has the `.aqualocal` suffix — Supavisor requires it. |
| `"role 'powerbi_reader' does not exist"` | Re-run the role creation block in section [Appendix A](#appendix-a--recreate-the-powerbi_reader-role). |
| Power BI shows old data after ETL | Click **Home → Refresh** (Import mode). For DirectQuery, click the data-source refresh icon on the visual. |
| `fact_pipeline_runs` is empty | Expected until Airflow ETL runs. View is correct. |
| "Ambiguous relationship" warning | Delete the offer_id bridge relationship (#8 or #9) — keep only one path between `dim_date` and `fact_recommendation_events`. |
| Connection times out | `docker compose ps supabase-pooler` must show healthy. Restart if needed: `docker compose restart supabase-pooler`. |

---

## Appendix A — Recreate the `powerbi_reader` role

If the role is missing or the password needs rotation:

```powershell
docker compose exec db psql -U postgres -d postgres -c @"
DROP ROLE IF EXISTS powerbi_reader;
CREATE ROLE powerbi_reader LOGIN PASSWORD :'powerbi_reader_password';
-- Run with: psql -v powerbi_reader_password="$POWERBI_READER_PASSWORD" -f ...
GRANT USAGE ON SCHEMA powerbi TO powerbi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA powerbi TO powerbi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA powerbi GRANT SELECT ON TABLES TO powerbi_reader;
"@
```

## Appendix B — Re-apply star-schema views

If the views become stale or need patching:

```powershell
Get-Content powerbi/star_schema.sql -Raw | docker compose exec -T db psql -U postgres -d postgres
```

## Appendix C — Quick host-side connection test (no Power BI)

```powershell
docker run --rm postgres:15-alpine psql `
  "postgresql://powerbi_reader.aqualocal:$env:POWERBI_READER_PASSWORD@host.docker.internal:54322/postgres" `
  -c "SELECT count(*) FROM powerbi.fact_job_offers;"
```

Expected: `1256`.
