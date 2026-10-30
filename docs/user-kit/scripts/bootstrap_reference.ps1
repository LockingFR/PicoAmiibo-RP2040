# Download reference sources only; no builds or flashing.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dir = Join-Path $root 'upstream'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$src = Join-Path $dir 'PicoSwitch2-v2.5.0'
if (-not (Test-Path $src)) {
    git clone --recursive --branch v2.5.0 --depth 1 https://github.com/notsosaelin/PicoSwitch2.git $src
    if ($LASTEXITCODE -ne 0) { throw 'Cannot clone PicoSwitch2 v2.5.0' }
}
$proto = Join-Path $dir 'switch2_controller_research'
if (-not (Test-Path $proto)) {
    git clone --depth 1 https://github.com/ndeadly/switch2_controller_research.git $proto
    if ($LASTEXITCODE -ne 0) { throw 'Cannot clone protocol reference' }
}
Write-Host 'References downloaded. Read their licenses; adapt the sources before targeting a non-W Pico.'
