# HomeWork Tracker Installer
# Installs the Purdue Assignment Tracker desktop widget
# Works on any Windows 10/11 machine with Python 3.10+

param(
    [string]$InstallDir = "$env:LOCALAPPDATA\HomeWorkTracker",
    [string]$ApiBase = ""
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HomeWork Tracker Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. Check Python ---
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ from python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
$pyVer = & python --version 2>&1
Write-Host "[OK] $pyVer" -ForegroundColor Green

# --- 2. Prompt for API base if not provided ---
if (-not $ApiBase) {
    $ApiBase = "http://127.0.0.1:8000"
}
Write-Host "[OK] API: $ApiBase" -ForegroundColor Green

# --- 3. Create install directory ---
if (Test-Path $InstallDir) {
    Write-Host "Updating existing installation..." -ForegroundColor Yellow
    Remove-Item "$InstallDir\venv" -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path "$InstallDir\static" -Force | Out-Null
New-Item -ItemType Directory -Path "$InstallDir\icon" -Force | Out-Null
Write-Host "[OK] Created $InstallDir" -ForegroundColor Green

# --- 4. Copy app files ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$filesToCopy = @(
    @{ Src = "app.py";              Dst = "app.py" },
    @{ Src = "cal_sync.py";         Dst = "cal_sync.py" },
    @{ Src = "static\index.html";   Dst = "static\index.html" },
    @{ Src = "icon\app-icon.png";   Dst = "icon\app-icon.png" },
    @{ Src = "icon\app-icon.ico";   Dst = "icon\app-icon.ico" }
)

foreach ($f in $filesToCopy) {
    $src = Join-Path $scriptDir $f.Src
    $dst = Join-Path $InstallDir $f.Dst
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied $($f.Src)" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: $($f.Src) not found in package" -ForegroundColor Yellow
    }
}
Write-Host "[OK] App files copied" -ForegroundColor Green

# --- 5. Google OAuth credentials ---
# The installer embeds NO credential. The app reads credentials.json from its own
# directory at runtime; place your own Google OAuth desktop-client file there.
if (Test-Path "$InstallDir\credentials.json") {
    Write-Host "[OK] Existing credentials.json found (left untouched)" -ForegroundColor Green
} else {
    Write-Host "[!] No credentials.json in $InstallDir" -ForegroundColor Yellow
    Write-Host "    Calendar Sync stays disabled until you copy your Google OAuth" -ForegroundColor Yellow
    Write-Host "    desktop-client credentials.json into that directory." -ForegroundColor Yellow
}

# --- 6. Write config.json ---
$config = @{
    api_base = $ApiBase
    on_top = $false
} | ConvertTo-Json
Set-Content -Path "$InstallDir\config.json" -Value $config -Encoding UTF8
Write-Host "[OK] Config written (api_base: $ApiBase)" -ForegroundColor Green

# --- 7. Create venv and install deps ---
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
& python -m venv "$InstallDir\venv"
Write-Host "Installing dependencies (this may take a minute)..." -ForegroundColor Cyan
$ErrorActionPreference = "Continue"
& "$InstallDir\venv\Scripts\pip.exe" install --quiet pywebview pystray Pillow httpx google-auth google-auth-oauthlib google-api-python-client 2>&1 | Out-Null
$ErrorActionPreference = "Stop"
if (-not (Test-Path "$InstallDir\venv\Scripts\pythonw.exe")) { Write-Host "ERROR: venv creation failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# --- 8. Create startup scheduled task ---
$taskName = "HomeWorkTracker"
$pythonw = "$InstallDir\venv\Scripts\pythonw.exe"
$appPy = "$InstallDir\app.py"

# Remove existing task if present
$ErrorActionPreference = "Continue"
schtasks /Delete /TN $taskName /F 2>&1 | Out-Null
$ErrorActionPreference = "Stop"

$ErrorActionPreference = "Continue"
schtasks /Create /TN $taskName /TR "`"$pythonw`" `"$appPy`"" /SC ONLOGON /RL HIGHEST /IT /F 2>&1 | Out-Null
$ErrorActionPreference = "Stop"
Write-Host "[OK] Startup task created: $taskName (runs on login)" -ForegroundColor Green

# --- 9. Create desktop shortcut ---
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "HomeWork Tracker.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$appPy`""
$shortcut.WorkingDirectory = $InstallDir
$shortcut.IconLocation = "$InstallDir\icon\app-icon.ico,0"
$shortcut.Description = "HomeWork Tracker - Purdue Assignment Tracker"
$shortcut.Save()
Write-Host "[OK] Desktop shortcut created" -ForegroundColor Green

# --- 10. Done ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installed to: $InstallDir"
Write-Host "Desktop shortcut: HomeWork Tracker"
Write-Host "Auto-starts on login"
Write-Host ""
Write-Host "First time Calendar Sync:" -ForegroundColor Cyan
Write-Host "  Click the sync button in the header bar"
Write-Host "  Your browser opens for Google authorization"
Write-Host "  After that, syncs are one-click"
Write-Host ""

Start-Process -FilePath $pythonw -ArgumentList "`"$appPy`"" -WorkingDirectory $InstallDir
Write-Host "Launched!" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 3





