# One-step setup of Crypto Chart AI in Docker on Windows (WL-087, docs/docker.md).
#
#   powershell -ExecutionPolicy Bypass -File setup.ps1                  install what is missing, start
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -Port 8010       another port than 8000
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -Provider none   set AI_PROVIDER in backend\.env
#
# Installs Docker Desktop (winget) when it is missing, starts it and sets it to start at
# sign-in, creates backend\.env, builds and starts the containers and waits until the
# portal answers. Safe to run again: the database volume is reused, never replaced.

param(
    [int]$Port = 0,
    [string]$Provider = "",
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$DockerExe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
$DockerBin = Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin'

function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Fail($text) { Write-Host "Setup stopped: $text" -ForegroundColor Yellow; exit 1 }
function Test-DockerCli { [bool](Get-Command docker -ErrorAction SilentlyContinue) }
function Test-DockerEngine {
    # docker writes to stderr when the engine is down; only the exit code matters here.
    $ErrorActionPreference = 'Continue'
    docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

# 1. Docker Desktop
if (-not (Test-DockerCli) -and (Test-Path $DockerBin)) { $env:Path = "$DockerBin;$env:Path" }
if (-not (Test-DockerCli)) {
    Step "Docker is not installed: installing Docker Desktop (Windows asks for permission)"
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "winget is missing. Install Docker Desktop from https://www.docker.com/products/docker-desktop/ and run setup.ps1 again."
    }
    $wslOk = $true
    try { wsl.exe --status *> $null; $wslOk = ($LASTEXITCODE -eq 0) } catch { $wslOk = $false }
    if (-not $wslOk) {
        Step "Turning on WSL 2, which Docker needs"
        Start-Process wsl.exe -ArgumentList '--install', '--no-distribution' -Verb RunAs -Wait
    }
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements `
        --override 'install --quiet --accept-license --backend=wsl-2'
    if ($LASTEXITCODE -ne 0 -and -not (Test-Path $DockerExe)) { Fail "the Docker Desktop install did not finish (winget exit $LASTEXITCODE)." }
    $env:Path = "$DockerBin;$env:Path"
    if (-not $wslOk) {
        Fail "Docker Desktop is installed. Restart Windows once (WSL 2 needs it), then run setup.ps1 again."
    }
}

# 2. Start Docker Desktop at sign-in, so the containers come back after a restart.
if (Test-Path $DockerExe) {
    $run = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    Set-ItemProperty -Path $run -Name 'Docker Desktop' -Value "`"$DockerExe`""
}

# 3. The Docker engine
if (-not (Test-DockerEngine)) {
    Step "Starting Docker Desktop"
    if (Test-Path $DockerExe) { Start-Process $DockerExe }
    $deadline = (Get-Date).AddMinutes(5)
    while (-not (Test-DockerEngine)) {
        if ((Get-Date) -gt $deadline) {
            Fail "Docker did not start within 5 minutes. Open Docker Desktop, finish its first-run screens, then run setup.ps1 again."
        }
        Start-Sleep -Seconds 5
    }
}
Step "Docker is running ($(docker --version))"

# 4. Settings: backend\.env (AI provider and keys) and .env (port and time zone for compose)
if (-not (Test-Path 'backend\.env')) {
    Copy-Item 'backend\.env.example' 'backend\.env'
    Step "Created backend\.env from backend\.env.example"
}
if ($Provider) {
    $lines = Get-Content 'backend\.env'
    if ($lines -match '^AI_PROVIDER=') { $lines = $lines -replace '^AI_PROVIDER=.*', "AI_PROVIDER=$Provider" }
    else { $lines += "AI_PROVIDER=$Provider" }
    [IO.File]::WriteAllLines((Join-Path $Root 'backend\.env'), [string[]]$lines)  # UTF-8, no BOM
    Step "AI_PROVIDER=$Provider"
}
$composeEnv = @{}
if (Test-Path '.env') {
    foreach ($line in Get-Content '.env') { if ($line -match '^(\w+)=(.*)$') { $composeEnv[$Matches[1]] = $Matches[2] } }
}
if ($Port -gt 0) { $composeEnv['PORT'] = "$Port" }
if (-not $composeEnv['PORT']) { $composeEnv['PORT'] = '8000' }
if (-not $composeEnv['TZ']) { $composeEnv['TZ'] = 'Asia/Karachi' }
Set-Content '.env' ($composeEnv.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -Encoding ascii
$Port = [int]$composeEnv['PORT']

New-Item -ItemType Directory -Force 'backups' | Out-Null
$seed = Get-ChildItem 'backups\*.db' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$volume = docker volume ls -q --filter name=^crypto-chart-ai-data$
if (-not $volume) {
    if ($seed) { Step "New database volume: it is filled from backups\$($seed.Name)" }
    else { Step "New database volume: no backup in backups\, starting empty" }
} else { Step "Keeping the existing database volume crypto-chart-ai-data" }

# 5. Build and start
# app first: on a new volume it copies the seed backup, which can take minutes. Waiting
# here instead of in compose's depends_on avoids its long health poll.
Step "Building and starting (the first build takes a few minutes)"
docker compose up -d --build app
if ($LASTEXITCODE -ne 0) { Fail "docker compose up failed (exit $LASTEXITCODE). See the output above." }

Step "Waiting for the portal to answer (the first start copies the database)"
$deadline = (Get-Date).AddMinutes(15)
$url = "http://127.0.0.1:$Port"
while ($true) {
    try { if ((Invoke-WebRequest "$url/api/health" -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200) { break } } catch { }
    if ((Get-Date) -gt $deadline) { Fail "the app did not answer within 15 minutes. Run: docker compose logs app" }
    Start-Sleep -Seconds 5
}

Step "Starting the scheduled jobs"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "starting the jobs container failed (exit $LASTEXITCODE). Run: docker compose up -d" }

Step "Crypto Chart AI is running at $url"
Write-Host "    It starts again by itself after a restart of Docker or of this computer."
Write-Host "    AI provider and keys: backend\.env (see docs\docker.md). Logs: docker compose logs -f"
if (-not $NoBrowser) { Start-Process $url }
