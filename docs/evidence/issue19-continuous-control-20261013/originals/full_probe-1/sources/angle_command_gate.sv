`timescale 1ns / 1ps
`default_nettype none

// Candidate same-clock command boundary. C samples the combinational command
// at the same rising edge; registered pulses are observations, not commands.
module angle_command_gate #(
    parameter integer SESSION_W = 32,
    parameter integer WINDOW_W = 32
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
    output logic [8:0]           angle_deg_o,
    output logic                 angle_valid_o,
    output logic                 accept_pulse_o,
    output logic                 reject_pulse_o,
    output logic [3:0]           reject_reason_o,
    output logic                 suppressed_o,
    output logic                 faulted_o,
    output logic                 armed_o,
    output logic                 seen_valid_o,
    output logic [WINDOW_W-1:0]  last_seen_window_o
);
    localparam logic [3:0] REJ_NONE            = 4'd0;
    localparam logic [3:0] REJ_FAULT           = 4'd1;
    localparam logic [3:0] REJ_STOP            = 4'd2;
    localparam logic [3:0] REJ_DISABLED        = 4'd3;
    localparam logic [3:0] REJ_CONFIG_INVALID  = 4'd4;
    localparam logic [3:0] REJ_SESSION_INVALID = 4'd5;
    localparam logic [3:0] REJ_RECONFIG        = 4'd6;
    localparam logic [3:0] REJ_UNARMED         = 4'd7;
    localparam logic [3:0] REJ_OLD_SESSION     = 4'd8;
    localparam logic [3:0] REJ_RESULT_INVALID  = 4'd9;
    localparam logic [3:0] REJ_NOT_FRESH       = 4'd10;
    localparam logic [3:0] REJ_DUPLICATE       = 4'd11;
    localparam logic [3:0] REJ_OUT_OF_ORDER    = 4'd12;
    localparam logic [3:0] REJ_OUT_OF_RANGE    = 4'd13;

    logic                 session_known_q;
    logic [SESSION_W-1:0] session_q;
    logic                 seen_valid_q;
    logic [WINDOW_W-1:0]  last_seen_q;
    logic                 config_valid_q;
    logic [8:0]           angle_min_q;
    logic [8:0]           angle_max_q;
    logic                 armed_q;

    logic config_good;
    logic config_changed;
    logic session_changed;
    logic transition;
    logic runnable;
    logic current_session_match;
    logic consume_window;
    logic window_new;
    logic angle_in_range;
    logic [3:0] reject_reason_d;

    assign config_good = config_valid_i && (angle_min_i <= angle_max_i);
    assign config_changed = (config_valid_i != config_valid_q) ||
                            (angle_min_i != angle_min_q) ||
                            (angle_max_i != angle_max_q);
    // An explicit known bit makes session zero a valid identity.
    assign session_changed = session_valid_i &&
                             (!session_known_q || (active_session_i != session_q));
    assign transition = config_changed || session_changed;
    assign runnable = enable_i && !stop_i && !fault_i &&
                      config_good && session_valid_i;
    assign current_session_match = session_valid_i &&
                                   (result_session_i == active_session_i);
    assign consume_window = result_strobe_i && current_session_match;
    assign window_new = !seen_valid_q || (result_window_i > last_seen_q);
    assign angle_in_range = (result_angle_i >= angle_min_i) &&
                            (result_angle_i <= angle_max_i);

    assign angle_deg_o = result_angle_i;
    // Direct qualification avoids routing the 4-bit priority encoder into C's
    // enable path. No angle, command, or retry is registered for later delivery.
    assign angle_valid_o = rst_n && result_strobe_i && runnable &&
                           !transition && armed_q && current_session_match &&
                           result_valid_i && result_fresh_i &&
                           window_new && angle_in_range;
    assign suppressed_o = !rst_n || !runnable || transition || !armed_q;
    assign faulted_o = rst_n && fault_i;
    assign armed_o = armed_q;
    assign seen_valid_o = seen_valid_q;
    assign last_seen_window_o = last_seen_q;

    // First-cause priority applies only to submitted results. Reset and a LOW
    // strobe report NONE and generate neither registered observation pulse.
    always_comb begin
        reject_reason_d = REJ_NONE;
        if (rst_n && result_strobe_i) begin
            if (fault_i)                     reject_reason_d = REJ_FAULT;
            else if (stop_i)                 reject_reason_d = REJ_STOP;
            else if (!enable_i)              reject_reason_d = REJ_DISABLED;
            else if (!config_good)           reject_reason_d = REJ_CONFIG_INVALID;
            else if (!session_valid_i)       reject_reason_d = REJ_SESSION_INVALID;
            else if (transition)             reject_reason_d = REJ_RECONFIG;
            else if (!armed_q)               reject_reason_d = REJ_UNARMED;
            else if (!current_session_match) reject_reason_d = REJ_OLD_SESSION;
            else if (!result_valid_i)         reject_reason_d = REJ_RESULT_INVALID;
            else if (!result_fresh_i)         reject_reason_d = REJ_NOT_FRESH;
            else if (seen_valid_q && (result_window_i == last_seen_q))
                                             reject_reason_d = REJ_DUPLICATE;
            else if (seen_valid_q && (result_window_i < last_seen_q))
                                             reject_reason_d = REJ_OUT_OF_ORDER;
            else if (!angle_in_range)        reject_reason_d = REJ_OUT_OF_RANGE;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            session_known_q <= 1'b0;
            session_q       <= '0;
            seen_valid_q    <= 1'b0;
            last_seen_q     <= '0;
            config_valid_q  <= 1'b0;
            angle_min_q     <= 9'd0;
            angle_max_q     <= 9'd0;
            armed_q         <= 1'b0;
            accept_pulse_o  <= 1'b0;
            reject_pulse_o  <= 1'b0;
            reject_reason_o <= REJ_NONE;
        end else begin
            config_valid_q <= config_valid_i;
            angle_min_q    <= angle_min_i;
            angle_max_q    <= angle_max_i;
            accept_pulse_o <= angle_valid_o;
            reject_pulse_o <= result_strobe_i && !angle_valid_o;
            reject_reason_o <= reject_reason_d;

            if (!runnable || transition)
                armed_q <= 1'b0;
            else if (!result_strobe_i)
                armed_q <= 1'b1;
            // HIGH leaves armed set in stable operation, permitting distinct
            // new windows at adjacent sampling edges without a queue.

            if (session_changed) begin
                session_known_q <= 1'b1;
                session_q       <= active_session_i;
                // Discard old history first, then consume a matching new
                // session submission even though this transition is blocked.
                seen_valid_q <= consume_window;
                last_seen_q  <= consume_window ? result_window_i : '0;
            end else if (consume_window && window_new) begin
                // Consumption is independent of acceptance: blocked, invalid,
                // stale, unarmed, and out-of-range submissions cannot retry.
                seen_valid_q <= 1'b1;
                last_seen_q  <= result_window_i;
            end
            // Same-session stop/fault/disable/config changes and invalidation
            // retain identity/history. Old-session results never consume it.
        end
    end

    // synthesis translate_off
    initial begin
        if ((SESSION_W <= 0) || (WINDOW_W <= 0))
            $fatal(1, "SESSION_W and WINDOW_W must both be positive");
    end
    // synthesis translate_on
endmodule

`default_nettype wire
