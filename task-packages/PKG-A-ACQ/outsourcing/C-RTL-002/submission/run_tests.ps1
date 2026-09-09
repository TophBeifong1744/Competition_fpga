# Run from any directory: & '<submission>/run_tests.ps1' -VivadoBin '<Vivado>/bin'
# Outputs: a NEW external temporary directory with raw logs and XSim caches.
# Next: check both ALL TESTS PASS markers; review logs before accepting.
param(
    [string]$VivadoBin = 'C:\AMDDesignTools\2025.2\Vivado\bin',
    [string]$RunDirectory = (Join-Path ([System.IO.Path]::GetTempPath()) ('c-rtl-002-' + [guid]::NewGuid().ToString('N')))
)
$ErrorActionPreference = 'Stop'
$package = $PSScriptRoot
$resolvedRun = [IO.Path]::GetFullPath($RunDirectory)
$packagePrefix = [IO.Path]::GetFullPath($package).TrimEnd('\') + '\'
if ($resolvedRun.Equals($packagePrefix.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase) -or
    $resolvedRun.StartsWith($packagePrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'RunDirectory must be outside submission.'
}
if (Test-Path -LiteralPath $resolvedRun) { throw 'Use a new RunDirectory to preserve earlier evidence.' }
foreach ($tool in @('xvlog.bat','xelab.bat','xsim.bat')) {
    if (!(Test-Path -LiteralPath (Join-Path $VivadoBin $tool))) { throw "Missing tool: $tool" }
}
New-Item -ItemType Directory -Path $resolvedRun | Out-Null
# Some automated Windows processes lack this variable; set only this process.
$previousArchitecture = $env:PROCESSOR_ARCHITECTURE
if (!$env:PROCESSOR_ARCHITECTURE -and [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq 'X64') {
    $env:PROCESSOR_ARCHITECTURE = 'AMD64'
}
function Invoke-Xilinx {
    param([string]$Tool, [string[]]$ToolArgs)
    & (Join-Path $VivadoBin $Tool) @ToolArgs
    if ($LASTEXITCODE -ne 0) { throw "$Tool failed: exit=$LASTEXITCODE; evidence in $resolvedRun" }
}
Push-Location $resolvedRun
try {
    # New .v files are parsed as Verilog, without --sv.
    Invoke-Xilinx 'xvlog.bat' @(
        (Join-Path $package 'rtl/stream_error_snapshot.v'),
        (Join-Path $package 'tb/tb_stream_error_snapshot.v'),
        (Join-Path $package 'tb/tb_stream_error_snapshot_integration.v'),
        '-log', 'compile_verilog.log'
    )
    # The pinned 001 reference remains byte-for-byte SystemVerilog.
    Invoke-Xilinx 'xvlog.bat' @('--sv', (Join-Path $package 'reference/stream_error_stats.sv'),
        '-log', 'compile_reference.log')
    foreach ($top in @('tb_stream_error_snapshot', 'tb_stream_error_snapshot_integration')) {
        Invoke-Xilinx 'xelab.bat' @("work.$top", '-s', $top, '-debug', 'typical',
            '-timescale', '1ns/1ps', '-log', "$top-elaborate.log")
        Invoke-Xilinx 'xsim.bat' @($top, '-runall', '-log', "$top-simulate.log")
        $simText = Get-Content -LiteralPath "$top-simulate.log" -Raw
        if ($simText -notmatch 'ALL TESTS PASS' -or $simText -match '(?im)^\s*(FAIL\b|FATAL\b|ERROR\b|TIMEOUT\b)') {
            throw "Missing success or failure marker in $top-simulate.log"
        }
    }
    Write-Output "VERIFIED BOTH TEST TOPS: $resolvedRun"
} finally {
    Pop-Location
    $env:PROCESSOR_ARCHITECTURE = $previousArchitecture
}
