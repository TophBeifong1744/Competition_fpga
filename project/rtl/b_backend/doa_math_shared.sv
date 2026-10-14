`timescale 1ns/1ps
// 两个私有client共享原192位核；接受沿记owner，响应无额外寄存级。
module doa_math_shared (
  input logic clk,cold_rst_n,cancel,
  input logic phat_start,
  output logic phat_ready,
  input logic [1:0] phat_operation,
  input logic signed [191:0] phat_operand_a,phat_operand_b,
  input logic signed [31:0] phat_shift,
  output logic phat_done,
  output logic signed [191:0] phat_result,
  input logic backend_start,
  output logic backend_ready,
  input logic [1:0] backend_operation,
  input logic signed [191:0] backend_operand_a,backend_operand_b,
  input logic signed [31:0] backend_shift,
  output logic backend_done,
  output logic signed [191:0] backend_result,
  output logic backend_busy
);
  logic owner_valid,owner_backend;
  logic core_start,core_ready,core_done,core_busy;
  logic accept_phat,accept_backend;
  logic [1:0] core_operation;
  logic signed [191:0] core_a,core_b,core_result;
  logic signed [31:0] core_shift;
  // 合法后端调用互斥；同时请求时PHAT固定优先，无排队或抢占。
  assign phat_ready=core_ready && cold_rst_n && !cancel;
  assign backend_ready=core_ready && !phat_start && cold_rst_n && !cancel;
  assign accept_phat=phat_start && phat_ready;
  assign accept_backend=backend_start && backend_ready;
  assign core_start=accept_phat || accept_backend;
  assign core_operation=accept_phat ? phat_operation : backend_operation;
  assign core_a=accept_phat ? phat_operand_a : backend_operand_a;
  assign core_b=accept_phat ? phat_operand_b : backend_operand_b;
  assign core_shift=accept_phat ? phat_shift : backend_shift;
  // 旧done仍按旧owner组合路由；下一沿可同时消费旧响应并接受新请求。
  assign phat_done=core_done && owner_valid && !owner_backend && cold_rst_n && !cancel;
  assign backend_done=core_done && owner_valid && owner_backend && cold_rst_n && !cancel;
  assign phat_result=owner_valid && !owner_backend ? core_result : 192'sd0;
  assign backend_result=owner_valid && owner_backend ? core_result : 192'sd0;
  assign backend_busy=core_busy && owner_valid && owner_backend;
  doa_math_serial math(.clk(clk),.cold_rst_n(cold_rst_n),.cancel(cancel),
    .start(core_start),.ready(core_ready),.operation(core_operation),.operand_a(core_a),
    .operand_b(core_b),.shift(core_shift),.done(core_done),.result(core_result),.busy(core_busy));
  always_ff @(posedge clk) begin
    // 取消/冷复位优先；新接受优先于旧done清owner，避免复用多等一拍。
    if(!cold_rst_n || cancel) begin owner_valid<=0;owner_backend<=0;end
    else if(core_start && core_ready) begin
      owner_valid<=1;owner_backend<=accept_backend;
    end else if(core_done) begin owner_valid<=0;owner_backend<=0;end
  end
endmodule
