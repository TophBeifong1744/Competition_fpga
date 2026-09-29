`timescale 1ns / 1ps
// 单路位置舵机 PWM；接口 v2（新增 angle_valid_i），纯 Verilog，无外部 RTL 依赖。
// 时钟：单 clk 域，CLK_FREQ_HZ 必须是正的 1 MHz 整数倍。
// 复位：低有效异步置位，调用方须同步释放；复位立即拉低 PWM。
// 输入：angle_valid_i 为高的时钟沿锁存角度，最新命令在 PWM 周期边界生效。
// 复位后持续输出 RESET_ANGLE_DEG，直到接受新命令；首次脉冲为复位位置。
// 边界同拍接受的命令在再下个周期生效；无位置反馈，不能判断机械是否到位。
// 不提供实际位置反馈、机械到位判定或自动寻零。
module motor_drive #(
    parameter integer CLK_FREQ_HZ = 100_000_000,
    // 舵机完整电气量程，不是云台机械限位；9 位角度输入支持 1~511。
    parameter integer MAX_ANGLE_DEG = 360,
    parameter integer RESET_ANGLE_DEG = MAX_ANGLE_DEG / 2
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire [8:0] angle_deg_i,
    input  wire       angle_valid_i, // 同域命令有效；通常拉高一个 clk 周期
    output reg        pwm_o
);
    localparam integer CLKS_PER_US = CLK_FREQ_HZ / 1_000_000;
    localparam integer PWM_PERIOD_US = 20_000;
    localparam [8:0] MAX_ANGLE_VALUE = MAX_ANGLE_DEG;
    localparam integer US_DIV_WIDTH =
        (CLKS_PER_US > 1) ? $clog2(CLKS_PER_US) : 1;

    reg [US_DIV_WIDTH-1:0] us_div_cnt;
    reg [14:0] period_us_cnt;       // 0~19999，每个计数对应 1 us
    reg [15:0] active_pulse_width_us; // 当前周期脉宽，周期内不改变
    reg running;
    reg [8:0] commanded_angle_deg;

    wire us_tick;
    wire period_end;
    wire [8:0] limited_angle_deg;
    wire [31:0] scaled_angle;
    wire [31:0] pulse_offset_us;
    wire [15:0] target_pulse_width_us;

    // 超过舵机满量程时饱和到 MAX_ANGLE_DEG；无符号输入不存在负数。
    assign limited_angle_deg = (commanded_angle_deg > MAX_ANGLE_VALUE)
                             ? MAX_ANGLE_VALUE : commanded_angle_deg;
    // 已由用户确认的映射：0~MAX_ANGLE_DEG 度 -> 500~2500 us，周期 20 ms。
    // 32 位中间量避免乘法截断；加半个除数实现四舍五入。
    assign scaled_angle = {23'd0, limited_angle_deg} * 32'd2000;
    assign pulse_offset_us = (scaled_angle + (MAX_ANGLE_DEG / 2)) / MAX_ANGLE_DEG;
    // offset 最大 2000，低 16 位能够完整表示，无精度丢失。
    assign target_pulse_width_us = 16'd500 + pulse_offset_us[15:0];

    // 连续比较产生使能，不创建新时钟。100 MHz 时每 100 拍有效一次。
    assign us_tick = (us_div_cnt == CLKS_PER_US - 1);
    assign period_end = (period_us_cnt == PWM_PERIOD_US - 1);

    // 参数错误仅用于仿真报错，不生成硬件。
    // synthesis translate_off
    initial begin
        if ((RESET_ANGLE_DEG < 0) || (RESET_ANGLE_DEG > MAX_ANGLE_DEG))
            $fatal(1, "RESET_ANGLE_DEG must be in 0..MAX_ANGLE_DEG");
        if ((MAX_ANGLE_DEG < 1) || (MAX_ANGLE_DEG > 511))
            $fatal(1, "MAX_ANGLE_DEG must be in 1..511");
        if ((CLK_FREQ_HZ < 1_000_000) ||
            ((CLK_FREQ_HZ % 1_000_000) != 0))
            $fatal(1, "CLK_FREQ_HZ must be a positive multiple of 1 MHz");
    end
    // synthesis translate_on

    // 保持最后一次有效命令，避免复位后被角度总线上的旧值覆盖。
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            commanded_angle_deg <= RESET_ANGLE_DEG;
        else if (angle_valid_i)
            commanded_angle_deg <= angle_deg_i;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            us_div_cnt            <= 0;
            period_us_cnt         <= 0;
            active_pulse_width_us <= 0;
            running               <= 1'b0;
            pwm_o                 <= 1'b0;
        end
        else if (!running) begin
            // 第一个有效时钟开始完整 PWM 周期，不先等待 20 ms。
            us_div_cnt            <= 0;
            period_us_cnt         <= 0;
            active_pulse_width_us <= target_pulse_width_us;
            running               <= 1'b1;
            pwm_o                 <= 1'b1;
        end
        else if (us_tick) begin
            us_div_cnt <= 0;
            if (period_end) begin
                period_us_cnt         <= 0;
                active_pulse_width_us <= target_pulse_width_us;
                pwm_o                 <= 1'b1;
            end
            else begin
                period_us_cnt <= period_us_cnt + 1'b1;
                // 非阻塞赋值读取旧值，故比较下一微秒区间的计数。
                // 1500 us 对应区间 0~1499 为高，1500~19999 为低。
                pwm_o <= ((period_us_cnt + 1'b1) < active_pulse_width_us);
            end
        end
        else begin
            us_div_cnt <= us_div_cnt + 1'b1;
            // 其他寄存器保持；输出为寄存器，避免组合比较毛刺。
        end
    end
endmodule
