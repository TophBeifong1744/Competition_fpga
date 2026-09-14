`timescale 1ns/1ps
module tb_b_golden;
reg clk=0; always #5 clk=~clk;
reg rst=1,in_valid=0,out_ready=1;
reg signed [7:0] a=0,b=0;
wire in_ready,out_valid; wire signed [7:0] y;
sat_add dut(.*); integer ai,bi,count=0;
initial begin
 @(posedge clk); #1;
 for(ai=-128;ai<128;ai=ai+1) for(bi=-128;bi<128;bi=bi+1) begin
  @(negedge clk); rst=0;in_valid=1;a=ai;b=bi;
  @(posedge clk); if(in_ready!==1'b1) $fatal(1,"SKILL_FAIL ready");
  #1; if(out_valid!==1'b1 || (^y===1'bx)) $fatal(1,"SKILL_FAIL validity/XZ");
  $display("B_RESULT a=%0d b=%0d y=%02h",ai,bi,y); count=count+1;
 end
 $display("SKILL_PASS cases=1 checks=%0d",count);$finish;
end
initial begin #1000000;$fatal(1,"SKILL_FAIL watchdog");end
endmodule
