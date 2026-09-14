`timescale 1ns/1ps
module tb_b_latency;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,in_valid=0,out_ready=1;reg [7:0] in_data=0;
wire in_ready,out_valid;wire [7:0] out_data;
elastic_stage #(.WIDTH(8)) dut(.*);
initial begin
 @(posedge clk);#1;
 @(negedge clk);rst_n=1;in_valid=1;in_data=8'h5a;
 @(posedge clk);if(in_ready!==1'b1)$fatal(1,"SKILL_FAIL empty ready");
 #1;$display("B_LATENCY first_accept_post_edge valid=%b data=%h expected_valid=1 expected_data=5a",out_valid,out_data);
 if(out_valid!==1'b1 || out_data!==8'h5a)$fatal(1,"SKILL_FAIL one-edge latency");
 $display("SKILL_PASS cases=1 checks=2");$finish;
end
initial begin #1000;$fatal(1,"SKILL_FAIL watchdog");end
endmodule
