`timescale 1ns / 1ps
// 自检测试仅观察输入输出边沿，不依赖 DUT 内部计数器。
module tb_motor_drive;
    parameter integer CLK_FREQ_HZ = 100_000_000;
    parameter integer MAX_ANGLE_DEG = 360;
    localparam integer RESET_ANGLE_DEG = (MAX_ANGLE_DEG == 220) ? 130 : 180;
    localparam integer RESET_WIDTH_US = (MAX_ANGLE_DEG == 220) ? 1682 : 1500;
    localparam real HALF_CLK_NS = 500_000_000.0 / CLK_FREQ_HZ;
    reg clk = 0;
    reg rst_n = 0;
    reg [8:0] angle_deg = 0;
    reg angle_valid = 0;
    wire pwm;
    integer checks = 0;
    time rise_time;
    motor_drive #(.CLK_FREQ_HZ(CLK_FREQ_HZ), .MAX_ANGLE_DEG(MAX_ANGLE_DEG), .RESET_ANGLE_DEG(RESET_ANGLE_DEG)) dut (
        .clk(clk), .rst_n(rst_n), .angle_deg_i(angle_deg), .angle_valid_i(angle_valid), .pwm_o(pwm)
    );
    always #(HALF_CLK_NS) clk = ~clk;

    task check_value;
        input [8*80-1:0] label_text;
        input time actual;
        input time expected;
        begin
            if (actual !== expected) begin
                $display("FAIL %0s actual=%0d expected=%0d ns", label_text, actual, expected);
                $fatal(1, "test failed");
            end
            checks = checks + 1;
        end
    endtask

    task send_angle;
        input [8:0] angle;
        begin
            @(negedge clk); angle_deg = angle; angle_valid = 1;
            @(negedge clk); angle_valid = 0;
        end
    endtask

    task start_angle;
        input [8:0] angle;
        time home_start;
        begin
            @(negedge clk);
            angle_valid = 0;
            rst_n = 0;
            angle_deg = angle;
            repeat (3) @(negedge clk);
            #1;
            check_value("reset low", pwm, 0);
            @(negedge clk);
            rst_n = 1;
            @(posedge pwm); home_start = $time;
            @(negedge pwm);
            check_value("first reset position", $time-home_start, RESET_WIDTH_US*1000);
            send_angle(angle);
        end
    endtask

    task check_frame;
        input integer width_us;
        time start_time;
        begin
            @(posedge pwm); start_time = $time;
            @(negedge pwm);
            check_value("pulse width", $time-start_time, width_us*1000);
            @(posedge pwm);
            check_value("period", $time-start_time, 20_000_000);
        end
    endtask

    initial begin
        // 独立给定期望值：端点、各象限、舍入和输入饱和。
        if (MAX_ANGLE_DEG == 360) begin
        start_angle(0);   check_frame(500);
        start_angle(90);  check_frame(1000);
        start_angle(180); check_frame(1500);
        start_angle(270); check_frame(2000);
        start_angle(360); check_frame(2500);
        start_angle(1);   check_frame(506);
        start_angle(2);   check_frame(511);
        start_angle(359); check_frame(2494);
        start_angle(361); check_frame(2500);
        start_angle(511); check_frame(2500);
        end else if (MAX_ANGLE_DEG == 220) begin
            // 独立固定期望，不能复制 DUT 公式作为测试判据。
            start_angle(0);   check_frame(500);
            start_angle(55);  check_frame(1000);
            start_angle(165); check_frame(2000);
            start_angle(221); check_frame(2500);
            start_angle(45);  check_frame(909);
            start_angle(90);  check_frame(1318);
            start_angle(110); check_frame(1500);
            start_angle(220); check_frame(2500);
            start_angle(1);   check_frame(509);
            start_angle(2);   check_frame(518);
            start_angle(219); check_frame(2491);
            start_angle(511); check_frame(2500);
        end else $fatal(1, "This regression supports MAX_ANGLE_DEG=360 or 220");


        // 高电平中改变目标：旧脉冲不能缩短，下一周期使用新值。
        start_angle(MAX_ANGLE_DEG);
        @(posedge pwm); rise_time = $time;
        #100_000;
        send_angle(0);
        @(negedge pwm);
        check_value("mid-high unchanged", $time-rise_time, 2_500_000);
        @(posedge pwm);
        check_value("update period", $time-rise_time, 20_000_000);
        rise_time = $time;
        @(negedge pwm);
        check_value("new width", $time-rise_time, 500_000);

        // 低电平中增大目标：不能重新拉高，直到下一周期。
        send_angle(MAX_ANGLE_DEG);
        @(posedge pwm);
        check_value("no extra pulse", $time-rise_time, 20_000_000);
        rise_time = $time;
        @(negedge pwm);
        check_value("new large width", $time-rise_time, 2_500_000);

        // 高电平期间异步复位，检查立即拉低及释放后完整重启。
        @(posedge pwm);
        #12_343; rst_n = 0;
        #1; check_value("async reset", pwm, 0);
        repeat (5) @(negedge clk);
        angle_deg = 180;
        rst_n = 1;
        check_frame(RESET_WIDTH_US);
        check_frame(RESET_WIDTH_US); // 旧角度总线不应覆盖复位位置

        // 低电平期间复位。
        @(negedge pwm);
        #123; rst_n = 0;
        #1; check_value("low reset", pwm, 0);
        repeat (5) @(negedge clk);
        angle_deg = 90;
        rst_n = 1;
        check_frame(RESET_WIDTH_US);
        // 未发送命令时改变总线，仍须保持复位位置。
        @(negedge clk); angle_deg = 511;
        check_frame(RESET_WIDTH_US);
        send_angle(0);
        check_frame(500); // 单拍新命令恢复运动
        send_angle(MAX_ANGLE_DEG);
        check_frame(2500);
        $display("PASS motor_drive checks=%0d CLK_FREQ_HZ=%0d MAX_ANGLE_DEG=%0d", checks, CLK_FREQ_HZ, MAX_ANGLE_DEG);
        $finish;
    end

    // 防止无输出时测试永久等待。
    initial begin
        #1_000_000_000;
        $fatal(1, "watchdog timeout");
    end
endmodule
