`timescale 1ns / 1ps
// Two independent instances of the active single-axis v2 RTL; no product pair wrapper.
module tb_servo_dual_axis_v2;
    parameter integer CLK_FREQ_HZ = 1_000_000;
    localparam integer CLOCK_NS = 1_000_000_000 / CLK_FREQ_HZ;
    localparam integer CLKS_PER_US = CLK_FREQ_HZ / 1_000_000;
    reg clk = 0;
    reg rst_n = 0;
    reg [8:0] horizontal_deg = 0;
    reg [8:0] vertical_deg = 0;
    reg horizontal_valid = 0;
    reg vertical_valid = 0;
    wire horizontal_pwm, vertical_pwm;
    integer checks = 0;
    time r0;

    motor_drive #(.CLK_FREQ_HZ(CLK_FREQ_HZ), .MAX_ANGLE_DEG(360), .RESET_ANGLE_DEG(180)) horizontal (
        .clk(clk), .rst_n(rst_n), .angle_deg_i(horizontal_deg),
        .angle_valid_i(horizontal_valid), .pwm_o(horizontal_pwm)
    );
    motor_drive #(.CLK_FREQ_HZ(CLK_FREQ_HZ), .MAX_ANGLE_DEG(220), .RESET_ANGLE_DEG(130)) vertical (
        .clk(clk), .rst_n(rst_n), .angle_deg_i(vertical_deg),
        .angle_valid_i(vertical_valid), .pwm_o(vertical_pwm)
    );
    always #(CLOCK_NS / 2) clk = ~clk;

    task automatic check_time(input string label_text, input time actual, input time expected);
        if (actual !== expected)
            $fatal(1, "FAIL %s actual_ns=%0d expected_ns=%0d", label_text, actual, expected);
        checks = checks + 1;
        $display("OBS %s actual_ns=%0d expected_ns=%0d", label_text, actual, expected);
    endtask

    task automatic check_pair_from(input time rise_ns, input integer h_us, input integer v_us, input string label_text);
        time h_fall, v_fall, h_rise, v_rise;
        fork
            begin @(negedge horizontal_pwm); h_fall = $time; end
            begin @(negedge vertical_pwm); v_fall = $time; end
        join
        check_time({label_text, " horizontal width"}, h_fall - rise_ns, h_us * 1000);
        check_time({label_text, " vertical width"}, v_fall - rise_ns, v_us * 1000);
        fork
            begin @(posedge horizontal_pwm); h_rise = $time; end
            begin @(posedge vertical_pwm); v_rise = $time; end
        join
        check_time({label_text, " horizontal period"}, h_rise - rise_ns, 20_000_000);
        check_time({label_text, " vertical period"}, v_rise - rise_ns, 20_000_000);
        check_time({label_text, " aligned rise"}, h_rise, v_rise);
    endtask

    task automatic start_pair(output time rise_ns);
        @(negedge clk);
        rst_n = 0;
        horizontal_valid = 0;
        vertical_valid = 0;
        repeat (3) @(negedge clk);
        if (horizontal_pwm !== 1'b0 || vertical_pwm !== 1'b0)
            $fatal(1, "FAIL pair reset outputs not low");
        rst_n = 1;
        @(posedge horizontal_pwm);
        rise_ns = $time;
        #1;
        if (vertical_pwm !== 1'b1) $fatal(1, "FAIL pair first rise not aligned");
    endtask

    initial begin
        if (CLK_FREQ_HZ != 1_000_000 && CLK_FREQ_HZ != 100_000_000)
            $fatal(1, "TB supports 1 MHz or 100 MHz");
        start_pair(r0);
        repeat (100 * CLKS_PER_US - 1) @(posedge clk);
        @(negedge clk);
        horizontal_deg = 90; horizontal_valid = 1;
        vertical_deg = 55; vertical_valid = 1;
        @(negedge clk); horizontal_valid = 0; vertical_valid = 0;
        check_pair_from(r0, 1500, 1682, "reset positions");
        check_pair_from($time, 1000, 1000, "simultaneous commands");
        r0 = $time;

        // Horizontal changes while vertical bus changes without valid: vertical holds.
        repeat (100 * CLKS_PER_US - 1) @(posedge clk);
        @(negedge clk);
        horizontal_deg = 270; horizontal_valid = 1;
        vertical_deg = 220; vertical_valid = 0;
        @(negedge clk); horizontal_valid = 0;
        check_pair_from(r0, 1000, 1000, "one-axis current");
        check_pair_from($time, 2000, 1000, "one-axis update");
        r0 = $time;

        // Only vertical gets a new command; horizontal holds its 270-degree target.
        repeat (100 * CLKS_PER_US - 1) @(posedge clk);
        @(negedge clk); vertical_deg = 0; vertical_valid = 1;
        @(negedge clk); vertical_valid = 0;
        check_pair_from(r0, 2000, 1000, "vertical current");
        check_pair_from($time, 2000, 500, "vertical update");

        // Reset both while PWM is high; then each returns to its own home width.
        #100_000;
        rst_n = 0;
        #1;
        if (horizontal_pwm !== 1'b0 || vertical_pwm !== 1'b0)
            $fatal(1, "FAIL asynchronous pair reset");
        checks = checks + 1;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(posedge horizontal_pwm); r0 = $time;
        #1;
        if (vertical_pwm !== 1'b1) $fatal(1, "FAIL pair reset release not aligned");
        check_pair_from(r0, 1500, 1682, "pair reset release");
        check_pair_from($time, 1500, 1682, "pair reset holds");

        $display("PASS v2 dual-axis checks=%0d CLK_FREQ_HZ=%0d", checks, CLK_FREQ_HZ);
        $finish;
    end

    initial begin
        #500_000_000;
        $fatal(1, "FAIL dual-axis watchdog");
    end
endmodule
