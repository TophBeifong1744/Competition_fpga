param([string]$VivadoBin = 'F:\AMD\2025.2\Vivado\bin')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$simdir = Join-Path $root 'evidence\sim'
New-Item -ItemType Directory -Force -Path $simdir | Out-Null
Push-Location $simdir
try {
    & (Join-Path $VivadoBin 'xvlog.bat') --sv (Join-Path $root 'rtl\test_source.sv') (Join-Path $root 'sim\tb_test_source.sv')
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoBin 'xelab.bat') tb_test_source -s task1_sim
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') task1_sim -runall
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $log = Get-Content -Raw -LiteralPath 'xsim.log'
    if ($log -notmatch 'ALL TASK1 TESTS PASS' -or $log -match '(?m)^(Fatal:|ERROR:)') {
        throw 'Self-check did not pass; inspect xsim.log'
    }
} finally { Pop-Location }
