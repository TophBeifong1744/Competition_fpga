`timescale 1ns/1ps
`default_nettype none
// Explicit single-tuple diagnostic lease. This is not a production freshness source.
module diag_single_source_v1 (
    input wire clk, rst_n,
    input wire arm_request, config_valid, stop_now, fault_now, cancel_now,
    input wire [88:0] config_tuple,
    input wire [164:0] declared_context,
    input wire [63:0] declared_generation,
    input wire [724:0] declared_tuple,
    output wire armed, current_qualified,
    output wire [724:0] leased_tuple,
    output wire [63:0] policy_id
);
    localparam [63:0] DIAGV001 = 64'h4449414756303031;
    reg arm_was_high, armed_q;
    reg [724:0] tuple_q;
    reg [88:0] config_q;
    // Parent context_t MSB layout: status[164:163], boot_valid[162],
    // epoch_valid[97], sid_valid[32]. Status 1 is DECLARED; zero is UNBOUND.
    wire context_declared = declared_context[164:163] == 2'd1 &&
                            declared_context[162] &&
                            declared_context[97] &&
                            declared_context[32];
    wire declared_consistent =
        context_declared &&
        declared_tuple[660:597] == declared_generation &&
        declared_tuple[596:432] == declared_context;
    wire valid_now = config_valid && config_tuple == config_q && declared_consistent &&
        declared_tuple == tuple_q && !stop_now && !fault_now && !cancel_now;
    assign armed = armed_q;
    assign leased_tuple = tuple_q;
    assign policy_id = DIAGV001;
    assign current_qualified = rst_n && armed_q && valid_now;

    always @(posedge clk) begin
        if (!rst_n) begin
            arm_was_high <= 1'b1; // require an observed LOW before an arm edge
            armed_q <= 1'b0;
            tuple_q <= 725'd0;
            config_q <= 89'd0;
        end else begin
            arm_was_high <= arm_request;
            if (armed_q && !valid_now)
                armed_q <= 1'b0;
            else if (!arm_was_high && arm_request && config_valid &&
                     declared_consistent && !stop_now && !fault_now && !cancel_now) begin
                tuple_q <= declared_tuple;
                config_q <= config_tuple;
                armed_q <= 1'b1;
            end
        end
    end
endmodule
`default_nettype wire
