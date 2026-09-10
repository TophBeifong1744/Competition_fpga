// C-RTL-004 interface c-rtl-004-if-1.0: transparent Verilog BD entry.
// COUNT_WIDTH 1..64; unsigned counts, no scaling or added latency.
module stream_error_stats_bd #(parameter integer COUNT_WIDTH = 32) (
    input wire clk,
    input wire rst_n,
    input wire clear,
    input wire overflow_event,
    input wire drop_event,
    output wire [COUNT_WIDTH-1:0] overflow_count,
    output wire [COUNT_WIDTH-1:0] drop_count,
    output wire overflow_sticky,
    output wire drop_sticky
);
    stream_error_stats #(.COUNT_WIDTH(COUNT_WIDTH)) core (
        .clk(clk), .rst_n(rst_n), .clear(clear),
        .overflow_event(overflow_event), .drop_event(drop_event),
        .overflow_count(overflow_count), .drop_count(drop_count),
        .overflow_sticky(overflow_sticky), .drop_sticky(drop_sticky)
    );
endmodule
