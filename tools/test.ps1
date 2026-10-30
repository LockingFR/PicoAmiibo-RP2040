param([string]$Distribution = 'Ubuntu-24.04')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$windowsPath = $root.Replace('\', '/')
$linuxRoot = (& wsl.exe -d $Distribution -- wslpath -u $windowsPath).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve project path in WSL' }
& wsl.exe -d $Distribution --cd $linuxRoot -- python3 tools/test.py
if ($LASTEXITCODE -ne 0) { throw 'Host tests failed' }
