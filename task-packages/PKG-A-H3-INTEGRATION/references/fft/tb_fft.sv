`timescale 1ns/1ps
module tb_fft;
  reg clk=0, rst=0;
  always #5 clk=~clk;
  reg [23:0] cfg=0;
  reg cv=0, iv=0, il=0, ordy=1;
  wire cr, ir, ov, ol;
  reg [63:0] id=0;
  wire [63:0] od;
  wire [23:0] ou;
  wire [7:0] status;
  wire sv, unexpected, missing, overflow;
  ss_fft dut(.aclk(clk),.aresetn(rst),
    .s_axis_config_tdata(cfg),.s_axis_config_tvalid(cv),.s_axis_config_tready(cr),
    .s_axis_data_tdata(id),.s_axis_data_tvalid(iv),.s_axis_data_tready(ir),.s_axis_data_tlast(il),
    .m_axis_data_tdata(od),.m_axis_data_tuser(ou),.m_axis_data_tvalid(ov),.m_axis_data_tready(ordy),.m_axis_data_tlast(ol),
    .m_axis_status_tdata(status),.m_axis_status_tvalid(sv),.m_axis_status_tready(1'b1),
    .event_tlast_unexpected(unexpected),.event_tlast_missing(missing),.event_fft_overflow(overflow));
  reg [63:0] mem [0:22527];
  integer cycle=0, job=0, received=0, first_in=0,last_in=0,first_out=0,last_out=0;
  integer datafile,timefile,n,scount=0,config_cycle=0;
  reg held=0;
  reg [88:0] held_payload;
  always @(posedge clk) begin
    if (cycle>1000000) $fatal(1,"TIMEOUT");
    if (rst) begin
      if (unexpected || missing || overflow) $fatal(1,"FFT event failure");
      if (sv) begin
        if (status[0]) $fatal(1,"overflow status");
        scount=scount+1;
      end
      if (held && (!ov || {od,ou,ol} !== held_payload)) $fatal(1,"output changed under backpressure");
      held=ov && !ordy;
      held_payload={od,ou,ol};
      if (ov && ordy) begin
        if (ou[9:0] !== received[9:0]) $fatal(1,"index mismatch");
        if (ol !== (received==1023)) $fatal(1,"TLAST mismatch");
        if (received==0) first_out=cycle;
        last_out=cycle;
        $fdisplay(datafile,"%0d,%0d,%0d,%0d",job,received,$signed(od[24:0]),$signed(od[56:32]));
        received=received+1;
      end
    end
  end
  always @(negedge clk) begin
    cycle=cycle+1;
    ordy=(job!=21 || cycle%7!=0);
  end
  initial begin
    $readmemh("inputs.mem",mem);
    datafile=$fopen("outputs.csv","w");
    timefile=$fopen("cycles.csv","w");
    repeat(10) @(negedge clk);
    rst=1;
    repeat(5) @(negedge clk);
    for(job=0;job<22;job=job+1) begin
      received=0;
      // Bit 0 direction; bits [20:1] ten two-bit shifts = 1 each.
      cfg=24'h0AAAAA | (job<6 ? 24'h1 : 24'h0);
      cv=1;
      @(posedge clk); while(!cr) @(posedge clk);
      config_cycle=cycle;
      @(negedge clk); cv=0;
      for(n=0;n<1024;n=n+1) begin
        if(job==21 && n%31==0) begin
          iv=0; repeat(2) @(negedge clk);
        end
        id=mem[job*1024+n];iv=1;il=(n==1023);
        @(posedge clk); while(!ir) @(posedge clk);
        if(n==0) first_in=cycle;
        last_in=cycle;
        @(negedge clk);
      end
      iv=0;il=0;
      wait(received==1024);
      @(negedge clk);
      wait(scount==job+1);
      $fdisplay(timefile,"%0d,%0d,%0d,%0d,%0d,%0d",job,config_cycle,first_in,last_in,first_out,last_out);
      repeat(4) @(negedge clk);
    end
    $display("PASS FFT probe: 22 jobs, 22528 outputs, TLAST/index/status/backpressure checked");
    $fclose(datafile);$fclose(timefile);$finish;
  end
endmodule
