# 从实际 XCI 提取的参数（只读对照）

完整含未使用probe默认项的参数见对应 JSON；以下只折叠未启用probe项。数值保持原字符串。新IP路径必须由本机官方工具生成。

## i17_board_ila

xilinx.com:ip:ila:6.2，revision 19

| 参数 | 值 |
|---|---|
| C_PROBE0_TYPE | `0` |
| C_PROBE0_WIDTH | `256` |
| C_DATA_DEPTH | `1024` |
| C_NUM_OF_PROBES | `1` |
| C_XLNX_HW_PROBE_INFO | `DEFAULT` |
| Component_Name | `i17_board_ila` |
| C_TRIGOUT_EN | `false` |
| C_EN_STRG_QUAL | `0` |
| C_EN_TIME_TAG | `0` |
| C_TIME_TAG_WIDTH | `32` |
| C_INPUT_PIPE_STAGES | `0` |
| C_EN_DDR_ILA | `FALSE` |
| C_DDR_CLK_GEN | `FALSE` |
| C_CLK_FREQ | `200` |
| C_ILA_CLK_FREQ | `2000000` |
| C_CLK_PERIOD | `5` |
| C_CLKFBOUT_MULT_F | `10` |
| C_DIVCLK_DIVIDE | `3` |
| C_CLKOUT0_DIVIDE_F | `10` |
| C_ADV_TRIGGER | `FALSE` |
| C_PROBE0_MU_CNT | `1` |
| C_TRIGIN_EN | `false` |
| EN_BRAM_DRC | `TRUE` |
| ALL_PROBE_SAME_MU | `TRUE` |
| ALL_PROBE_SAME_MU_CNT | `1` |
| C_NUM_MONITOR_SLOTS | `1` |
| C_SLOT_0_AXI_ARUSER_WIDTH | `1` |
| C_SLOT_0_AXI_RUSER_WIDTH | `1` |
| C_SLOT_0_AXI_AWUSER_WIDTH | `1` |
| C_SLOT_0_AXI_WUSER_WIDTH | `1` |
| C_SLOT_0_AXI_BUSER_WIDTH | `1` |
| C_SLOT_0_AXI_ID_WIDTH | `1` |
| C_SLOT_0_AXI_DATA_WIDTH | `32` |
| C_SLOT_0_AXI_ADDR_WIDTH | `32` |
| C_SLOT_0_AXI_PROTOCOL | `AXI4` |
| C_SLOT_0_AXIS_TDATA_WIDTH | `32` |
| C_SLOT_0_AXIS_TID_WIDTH | `1` |
| C_SLOT_0_AXIS_TUSER_WIDTH | `1` |
| C_SLOT_0_AXIS_TDEST_WIDTH | `1` |
| C_ENABLE_ILA_AXI_MON | `false` |
| C_MONITOR_TYPE | `Native` |

## i17_board_vio

xilinx.com:ip:vio:3.0，revision 27

| 参数 | 值 |
|---|---|
| C_PROBE_OUT3_INIT_VAL | `0x00000000` |
| C_PROBE_OUT2_INIT_VAL | `0x000400000000000000000000` |
| C_PROBE_OUT1_INIT_VAL | `0x0000000000000001000000000000000100000001` |
| C_PROBE_OUT0_INIT_VAL | `0x00000004` |
| C_PROBE_OUT3_WIDTH | `32` |
| C_PROBE_OUT2_WIDTH | `96` |
| C_PROBE_OUT1_WIDTH | `160` |
| C_PROBE_OUT0_WIDTH | `32` |
| C_PROBE_IN3_WIDTH | `128` |
| C_PROBE_IN2_WIDTH | `32` |
| C_PROBE_IN1_WIDTH | `64` |
| C_PROBE_IN0_WIDTH | `64` |
| C_EN_SYNCHRONIZATION | `1` |
| C_NUM_PROBE_OUT | `4` |
| C_EN_PROBE_IN_ACTIVITY | `0` |
| C_NUM_PROBE_IN | `4` |
| Component_Name | `i17_board_vio` |

## ss_fft29

xilinx.com:ip:xfft:9.1，revision 15

| 参数 | 值 |
|---|---|
| Component_Name | `ss_fft29` |
| channels | `1` |
| transform_length | `1024` |
| target_clock_frequency | `100` |
| implementation_options | `radix_2_burst_io` |
| target_data_throughput | `50` |
| run_time_configurable_transform_length | `false` |
| data_format | `fixed_point` |
| input_width | `29` |
| phase_factor_width | `24` |
| scaling_options | `scaled` |
| rounding_modes | `convergent_rounding` |
| aclken | `false` |
| aresetn | `true` |
| ovflo | `true` |
| xk_index | `true` |
| throttle_scheme | `nonrealtime` |
| output_ordering | `natural_order` |
| cyclic_prefix_insertion | `false` |
| memory_options_data | `block_ram` |
| memory_options_phase_factors | `block_ram` |
| memory_options_reorder | `block_ram` |
| number_of_stages_using_block_ram_for_data_and_phase_factors | `0` |
| memory_options_hybrid | `false` |
| complex_mult_type | `use_mults_resources` |
| butterfly_type | `use_luts` |
| super_sample_rates | `1` |
| systolicfft_inv | `false` |
| blocking_run_time_configuration | `false` |

## ss_ifft25

xilinx.com:ip:xfft:9.1，revision 15

| 参数 | 值 |
|---|---|
| Component_Name | `ss_ifft25` |
| channels | `1` |
| transform_length | `1024` |
| target_clock_frequency | `100` |
| implementation_options | `radix_2_burst_io` |
| target_data_throughput | `50` |
| run_time_configurable_transform_length | `false` |
| data_format | `fixed_point` |
| input_width | `25` |
| phase_factor_width | `24` |
| scaling_options | `scaled` |
| rounding_modes | `convergent_rounding` |
| aclken | `false` |
| aresetn | `true` |
| ovflo | `true` |
| xk_index | `true` |
| throttle_scheme | `nonrealtime` |
| output_ordering | `natural_order` |
| cyclic_prefix_insertion | `false` |
| memory_options_data | `block_ram` |
| memory_options_phase_factors | `block_ram` |
| memory_options_reorder | `block_ram` |
| number_of_stages_using_block_ram_for_data_and_phase_factors | `0` |
| memory_options_hybrid | `false` |
| complex_mult_type | `use_mults_resources` |
| butterfly_type | `use_luts` |
| super_sample_rates | `1` |
| systolicfft_inv | `false` |
| blocking_run_time_configuration | `false` |

