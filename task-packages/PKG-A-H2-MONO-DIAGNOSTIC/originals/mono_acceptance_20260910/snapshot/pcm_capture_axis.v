`timescale 1ns/1ps
// 4 AXIS words per mono sample: id_lo, id_hi, sign-extended PCM24, flags.
// Flags bit1=output saturation. FIFO overflow aborts acquisition, sticky status.
// IDs count filtered samples since frontend reset, including warmup/idle samples.
module pcm_capture_axis #(
 parameter TOTAL_SAMPLES=48000, parameter SAMPLES_PER_PACKET=250,
 parameter FIFO_LOG2=10
)(input wire clk,input wire rst_n,input wire start,input wire ready,
 input wire pcm_valid,input wire signed [23:0] pcm,input wire clipped,
 input wire [63:0] sample_id,
 output wire [31:0] m_axis_tdata,output wire [3:0] m_axis_tkeep,
 output wire m_axis_tvalid,input wire m_axis_tready,output wire m_axis_tlast,
 output wire [31:0] status);
 localparam DEPTH=1<<FIFO_LOG2;
 reg [127:0] mem[0:DEPTH-1];
 reg [FIFO_LOG2-1:0] wp,rp;
 reg [FIFO_LOG2:0] count;
 reg [1:0] beat;
 reg [31:0] captured,sent;
 reg [15:0] packet_sample;
 reg busy,overflow,done,clip_seen;
 reg [15:0] drops;
 wire pop=m_axis_tvalid && m_axis_tready && beat==3;
 wire space=(count<DEPTH)||pop;
 wire push=busy && pcm_valid && space;
 wire accept_start=start && ready && !busy && count==0 && !overflow;
 wire [127:0] head=mem[rp];
 assign m_axis_tdata=head >> (beat*32);
 assign m_axis_tkeep=4'hf;
 assign m_axis_tvalid=(count!=0);
 assign m_axis_tlast=m_axis_tvalid && beat==3 &&
       ((packet_sample==SAMPLES_PER_PACKET-1)||(sent==TOTAL_SAMPLES-1));
 assign status={drops,11'b0,clip_seen,done,overflow,ready,busy};
 always @(posedge clk) begin
  if(!rst_n) begin
   wp<=0;rp<=0;count<=0;beat<=0;captured<=0;sent<=0;
   packet_sample<=0;busy<=0;overflow<=0;done<=0;clip_seen<=0;drops<=0;
  end else begin
   if(accept_start) begin
    busy<=1;done<=0;clip_seen<=0;captured<=0;sent<=0;packet_sample<=0;
   end
   if(push) begin
    mem[wp]<={{30'b0,clipped,1'b0},{{8{pcm[23]}},pcm},sample_id};
    wp<=wp+1'b1;captured<=captured+1'b1;
    if(clipped) clip_seen<=1;
    if(captured==TOTAL_SAMPLES-1) busy<=0;
   end
   if(busy && pcm_valid && !space) begin
    overflow<=1;busy<=0;
    if(drops!=16'hffff) drops<=drops+1'b1;
   end
   case({push,pop})
    2'b10:count<=count+1'b1;
    2'b01:count<=count-1'b1;
    default:count<=count;
   endcase
   if(m_axis_tvalid && m_axis_tready) begin
    beat<=beat+1'b1;
    if(beat==3) begin
     rp<=rp+1'b1;sent<=sent+1'b1;
     if(m_axis_tlast) packet_sample<=0;
     else packet_sample<=packet_sample+1'b1;
     if(sent==TOTAL_SAMPLES-1) done<=1;
    end
   end
  end
 end
endmodule
