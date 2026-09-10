param(
    [Parameter(Mandatory=$true)][string]$VivadoBin
)
# Run: & ./run_xsim.ps1 -VivadoBin 'C:/AMDDesignTools/2025.2/Vivado/bin'
# Outputs: logs/{xvlog,xelab,xsim}.log and logs/run-summary.txt.
# Next: check ALL TESTS PASS, then review README and regenerate the manifest.
$ErrorActionPreference = 'Stop'
$packageDir = $PSScriptRoot
$toolDir = (Resolve-Path -LiteralPath $VivadoBin).Path
$logDir = Join-Path $packageDir 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$runDir = Join-Path ([IO.Path]::GetTempPath()) ('pcm4-xsim-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDir | Out-Null
$started = Get-Date -Format o
$previousArchitecture = $env:PROCESSOR_ARCHITECTURE
if (!$env:PROCESSOR_ARCHITECTURE -and [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq 'X64') {
    $env:PROCESSOR_ARCHITECTURE = 'AMD64'
}
$previousLogs = @(Get-ChildItem -LiteralPath $logDir -File | Where-Object { $_.Name -in @('xvlog.log','xelab.log','xsim.log','run-summary.txt') })
if ($previousLogs.Count -gt 0) {
    $archiveDir = Join-Path $logDir ('attempt-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $archiveDir | Out-Null
    $previousLogs | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $archiveDir }
}
Push-Location $runDir
try {
    & (Join-Path $toolDir 'xvlog.bat') (Join-Path $packageDir 'rtl/pcm4_signext_pack.v') (Join-Path $packageDir 'tb/tb_pcm4_signext_pack.v') -log (Join-Path $logDir 'xvlog.log')
    if ($LASTEXITCODE -ne 0) { throw "xvlog failed: $LASTEXITCODE" }
    & (Join-Path $toolDir 'xelab.bat') 'work.tb_pcm4_signext_pack' -s 'pcm4_test' -log (Join-Path $logDir 'xelab.log')
    if ($LASTEXITCODE -ne 0) { throw "xelab failed: $LASTEXITCODE" }
    & (Join-Path $toolDir 'xsim.bat') 'pcm4_test' -runall -log (Join-Path $logDir 'xsim.log')
    if ($LASTEXITCODE -ne 0) { throw "xsim failed: $LASTEXITCODE" }
    $simulationLog = Get-Content -Raw -LiteralPath (Join-Path $logDir 'xsim.log')
    if ($simulationLog -notmatch 'ALL TESTS PASS' -or $simulationLog -match '(?im)^\s*(Fatal:|Error:|FAIL\b)') {
        throw 'Simulation did not complete cleanly with ALL TESTS PASS'
    }
    @("Started: $started", "Ended: $(Get-Date -Format o)", "VivadoBin: $toolDir", "Build directory (outside package): $runDir", 'RESULT: PASS') |
        Set-Content -LiteralPath (Join-Path $logDir 'run-summary.txt') -Encoding utf8
} catch {
    @("Started: $started", "Ended: $(Get-Date -Format o)", "Build directory: $runDir", "RESULT: FAIL - $_") |
        Set-Content -LiteralPath (Join-Path $logDir 'run-summary.txt') -Encoding utf8
    throw
} finally {
    Pop-Location
    $env:PROCESSOR_ARCHITECTURE = $previousArchitecture
}

