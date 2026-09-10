`timescale 1ns/1ps
// Pure Verilog Module Reference top. ALL connected AXI peripherals must use
// the same 61.44 MHz clock/reset. Do not connect directly to a 100 MHz DMA.
// LR=0: mic drives DATA after falling CLOCK. Local physical sample at phase7,
// approx130.2ns after falling edge, 32.6ns before rising edge. Board timing pending.
module single_mic_top #(
 parameter WARMUP_SAMPLES=4096, parameter TOTAL_SAMPLES=48000
)(
 (* X_INTERFACE_PARAMETER="ASSOCIATED_BUSIF m_axis,ASSOCIATED_RESET aresetn,FREQ_HZ 61440000" *)
 input wire aclk,
 (* X_INTERFACE_PARAMETER="POLARITY ACTIVE_LOW" *) input wire aresetn,
 input wire start,
 input wire pdm_data,

 (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 pdm_clk CLK" *)
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME pdm_clk, FREQ_HZ 3072000" *)
 output reg pdm_clk,
 output wire [31:0] status,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TDATA" *) output wire [31:0] m_axis_tdata,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TKEEP" *) output wire [3:0] m_axis_tkeep,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TVALID" *) output wire m_axis_tvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TREADY" *) input wire m_axis_tready,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TLAST" *) output wire m_axis_tlast
);
 reg [4:0] phase;
 (* ASYNC_REG="TRUE" *) reg pdm_meta,pdm_sync;
 reg [31:0] warmup;
 reg [63:0] id;
 wire ready=(warmup>=WARMUP_SAMPLES);
 wire pv,clip;
 wire signed [23:0] pcm;
 // Continuous pin synchronizer. At phase9, pdm_sync represents phase7.
 always @(posedge aclk) begin
  if(!aresetn) begin
   phase<=0;pdm_clk<=0;pdm_meta<=0;pdm_sync<=0;warmup<=0;id<=0;
  end else begin
   pdm_meta<=pdm_data;pdm_sync<=pdm_meta;
   if(phase==19) begin phase<=0;pdm_clk<=0;end
   else begin phase<=phase+1'b1;if(phase==9) pdm_clk<=1;end
   if(pv) begin id<=id+1'b1;if(!ready) warmup<=warmup+1'b1;end
  end
 end
 pdm_cic3 filter(aclk,aresetn,(phase==9),pdm_sync,pv,pcm,clip);
 pcm_capture_axis #(.TOTAL_SAMPLES(TOTAL_SAMPLES)) capture(
  aclk,aresetn,start,ready,pv,pcm,clip,id,
  m_axis_tdata,m_axis_tkeep,m_axis_tvalid,m_axis_tready,m_axis_tlast,status);
endmodule
