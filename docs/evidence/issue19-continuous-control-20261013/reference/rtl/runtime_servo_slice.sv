`timescale 1ns / 1ps
`default_nettype none

// Same-clock runtime boundary; command qualification remains combinational.
module runtime_servo_slice #(
    parameter integer SESSION_W = 32,
    parameter integer WINDOW_W = 32,
    parameter integer CLK_FREQ_HZ = 100_000_000,
    parameter integer MAX_ANGLE_DEG = 360,
    parameter integer RESET_ANGLE_DEG = MAX_ANGLE_DEG / 2
) (
    input  wire logic                 clk,
    input  wire logic                 rst_n,
    input  wire logic                 enable_i,
    input  wire logic                 stop_i,
    input  wire logic                 fault_i,
    input  wire logic                 config_valid_i,
    input  wire logic [8:0]           angle_min_i,
    input  wire logic [8:0]           angle_max_i,
    input  wire logic                 session_valid_i,
    input  wire logic [SESSION_W-1:0] active_session_i,
    input  wire logic                 result_strobe_i,
    input  wire logic                 result_valid_i,
    input  wire logic                 result_fresh_i,
    input  wire logic [SESSION_W-1:0] result_session_i,
    input  wire logic [WINDOW_W-1:0]  result_window_i,
    input  wire logic [8:0]           result_angle_i,
    output wire logic [8:0]           angle_deg_o,
    output wire logic                 angle_valid_o,
    output wire logic                 accept_pulse_o,
    output wire logic                 reject_pulse_o,
    output wire logic [3:0]           reject_reason_o,
    output wire logic                 suppressed_o,
    output wire logic                 faulted_o,
    output wire logic                 armed_o,
    output wire logic                 seen_valid_o,
    output wire logic [WINDOW_W-1:0]  last_seen_window_o,
    output wire logic                 pwm_o
);
    wire logic effective_config_valid;

    // Legal parent MAX is a positive integer in 1..511; no 9-bit truncation.
    assign effective_config_valid = config_valid_i
                                  && (angle_min_i <= angle_max_i)
                                  && (angle_max_i <= MAX_ANGLE_DEG);

    angle_command_gate #(
        .SESSION_W(SESSION_W),
        .WINDOW_W(WINDOW_W)
    ) u_gate (
        .clk(clk),
        .rst_n(rst_n),
        .enable_i(enable_i),
        .stop_i(stop_i),
        .fault_i(fault_i),
        .config_valid_i(effective_config_valid),
        .angle_min_i(angle_min_i),
        .angle_max_i(angle_max_i),
        .session_valid_i(session_valid_i),
        .active_session_i(active_session_i),
        .result_strobe_i(result_strobe_i),
        .result_valid_i(result_valid_i),
        .result_fresh_i(result_fresh_i),
        .result_session_i(result_session_i),
        .result_window_i(result_window_i),
        .result_angle_i(result_angle_i),
        .angle_deg_o(angle_deg_o),
        .angle_valid_o(angle_valid_o),
        .accept_pulse_o(accept_pulse_o),
        .reject_pulse_o(reject_pulse_o),
        .reject_reason_o(reject_reason_o),
        .suppressed_o(suppressed_o),
        .faulted_o(faulted_o),
        .armed_o(armed_o),
        .seen_valid_o(seen_valid_o),
        .last_seen_window_o(last_seen_window_o)
    );

    // C samples the public combinational command at the same S edge.
    // The registered accept observation is not a motor command.
    motor_drive #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .MAX_ANGLE_DEG(MAX_ANGLE_DEG),
        .RESET_ANGLE_DEG(RESET_ANGLE_DEG)
    ) u_motor (
        .clk(clk),
        .rst_n(rst_n),
        .angle_deg_i(angle_deg_o),
        .angle_valid_i(angle_valid_o),
        .pwm_o(pwm_o)
    );
endmodule

`default_nettype wire
