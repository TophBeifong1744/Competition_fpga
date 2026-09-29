#requires -Version 7.0
param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [ValidateSet('single','dual','canary')][string]$Mode='single',
    [ValidateSet(1000000,100000000)][int]$ClockHz=1000000,
    [ValidateSet(220,360)][int]$MaxAngleDeg=360,
    [string]$VivadoBin='C:\AMDDesignTools\2025.2\Vivado\bin'
)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $out){throw "Use a new output directory: $out"}
$source=Join-Path $repo 'project/rtl/servo/motor_drive.v'
$tb=if($Mode -eq 'dual'){
    Join-Path $PSScriptRoot 'tb_servo_dual_axis_v2.sv'
}else{
    Join-Path $PSScriptRoot 'tb_motor_drive_v2_targeted.sv'
}
$top=if($Mode -eq 'dual'){'tb_servo_dual_axis_v2'}else{'tb_motor_drive_v2_targeted'}
$marker=if($Mode -eq 'dual'){'PASS v2 dual-axis checks='}else{'PASS v2 targeted checks='}
$architecture=$env:PROCESSOR_ARCHITECTURE
if(-not $architecture -and [Environment]::Is64BitOperatingSystem){$env:PROCESSOR_ARCHITECTURE='AMD64'}
New-Item -ItemType Directory -Path $out -Force | Out-Null
$result=[ordered]@{
    mode=$Mode; status='RUNNING'; claim='AUTHOR_DIRECTED_SIM_ONLY';
    clock_hz=$ClockHz; max_angle_deg=if($Mode -eq 'dual'){$null}else{$MaxAngleDeg};
    source=$source; tb=$tb; vivado_bin=$VivadoBin; stages=@()
}
try {
    if($Mode -eq 'canary'){
        $text=[IO.File]::ReadAllText($source)
        $needle='else if (angle_valid_i)'
        if(($text.Split(@($needle),[StringSplitOptions]::None).Count-1) -ne 1){throw 'Canary edit point is not unique'}
        $source=Join-Path $out 'motor_drive_fault.v'
        [IO.File]::WriteAllText($source,$text.Replace($needle,"else if (1'b0)"),[Text.UTF8Encoding]::new($false))
        $result.source=$source
        $result.canary_mutation='Suppress angle_valid_i command latch in copied RTL only'
    }
    Push-Location $out
    try {
        & (Join-Path $VivadoBin 'xvlog.bat') -sv $source $tb *> xvlog.txt
        $result.stages+=@{name='xvlog';exit_code=$LASTEXITCODE;log='xvlog.txt'}
        if($LASTEXITCODE -ne 0){throw 'xvlog failed'}
        $clockGeneric='"CLK_FREQ_HZ='+$ClockHz+'"'
        if($Mode -eq 'dual'){
            & (Join-Path $VivadoBin 'xelab.bat') $top -generic_top $clockGeneric -s servo_v2_targeted *> xelab.txt
        }else{
            $angleGeneric='"MAX_ANGLE_DEG='+$MaxAngleDeg+'"'
            & (Join-Path $VivadoBin 'xelab.bat') $top -generic_top $clockGeneric -generic_top $angleGeneric -s servo_v2_targeted *> xelab.txt
        }
        $result.stages+=@{name='xelab';exit_code=$LASTEXITCODE;log='xelab.txt'}
        if($LASTEXITCODE -ne 0){throw 'xelab failed'}
        & (Join-Path $VivadoBin 'xsim.bat') servo_v2_targeted -runall -log simulation.log *> xsim.stdout.txt
        $result.stages+=@{name='xsim';exit_code=$LASTEXITCODE;log='simulation.log'}
        $log=Get-Content -LiteralPath simulation.log -Raw
        if($Mode -eq 'canary'){
            # XSim 2025.2 may return 0 even after $fatal; require the exact fatal
            # signature and absence of PASS rather than assuming a process code.
            if($log -notmatch 'Fatal: FAIL valid B-1 width' -or $log.Contains($marker)){
                throw 'Canary did not fail at the expected first timing check'
            }
            $result.canary_exit_note='XSim returned its recorded process code; verdict uses exact Fatal signature because $fatal may exit 0'
            $result.status='EXPECTED_FAIL_CHECKER'
        }else{
            if($LASTEXITCODE -ne 0 -or -not $log.Contains($marker) -or $log -match 'FAIL|Fatal:|ERROR:'){
                throw 'Directed simulation did not report clean PASS'
            }
            $result.status='PASS_DIRECTED_SIM_AUTHOR'
        }
    }finally{Pop-Location}
}catch{
    $result.status='FAIL'
    $result.error=$_.Exception.Message
    throw
}finally{
    $result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8
    $env:PROCESSOR_ARCHITECTURE=$architecture
}
Write-Output "$($result.status) $Mode CLK_FREQ_HZ=$ClockHz MAX_ANGLE_DEG=$MaxAngleDeg output=$out"
