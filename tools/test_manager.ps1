param([switch]$Frozen)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python=Join-Path $root '.deps\manager-env\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run tools/build_manager.ps1 to prepare the private environment' }
& $python -m pytest manager\tests tests\test_loader.py tests\test_uf2.py -q
if ($LASTEXITCODE -ne 0) { throw 'Manager tests failed' }
if ($Frozen) {
    $profile=Join-Path $root ('build\manager-exe-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
    & $python tools\manager_test_profile.py $profile
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create isolated artificial test profile' }
    $exe=Join-Path $root 'dist\PicoAmiibo-Manager\PicoAmiibo-Manager.exe'
    $screens=Join-Path $root 'artifacts\manager-v1\screenshots\release'
    $process=Start-Process -FilePath $exe -ArgumentList @('--smoke-test','--no-usb','--data-dir',('"'+$profile+'"'),'--screenshots',('"'+$screens+'"')) -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(30000)) { throw ('EXE smoke test exceeded 30 seconds; inspect exact PID '+$process.Id) }
    if ($process.ExitCode -ne 0) { throw ('EXE smoke failed: '+$process.ExitCode) }
    $result=Get-Content -Raw -LiteralPath (Join-Path $profile 'smoke-result.json') | ConvertFrom-Json
    if (-not $result.success -or -not $result.frozen -or -not $result.usb_disabled -or $result.pages.Count -ne 6) { throw 'Frozen EXE did not verify all six views' }
    $result | Add-Member -NotePropertyName exe_sha256 -NotePropertyValue (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLower()
    $result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 artifacts\manager-v1\exe-smoke-result.json
    Write-Output 'PASS: actual Windows x64 EXE; six rendered views; isolated artificial library; USB disabled. Hardware UNTESTED.'
}
