`timescale 1ns/1ps
// Derived from A ac0ff38 tb_fft.sv. Candidate width only; no active default edit.
module tb_fft29;
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
  ss_fft29 dut(.aclk(clk),.aresetn(rst),
    .s_axis_config_tdata(cfg),.s_axis_config_tvalid(cv),.s_axis_config_tready(cr),
    .s_axis_data_tdata(id),.s_axis_data_tvalid(iv),.s_axis_data_tready(ir),.s_axis_data_tlast(il),
    .m_axis_data_tdata(od),.m_axis_data_tuser(ou),.m_axis_data_tvalid(ov),.m_axis_data_tready(ordy),.m_axis_data_tlast(ol),
    .m_axis_status_tdata(status),.m_axis_status_tvalid(sv),.m_axis_status_tready(1'b1),
    .event_tlast_unexpected(unexpected),.event_tlast_missing(missing),.event_fft_overflow(overflow));
  reg [63:0] mem [0:836607]; // 817 jobs * 1024: remaining 136 cases + first-job repeat.
  integer cycle=0, job=0, received=0, first_in=0,last_in=0,first_out=0,last_out=0;
  integer datafile,timefile,statusfile,countfile,n,scount=0,config_cycle=0,njobs=0,dummy;
  reg held=0;
  reg [88:0] held_payload;
  always @(posedge clk) begin
    if (cycle>12000000) $fatal(1,"TIMEOUT");
    if (rst) begin
      if (unexpected || missing) $fatal(1,"TLAST input event failure");
      if (overflow) $fatal(1,"FFT overflow event");
      if (sv) begin
        $fdisplay(statusfile,"%0d,%0d,%0d",scount,cycle,status[0]);
        if (status[0] !== 1'b0) $fatal(1,"overflow/unknown status");
        scount=scount+1;
      end
      if (held && (!ov || {od,ou,ol} !== held_payload)) $fatal(1,"output changed under backpressure");
      held=ov && !ordy;
      held_payload={od,ou,ol};
      if (ov && ordy) begin
        if (received>=1024) $fatal(1,"extra output");
        if (ou[9:0] !== received[9:0]) $fatal(1,"index mismatch");
        if (ol !== (received==1023)) $fatal(1,"TLAST mismatch");
        if ((^od[28:0] === 1'bx) || (^od[60:32] === 1'bx)) $fatal(1,"unknown output");
        if (received==0) first_out=cycle;
        last_out=cycle;
        $fdisplay(datafile,"%0d,%0d,%0d,%0d",job,received,$signed(od[28:0]),$signed(od[60:32]));
        received=received+1;
      end
    end
  end
  always @(negedge clk) begin
    cycle=cycle+1;
    ordy=(job!=njobs-1 || cycle%7!=0);
  end
  initial begin
    countfile=$fopen("job-count.mem","r");
    if (!countfile) $fatal(1,"missing job-count.mem");
    dummy=$fscanf(countfile,"%d",njobs); $fclose(countfile);
    if (dummy!=1 || njobs!=817) $fatal(1,"wrong predeclared job count");
    $readmemh("inputs.mem",mem);
    datafile=$fopen("outputs.csv","w");
    timefile=$fopen("cycles.csv","w");
    statusfile=$fopen("status.csv","w");
    if (!datafile || !timefile || !statusfile) $fatal(1,"cannot open evidence files");
    repeat(10) @(negedge clk);
    rst=1;
    repeat(5) @(negedge clk);
    for(job=0;job<njobs;job=job+1) begin
      received=0;
      // Bit 0 forward; bits [20:1] ten two-bit shifts = 1 each.
      cfg=24'h0AAAAB;
      cv=1;
      @(posedge clk); while(!cr) @(posedge clk);
      config_cycle=cycle;
      @(negedge clk); cv=0;
      for(n=0;n<1024;n=n+1) begin
        if(job==njobs-1 && n%31==0) begin
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
      if (job%30==0) $display("PROGRESS job=%0d cycle=%0d",job,cycle);
      repeat(4) @(negedge clk);
    end
    $display("PASS FFT29 archive replay: %0d jobs; TLAST/index/status/backpressure checked",njobs);
    $fclose(datafile);$fclose(timefile);$fclose(statusfile);$finish;
  end
endmodule
