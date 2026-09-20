param(
    [string]$VivadoBin = 'C:\AMDDesignTools\2025.2\Vivado\bin',
    [int]$ClockHz = 100000000,
    [ValidateSet(360,220)][int]$MaxAngleDeg = 360,
    [string]$OutputDirectory = ''
)
$ErrorActionPreference = 'Stop'
# 部分受限终端没有架构环境变量，旧版 Vivado 会误选 win32。
$savedArchitecture = $env:PROCESSOR_ARCHITECTURE
if (-not $savedArchitecture -and [Environment]::Is64BitOperatingSystem) {
    $env:PROCESSOR_ARCHITECTURE = 'AMD64'
}
$packageRoot = Split-Path $PSScriptRoot -Parent
$repoRoot = Split-Path (Split-Path $packageRoot -Parent) -Parent
# 每轮使用新输出目录，保留历史证据；显式目录存在时拒绝覆盖。
if ($OutputDirectory) {
    $buildDir = [IO.Path]::GetFullPath($OutputDirectory)
} else {
    $runTag = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $buildDir = Join-Path $repoRoot "sim/build/servo-pwm-$ClockHz-$MaxAngleDeg-$runTag"
}
if (Test-Path -LiteralPath $buildDir) { throw "Output already exists: $buildDir" }
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
Push-Location $buildDir
try {
    & (Join-Path $VivadoBin 'xvlog.bat') (Join-Path $packageRoot 'rtl/motor_drive.v') (Join-Path $packageRoot 'tb/tb_motor_drive.v')
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    # 保留字面引号，防止 Windows .bat 把等号拆成两个参数。
    $genericArgument = '"CLK_FREQ_HZ=' + $ClockHz + '"'
    $angleArgument = '"MAX_ANGLE_DEG=' + $MaxAngleDeg + '"'
    & (Join-Path $VivadoBin 'xelab.bat') tb_motor_drive -generic_top $genericArgument -generic_top $angleArgument -s servo_pwm_test
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') servo_pwm_test -runall -log simulation.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $simText = Get-Content -Raw simulation.log
    $expectedChecks = if ($MaxAngleDeg -eq 220) { 69 } else { 61 }
    $expectedPass = "PASS motor_drive checks=$expectedChecks CLK_FREQ_HZ=$ClockHz MAX_ANGLE_DEG=$MaxAngleDeg"
    if (-not $simText.Contains($expectedPass) -or $simText -match 'FAIL|Fatal:|ERROR:') {
        throw 'Simulation did not report a clean PASS'
    }
    Write-Host "Verified PASS; logs: $buildDir"
}
finally {
    Pop-Location
    $env:PROCESSOR_ARCHITECTURE = $savedArchitecture
}
