param([string]$Bsp='F:/College/verilog_digital_system/Vitis/dma_platform/export/dma_platform/sw/standalone_ps7_cortexa9_0', [string]$OutDir)
$ErrorActionPreference='Stop'
if (!$OutDir) { throw 'Specify a fresh OutDir; old builds are preserved' }
if (Test-Path -LiteralPath $OutDir) {throw 'Output already exists'}
New-Item -ItemType Directory -Path $OutDir | Out-Null
$out=(Resolve-Path -LiteralPath $OutDir).Path
$scratch='F:/College/verilog_digital_system/four_diagnostic_work/ps-'+[guid]::NewGuid().ToString('N')
New-Item -ItemType Directory -Path $scratch | Out-Null
Copy-Item "$PSScriptRoot/source/ps/main_four_capture.c","$PSScriptRoot/source/ps/lscript.ld" $scratch
$gcc='F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe'
$argsBuild=@('-DSDT','-mcpu=cortex-a9','-mfpu=vfpv3','-mfloat-abi=hard','-std=c11','-Wall','-Wextra','-Werror','-O0','-g3',"-specs=$Bsp/Xilinx.spec","-I$Bsp/include", "$scratch/main_four_capture.c",'-o',"$scratch/four_mic_capture.elf","-L$Bsp/lib","-Wl,-T,$scratch/lscript.ld","-Wl,-Map=$scratch/four_mic_capture.map,--cref",'-Wl,--start-group','-lxilstandalone','-lxiltimer','-lxil','-lgcc','-lc','-Wl,--end-group')
& $gcc --version | Out-File "$out/compiler.txt"
$argsBuild | ConvertTo-Json | Out-File "$out/arguments.json"
& $gcc @argsBuild 2>&1 | Tee-Object "$out/build.log"
if($LASTEXITCODE -ne 0){throw 'PS build failed; log retained'}
Copy-Item "$scratch/four_mic_capture.elf","$scratch/four_mic_capture.map" $out
& ($gcc -replace 'gcc.exe$','size.exe') "$scratch/four_mic_capture.elf" | Tee-Object -Append "$out/build.log"
if($LASTEXITCODE -ne 0){throw 'Size failed'}
Write-Output 'PS_BUILD_PASS_NOT_BOARD_TEST'
