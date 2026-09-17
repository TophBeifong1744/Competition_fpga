param(
    [string]$VivadoBin = 'F:/AMD/2025.2/Vivado/bin',
    [string]$PythonExe = 'python',
    [string]$RecordName = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RecordName) { $RecordName = 'run-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') }
if ($RecordName -notmatch '^[A-Za-z0-9_-]+$') { throw 'RecordName must be a simple filename.' }
$record = Join-Path $root ('evidence/' + $RecordName)
if (Test-Path -LiteralPath $record) { throw "Evidence directory exists: $record" }
foreach ($tool in @('xvlog.bat','xelab.bat','xsim.bat')) {
    if (-not (Test-Path -LiteralPath (Join-Path $VivadoBin $tool))) { throw "Missing $tool in $VivadoBin" }
}
if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) { throw "Missing Python: $PythonExe" }
New-Item -ItemType Directory -Path $record -Force | Out-Null

function Invoke-Recorded {
    param([string]$Label, [string]$Executable, [string[]]$Arguments)
    $log = Join-Path $record ($Label + '.log')
    & $Executable @Arguments 2>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "$Label failed with exit code $code; see $log" }
}

Push-Location $root
try {
    Invoke-Recorded 'model' $PythonExe @('-m','unittest','discover','-s','tests','-v')
    Invoke-Recorded 'xvlog' (Join-Path $VivadoBin 'xvlog.bat') @('-sv','rtl/pcm4_overlap_framer.v','sim/tb_pcm4_overlap_framer.sv')
    Invoke-Recorded 'xelab' (Join-Path $VivadoBin 'xelab.bat') @('tb_pcm4_overlap_framer','-s','tb_pcm4_overlap_framer_sim')
    Invoke-Recorded 'xsim' (Join-Path $VivadoBin 'xsim.bat') @('tb_pcm4_overlap_framer_sim','-runall')
    $simLog = Get-Content -Raw -LiteralPath (Join-Path $record 'xsim.log')
    if ($simLog -notmatch 'PASS frame_adapter RTL: frames=7 events=9' -or $simLog -match '(?m)^FAIL ') {
        throw 'Simulator did not emit the exact expected PASS; preserve evidence.'
    }
    $paths = @('rtl/pcm4_overlap_framer.v','sim/tb_pcm4_overlap_framer.sv',
               'model/framing_model.py','tests/test_framing_model.py','reproduce.ps1')
    $hashes = foreach ($path in $paths) {
        $full = Join-Path $root $path
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $full).Hash.ToLowerInvariant()
        "$hash  $path"
    }
    [System.IO.File]::WriteAllLines((Join-Path $record 'SHA256.txt'), $hashes)
    Write-Output "CANDIDATE_TEST_PASS_NOT_SYNTH_NOT_BOARD $record"
} finally {
    Pop-Location
}
