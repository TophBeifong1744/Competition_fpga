`timescale 1ns/1ps
// Four-channel record: id_lo,id_hi,mic0..3,flags,reserved. All ports clk-domain.
// flags[3:0] = per-channel saturation; fatal errors are sticky status, not fake rows.
module pcm4_capture_axis #(
    parameter TOTAL_SAMPLES=32000, SAMPLES_PER_PACKET=250, FIFO_LOG2=10
)(
    input wire clk, rst_n, start, ready,
    input wire [3:0] pcm_valid,
    input wire [95:0] pcm, // mic0 in low 24 bits
    input wire [3:0] clipped,
    input wire [63:0] sample_id,
    output wire [31:0] m_axis_tdata,
    output wire [3:0] m_axis_tkeep,
    output wire m_axis_tvalid, m_axis_tlast,
    input wire m_axis_tready,
    output wire [31:0] status
);
    localparam DEPTH=1<<FIFO_LOG2;
    reg [255:0] mem[0:DEPTH-1];
    reg [FIFO_LOG2-1:0] wp,rp;
    reg [FIFO_LOG2:0] count;
    reg [2:0] beat;
    reg [31:0] captured,sent,packet_sample;
    reg busy,overflow,done,clip_seen,sync_error;
    reg [15:0] drops;
    wire mismatch=(|pcm_valid) && !(&pcm_valid);
    wire pop=m_axis_tvalid && m_axis_tready && beat==7;
    wire space=(count<DEPTH)||pop;
    wire push=busy && (&pcm_valid) && space && !sync_error;
    wire accept_start=start && ready && !busy && count==0 && !overflow && !sync_error && !mismatch;
    wire [255:0] head=mem[rp];
    assign m_axis_tdata=head >> (beat*32);
    assign m_axis_tkeep=4'hf;
    assign m_axis_tvalid=(count!=0);
    assign m_axis_tlast=m_axis_tvalid && beat==7 &&
        ((packet_sample==SAMPLES_PER_PACKET-1)||(sent==TOTAL_SAMPLES-1));
    // bits 0 busy,1 ready,2 overflow,3 done,4 clip_seen,5 sync_error,31:16 drops
    assign status={drops,10'b0,sync_error,clip_seen,done,overflow,ready,busy};
    always @(posedge clk) begin
        if(!rst_n) begin
            wp<=0;rp<=0;count<=0;beat<=0;captured<=0;sent<=0;packet_sample<=0;
            busy<=0;overflow<=0;done<=0;clip_seen<=0;sync_error<=0;drops<=0;
        end else begin
            if(accept_start) begin
                busy<=1;done<=0;clip_seen<=0;captured<=0;sent<=0;packet_sample<=0;
            end
            // Detect desynchronization even in idle: recovery requires frontend reset.
            if(mismatch) begin sync_error<=1;busy<=0;done<=0;end
            if(push) begin
                mem[wp]<={32'b0,{28'b0,clipped},
                    {{8{pcm[95]}},pcm[95:72]},{{8{pcm[71]}},pcm[71:48]},
                    {{8{pcm[47]}},pcm[47:24]},{{8{pcm[23]}},pcm[23:0]},sample_id};
                wp<=wp+1'b1;captured<=captured+1'b1;
                if(|clipped) clip_seen<=1;
                if(captured==TOTAL_SAMPLES-1) busy<=0;
            end
            if(busy && (&pcm_valid) && !space) begin
                overflow<=1;busy<=0;done<=0;
                if(drops!=16'hffff) drops<=drops+1'b1;
            end
            case({push,pop})
                2'b10:count<=count+1'b1;
                2'b01:count<=count-1'b1;
                default:count<=count;
            endcase
            if(m_axis_tvalid && m_axis_tready) begin
                beat<=beat+1'b1;
                if(beat==7) begin
                    rp<=rp+1'b1;sent<=sent+1'b1;
                    if(m_axis_tlast) packet_sample<=0;
                    else packet_sample<=packet_sample+1'b1;
                    if(sent==TOTAL_SAMPLES-1 && !overflow && !sync_error && !mismatch) done<=1;
                end
            end
        end
    end
endmodule
