param(
    [string]$SupabaseDbUrl = "",
    [string]$LocalDbUser = "",
    [string]$LocalDbName = "",
    [string]$EnvFile = ".env",
    [switch]$SkipPostRestore,
    [switch]$KeepDump
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$helperPath = Join-Path $PSScriptRoot "_db_helpers.ps1"

if (-not (Test-Path $helperPath)) {
    throw "Helper script not found: $helperPath"
}

. $helperPath
Import-ProjectDotEnv -ProjectRoot $projectRoot -EnvFile $EnvFile

if ([string]::IsNullOrWhiteSpace($SupabaseDbUrl)) {
    $SupabaseDbUrl = $env:SUPABASE_DB_URL
}

if ([string]::IsNullOrWhiteSpace($LocalDbUser)) {
    $LocalDbUser = if ($env:LOCAL_DB_USER) { $env:LOCAL_DB_USER } else { "postgres" }
}

if ([string]::IsNullOrWhiteSpace($LocalDbName)) {
    $LocalDbName = if ($env:LOCAL_DB_NAME) { $env:LOCAL_DB_NAME } else { "job_intelligent" }
}

$LocalDbPwd = if ($env:LOCAL_DB_PASSWORD) { $env:LOCAL_DB_PASSWORD } else { "postgres" }

function Invoke-Step {
    param(
        [string]$Message,
        [scriptblock]$Script
    )

    Write-Host "==> $Message" -ForegroundColor Cyan
    & $Script
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Message (exit code: $LASTEXITCODE)"
    }
}

$dumpPath = "/tmp/supabase_snapshot.dump"

if ([string]::IsNullOrWhiteSpace($SupabaseDbUrl)) {
    throw "SUPABASE_DB_URL is required. Set it in your environment or pass -SupabaseDbUrl."
}

$sourceConn = ConvertFrom-PgConnectionUrl -ConnectionUrl $SupabaseDbUrl

if (-not (Test-PgHostHasIPv4 -HostName $sourceConn.Host)) {
    throw "Supabase DB host '$($sourceConn.Host)' has no IPv4 DNS record in this environment. Use Supabase pooler connection string (IPv4, usually port 6543) in SUPABASE_DB_URL."
}

Set-Location $projectRoot

Invoke-Step "Starting local app-db container" {
    docker compose up -d --wait app-db
}

Invoke-Step "Creating Supabase dump inside app-db container" {
    docker compose exec -T -e SRC_HOST="$($sourceConn.Host)" -e SRC_PORT="$($sourceConn.Port)" -e SRC_USER="$($sourceConn.User)" -e SRC_PASSWORD="$($sourceConn.Password)" -e SRC_DATABASE="$($sourceConn.Database)" -e DUMP_PATH="$dumpPath" app-db sh -lc 'PGPASSWORD="$SRC_PASSWORD" pg_dump --host="$SRC_HOST" --port="$SRC_PORT" --username="$SRC_USER" --dbname="$SRC_DATABASE" --format=custom --no-owner --no-privileges --file="$DUMP_PATH"'
}

Invoke-Step "Restoring dump into local database $LocalDbName" {
    docker compose exec -T -e PGPASSWORD="$LocalDbPwd" -e LOCAL_DB_USER="$LocalDbUser" -e LOCAL_DB_NAME="$LocalDbName" -e DUMP_PATH="$dumpPath" app-db sh -lc 'pg_restore --clean --if-exists --no-owner --no-privileges --host=localhost --port=5432 --username="$LOCAL_DB_USER" --dbname="$LOCAL_DB_NAME" "$DUMP_PATH"'
}

if (-not $SkipPostRestore) {
    $postRestoreSqlPath = Join-Path $projectRoot "sql/009_local_dev_post_restore.sql"
    if (-not (Test-Path $postRestoreSqlPath)) {
        throw "Post-restore SQL file not found: $postRestoreSqlPath"
    }

    Invoke-Step "Applying local post-restore SQL" {
        Get-Content -Path $postRestoreSqlPath -Raw | docker compose exec -T -e PGPASSWORD="$LocalDbPwd" -e LOCAL_DB_USER="$LocalDbUser" -e LOCAL_DB_NAME="$LocalDbName" app-db sh -lc 'psql --host=localhost --port=5432 --username="$LOCAL_DB_USER" --dbname="$LOCAL_DB_NAME" -v ON_ERROR_STOP=1'
    }
}

if (-not $KeepDump) {
    Invoke-Step "Cleaning temporary dump file" {
        docker compose exec -T -e DUMP_PATH="$dumpPath" app-db sh -lc 'rm -f "$DUMP_PATH"'
    }
}

Invoke-Step "Printing key table counts from local database" {
    docker compose exec -T -e PGPASSWORD="$LocalDbPwd" -e LOCAL_DB_USER="$LocalDbUser" -e LOCAL_DB_NAME="$LocalDbName" app-db sh -lc 'psql --host=localhost --port=5432 --username="$LOCAL_DB_USER" --dbname="$LOCAL_DB_NAME" -v ON_ERROR_STOP=1 -c "SELECT ''sources'' AS table_name, count(*)::bigint AS row_count FROM sources UNION ALL SELECT ''raw_job_offers'', count(*)::bigint FROM raw_job_offers UNION ALL SELECT ''job_offers'', count(*)::bigint FROM job_offers UNION ALL SELECT ''dw_job_offers'', count(*)::bigint FROM dw_job_offers UNION ALL SELECT ''candidate_profiles'', count(*)::bigint FROM candidate_profiles UNION ALL SELECT ''cv_documents'', count(*)::bigint FROM cv_documents UNION ALL SELECT ''recommendation_history'', count(*)::bigint FROM recommendation_history UNION ALL SELECT ''pipeline_runs'', count(*)::bigint FROM pipeline_runs ORDER BY table_name"'
}

Write-Host "Migration completed. Your local app DB is running in docker service: app-db" -ForegroundColor Green
Write-Host "Next step: run scripts/verify_local_snapshot.ps1 to compare Supabase vs local counts." -ForegroundColor Green
