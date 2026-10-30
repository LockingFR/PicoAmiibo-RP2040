param(
    [string]$ArmToolchain = 'C:\devkitPro\devkitARM',
    [string]$BuildDirectory = 'build\pico'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$cmake = Join-Path $root '.deps\cmake\cmake-3.31.6-windows-x86_64\bin\cmake.exe'
$ninja = Join-Path $root '.deps\ninja\ninja.exe'
$sdk = Join-Path $root '.deps\pico-sdk'
$git = (Get-Command git.exe -All | Where-Object { $_.Source -like '*Program Files\Git\cmd\git.exe' } | Select-Object -First 1).Source
if (-not $git) { $git = (Get-Command git.exe).Source }
$python = (Get-Command python.exe).Source
foreach ($file in @($cmake, $ninja, (Join-Path $ArmToolchain 'bin\arm-none-eabi-gcc.exe'))) {
    if (-not (Test-Path -LiteralPath $file)) { throw "Missing $file. Run tools\setup.ps1 or pass -ArmToolchain." }
}
if ((& $git -C $sdk rev-parse HEAD) -ne 'a1438dff1d38bd9c65dbd693f0e5db4b9ae91779') { throw 'Pico SDK revision mismatch' }
if ((& $git -C (Join-Path $sdk 'lib\tinyusb') rev-parse HEAD) -ne '86ad6e56c1700e85f1c5678607a762cfe3aa2f47') { throw 'TinyUSB revision mismatch' }
New-Item -ItemType Directory -Path artifacts -Force | Out-Null
$log = Join-Path $root 'artifacts\build.log'
# Windows PowerShell 5.1 treats redirected native stderr as ErrorRecord objects.
# CMake uses stderr for informational SDK messages. Trust its actual exit code.
$ErrorActionPreference = 'Continue'
& $cmake -S . -B $BuildDirectory -G Ninja '-DPICO_BOARD=pico' "-DPICO_SDK_PATH=$sdk" "-DPICO_TOOLCHAIN_PATH=$ArmToolchain" "-DCMAKE_MAKE_PROGRAM=$ninja" '-DCMAKE_BUILD_TYPE=Release' "-DPython3_EXECUTABLE=$python" "-DGIT_EXECUTABLE=$git" 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $log
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed' }
& $cmake --build $BuildDirectory --parallel 4 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) { throw 'Firmware build failed' }
& $python tools\uf2.py inspect (Join-Path $BuildDirectory 'PicoAmiibo-RP2040-pico-empty.uf2')
if ($LASTEXITCODE -ne 0) { throw 'UF2 inspection failed' }
$ErrorActionPreference = 'Stop'
