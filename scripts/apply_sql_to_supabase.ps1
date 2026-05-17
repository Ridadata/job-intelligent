param(
    [Parameter(Mandatory = $true)]
    [string]$SqlFile,
    [string]$SupabaseDbUrl = "",
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

if ([string]::IsNullOrWhiteSpace($SupabaseDbUrl)) {
    throw "SUPABASE_DB_URL is required. Set it in .env, environment, or pass -SupabaseDbUrl."
}

$sourceConn = ConvertFrom-PgConnectionUrl -ConnectionUrl $SupabaseDbUrl

if (-not (Test-PgHostHasIPv4 -HostName $sourceConn.Host)) {
    throw "Supabase DB host '$($sourceConn.Host)' has no IPv4 DNS record in this environment. Use Supabase pooler connection string (IPv4, usually port 6543) in SUPABASE_DB_URL."
}

$sqlPath = if ([System.IO.Path]::IsPathRooted($SqlFile)) {
    $SqlFile
}
else {
    Join-Path $projectRoot $SqlFile
}

if (-not (Test-Path $sqlPath)) {
    throw "SQL file not found: $sqlPath"
}

Set-Location $projectRoot

docker compose up -d --wait app-db | Out-Null

Get-Content -Path $sqlPath -Raw |
    docker compose exec -T -e SRC_HOST="$($sourceConn.Host)" -e SRC_PORT="$($sourceConn.Port)" -e SRC_USER="$($sourceConn.User)" -e SRC_PASSWORD="$($sourceConn.Password)" -e SRC_DATABASE="$($sourceConn.Database)" app-db sh -lc 'PGPASSWORD="$SRC_PASSWORD" psql --host="$SRC_HOST" --port="$SRC_PORT" --username="$SRC_USER" --dbname="$SRC_DATABASE" -v ON_ERROR_STOP=1'

if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply SQL to Supabase (exit code: $LASTEXITCODE)."
}

Write-Host "Applied SQL to Supabase successfully: $SqlFile" -ForegroundColor Green
