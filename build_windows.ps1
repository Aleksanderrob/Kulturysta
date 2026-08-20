$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Brak .venv. Utwórz je poleceniem: py -3.12 -m venv .venv"
}

$Python = Resolve-Path ".venv\Scripts\python.exe"
$Version = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
if ($Version -ne "3.12") {
    throw "Budowę należy wykonać Pythonem 3.12; wykryto $Version."
}

& $Python -m pytest
if ($LASTEXITCODE -ne 0) { throw "Testy nie przeszły; budowanie przerwane." }

if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

& $Python -m PyInstaller --noconfirm "Kulturysta.spec"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller zakończył się błędem." }

New-Item -ItemType Directory -Force "dist\Kulturysta\config" | Out-Null
New-Item -ItemType Directory -Force "dist\Kulturysta\assets" | Out-Null
New-Item -ItemType Directory -Force "dist\Kulturysta\data\participants" | Out-Null
New-Item -ItemType Directory -Force "dist\Kulturysta\data\sessions" | Out-Null
New-Item -ItemType Directory -Force "dist\Kulturysta\data\exports" | Out-Null
New-Item -ItemType Directory -Force "dist\Kulturysta\data\reports" | Out-Null
New-Item -ItemType Directory -Force "dist\Kulturysta\data\logs" | Out-Null
Copy-Item "config\default_config.json" "dist\Kulturysta\config\default_config.json" -Force
Copy-Item "assets\logo_placeholder.png" "dist\Kulturysta\assets\logo_placeholder.png" -Force

Write-Host "Gotowe: $ProjectRoot\dist\Kulturysta\Kulturysta.exe"
