param(
    [string]$SupabaseDbUrl = "",
    [string]$LocalDbUser = "",
    [string]$LocalDbName = "",
    [string]$EnvFile = ".env"
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

if ([string]::IsNullOrWhiteSpace($SupabaseDbUrl)) {
    throw "SUPABASE_DB_URL is required. Set it in your environment or pass -SupabaseDbUrl."
}

$sourceConn = ConvertFrom-PgConnectionUrl -ConnectionUrl $SupabaseDbUrl

if (-not (Test-PgHostHasIPv4 -HostName $sourceConn.Host)) {
    throw "Supabase DB host '$($sourceConn.Host)' has no IPv4 DNS record in this environment. Use Supabase pooler connection string (IPv4, usually port 6543) in SUPABASE_DB_URL."
}

Set-Location $projectRoot

docker compose up -d --wait app-db | Out-Null

$tables = @(
    "sources",
    "raw_job_offers",
    "job_offers",
    "dw_job_offers",
    "candidate_profiles",
    "cv_documents",
    "recommendation_history",
    "pipeline_runs"
)

$countSql = "SELECT 'sources' AS table_name, count(*)::bigint AS row_count FROM sources UNION ALL SELECT 'raw_job_offers', count(*)::bigint FROM raw_job_offers UNION ALL SELECT 'job_offers', count(*)::bigint FROM job_offers UNION ALL SELECT 'dw_job_offers', count(*)::bigint FROM dw_job_offers UNION ALL SELECT 'candidate_profiles', count(*)::bigint FROM candidate_profiles UNION ALL SELECT 'cv_documents', count(*)::bigint FROM cv_documents UNION ALL SELECT 'recommendation_history', count(*)::bigint FROM recommendation_history UNION ALL SELECT 'pipeline_runs', count(*)::bigint FROM pipeline_runs ORDER BY table_name"

$sourceRows = docker compose exec -T -e SRC_HOST="$($sourceConn.Host)" -e SRC_PORT="$($sourceConn.Port)" -e SRC_USER="$($sourceConn.User)" -e SRC_PASSWORD="$($sourceConn.Password)" -e SRC_DATABASE="$($sourceConn.Database)" -e COUNT_SQL="$countSql" app-db sh -lc 'PGPASSWORD="$SRC_PASSWORD" psql --host="$SRC_HOST" --port="$SRC_PORT" --username="$SRC_USER" --dbname="$SRC_DATABASE" -v ON_ERROR_STOP=1 -At -F"," -c "$COUNT_SQL"'

if ($LASTEXITCODE -ne 0) {
    throw "Failed to query source Supabase row counts."
}

$localRows = docker compose exec -T -e PGPASSWORD="$LocalDbPwd" -e LOCAL_DB_USER="$LocalDbUser" -e LOCAL_DB_NAME="$LocalDbName" -e COUNT_SQL="$countSql" app-db sh -lc 'psql --host=localhost --port=5432 --username="$LOCAL_DB_USER" --dbname="$LOCAL_DB_NAME" -v ON_ERROR_STOP=1 -At -F"," -c "$COUNT_SQL"'

if ($LASTEXITCODE -ne 0) {
    throw "Failed to query local row counts."
}

function ConvertTo-CountMap {
    param([string[]]$Lines)

    $result = @{}
    foreach ($line in $Lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $parts = $line.Split(",", 2)
        if ($parts.Count -ne 2) {
            continue
        }

        $tableName = $parts[0].Trim()
        $value = 0
        [void][long]::TryParse($parts[1].Trim(), [ref]$value)
        $result[$tableName] = $value
    }

    return $result
}

$sourceMap = ConvertTo-CountMap -Lines $sourceRows
$localMap = ConvertTo-CountMap -Lines $localRows

$hasMismatch = $false
Write-Host "Table row count comparison (Supabase -> local):" -ForegroundColor Cyan
foreach ($table in $tables) {
    $source = if ($sourceMap.ContainsKey($table)) { $sourceMap[$table] } else { 0 }
    $local = if ($localMap.ContainsKey($table)) { $localMap[$table] } else { 0 }
    $delta = $local - $source

    if ($delta -eq 0) {
        Write-Host ("  {0,-24} source={1,10}  local={2,10}  delta={3,8}" -f $table, $source, $local, $delta) -ForegroundColor Green
    }
    else {
        $hasMismatch = $true
        Write-Host ("  {0,-24} source={1,10}  local={2,10}  delta={3,8}" -f $table, $source, $local, $delta) -ForegroundColor Yellow
    }
}

if ($hasMismatch) {
    Write-Host "Mismatch detected. Re-run migration or inspect divergent tables before cutover." -ForegroundColor Yellow
    exit 2
}

Write-Host "Snapshot verification passed. Source and local counts match for tracked tables." -ForegroundColor Green
