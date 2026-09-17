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
New-Item -ItemType Directory -Path $record | Out-Null

function Invoke-Recorded {
    param([string]$Label, [string]$Executable, [string[]]$Arguments)
    # Use .txt because the repository globally ignores *.log.
    $log = Join-Path $record ($Label + '.txt')
    & $Executable @Arguments 2>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "$Label failed with exit code $code; see $log" }
}

Push-Location $root
try {
    Invoke-Recorded 'model' $PythonExe @('-m','unittest','discover','-s','tests','-v')
    Invoke-Recorded 'xvlog' (Join-Path $VivadoBin 'xvlog.bat') @(
        '-sv',
        '../frame-adapter-candidate-01/rtl/pcm4_overlap_framer.v',
        'rtl/pcm4_overlap_framer_bram.v',
        'sim/tb_pcm4_overlap_framer_bram.sv',
        'sim/tb_pcm4_overlap_boundaries.sv',
        'sim/tb_pcm4_overlap_equivalence.sv'
    )
    Invoke-Recorded 'xelab-self' (Join-Path $VivadoBin 'xelab.bat') @(
        'tb_pcm4_overlap_framer_bram','-s','tb_pcm4_overlap_framer_bram_sim')
    Invoke-Recorded 'xsim-self' (Join-Path $VivadoBin 'xsim.bat') @(
        'tb_pcm4_overlap_framer_bram_sim','-runall')
    Invoke-Recorded 'xelab-boundaries' (Join-Path $VivadoBin 'xelab.bat') @(
        'tb_pcm4_overlap_boundaries','-s','tb_pcm4_overlap_boundaries_sim')
    Invoke-Recorded 'xsim-boundaries' (Join-Path $VivadoBin 'xsim.bat') @(
        'tb_pcm4_overlap_boundaries_sim','-runall')
    Invoke-Recorded 'xelab-equivalence' (Join-Path $VivadoBin 'xelab.bat') @(
        'tb_pcm4_overlap_equivalence','-s','tb_pcm4_overlap_equivalence_sim')
    Invoke-Recorded 'xsim-equivalence' (Join-Path $VivadoBin 'xsim.bat') @(
        'tb_pcm4_overlap_equivalence_sim','-runall')

    $selfLog = Get-Content -Raw -LiteralPath (Join-Path $record 'xsim-self.txt')
    $boundaryLog = Get-Content -Raw -LiteralPath (Join-Path $record 'xsim-boundaries.txt')
    $eqLog = Get-Content -Raw -LiteralPath (Join-Path $record 'xsim-equivalence.txt')
    if ($selfLog -notmatch 'PASS BRAM_FRAMER frames=5 events=10' -or $selfLog -match '(?m)^FAIL ') {
        throw 'Self-check did not emit its exact PASS marker; preserve evidence.'
    }
    if ($boundaryLog -notmatch 'PASS BRAM_BOUNDARIES cases=6 groups=0,1023,1024,1535,1536,2048' -or $boundaryLog -match '(?m)^FAIL ') {
        throw 'Boundary matrix did not emit its exact PASS marker; preserve evidence.'
    }
    if ($eqLog -notmatch 'PASS BRAM_EQUIVALENCE outputs=3072 events=1' -or $eqLog -match '(?m)^FAIL ') {
        throw 'Equivalence check did not emit its exact PASS marker; preserve evidence.'
    }

    $paths = @(
        'rtl/pcm4_overlap_framer_bram.v',
        'sim/tb_pcm4_overlap_framer_bram.sv',
        'sim/tb_pcm4_overlap_boundaries.sv',
        'sim/tb_pcm4_overlap_equivalence.sv',
        'model/framing_model.py',
        'tests/test_framing_model.py',
        'reproduce.ps1',
        '../frame-adapter-candidate-01/rtl/pcm4_overlap_framer.v'
    )
    $hashes = foreach ($path in $paths) {
        $full = Join-Path $root $path
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $full).Hash.ToLowerInvariant()
        "$hash  $path"
    }
    [System.IO.File]::WriteAllLines((Join-Path $record 'SHA256.txt'), $hashes)
    Write-Output "BRAM_CANDIDATE_TEST_PASS_NOT_SYNTH_NOT_BOARD $record"
} finally {
    Pop-Location
}
