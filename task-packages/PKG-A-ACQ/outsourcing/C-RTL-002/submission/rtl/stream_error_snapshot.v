`timescale 1ns/1ps
// C-RTL-002: inputs synchronous to clk; COUNT_WIDTH supports 1..64.
module stream_error_snapshot #(parameter integer COUNT_WIDTH = 32) (
    input wire clk,
    input wire rst_n,
    input wire snapshot_req,
    input wire [COUNT_WIDTH-1:0] live_overflow_count,
    input wire [COUNT_WIDTH-1:0] live_drop_count,
    input wire live_overflow_sticky,
    input wire live_drop_sticky,
    output reg [COUNT_WIDTH-1:0] snapshot_overflow_count,
    output reg [COUNT_WIDTH-1:0] snapshot_drop_count,
    output reg snapshot_overflow_sticky,
    output reg snapshot_drop_sticky,
    output reg snapshot_valid
);
    always @(posedge clk) begin
        if (!rst_n) begin
            snapshot_overflow_count <= {COUNT_WIDTH{1'b0}};
            snapshot_drop_count <= {COUNT_WIDTH{1'b0}};
            snapshot_overflow_sticky <= 1'b0;
            snapshot_drop_sticky <= 1'b0;
            snapshot_valid <= 1'b0;
        end else begin
            snapshot_valid <= snapshot_req;
            if (snapshot_req) begin
                snapshot_overflow_count <= live_overflow_count;
                snapshot_drop_count <= live_drop_count;
                snapshot_overflow_sticky <= live_overflow_sticky;
                snapshot_drop_sticky <= live_drop_sticky;
            end
        end
    end
endmodule
