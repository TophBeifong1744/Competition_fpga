param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$Vivado,
    [Parameter(Mandatory=$true)][string]$OutRoot
)
$ErrorActionPreference = 'Stop'
$pkg = Split-Path -Parent $PSScriptRoot
if (Test-Path -LiteralPath $OutRoot) { throw 'OutRoot must be a NEW short path; refusing overwrite.' }
New-Item -ItemType Directory -Path $OutRoot | Out-Null
$runRoot = (Resolve-Path -LiteralPath $OutRoot).Path
& $Python "$PSScriptRoot/test_checker.py" 2>&1 | Tee-Object -FilePath "$runRoot/checker-tests.txt"
if ($LASTEXITCODE -ne 0) { throw 'checker self-tests failed' }
& $Python "$PSScriptRoot/prepare.py" --reference "$pkg/reference/b-dynamic-range" --out "$runRoot/vectors" 2>&1 | Tee-Object -FilePath "$runRoot/prepare.txt"
if ($LASTEXITCODE -ne 0) { throw 'input archive verification failed' }
& $Vivado -mode batch -notrace -source "$PSScriptRoot/build.tcl" -log "$runRoot/build.log" -journal "$runRoot/build.jou" -tclargs "$runRoot/project" 2>&1 | Tee-Object -FilePath "$runRoot/build-console.txt"
if ($LASTEXITCODE -ne 0) { throw 'Vivado build failed' }
& $Vivado -mode batch -notrace -source "$PSScriptRoot/simulate.tcl" -log "$runRoot/simulation.log" -journal "$runRoot/simulation.jou" -tclargs "$runRoot/project" "$runRoot/vectors" 2>&1 | Tee-Object -FilePath "$runRoot/simulation-console.txt"
if ($LASTEXITCODE -ne 0) { throw 'Vivado simulation command failed' }
& $Python "$PSScriptRoot/check.py" --vectors "$runRoot/vectors" --simulation "$runRoot/project/fft29_budget.sim/sim_1/behav/xsim" --out "$runRoot/check.json" 2>&1 | Tee-Object -FilePath "$runRoot/check-console.txt"
if ($LASTEXITCODE -ne 0) { throw 'FFT29 bit-exact check failed; keep all logs' }
Write-Output "Completed isolated candidate replay: $runRoot. Not default/board/full-chain approval."
