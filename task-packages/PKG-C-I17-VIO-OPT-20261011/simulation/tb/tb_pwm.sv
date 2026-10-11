`timescale 1ns/1ps
// Independent edge-indexed requirements model; no DUT internal state is used.
module pwm_case #(parameter integer HZ=61440000, MAX_A=360, RESET_A=180, ID=0)
 (output reg done=0);
 localparam longint PERIOD=(64'd20000*HZ)/1000000;
 reg clk=0, rst=0, valid=1;
 reg [8:0] angle=511;
 wire pwm, old_pwm;
 always #5 if(!done) clk=~clk;
 motor_drive #(.CLK_FREQ_HZ(HZ),.MAX_ANGLE_DEG(MAX_A),.RESET_ANGLE_DEG(RESET_A))
   dut(clk,rst,angle,valid,pwm);
 generate if(HZ%1000000==0) begin: miter
   motor_drive_frozen #(.CLK_FREQ_HZ(HZ),.MAX_ANGLE_DEG(MAX_A),.RESET_ANGLE_DEG(RESET_A))
     original(clk,rst,angle,valid,old_pwm);
 end else begin assign old_pwm=0; end endgenerate

 longint cycle=0, age=-1, width_cycles=0;
 integer pending=RESET_A, width_us=0, fd, rises=0, falls=0;
 integer cov500=0,cov1500=0,cov2500=0,covfraction=0;
 reg expected=0, last=0, observed;
 integer canary_model,canary_miter,canary_reset;
 function automatic integer pulse_us(input integer a);
   integer bounded;
   begin bounded=(a>MAX_A)?MAX_A:a;
     pulse_us=500+(bounded*2000+MAX_A/2)/MAX_A;
   end
 endfunction
 function automatic longint ceil_cycles(input integer us);
   ceil_cycles=(64'(us)*HZ+999999)/1000000;
 endfunction
 initial begin
   canary_model=$test$plusargs("CANARY_MODEL");
   canary_miter=$test$plusargs("CANARY_MITER");
   canary_reset=$test$plusargs("CANARY_RESET");
   fd=$fopen($sformatf("edges_%0d.csv",ID),"w");
   if(!fd) $fatal(1,"TESTBENCH_FAIL: cannot create edge log");
   $fdisplay(fd,"case,cycle,age,event,width_us,expected,observed");
 end
 always @(posedge clk) begin
   cycle=cycle+1;
   if(!rst) begin age=-1; pending=RESET_A; expected=0; end
   else begin
     age=age+1;
     if(age%PERIOD==0) begin
       width_us=pulse_us(pending);
       width_cycles=ceil_cycles(width_us);
       if(width_us==500) cov500=cov500+1;
       if(width_us==1500) cov1500=cov1500+1;
       if(width_us==2500) cov2500=cov2500+1;
       if((64'(width_us)*HZ)%1000000!=0) covfraction=covfraction+1;
     end
     expected=((age%PERIOD)<width_cycles);
     // The edge samples the old command for a boundary; same-edge valid is later.
     if(valid) begin
       pending=angle;
       $fdisplay(fd,"%0d,%0d,%0d,accept_%0d,%0d,%0b,%0b",ID,cycle,age,angle,width_us,expected,pwm);
     end
   end
   #1; // race-free post-NBA observation
   observed=pwm;
   if(canary_model && ID==0 && cycle==10) observed=~observed;
   if(observed!==expected) begin
     $display("PWM_CHECK_FAIL case=%0d cycle=%0d age=%0d expected=%b observed=%b width_us=%0d",ID,cycle,age,expected,observed,width_us);
     $fatal(1,"ASSERTION_FAIL PWM_CHECK");
   end
   if(HZ%1000000==0) begin
     observed=old_pwm;
     if(canary_miter && ID==0 && cycle==10) observed=~observed;
     if(pwm!==observed) $fatal(1,"ASSERTION_FAIL MITER_CHECK case=%0d cycle=%0d",ID,cycle);
   end
   if(pwm!==last) begin
     $fdisplay(fd,"%0d,%0d,%0d,edge,%0d,%0b,%0b",ID,cycle,age,width_us,expected,pwm);
     if(pwm) rises=rises+1; else falls=falls+1;
   end
   last=pwm;
 end
 task automatic async_reset(input integer phase);
   begin
     @(negedge clk); #2;
     if(pwm!==phase[0]) $fatal(1,"TESTBENCH_FAIL reset stimulus phase=%0d actual=%b",phase,pwm);
     rst=0; valid=1; angle=511;
     #1;
     observed=pwm;
     if(canary_reset && ID==0) observed=1;
     if(observed!==0) $fatal(1,"ASSERTION_FAIL ASYNC_RESET_CHECK case=%0d",ID);
     $fdisplay(fd,"%0d,%0d,%0d,async_reset_from_%0d,0,0,%0b",ID,cycle,age,phase,pwm);
     repeat(3) @(negedge clk);
     rst=1; valid=0;
   end
 endtask
 longint i;
 initial begin
   repeat(3) @(negedge clk);
   rst=1;
   for(i=0;i<8*PERIOD+100;i=i+1) begin
     valid=0; angle=511;
     if(i==0) begin valid=1;angle=MAX_A;end
     if(i==PERIOD) begin valid=1;angle=0;end
     if(i==PERIOD+5) begin valid=1;angle=1;end
     if(i==2*PERIOD) begin valid=1;angle=MAX_A;end
     if(i==3*PERIOD+100) begin valid=1;angle=0;end
     if(i==4*PERIOD+100) begin valid=1;angle=MAX_A;end
     if(i==5*PERIOD-1) begin valid=1;angle=MAX_A/2;end
     if(i==5*PERIOD) begin valid=1;angle=0;end
     // Deterministic seed 17010: sustained valid, latest wins, includes >MAX.
     if(i>=6*PERIOD+100 && i<6*PERIOD+200) begin valid=1;angle=(i*73+17010)%512;end
     @(negedge clk);
   end
   async_reset(1);
   repeat(ceil_cycles(3000)) @(negedge clk);
   async_reset(0);
   repeat(ceil_cycles(2600)) @(negedge clk);
   if(cov500==0 || cov2500==0 || (MAX_A==360 && cov1500==0))
     $fatal(1,"TESTBENCH_FAIL coverage widths case=%0d",ID);
   if(HZ==61440000 && MAX_A==360 && covfraction==0)
     $fatal(1,"TESTBENCH_FAIL fractional width not covered");
   $display("CASE_COMPLETE id=%0d HZ=%0d MAX=%0d cycles=%0d rises=%0d falls=%0d width500=%0d width1500=%0d width2500=%0d fractional=%0d",ID,HZ,MAX_A,cycle,rises,falls,cov500,cov1500,cov2500,covfraction);
   $fclose(fd); done=1;
 end
endmodule
module tb_pwm;
 wire [5:0] done;
 pwm_case #(.HZ(1000000),.ID(0)) a(done[0]);
 pwm_case #(.HZ(50000000),.ID(1)) b(done[1]);
 pwm_case #(.HZ(100000000),.ID(2)) c(done[2]);
 pwm_case #(.HZ(61440000),.ID(3)) d(done[3]);
 pwm_case #(.HZ(1000000),.MAX_A(1),.RESET_A(0),.ID(4)) e(done[4]);
 pwm_case #(.HZ(1000000),.MAX_A(511),.RESET_A(511),.ID(5)) f(done[5]);
 initial begin wait(&done); $display("ALL_CHECKERS_COMPLETE seed=17010 pending=0"); $finish; end
 initial begin #200000000; $fatal(1,"TIMEOUT_HANG"); end
endmodule
