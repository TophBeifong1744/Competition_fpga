`timescale 1ns/1ps
`default_nettype none
// 中文用途：五bank轮询真实导出，下游握手才逐字ACK；保留原select/ack低相重装语义。
module i17_diag_consumer (
    input wire clk, rst_n,
    input wire [31:0] bank_counts,
    output wire select_valid, output wire [2:0] select_bank,
    output wire ack_valid, output wire [63:0] ack_sequence, output wire [5:0] ack_word,
    input wire export_valid, input wire [31:0] export_data,
    input wire [2:0] export_bank, input wire [63:0] export_sequence,
    input wire [5:0] export_word, export_words, input wire export_last,
    output wire m_valid, input wire m_ready, output wire [31:0] m_data,
    output wire [2:0] m_bank, output wire [63:0] m_sequence,
    output wire [5:0] m_word, m_words, output wire m_last,
    output wire idle, output reg [63:0] records_consumed
);
    localparam [2:0] SCAN=0, SELECT=1, WAIT_EXPORT=2, STREAM=3, ACK_GAP=4, NEXT=5;
    reg [2:0] state, bank_q;
    wire present = bank_q==0 ? bank_counts[6:0]!=0 :
        bank_q==1 ? bank_counts[10:7]!=0 : bank_q==2 ? bank_counts[14:11]!=0 :
        bank_q==3 ? bank_counts[18:15]!=0 : bank_counts[22:19]!=0;
    assign select_valid = rst_n && state==SELECT;
    assign select_bank = bank_q;
    assign m_valid = rst_n && state==STREAM && export_valid;
    assign m_data=export_data;
    assign m_bank=export_bank;
    assign m_sequence=export_sequence;
    assign m_word=export_word;
    assign m_words=export_words;
    assign m_last=export_last;
    assign ack_valid=m_valid && m_ready;
    assign ack_sequence=export_sequence;
    assign ack_word=export_word;
    assign idle=state==SCAN && bank_counts==0 && !export_valid;
    always @(posedge clk) begin
        if(!rst_n) begin state<=SCAN; bank_q<=0; records_consumed<=0; end
        else case(state)
            SCAN: if(present) state<=SELECT; else bank_q<=bank_q==4 ? 0 : bank_q+1'b1;
            SELECT: state<=WAIT_EXPORT;
            WAIT_EXPORT: if(export_valid) state<=STREAM;
            STREAM: if(ack_valid) begin
                if(export_last) begin
                    if(records_consumed!=64'hffffffffffffffff) records_consumed<=records_consumed+1'b1;
                    state<=NEXT;
                end else state<=ACK_GAP;
            end
            ACK_GAP: state<=STREAM;
            NEXT: begin bank_q<=bank_q==4 ? 0 : bank_q+1'b1; state<=SCAN; end
            default: state<=SCAN;
        endcase
    end
endmodule
`default_nettype wire
