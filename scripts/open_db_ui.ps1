param(
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

Set-Location $projectRoot
docker compose up -d --wait app-db db-ui | Out-Null

$localDbName = if ($env:LOCAL_DB_NAME) { $env:LOCAL_DB_NAME } else { "job_intelligent" }
$localUser = if ($env:LOCAL_DB_USER) { $env:LOCAL_DB_USER } else { "postgres" }

$adminerUrl = "http://localhost:8081/?pgsql=app-db&username=$localUser&db=$localDbName"
Write-Host "Opening local DB UI (Adminer): $adminerUrl" -ForegroundColor Green
Start-Process $adminerUrl

if (-not [string]::IsNullOrWhiteSpace($env:SUPABASE_URL)) {
    if ($env:SUPABASE_URL -match '^https://([^.]+)\.supabase\.co/?$') {
        $projectRef = $matches[1]
        $supabaseUi = "https://supabase.com/dashboard/project/$projectRef/editor"
        Write-Host "Opening Supabase SQL Editor: $supabaseUi" -ForegroundColor Green
        Start-Process $supabaseUi
    }
}
