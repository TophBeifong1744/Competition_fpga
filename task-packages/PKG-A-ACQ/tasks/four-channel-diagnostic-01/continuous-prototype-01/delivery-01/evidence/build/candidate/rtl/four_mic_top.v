`timescale 1ns/1ps
// C1 independent candidate. start is RUN LEVEL, bypass start_pulse in candidate BD.
// TOTAL_SAMPLES retained ONLY for BD parameter compatibility; no finite limit.
module four_mic_top #(
    parameter WARMUP_SAMPLES=4096, TOTAL_SAMPLES=32000,
    parameter SAMPLES_PER_PACKET=250, FIFO_LOG2=10
)(
    (* X_INTERFACE_PARAMETER="ASSOCIATED_BUSIF m_axis,ASSOCIATED_RESET aresetn,FREQ_HZ 61440000" *)
    input wire aclk,
    (* X_INTERFACE_PARAMETER="POLARITY ACTIVE_LOW" *) input wire aresetn,
    input wire start,
    input wire [3:0] pdm_data,
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 pdm_clk1 CLK" *)
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME pdm_clk1, FREQ_HZ 3072000" *) output wire pdm_clk1,
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 pdm_clk2 CLK" *)
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME pdm_clk2, FREQ_HZ 3072000" *) output wire pdm_clk2,
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 pdm_clk3 CLK" *)
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME pdm_clk3, FREQ_HZ 3072000" *) output wire pdm_clk3,
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 pdm_clk4 CLK" *)
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME pdm_clk4, FREQ_HZ 3072000" *) output wire pdm_clk4,
    output wire [31:0] status,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TDATA" *) output wire [31:0] m_axis_tdata,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TKEEP" *) output wire [3:0] m_axis_tkeep,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TVALID" *) output wire m_axis_tvalid,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TREADY" *) input wire m_axis_tready,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 m_axis TLAST" *) output wire m_axis_tlast
);
    // C adapter: one divider/state, four independent physical output buffers.
    // DATA1..4 -> pdm_data[0..3] -> mic0..3; never tie outputs on the PCB.
    reg pdm_clk;
    assign {pdm_clk4,pdm_clk3,pdm_clk2,pdm_clk1} = {4{pdm_clk}};
    reg [4:0] phase;
    (* ASYNC_REG="TRUE" *) reg [3:0] pdm_meta,pdm_sync;
    reg [31:0] warmup;
    reg [63:0] id;
    wire ready=(warmup>=WARMUP_SAMPLES);
    wire [3:0] pv,clip;
    wire [95:0] pcm;
    always @(posedge aclk) begin
        if(!aresetn) begin
            phase<=0;pdm_clk<=0;pdm_meta<=0;pdm_sync<=0;warmup<=0;id<=0;
        end else begin
            pdm_meta<=pdm_data;pdm_sync<=pdm_meta;
            if(phase==19) begin phase<=0;pdm_clk<=0;end
            else begin phase<=phase+1'b1;if(phase==9) pdm_clk<=1;end
            if(&pv) begin id<=id+1'b1;if(!ready) warmup<=warmup+1'b1;end
        end
    end
    genvar ch;
    generate for(ch=0;ch<4;ch=ch+1) begin: channels
        pdm_cic3 filter(aclk,aresetn,(phase==9),pdm_sync[ch],pv[ch],pcm[ch*24+:24],clip[ch]);
    end endgenerate
    pcm4_continuous_axis #(.SAMPLES_PER_PACKET(SAMPLES_PER_PACKET),.FIFO_LOG2(FIFO_LOG2)) capture(
        .clk(aclk),.rst_n(aresetn),.run(start),.ready(ready),.pcm_valid(pv),.pcm(pcm),
        .clipped(clip),.sample_id(id),.m_axis_tdata(m_axis_tdata),.m_axis_tkeep(m_axis_tkeep),
        .m_axis_tvalid(m_axis_tvalid),.m_axis_tlast(m_axis_tlast),.m_axis_tready(m_axis_tready),.status(status));
endmodule
