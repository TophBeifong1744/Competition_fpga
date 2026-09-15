`timescale 1ns/1ps
// Candidate only. RUN rising edge starts; RUN low requests a full-packet stop.
// Frontend keeps sampling while stopped. IDs are never rewritten here.
module pcm4_continuous_axis #(
    parameter SAMPLES_PER_PACKET=250, FIFO_LOG2=10
)(
    input wire clk, rst_n, run, ready,
    input wire [3:0] pcm_valid,
    input wire [95:0] pcm,
    input wire [3:0] clipped,
    input wire [63:0] sample_id,
    output wire [31:0] m_axis_tdata,
    output wire [3:0] m_axis_tkeep,
    output wire m_axis_tvalid, m_axis_tlast,
    input wire m_axis_tready,
    output wire [31:0] status
);
    localparam DEPTH=1<<FIFO_LOG2;
    reg [255:0] mem [0:DEPTH-1];
    reg [FIFO_LOG2-1:0] wp,rp;
    reg [FIFO_LOG2:0] count,packets;
    reg [2:0] beat;
    reg [31:0] in_packet,out_packet;
    reg busy,stop_pending,run_d,overflow,sync_error,clip_seen;
    reg [15:0] rejected;
    wire mismatch=(|pcm_valid) && !(&pcm_valid);
    wire fatal=overflow || sync_error;
    wire stop_now=stop_pending || !run;
    wire fire=m_axis_tvalid && m_axis_tready;
    wire pop=fire && beat==7;
    wire space=count<DEPTH || pop;
    // At an empty packet boundary stop before accepting another group.
    wire want=busy && (&pcm_valid) && !(stop_now && in_packet==0) && !fatal && !mismatch;
    wire push=want && space;
    wire packet_in=push && in_packet==SAMPLES_PER_PACKET-1;
    wire packet_out=fire && m_axis_tlast;
    wire accept_start=run && !run_d && ready && !busy && count==0 && !fatal && !mismatch;
    wire drained=!busy && count==0 && !fatal;
    wire [255:0] head=mem[rp];
    assign m_axis_tdata=head >> (beat*32);
    assign m_axis_tkeep=4'hf;
    assign m_axis_tvalid=count!=0;
    assign m_axis_tlast=m_axis_tvalid && beat==7 && out_packet==SAMPLES_PER_PACKET-1;
    // C1 ABI signature; rejected count is sticky/saturating across clean restarts.
    // [7] stopping, [6] >=1 complete packet queued, [5] sync, [4] clip-ever,
    // [3] drained, [2] overflow, [1] warm, [0] accepting samples.
    assign status={8'hc1,rejected,stop_pending,(packets!=0),sync_error,clip_seen,drained,overflow,ready,busy};
    always @(posedge clk) begin
        if(!rst_n) begin
            wp<=0;rp<=0;count<=0;packets<=0;beat<=0;in_packet<=0;out_packet<=0;
            busy<=0;stop_pending<=0;run_d<=0;overflow<=0;sync_error<=0;clip_seen<=0;rejected<=0;
        end else begin
            run_d<=run;
            if(accept_start) begin busy<=1;stop_pending<=0;end
            if(busy && !run) stop_pending<=1;
            if(busy && stop_now && (in_packet==0 || packet_in)) busy<=0;
            if(drained) stop_pending<=0;
            if(mismatch) begin sync_error<=1;busy<=0;end
            if(want && !space) begin
                overflow<=1;busy<=0;
                if(rejected!=16'hffff) rejected<=rejected+1'b1;
            end
            if(push) begin
                mem[wp]<={32'b0,{28'b0,clipped},
                    {{8{pcm[95]}},pcm[95:72]},{{8{pcm[71]}},pcm[71:48]},
                    {{8{pcm[47]}},pcm[47:24]},{{8{pcm[23]}},pcm[23:0]},sample_id};
                wp<=wp+1'b1;
                in_packet<=packet_in ? 0 : in_packet+1'b1;
                if(|clipped) clip_seen<=1;
            end
            case({push,pop})
                2'b10:count<=count+1'b1;
                2'b01:count<=count-1'b1;
                default:count<=count;
            endcase
            case({packet_in,packet_out})
                2'b10:packets<=packets+1'b1;
                2'b01:packets<=packets-1'b1;
                default:packets<=packets;
            endcase
            if(fire) begin
                beat<=beat+1'b1;
                if(pop) begin
                    rp<=rp+1'b1;
                    out_packet<=packet_out ? 0 : out_packet+1'b1;
                end
            end
        end
    end
endmodule
