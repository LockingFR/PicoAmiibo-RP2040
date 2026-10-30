# Local dependencies only. No installer, PATH changes, admin access, or flashing.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
New-Item -ItemType Directory -Path .deps -Force | Out-Null
function Get-Archive([string]$Url, [string]$File, [string]$Sha, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $File)) {
        & curl.exe -L --fail --max-time 180 -o $File $Url
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $Url" }
    }
    if ((Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Sha) { throw "Hash mismatch: $File" }
    if (-not (Test-Path -LiteralPath $Destination)) { Expand-Archive -LiteralPath $File -DestinationPath $Destination }
}
Get-Archive 'https://github.com/Kitware/CMake/releases/download/v3.31.6/cmake-3.31.6-windows-x86_64.zip' '.deps\cmake.zip' 'd163cd3ab4959b0a53fa8988f2ddbd2e6c501658201e6a154386bad9dbe4f836' '.deps\cmake'
Get-Archive 'https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-win.zip' '.deps\ninja.zip' 'f550fec705b6d6ff58f2db3c374c2277a37691678d6aba463adcbb129108467a' '.deps\ninja'
$git = (Get-Command git.exe -All | Where-Object { $_.Source -like '*Program Files\Git\cmd\git.exe' } | Select-Object -First 1).Source
if (-not $git) { $git = (Get-Command git.exe).Source }
if (-not (Test-Path -LiteralPath .deps\pico-sdk)) {
    & $git clone --depth 1 --branch 2.2.0 https://github.com/raspberrypi/pico-sdk.git .deps\pico-sdk
    if ($LASTEXITCODE -ne 0) { throw 'SDK clone failed' }
}
if ((& $git -C .deps\pico-sdk rev-parse HEAD) -ne 'a1438dff1d38bd9c65dbd693f0e5db4b9ae91779') { throw 'SDK revision mismatch' }
& $git -C .deps\pico-sdk submodule update --init lib/tinyusb
if ($LASTEXITCODE -ne 0) { throw 'TinyUSB checkout failed' }
if (-not (Test-Path -LiteralPath .deps\python\serial\__init__.py)) {
    & python.exe -m pip install --target .deps\python pyserial==3.5
    if ($LASTEXITCODE -ne 0) { throw 'Local pyserial installation failed' }
}
Write-Output 'Dependencies ready. ARM GCC is required separately; this PC uses its existing devkitARM 16.1.0.'
