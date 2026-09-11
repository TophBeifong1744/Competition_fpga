param([Parameter(Mandatory=$true)][string]$OutDir,
      [string]$VivadoBin='F:/AMD/2025.2/Vivado/bin')
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutDir){throw 'Output must be a new directory; preserve prior logs.'}
$srcRoot=Join-Path $PSScriptRoot 'source'
New-Item -ItemType Directory -Path $OutDir | Out-Null
Push-Location $OutDir
try {
    & "$VivadoBin/xvlog.bat" "$srcRoot/rtl/pdm_cic3.v" "$srcRoot/rtl/pcm4_capture_axis.v" "$srcRoot/rtl/four_mic_top.v" 2>&1 | Tee-Object compile-console.txt
    if($LASTEXITCODE -ne 0){throw 'xvlog failed'}
    & "$VivadoBin/xvlog.bat" --sv "$srcRoot/sim/tb_four_mic.sv" 2>&1 | Tee-Object compile-tb-console.txt
    if($LASTEXITCODE -ne 0){throw 'xvlog TB failed'}
    & "$VivadoBin/xelab.bat" tb_four_mic -s four_test 2>&1 | Tee-Object elaborate-console.txt
    if($LASTEXITCODE -ne 0){throw 'xelab failed'}
    & "$VivadoBin/xsim.bat" four_test -runall 2>&1 | Tee-Object simulate-console.txt
    if($LASTEXITCODE -ne 0){throw 'xsim failed'}
    if(!(Select-String -Path simulate-console.txt -SimpleMatch 'ALL_FOUR_TESTS_PASS' -Quiet)){throw 'PASS marker absent'}
} finally {Pop-Location}
