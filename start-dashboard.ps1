param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8790,
    [switch]$NoReload,
    [switch]$Reload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Pause-OnError {
    param([string]$Message)

    Write-Host $Message -ForegroundColor Red
    if ($Host.Name -eq "ConsoleHost" -and -not $env:CI) {
        Read-Host "Premi INVIO per chiudere"
    }
    exit 1
}

Write-Host "Starting MCP Dashboard on http://$BindHost`:$Port" -ForegroundColor Cyan
Write-Host "Project root: $projectRoot"

$pythonExe = $null
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = (Get-Command python).Source
}
else {
    Pause-OnError "Python non trovato. Installa Python o crea una .venv in $projectRoot"
}

& $pythonExe -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('fastapi') and importlib.util.find_spec('uvicorn') else 1)" | Out-Null
$depsExitCode = $LASTEXITCODE
if ($depsExitCode -ne 0) {
    Pause-OnError "Dipendenze mancanti su $pythonExe. Esegui: pip install -r $backendDir\requirements.txt"
}

$enableReload = $false
if ($Reload) {
    $enableReload = $true
}
elseif ($NoReload) {
    $enableReload = $false
}

$reloadArgs = @()
if ($enableReload) {
    $reloadArgs += "--reload"
}

Push-Location $backendDir
try {
    & $pythonExe -m uvicorn app.main:app --host $BindHost --port $Port @reloadArgs
    if ($LASTEXITCODE -ne 0) {
        Pause-OnError "Uvicorn terminato con exit code $LASTEXITCODE. Controlla dipendenze e configurazione."
    }
}
catch {
    Pause-OnError ("Avvio dashboard fallito: " + $_.Exception.Message)
}
finally {
    Pop-Location
}
