`timescale 1ns/1ps
// 公开兼容入口：同一PHAT控制器配独占原192位核，保持端口与完成沿。
module doa_phat_serial (
  input logic clk,cold_rst_n,cancel,start,
  output logic ready,done,
  input logic signed [50:0] in_real,in_imag,
  input logic [191:0] in_square,
  output logic [51:0] result,
  output logic busy
);
  logic alu_start,alu_ready,alu_done,alu_busy;
  logic [1:0] alu_op;
  logic signed [191:0] alu_a,alu_b,alu_result;
  logic signed [31:0] alu_shift;
  doa_phat_client client(.clk(clk),.cold_rst_n(cold_rst_n),.cancel(cancel),
    .start(start),.ready(ready),.done(done),.in_real(in_real),.in_imag(in_imag),
    .in_square(in_square),.result(result),.busy(busy),
    .alu_start(alu_start),.alu_ready(alu_ready),.alu_done(alu_done),.alu_op(alu_op),
    .alu_a(alu_a),.alu_b(alu_b),.alu_shift(alu_shift),.alu_result(alu_result));
  doa_math_serial math(.clk(clk),.cold_rst_n(cold_rst_n),.cancel(cancel),
    .start(alu_start),.ready(alu_ready),.operation(alu_op),.operand_a(alu_a),
    .operand_b(alu_b),.shift(alu_shift),.done(alu_done),.result(alu_result),.busy(alu_busy));
endmodule
