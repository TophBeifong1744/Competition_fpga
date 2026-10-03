`timescale 1ns / 1ps
// 独立双轴定角测试入口；配套 motor_drive 接口 v2。
// 参数为目标角，先按机械范围限幅，再转换为 9 位无符号输入。
// 配置后等待 16 拍同步释放内部复位；没有外部复位或动态命令端口。
module servo_dual_test_top #(
    parameter integer CLK_FREQ_HZ = 50_000_000,
    parameter integer HORIZONTAL_DEG = 180,
    parameter integer VERTICAL_DEG = 130
)(
    input  wire sys_clk,
    output wire pwm_horizontal,
    output wire pwm_vertical
);
    localparam integer H_LIMITED = (HORIZONTAL_DEG < 0) ? 0 :
                                  (HORIZONTAL_DEG > 360) ? 360 : HORIZONTAL_DEG;
    localparam integer V_LIMITED = (VERTICAL_DEG < 40) ? 40 :
                                  (VERTICAL_DEG > 220) ? 220 : VERTICAL_DEG;
    localparam [8:0] H_ANGLE = H_LIMITED;
    localparam [8:0] V_ANGLE = V_LIMITED;

    // FPGA 配置初始化值；只支持配置启动，非运行中复位接口。
    reg [15:0] startup = 16'd0;
    reg command_sent = 1'b0;
    wire rst_n = startup[15];
    wire command_valid = rst_n && !command_sent;

    always @(posedge sys_clk)
        startup <= {startup[14:0], 1'b1};

    always @(posedge sys_clk) begin
        if (!rst_n)
            command_sent <= 1'b0;
        else
            command_sent <= 1'b1;
    end

    // 首周期输出复位位置；启动命令在随后 PWM 周期边界生效。
    motor_drive #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .MAX_ANGLE_DEG(360),
        .RESET_ANGLE_DEG(180)
    ) horizontal (
        .clk(sys_clk),
        .rst_n(rst_n),
        .angle_deg_i(H_ANGLE),
        .angle_valid_i(command_valid),
        .pwm_o(pwm_horizontal)
    );

    motor_drive #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .MAX_ANGLE_DEG(220),
        .RESET_ANGLE_DEG(130)
    ) vertical (
        .clk(sys_clk),
        .rst_n(rst_n),
        .angle_deg_i(V_ANGLE),
        .angle_valid_i(command_valid),
        .pwm_o(pwm_vertical)
    );
endmodule
