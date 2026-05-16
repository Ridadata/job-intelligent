function Import-ProjectDotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot,
        [string]$EnvFile = ".env"
    )

    $envPath = Join-Path $ProjectRoot $EnvFile
    if (-not (Test-Path $envPath)) {
        return
    }

    foreach ($line in Get-Content -Path $envPath) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("#")) {
            continue
        }

        if ($trimmed -notmatch '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            continue
        }

        $key = $matches[1]
        $value = $matches[2].Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            if ($value.Length -ge 2) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }

        if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($key, "Process"))) {
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

function ConvertFrom-PgConnectionUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConnectionUrl
    )

    if (-not $ConnectionUrl.StartsWith("postgresql://")) {
        throw "Connection URL must start with postgresql://"
    }

    $pattern = '^postgresql:\/\/(?<user>[^:\/?#]+):(?<password>.*)@(?<host>[^:\/?#]+):(?<port>\d+)\/(?<database>[^?]+)(\?.*)?$'
    $match = [regex]::Match($ConnectionUrl, $pattern)

    if (-not $match.Success) {
        throw "Invalid PostgreSQL URL format. Expected postgresql://user:password@host:port/database"
    }

    return @{
        User = [System.Uri]::UnescapeDataString($match.Groups["user"].Value)
        Password = [System.Uri]::UnescapeDataString($match.Groups["password"].Value)
        Host = $match.Groups["host"].Value
        Port = $match.Groups["port"].Value
        Database = [System.Uri]::UnescapeDataString($match.Groups["database"].Value)
    }
}

function Test-PgHostHasIPv4 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HostName
    )

    try {
        $records = Resolve-DnsName -Name $HostName -Type A -ErrorAction Stop
        return (($records | Where-Object { $_.IPAddress }).Count -gt 0)
    }
    catch {
        return $false
    }
}
