// C-RTL-001: independent overflow/drop event counters.
// COUNT_WIDTH: 1..64; unsigned counters saturate at all ones.
// Single clock domain; all inputs must already be synchronous to clk.
// Synchronous active-low reset; no additional pipeline stage.
module stream_error_stats #(
    parameter integer COUNT_WIDTH = 32
) (
    input  logic                   clk,
    input  logic                   rst_n,
    input  logic                   clear,
    input  logic                   overflow_event,
    input  logic                   drop_event,
    output logic [COUNT_WIDTH-1:0] overflow_count,
    output logic [COUNT_WIDTH-1:0] drop_count,
    output logic                   overflow_sticky,
    output logic                   drop_sticky
);

    localparam logic [COUNT_WIDTH-1:0] COUNT_MAX = {COUNT_WIDTH{1'b1}};

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            // Reset overrides clear and both current events.
            overflow_count  <= '0;
            drop_count      <= '0;
            overflow_sticky <= 1'b0;
            drop_sticky     <= 1'b0;
        end else if (clear) begin
            // Clear history, then count this edge's events (zero or one).
            // Unsigned one-bit inputs are zero-extended to COUNT_WIDTH.
            overflow_count  <= overflow_event;
            drop_count      <= drop_event;
            overflow_sticky <= overflow_event;
            drop_sticky     <= drop_event;
        end else begin
            // Every asserted cycle counts, independently for each lane.
            if (overflow_event) begin
                overflow_sticky <= 1'b1;
                if (overflow_count != COUNT_MAX)
                    overflow_count <= overflow_count + 1'b1;
            end

            if (drop_event) begin
                drop_sticky <= 1'b1;
                if (drop_count != COUNT_MAX)
                    drop_count <= drop_count + 1'b1;
            end
            // Registers otherwise hold their state, including at saturation.
        end
    end
endmodule
