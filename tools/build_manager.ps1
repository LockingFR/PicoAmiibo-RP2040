param([string]$DistributionRoot='dist\preview')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python=Join-Path $root '.deps\manager-env\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    & python.exe -m venv .deps\manager-env
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create private Manager environment' }
    & $python -m pip install -r manager\requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Cannot install private Manager dependencies' }
}
$destination=[IO.Path]::GetFullPath((Join-Path $root $DistributionRoot))
$package=Join-Path $destination 'PicoAmiibo-Manager'
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'dist'))+[IO.Path]::DirectorySeparatorChar
if (-not $package.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output is outside the project distribution directory' }
New-Item -ItemType Directory -Path artifacts\manager-preview,manager\assets -Force | Out-Null
& $python tools\manager_assets.py
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed' }
$ErrorActionPreference='Continue'
& $python -m PyInstaller --noconfirm --windowed --onedir --name PicoAmiibo-Manager --icon (Join-Path $root 'manager\assets\icon.ico') --add-data "$(Join-Path $root 'manager\assets\rewards_totk.json');manager/assets" --workpath build\manager-pyinstaller --specpath build\manager-spec --distpath $destination --exclude-module tkinter --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick (Join-Path $root 'manager_entry.py') 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object artifacts\manager-preview\build.log
if ($LASTEXITCODE -ne 0) { throw 'Manager EXE build failed' }
$ErrorActionPreference='Stop'
& (Join-Path $root 'tools\test_manager.ps1') -Frozen -DistributionRoot $DistributionRoot
& $python tools\package_manager.py --distribution-root $DistributionRoot
if ($LASTEXITCODE -ne 0) { throw 'Portable package validation failed' }
Write-Output (Join-Path $package 'PicoAmiibo-Manager.exe')
