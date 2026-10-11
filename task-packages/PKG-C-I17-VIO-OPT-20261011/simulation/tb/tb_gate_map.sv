`timescale 1ns/1ps
module tb_gate_map;
 reg clk=0,rst_n=0,permit_open=0,internal_pwm=1;always #5 clk=~clk;
 wire physical_pwm,opened;i17_pwm_gate dut(.*);
 reg config_valid=1;reg signed [17:0] angle_q8=0,domain_min_q8=-46080,domain_max_q8=46079;
 reg signed [23:0] offset_q8=46080;reg signed [1:0] direction=1;
 reg [8:0] mechanical_min=0,mechanical_max=360,servo_max=360;
 wire config_legal,valid;wire [8:0] angle_deg;
 signed_angle_map map_dut(.*);
 integer checks=0,a,sgn,mapped,rounded,fraction;bit good;
 reg observed_gate;
 task step;begin @(posedge clk);#2;end endtask
 task check(input bit ok,input string why);begin checks++;if(!ok)$fatal(1,"GATE_MAP_CHECK %s",why);end endtask
 initial begin
  step;check(!physical_pwm&&!opened,"cold reset off");rst_n=1;
  repeat(4)begin step;check(!physical_pwm&&!opened,"observe internal high isolated");end
  permit_open=1;step;observed_gate=physical_pwm;
  // Isolated observation fault: test the real no-mid-high-opening checker.
  if($test$plusargs("CANARY_GATE"))observed_gate=~observed_gate;
  check(!observed_gate&&!opened,"no opening mid high pulse");
  internal_pwm=0;step;check(opened&&!physical_pwm,"open only low phase");
  internal_pwm=1;#1;check(physical_pwm,"next full high is passed");
  permit_open=0;step;check(opened&&physical_pwm,"STOP holds already-open gate");
  @(negedge clk);#2;rst_n=0;#1;check(!physical_pwm&&!opened,"async cold reset closes gate");
  rst_n=1;step;check(!physical_pwm&&!opened,"new observation defaults off");
  // Signed arithmetic oracle: integer quotient/remainder, nearest ties-even.
  for(sgn=-1;sgn<=1;sgn=sgn+2)begin
   direction=sgn;
   for(a=-46100;a<=46100;a=a+127)begin
    angle_q8=a;#1;mapped=46080+sgn*a;rounded=mapped/256;fraction=mapped%256;
    if(fraction>128 || (fraction==128 && rounded%2!=0))rounded++;
    good=(a>=-46080&&a<=46079&&mapped>=0&&mapped<=92160);
    check(config_legal&&valid==good,"signed map domain validity");
    if(good)check(angle_deg==rounded,"signed map arithmetic");
   end
  end
  direction=1;angle_q8=128;#1;check(valid&&angle_deg==180,"tie even down");
  angle_q8=384;#1;check(valid&&angle_deg==182,"tie odd up");
  domain_max_q8=46080;#1;check(!config_legal&&!valid,"+180 domain illegal");
  domain_max_q8=46079;direction=0;#1;check(!config_legal,"direction zero illegal");
  direction=1;mechanical_min=200;mechanical_max=100;#1;check(!config_legal,"reversed mechanical limits");
  $display("GATE_MAP_COMPLETE checks=%0d pending=0",checks);$finish;
 end
endmodule
