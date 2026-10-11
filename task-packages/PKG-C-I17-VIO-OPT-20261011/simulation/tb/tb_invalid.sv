`timescale 1ns/1ps
module tb_invalid #(parameter integer HZ=999999, MAX_A=360, RESET_A=180);
 reg clk=0;
 wire pwm;
 always #5 clk=~clk;
 motor_drive #(.CLK_FREQ_HZ(HZ),.MAX_ANGLE_DEG(MAX_A),.RESET_ANGLE_DEG(RESET_A))
   dut(clk,1'b0,9'd0,1'b0,pwm);
 initial begin #100; $display("INVALID_NOT_REJECTED"); $finish; end
endmodule
