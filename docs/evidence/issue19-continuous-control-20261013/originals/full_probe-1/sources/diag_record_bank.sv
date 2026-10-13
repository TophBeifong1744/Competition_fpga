`timescale 1ns/1ps
// TEST_ONLY. Complete records include sequence and local capture cycle.
// No memory reset and no pop-to-push capacity lookthrough.
module diag_record_bank #(
    parameter integer PAYLOAD_BITS=1056,
    parameter integer DEPTH=64,
    parameter integer PTR_BITS=(DEPTH<=2 ? 1 : $clog2(DEPTH)),
    parameter integer COUNT_BITS=$clog2(DEPTH+1)
)(
    input wire clk, input wire cold_rst_n,
    input wire push_valid, output wire push_ready,
    input wire [PAYLOAD_BITS-1:0] push_payload,
    input wire [63:0] push_cycle, input wire [63:0] push_seq,
    input wire pop,
    output wire head_valid,
    output wire [PAYLOAD_BITS+127:0] head_record,
    output wire [COUNT_BITS-1:0] count
);
    reg [PAYLOAD_BITS+127:0] records [0:DEPTH-1];
    reg [PTR_BITS-1:0] head_q, tail_q;
    reg [COUNT_BITS-1:0] count_q;
    wire push=push_valid && push_ready;
    wire take=pop && head_valid;
    assign count=count_q;
    assign push_ready=cold_rst_n && count_q<DEPTH;
    assign head_valid=cold_rst_n && count_q!=0;
    assign head_record=head_valid ? records[head_q] : {(PAYLOAD_BITS+128){1'b0}};
    always @(posedge clk) begin
        if (!cold_rst_n) begin head_q<=0; tail_q<=0; count_q<=0; end
        else begin
            if (push) begin
                records[tail_q]<={push_seq,push_cycle,push_payload};
                tail_q<=(tail_q==DEPTH-1) ? 0 : tail_q+1'b1;
            end
            if (take) head_q<=(head_q==DEPTH-1) ? 0 : head_q+1'b1;
            case ({push,take})
                2'b10: count_q<=count_q+1'b1;
                2'b01: count_q<=count_q-1'b1;
                default: count_q<=count_q;
            endcase
        end
    end
endmodule
