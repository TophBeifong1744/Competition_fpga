`timescale 1ns/1ps
`default_nettype none
// 中文用途：非VIO有限已知方向输入；表项完整身份由调用方冻结，不伪造声学结果或实际采样时间。
module i17_turntable_known_source #(
    parameter integer CONFIGURED = 0,
    parameter integer COUNT = 1,
    parameter integer SPACING_CYCLES = 0,
    parameter [COUNT*18-1:0] ANGLES_Q8 = 0,
    parameter [COUNT*725-1:0] IDENTITIES = 0
) (
    input wire clk, rst_n,
    input wire start_i, enable_i, stop_i, fault_i,
    output wire result_strobe_o,
    output wire signed [17:0] result_angle_q8_o,
    output wire [724:0] result_identity_o,
    output wire known_injection_o,
    output reg busy_o, done_o, cancelled_o,
    output reg [31:0] index_o
);
    reg start_q;
    reg start_armed_q;
    reg [31:0] wait_q;
    localparam integer LEGAL = CONFIGURED == 1 && COUNT >= 1 && COUNT <= 256 && SPACING_CYCLES >= 3;
    assign result_strobe_o = LEGAL && rst_n && busy_o && enable_i && !stop_i && !fault_i && wait_q == 0;
    assign result_angle_q8_o = LEGAL ? ANGLES_Q8[index_o*18 +: 18] : 18'sd0;
    assign result_identity_o = LEGAL ? IDENTITIES[index_o*725 +: 725] : 725'd0;
    assign known_injection_o = 1'b1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start_q <= 0; start_armed_q <= 0;
            busy_o <= 0; done_o <= 0; cancelled_o <= 0; index_o <= 0; wait_q <= 0;
        end else begin
            start_q <= start_i;
            if (!start_i) start_armed_q <= 1;
            if (busy_o) begin
                if (stop_i || fault_i || !enable_i) begin
                    busy_o <= 0; cancelled_o <= 1;
                end else if (result_strobe_o) begin
                    if (index_o == COUNT-1) begin busy_o <= 0; done_o <= 1; end
                    else begin index_o <= index_o + 1'b1; wait_q <= SPACING_CYCLES-1; end
                end else if (wait_q != 0) wait_q <= wait_q - 1'b1;
            end else if (LEGAL && start_armed_q && start_i && !start_q && enable_i && !stop_i && !fault_i) begin
                start_armed_q <= 0;
                busy_o <= 1; done_o <= 0; cancelled_o <= 0; index_o <= 0;
                // 启动后先留完整稳定/无strobe区间，供原runtime建立session/config并arm。
                wait_q <= SPACING_CYCLES-1;
            end
        end
    end
    // synthesis translate_off
    initial begin
        if (CONFIGURED && !LEGAL) $fatal(1,"Known source requires COUNT1..256 and explicit SPACING_CYCLES>=3");
    end
    // synthesis translate_on
endmodule
`default_nettype wire
