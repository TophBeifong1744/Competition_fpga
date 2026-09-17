#requires -Version 7.0
param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$VivadoBin='F:/AMD/2025.2/Vivado/bin',
    [int]$ClockHz=100000000
)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $out){throw 'Use a new output directory'}
$manifest=Get-Content (Join-Path $PSScriptRoot 'modules.json') -Raw | ConvertFrom-Json
$files=@($manifest.files | Where-Object {$_.target -like '*/servo/*'})
if($files.Count -ne 2){throw 'Expected two approved servo files'}
foreach($file in $files){
    $path=Join-Path $repo $file.target
    $normal=(Get-Content -LiteralPath $path -Raw).Replace("`r`n","`n")
    $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($normal))).ToLowerInvariant()
    if($hash -ne $file.normalized_sha256){throw "Source mismatch: $path"}
}
New-Item -ItemType Directory -Path $out | Out-Null
$prior=$env:PROCESSOR_ARCHITECTURE
if(!$prior){$env:PROCESSOR_ARCHITECTURE='AMD64'}
$result=[ordered]@{status='RUNNING';clock_hz=$ClockHz;vivado_bin=$VivadoBin;sources=@($files | ForEach-Object {Join-Path $repo $_.target});stages=@()}
Push-Location $out
try{
    & (Join-Path $VivadoBin 'xvlog.bat') @($result.sources) *> compile.txt
    $result.stages+=@{name='xvlog';exit_code=$LASTEXITCODE}
    if($LASTEXITCODE -ne 0){throw 'Compile failed'}
    $generic='"CLK_FREQ_HZ='+$ClockHz+'"'
    & (Join-Path $VivadoBin 'xelab.bat') tb_motor_drive -generic_top $generic -s servo_library *> elaborate.txt
    $result.stages+=@{name='xelab';exit_code=$LASTEXITCODE}
    if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
    & (Join-Path $VivadoBin 'xsim.bat') servo_library -runall -log simulation.log *> simulate.txt
    $result.stages+=@{name='xsim';exit_code=$LASTEXITCODE}
    if($LASTEXITCODE -ne 0){throw 'Simulation process failed'}
    $log=Get-Content simulation.log -Raw
    if($log -notmatch 'PASS motor_drive checks=39' -or $log -match 'FAIL|Fatal:|ERROR:'){throw 'Simulation verdict failed'}
    $result.status='PASS_MODULE_SIMULATION'
    Write-Output "PASS servo active-library CLK_FREQ_HZ=$ClockHz"
}catch{
    $result.status='FAIL';$result.error=$_.Exception.Message;throw
}finally{
    $result | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'result.json') -Encoding utf8
    Pop-Location
    $env:PROCESSOR_ARCHITECTURE=$prior
}
