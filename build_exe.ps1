param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$mode = if ($OneFile) { "--onefile" } else { "--onedir" }
$python = if (Test-Path ".venv\Scripts\python.exe") {
    ".venv\Scripts\python.exe"
} else {
    "python"
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    $mode `
    --name "DesktopDuck" `
    --icon "assets\duck.ico" `
    --add-data "assets\duck.ico;assets" `
    --add-data "assets\sprites\duck_sprite.png;assets\sprites" `
    "main.py"

Write-Host "Build complete: $projectRoot\dist\DesktopDuck"
