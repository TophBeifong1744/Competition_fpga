param(
    [string]$VivadoBin = 'D:\Vivado\2018.3\bin',
    [int]$ClockHz = 100000000
)
$ErrorActionPreference = 'Stop'
# 部分受限终端没有架构环境变量，旧版 Vivado 会误选 win32。
$savedArchitecture = $env:PROCESSOR_ARCHITECTURE
if (-not $savedArchitecture -and [Environment]::Is64BitOperatingSystem) {
    $env:PROCESSOR_ARCHITECTURE = 'AMD64'
}
$packageRoot = Split-Path $PSScriptRoot -Parent
$repoRoot = Split-Path (Split-Path $packageRoot -Parent) -Parent
$buildDir = Join-Path $repoRoot "sim/build/servo-pwm-$ClockHz"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
Push-Location $buildDir
try {
    & (Join-Path $VivadoBin 'xvlog.bat') (Join-Path $packageRoot 'rtl/motor_drive.v') (Join-Path $packageRoot 'tb/tb_motor_drive.v')
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    # 保留字面引号，防止 Windows .bat 把等号拆成两个参数。
    $genericArgument = '"CLK_FREQ_HZ=' + $ClockHz + '"'
    & (Join-Path $VivadoBin 'xelab.bat') tb_motor_drive -generic_top $genericArgument -s servo_pwm_test
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') servo_pwm_test -runall -log simulation.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $simText = Get-Content -Raw simulation.log
    if ($simText -notmatch 'PASS motor_drive' -or $simText -match 'FAIL|Fatal:') {
        throw 'Simulation did not report a clean PASS'
    }
    Write-Host "Verified PASS; logs: $buildDir"
}
finally {
    Pop-Location
    $env:PROCESSOR_ARCHITECTURE = $savedArchitecture
}
