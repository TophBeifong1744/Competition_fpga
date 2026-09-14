`timescale 1ns/1ps
module tb_sat_add;
reg clk=0;
always #5 clk=~clk;
reg rst=0, in_valid=0, out_ready=0;
reg signed [7:0] a=0,b=0;
wire in_ready,out_valid;
wire signed [7:0] y;
sat_add dut(.*);
integer cycles=0,checks=0,cases=0,accepted=0,consumed=0,discarded=0;
integer pending=0, expected=0, expected_id=0;
integer av,bv,total,ready_expected;
integer stalls=0,replaces=0,reset_pending=0,fullrate=0;
integer i,j,k,hold_a,hold_b,offering;
reg [31:0] rng=32'h57124abc;
function automatic integer golden(input integer x,input integer z);
integer s;
begin s=x+z; if(s>127) golden=127; else if(s< -128) golden=-128; else golden=s; end
endfunction
task automatic fail(input string msg);
begin $display("SKILL_FAIL cycle=%0d id=%0d expected=%0d actual=%0d bits=%b pending=%0d a=%0d b=%0d: %s",cycles,expected_id,expected,$signed(y),y,pending,$signed(a),$signed(b),msg); $fatal(1,"first mismatch"); end
endtask
task automatic step(input reg r,input reg v,input reg [7:0] aa,input reg [7:0] bb,input reg ready);
begin
 @(negedge clk); rst=r; in_valid=v; a=aa; b=bb; out_ready=ready;
 @(posedge clk); cycles=cycles+1;
 if(cycles>1) begin
  checks=checks+1; if(out_valid !== (pending!=0)) fail("registered validity/latency");
  ready_expected=(pending==0)||ready;
  checks=checks+1; if(in_ready !== (ready_expected!=0)) fail("ready/throughput");
  if(pending!=0) begin checks=checks+1; if(y !== expected[7:0]) fail("payload or hold"); end
 end
 if(r) begin
  if(pending!=0) begin discarded=discarded+1; reset_pending=reset_pending+1; end
  pending=0;
 end else begin
  if(pending!=0 && !ready) stalls=stalls+1;
  if(pending!=0 && ready && v) replaces=replaces+1;
  if(pending!=0 && ready) begin consumed=consumed+1; pending=0; end
  if(v && in_ready) begin
   if((^aa === 1'bx)||(^bb === 1'bx)) fail("unsupported accepted X/Z input");
   av=$signed(aa); bv=$signed(bb); expected=golden(av,bv);
   accepted=accepted+1; expected_id=accepted; pending=1; cases=cases+1;
  end
 end
 #1;
 checks=checks+1; if(out_valid !== (pending!=0)) fail("post-edge validity/one-cycle latency");
 if(r) begin checks=checks+1; if(y !== 8'h00) fail("reset payload"); end
 else if(pending!=0) begin checks=checks+1; if(y !== expected[7:0]) fail("post-edge numeric/hold"); end
end
endtask
initial begin
 step(1,1,8'hxx,8'hzz,1);
 step(0,0,8'hxx,8'hzz,0);
 // First nontrivial negative overflow; must saturate exactly to -128.
 step(0,1,-128,-1,1);
 step(0,1,-128,0,1);
 step(0,1,127,1,1);
 step(0,1,127,-128,1);
 step(0,0,8'hzz,8'hxx,1);
 // Exhaust all signed operand pairs at full rate, including clipping thresholds.
 for(i=-128;i<=127;i=i+1) for(j=-128;j<=127;j=j+1) begin
  step(0,1,i,j,1); fullrate=fullrate+1;
 end
 step(0,0,0,0,1);
 step(0,1,30,40,0); // empty slot accepts against downstream stall
 for(k=0;k<32;k=k+1) step(0,1,-80,20,0);
 step(0,1,-80,20,1); // accept held producer while consuming old output
 step(1,1,8'hxx,8'hzz,0); // drop pending, reset beats stalled input
 step(0,1,12,13,1);
 step(1,1,8'hzz,8'hxx,1); // reset beats simultaneous input and output
 step(1,0,0,0,0);
 // Fixed LCG traffic, with legal stable offers through stalls.
 offering=0; hold_a=0; hold_b=0;
 for(k=0;k<2048;k=k+1) begin
  rng=rng*32'd1664525+32'd1013904223;
  if(!offering) begin offering=rng[3]; hold_a=rng[15:8]; hold_b=rng[23:16]; end
  step(0,offering,hold_a,hold_b,rng[29]);
  if(offering && ready_expected) offering=0;
 end
 if(offering) step(0,1,hold_a,hold_b,1);
 step(0,0,8'hxx,8'hzz,1);
 step(0,0,8'hzz,8'hxx,1);
 checks=checks+5;
 if(pending!=0 || out_valid!==0) fail("undrained");
 if(accepted!=consumed+discarded) fail("transaction accounting");
 if(fullrate!=65536 || replaces<65535) fail("full-rate coverage");
 if(stalls<32 || reset_pending!=2) fail("stall/reset coverage");
 if(checks<300000 || cases<65536) fail("insufficient coverage");
 $display("COVER accepted=%0d consumed=%0d discarded=%0d stalls=%0d replaces=%0d fullrate=%0d seed=57124abc",accepted,consumed,discarded,stalls,replaces,fullrate);
 $display("SKILL_PASS cases=%0d checks=%0d",cases,checks);
 $finish;
end
initial begin #1000000; fail("watchdog"); end
endmodule
