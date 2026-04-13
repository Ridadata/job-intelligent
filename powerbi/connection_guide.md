# Power BI — Supabase PostgreSQL Connection Guide

## Prerequisites
- Power BI Desktop (latest version)
- PostgreSQL ODBC driver or Npgsql provider
- Supabase project with connection pooling enabled

## Connection Steps

### 1. Get Connection Details
From your Supabase dashboard → Settings → Database:
- **Host**: `db.<project-ref>.supabase.co`
- **Port**: `5432` (direct) or `6543` (transaction pooler)
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: Your database password

### 2. Connect in Power BI
1. Open Power BI Desktop
2. **Get Data** → **PostgreSQL database**
3. Enter:
   - Server: `db.<project-ref>.supabase.co:5432`
   - Database: `postgres`
4. Select **DirectQuery** (recommended for live dashboards)
5. Enter credentials:
   - User: `postgres`
   - Password: Your database password

### 3. Select Tables/Views
Import the materialized views:
- `mv_offers_by_skill`
- `mv_salary_by_role`
- `mv_offers_by_location`
- `mv_market_trends`
- `mv_top_companies`

### 4. SSL Configuration
Supabase requires SSL. If connection fails:
1. Download the Supabase CA certificate
2. In Power BI connection settings, enable SSL
3. Or append `?sslmode=require` to the connection string

### 5. Scheduled Refresh
1. Publish report to Power BI Service
2. Go to dataset settings → Scheduled refresh
3. Set refresh schedule to every 6 hours (aligned with ETL)
4. Configure gateway if using on-premises gateway

## Performance Tips
- Use materialized views (pre-aggregated) instead of base tables
- Prefer Import mode for small datasets, DirectQuery for live updates
- Add appropriate indexes (already included in schema)
- Use connection pooler (port 6543) for multiple concurrent connections

## Troubleshooting
| Issue | Solution |
|-------|----------|
| Connection timeout | Check Supabase project is active; use port 6543 |
| SSL error | Enable SSL in connection; download CA cert |
| Permission denied | Use `postgres` user or grant SELECT on views |
| Slow queries | Ensure MVs are refreshed; check HNSW index |
