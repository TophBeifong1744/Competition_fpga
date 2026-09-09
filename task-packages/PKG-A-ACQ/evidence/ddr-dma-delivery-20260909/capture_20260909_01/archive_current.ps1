$ErrorActionPreference = 'Stop'
$dest = $PSScriptRoot
$appRoot = 'F:/College/verilog_digital_system/Vitis/dma_test'
$platformRoot = 'F:/College/verilog_digital_system/Vitis/dma_platform'
$oneRoot = 'F:/College/verilog_digital_system/AMD/Competiton/one'
$items = @(
    @('E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-B-ALG/payload/model/python/h1_reader.py', 'reader/h1_reader.py'),
    @("$appRoot/src/main.c", 'software/main.c'),
    @("$appRoot/src/lscript.ld", 'software/lscript.ld'),
    @("$appRoot/src/UserConfig.cmake", 'software/UserConfig.cmake'),
    @("$appRoot/src/CMakeLists.txt", 'software/CMakeLists.txt'),
    @("$appRoot/build/dma_test.elf", 'software/dma_test.elf'),
    @("$appRoot/build/dma_test.map", 'software/dma_test.map'),
    @("$appRoot/build/compile_commands.json", 'software/compile_commands.json'),
    @("$platformRoot/export/dma_platform/sw/standalone_ps7_cortexa9_0/include/xparameters.h", 'software/xparameters.h'),
    @("$platformRoot/vitis-comp.json", 'software/platform.json'),
    @("$platformRoot/export/dma_platform/hw/one_dma_v1.xsa", 'hardware/one_dma_v1.xsa'),
    @("$appRoot/_ide/bitstream/one_dma_v1.bit", 'hardware/one_dma_v1.bit'),
    @("$oneRoot/one.xpr", 'hardware/one.xpr'),
    @("$oneRoot/one.srcs/sources_1/bd/system/system.bd", 'hardware/system.bd'),
    @("$oneRoot/one.srcs/sources_1/imports/rtl/test_source.sv", 'hardware/test_source.sv'),
    @("$oneRoot/one.srcs/sources_1/new/test_source_bd.v", 'hardware/test_source_bd.v'),
    @("$oneRoot/one.srcs/sources_1/new/start_pulse.v", 'hardware/start_pulse.v'),
    @("$oneRoot/one.runs/impl_1/system_wrapper_timing_summary_routed.rpt", 'hardware/timing_summary_routed.rpt'),
    @("$oneRoot/one.runs/impl_1/system_wrapper_drc_routed.rpt", 'hardware/drc_routed.rpt'),
    @("$oneRoot/one.runs/impl_1/system_wrapper_utilization_placed.rpt", 'hardware/utilization_placed.rpt')
)
$records = foreach ($item in $items) {
    $target = Join-Path $dest $item[1]
    if (Test-Path -LiteralPath $target) { throw "Refusing to overwrite snapshot: $target" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    $originalHash = (Get-FileHash -LiteralPath $item[0] -Algorithm SHA256).Hash
    Copy-Item -LiteralPath $item[0] -Destination $target
    $copiedHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($originalHash -ne $copiedHash) { throw "Copy mismatch: $target" }
    [pscustomobject]@{
        source=$item[0]; saved=$item[1]; sha256=$copiedHash
        bytes=(Get-Item -LiteralPath $target).Length
        sourceLastWriteUtc=(Get-Item -LiteralPath $item[0]).LastWriteTimeUtc.ToString('o')
    }
}
$manifest = [ordered]@{
    archivedAtUtc=[DateTime]::UtcNow.ToString('o')
    provenance='User pasted one-batch export; underscore escapes normalized. Current software and hardware files snapshotted.'
    status='One-batch capture reports PASS. Local artifact snapshot not proof of loaded board image.'
    files=@($records)
    captureFiles=@('metadata.json','samples.csv','uart_user_supplied.log','validate_capture.py','README.md' | ForEach-Object { [pscustomobject]@{saved=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $dest $_)).Hash} })
    uartSha256=(Get-FileHash -LiteralPath (Join-Path $dest 'uart_user_supplied.log')).Hash
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $dest 'manifest.json') -Encoding utf8
'SNAPSHOT_PASS'
