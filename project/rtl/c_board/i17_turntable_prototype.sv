`timescale 1ns/1ps
`default_nettype none
// 中文用途：有限已知方向直接接C控制链的内部原型入口；不是板级顶层，不含DOA或自动运动许可。
module i17_turntable_prototype #(
    parameter integer CONFIGURED = 0,
    parameter integer COUNT = 1,
    parameter integer SPACING_CYCLES = 0,
    parameter [COUNT*18-1:0] ANGLES_Q8 = 0,
    parameter [COUNT*725-1:0] IDENTITIES = 0,
    parameter integer CLK_FREQ_HZ = 0,
    parameter integer MAX_ANGLE_DEG = 0,
    parameter integer RESET_ANGLE_DEG = -1
) (
    input wire clk, rst_n,
    input wire start_i, enable_i, command_stop_i, fault_i,
    input wire mechanical_approved_i, output_permit_i, output_revoke_i,
    input wire config_valid_i,
    input wire signed [23:0] offset_q8_i,
    input wire signed [1:0] direction_i,
    input wire signed [17:0] domain_min_q8_i, domain_max_q8_i,
    input wire [8:0] mechanical_min_i, mechanical_max_i,
    output wire known_injection_o, busy_o, done_o, cancelled_o,
    output wire [31:0] index_o,
    output wire source_strobe_o,
    output wire signed [17:0] source_angle_q8_o,
    output wire [724:0] source_identity_o,
    output wire config_legal_o, map_valid_o,
    output wire [8:0] mapped_angle_o,
    output wire command_valid_o, accept_pulse_o, reject_pulse_o,
    output wire [3:0] reject_reason_o,
    output wire raw_pwm_o, pwm_o, output_open_o, output_draining_o, awaiting_command_o,
    output wire accepted_identity_valid_o,
    output wire [724:0] last_accepted_identity_o,
    output wire [7:0] first_fault_o,
    output wire [63:0] last_seen_generation_o,
    output wire seen_valid_o
);
    wire identity_match;
    i17_turntable_known_source #(.CONFIGURED(CONFIGURED),.COUNT(COUNT),
        .SPACING_CYCLES(SPACING_CYCLES),.ANGLES_Q8(ANGLES_Q8),.IDENTITIES(IDENTITIES)) source (
        .clk(clk),.rst_n(rst_n),.start_i(start_i),.enable_i(enable_i),
        .stop_i(command_stop_i || output_revoke_i),.fault_i(fault_i),
        .result_strobe_o(source_strobe_o),.result_angle_q8_o(source_angle_q8_o),
        .result_identity_o(source_identity_o),.known_injection_o(known_injection_o),
        .busy_o(busy_o),.done_o(done_o),.cancelled_o(cancelled_o),.index_o(index_o));
    // 此处来源是本有限表本身，不是实际租约或麦克风资格的证明；实方向需外部真实active tuple。
    i17_turntable_result_slice #(.CLK_FREQ_HZ(CLK_FREQ_HZ),.MAX_ANGLE_DEG(MAX_ANGLE_DEG),
        .RESET_ANGLE_DEG(RESET_ANGLE_DEG)) consumer (
        .clk(clk),.rst_n(rst_n),.enable_i(enable_i),.command_stop_i(command_stop_i),.fault_i(fault_i),
        .mechanical_approved_i(mechanical_approved_i),.output_permit_i(output_permit_i),
        .output_revoke_i(output_revoke_i),.config_valid_i(config_valid_i),
        .offset_q8_i(offset_q8_i),.direction_i(direction_i),
        .domain_min_q8_i(domain_min_q8_i),.domain_max_q8_i(domain_max_q8_i),
        .mechanical_min_i(mechanical_min_i),.mechanical_max_i(mechanical_max_i),
        .active_identity_valid_i(busy_o || done_o || cancelled_o),.active_identity_i(source_identity_o),
        .result_strobe_i(source_strobe_o),.result_identity_i(source_identity_o),
        .result_angle_q8_i(source_angle_q8_o),
        .numeric_valid_i(1'b1),.delivery_eligible_i(1'b1),.fresh_i(1'b1),.abort_i(1'b0),
        .config_legal_o(config_legal_o),.identity_match_o(identity_match),.map_valid_o(map_valid_o),
        .mapped_angle_o(mapped_angle_o),.command_valid_o(command_valid_o),
        .accept_pulse_o(accept_pulse_o),.reject_pulse_o(reject_pulse_o),.reject_reason_o(reject_reason_o),
        .raw_pwm_o(raw_pwm_o),.pwm_o(pwm_o),.output_open_o(output_open_o),
        .output_draining_o(output_draining_o),.awaiting_command_o(awaiting_command_o),
        .accepted_identity_valid_o(accepted_identity_valid_o),.last_accepted_identity_o(last_accepted_identity_o),
        .first_fault_o(first_fault_o),.last_seen_generation_o(last_seen_generation_o),.seen_valid_o(seen_valid_o));
endmodule
`default_nettype wire
