# Run: & '<submission>/audit_mutations.ps1' -VivadoBin '<Vivado>/bin'
# Output: a new temp directory containing six mutated RTL copies, raw logs,
# and summary.json. Next: every mutant must report DETECTED; official RTL is never edited.
param(
    [string]$VivadoBin = 'C:\AMDDesignTools\2025.2\Vivado\bin',
    [string]$RunDirectory = (Join-Path ([IO.Path]::GetTempPath()) ('c-rtl-002-mutations-' + [guid]::NewGuid().ToString('N')))
)
$ErrorActionPreference = 'Stop'
$rtlPath = Join-Path $PSScriptRoot 'rtl/stream_error_snapshot.v'
$tbPath = Join-Path $PSScriptRoot 'tb/tb_stream_error_snapshot.v'
$original = [IO.File]::ReadAllText($rtlPath)
$beforeHash = (Get-FileHash -LiteralPath $rtlPath -Algorithm SHA256).Hash
$resolvedRun = [IO.Path]::GetFullPath($RunDirectory)
$packagePrefix = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
if ($resolvedRun.Equals($packagePrefix.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase) -or $resolvedRun.StartsWith($packagePrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Mutation output must be outside submission.'
}
if (Test-Path -LiteralPath $resolvedRun) { throw 'Use a new directory; preserve previous evidence.' }
New-Item -ItemType Directory -Path $resolvedRun | Out-Null
$cases = @(
    @{name='async_reset'; old='always @(posedge clk)'; new='always @(posedge clk or negedge rst_n)'},
    @{name='capture_without_request'; old='if (snapshot_req)'; new="if (1'b1)"},
    @{name='sticky_valid'; old='snapshot_valid <= snapshot_req;'; new="if (snapshot_req) snapshot_valid <= 1'b1;"},
    @{name='crossed_counter_lanes'; old='snapshot_overflow_count <= live_overflow_count;'; new='snapshot_overflow_count <= live_drop_count;'},
    @{name='bit17_copied_from_bit19'; old='snapshot_overflow_count <= live_overflow_count;'; new="snapshot_overflow_count <= live_overflow_count ^ ((((live_overflow_count >> 17) ^ (live_overflow_count >> 19)) & 64'd1) << 17);"},
    @{name='reset_loses_to_request'; old='if (!rst_n)'; new='if (!rst_n && !snapshot_req)'}
)
$previousArchitecture = $env:PROCESSOR_ARCHITECTURE
if (!$env:PROCESSOR_ARCHITECTURE -and [Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq 'X64') { $env:PROCESSOR_ARCHITECTURE = 'AMD64' }
$results = @()
try {
    foreach ($case in $cases) {
        if (($original.Split([string[]]@($case.old), [StringSplitOptions]::None).Length - 1) -ne 1) { throw "Mutation target not unique: $($case.name)" }
        $caseDir = Join-Path $resolvedRun $case.name
        New-Item -ItemType Directory -Path $caseDir | Out-Null
        $mutantPath = Join-Path $caseDir 'mutant.v'
        [IO.File]::WriteAllText($mutantPath, $original.Replace($case.old, $case.new), [Text.UTF8Encoding]::new($false))
        Push-Location $caseDir
        try {
            & (Join-Path $VivadoBin 'xvlog.bat') $mutantPath $tbPath -log compile.log *> compile-console.txt
            if ($LASTEXITCODE -ne 0) { throw "Mutation compile failure is NOT detection: $($case.name)" }
            & (Join-Path $VivadoBin 'xelab.bat') work.tb_stream_error_snapshot -s mutation -timescale 1ns/1ps -log elaborate.log *> elaborate-console.txt
            if ($LASTEXITCODE -ne 0) { throw "Mutation elaboration failure is NOT detection: $($case.name)" }
            & (Join-Path $VivadoBin 'xsim.bat') mutation -runall -log simulate.log *> simulate-console.txt
            $simExit = $LASTEXITCODE
            $log = Get-Content -LiteralPath simulate.log -Raw
            $failure = [regex]::Match($log, '(?m)^FAIL W=.*')
            if (!$failure.Success -or $log -match 'ALL TESTS PASS' -or $log -match 'TIMEOUT') { throw "Mutant escaped or did not fail as expected: $($case.name)" }
            $results += [ordered]@{mutation=$case.name; result='DETECTED'; simulation_exit=$simExit; failure=$failure.Value.Trim()}
            Write-Output "DETECTED: $($case.name): $($failure.Value.Trim())"
        } finally { Pop-Location }
    }
    $results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $resolvedRun 'summary.json') -Encoding utf8
    if ((Get-FileHash -LiteralPath $rtlPath -Algorithm SHA256).Hash -ne $beforeHash) { throw 'Official RTL changed unexpectedly' }
    Write-Output "ALL 6 MUTANTS DETECTED: $resolvedRun"
} finally { $env:PROCESSOR_ARCHITECTURE = $previousArchitecture }
