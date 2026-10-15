`timescale 1ns/1ps
`default_nettype none
// 中文用途：已知方向/真实方向共用的同域结果消费切口；完整来源身份匹配后复用C映射与运行门。
module i17_turntable_result_slice #(
    parameter integer CLK_FREQ_HZ = 0,
    parameter integer MAX_ANGLE_DEG = 0,
    parameter integer RESET_ANGLE_DEG = -1
) (
    input wire clk, rst_n,
    input wire enable_i, command_stop_i, fault_i,
    input wire mechanical_approved_i, output_permit_i, output_revoke_i,
    input wire config_valid_i,
    input wire signed [23:0] offset_q8_i,
    input wire signed [1:0] direction_i,
    input wire signed [17:0] domain_min_q8_i, domain_max_q8_i,
    input wire [8:0] mechanical_min_i, mechanical_max_i,
    input wire active_identity_valid_i,
    input wire [724:0] active_identity_i,
    input wire result_strobe_i,
    input wire [724:0] result_identity_i,
    input wire signed [17:0] result_angle_q8_i,
    input wire numeric_valid_i, delivery_eligible_i, fresh_i, abort_i,
    output wire config_legal_o, identity_match_o, map_valid_o,
    output wire [8:0] mapped_angle_o,
    output wire command_valid_o, accept_pulse_o, reject_pulse_o,
    output wire [3:0] reject_reason_o,
    output wire raw_pwm_o, pwm_o, output_open_o, output_draining_o, awaiting_command_o,
    output reg accepted_identity_valid_o,
    output reg [724:0] last_accepted_identity_o,
    output reg [7:0] first_fault_o,
    output wire [63:0] last_seen_generation_o,
    output wire seen_valid_o
);
    wire map_config_legal;
    wire [8:0] runtime_angle;
    wire runtime_armed, runtime_suppressed, runtime_faulted;
    wire approved_config = mechanical_approved_i && map_config_legal &&
        mechanical_min_i <= RESET_ANGLE_DEG && mechanical_max_i >= RESET_ANGLE_DEG;
    wire [80:0] config_tuple = {config_valid_i,offset_q8_i,direction_i,
        domain_min_q8_i,domain_max_q8_i,mechanical_min_i,mechanical_max_i};
    reg [80:0] config_q;
    reg [164:0] context_q;
    reg identity_valid_q;
    wire context_change = active_identity_valid_i &&
        (!identity_valid_q || context_q != active_identity_i[596:432]);
    wire config_change = config_q != config_tuple;
    wire independent_revoke = output_revoke_i || fault_i || !enable_i ||
        !approved_config || !active_identity_valid_i || context_change || config_change;
    assign config_legal_o = approved_config;
    assign identity_match_o = active_identity_valid_i && (active_identity_i == result_identity_i);
    signed_angle_map mapper (
        .config_valid(config_valid_i),.angle_q8(result_angle_q8_i),
        .offset_q8(offset_q8_i),.direction(direction_i),
        .domain_min_q8(domain_min_q8_i),.domain_max_q8(domain_max_q8_i),
        .mechanical_min(mechanical_min_i),.mechanical_max(mechanical_max_i),
        .servo_max(MAX_ANGLE_DEG[8:0]),.config_legal(map_config_legal),
        .valid(map_valid_o),.angle_deg(mapped_angle_o));
    runtime_servo_slice #(.SESSION_W(165),.WINDOW_W(64),
        .CLK_FREQ_HZ(CLK_FREQ_HZ),.MAX_ANGLE_DEG(MAX_ANGLE_DEG),
        .RESET_ANGLE_DEG(RESET_ANGLE_DEG)) runtime (
        .clk(clk),.rst_n(rst_n),.enable_i(enable_i && mechanical_approved_i),
        .stop_i(command_stop_i || output_revoke_i || config_change || context_change),.fault_i(fault_i),
        .config_valid_i(approved_config),
        .angle_min_i(mechanical_min_i),.angle_max_i(mechanical_max_i),
        .session_valid_i(active_identity_valid_i),.active_session_i(active_identity_i[596:432]),
        .result_strobe_i(result_strobe_i),
        .result_valid_i(identity_match_o && numeric_valid_i && delivery_eligible_i && map_valid_o && !abort_i),
        .result_fresh_i(fresh_i),.result_session_i(result_identity_i[596:432]),
        .result_window_i(result_identity_i[660:597]),.result_angle_i(mapped_angle_o),
        .angle_deg_o(runtime_angle),.angle_valid_o(command_valid_o),
        .accept_pulse_o(accept_pulse_o),.reject_pulse_o(reject_pulse_o),
        .reject_reason_o(reject_reason_o),.suppressed_o(runtime_suppressed),
        .faulted_o(runtime_faulted),.armed_o(runtime_armed),
        .seen_valid_o(seen_valid_o),.last_seen_window_o(last_seen_generation_o),.pwm_o(raw_pwm_o));
    i17_turntable_pwm_guard guard (
        .clk(clk),.rst_n(rst_n),.raw_pwm_i(raw_pwm_o),
        .permit_i(output_permit_i && approved_config),.output_revoke_i(independent_revoke),
        .fresh_command_i(command_valid_o),.pwm_o(pwm_o),.open_o(output_open_o),
        .draining_o(output_draining_o),.awaiting_command_o(awaiting_command_o));
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            config_q <= 0; context_q <= 0; identity_valid_q <= 0;
            accepted_identity_valid_o <= 0; last_accepted_identity_o <= 0; first_fault_o <= 0;
        end else begin
            config_q <= config_tuple;
            context_q <= active_identity_i[596:432]; identity_valid_q <= active_identity_valid_i;
            if (command_valid_o) begin
                accepted_identity_valid_o <= 1; last_accepted_identity_o <= result_identity_i;
            end
            // 首错保留至cold reset；STOP/重新使能不删除审计，不称机械故障分类。
            if (first_fault_o == 0) begin
                if (fault_i) first_fault_o <= 8'h01;
                else if (result_strobe_i && abort_i) first_fault_o <= 8'h02;
                else if (result_strobe_i && !numeric_valid_i) first_fault_o <= 8'h03;
            end
        end
    end
    // synthesis translate_off
    initial begin
        if (CLK_FREQ_HZ < 1000000 || MAX_ANGLE_DEG < 1 || MAX_ANGLE_DEG > 511 ||
            RESET_ANGLE_DEG < 0 || RESET_ANGLE_DEG > MAX_ANGLE_DEG)
            $fatal(1,"Explicit legal electrical clock/range/reset parameters required");
    end
    // synthesis translate_on
endmodule
`default_nettype wire
