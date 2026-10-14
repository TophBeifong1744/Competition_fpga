`timescale 1ns/1ps
`default_nettype none
// 中文用途：上电保持引脚低；得到真实许可后只在 PWM 低相开门，不制造半截脉冲。
// STOP 不关闭已打开的门，保留原驱动“保持最后位置”语义；冷复位立即关闭。
module i17_pwm_gate (
    input wire clk, rst_n, permit_open, internal_pwm,
    output wire physical_pwm,
    output reg opened
);
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) opened<=1'b0;
        else if(permit_open && !internal_pwm) opened<=1'b1;
    end
    assign physical_pwm=internal_pwm && opened && rst_n;
endmodule
`default_nettype wire
