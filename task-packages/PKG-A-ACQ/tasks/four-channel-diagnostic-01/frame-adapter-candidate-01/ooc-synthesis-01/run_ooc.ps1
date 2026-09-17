param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_-]+$')]
    [string]$RunName,
    [string]$VivadoBat = 'F:/AMD/2025.2/Vivado/bin/vivado.bat'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runDir = Join-Path $root ('runs/' + $RunName)
$launcherDir = Join-Path $root ('launcher-logs/' + $RunName)
if (-not (Test-Path -LiteralPath $VivadoBat -PathType Leaf)) {
    throw "Vivado launcher is missing: $VivadoBat"
}
if (Test-Path -LiteralPath $runDir) {
    throw "Refusing to overwrite OOC output: $runDir"
}
if (Test-Path -LiteralPath $launcherDir) {
    throw "Refusing to overwrite launcher logs: $launcherDir"
}
New-Item -ItemType Directory -Path $launcherDir | Out-Null
$tcl = Join-Path $root 'run_ooc.tcl'
$log = Join-Path $launcherDir 'vivado.log'
$journal = Join-Path $launcherDir 'vivado.jou'
$command = "& '$VivadoBat' -mode batch -log '$log' -journal '$journal' -source '$tcl' -tclargs '$RunName'"
[IO.File]::WriteAllText((Join-Path $launcherDir 'command.txt'), $command + [Environment]::NewLine)

& $VivadoBat -mode batch -log $log -journal $journal -source $tcl -tclargs $RunName
$code = $LASTEXITCODE
[IO.File]::WriteAllText((Join-Path $launcherDir 'exit-code.txt'), "$code`r`n")
if ($code -ne 0) {
    throw "Vivado OOC synthesis failed with exit code $code. Preserve $launcherDir and any partial $runDir."
}
$status = Join-Path $runDir 'STATUS.txt'
if (-not (Test-Path -LiteralPath $status -PathType Leaf) -or
    (Get-Content -Raw -LiteralPath $status) -notmatch 'OOC_SYNTH_COMPLETE_NOT_IMPL_NOT_BOARD') {
    throw "Vivado exited zero but the bound completion marker is missing: $status"
}
Write-Output "OOC_SYNTH_RUN_COMPLETE_NOT_ANALYZED $runDir"
