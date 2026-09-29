`timescale 1ns / 1ps
// #19 directed v2 timing oracle. Expectations are fixed at the output pins.
module tb_motor_drive_v2_targeted;
    parameter integer CLK_FREQ_HZ = 1_000_000;
    parameter integer MAX_ANGLE_DEG = 360;
    localparam integer CLOCK_NS = 1_000_000_000 / CLK_FREQ_HZ;
    localparam integer CLKS_PER_US = CLK_FREQ_HZ / 1_000_000;
    localparam integer PERIOD_CYCLES = CLK_FREQ_HZ / 50;
    localparam integer HOME_US = (MAX_ANGLE_DEG == 220) ? 1682 : 1500;
    localparam integer HOME_DEG = (MAX_ANGLE_DEG == 220) ? 130 : 180;
    reg clk = 0;
    reg rst_n = 0;
    reg [8:0] angle_deg = 0;
    reg angle_valid = 0;
    wire pwm;
    integer checks = 0;
    time r0, r1;

    motor_drive #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .MAX_ANGLE_DEG(MAX_ANGLE_DEG),
        .RESET_ANGLE_DEG(HOME_DEG)
    ) dut (
        .clk(clk), .rst_n(rst_n), .angle_deg_i(angle_deg),
        .angle_valid_i(angle_valid), .pwm_o(pwm)
    );
    always #(CLOCK_NS / 2) clk = ~clk;

    task automatic check_time(input string label_text, input time actual, input time expected);
        if (actual !== expected)
            $fatal(1, "FAIL %s actual_ns=%0d expected_ns=%0d", label_text, actual, expected);
        checks = checks + 1;
        $display("OBS %s actual_ns=%0d expected_ns=%0d", label_text, actual, expected);
    endtask

    // Called immediately after a PWM rising edge, or with its saved timestamp.
    // Waiting for both falling and next rising edge detects truncation and extra pulses.
    task automatic expect_frame_from(input time rise_ns, input integer width_us, input string label_text);
        @(negedge pwm);
        check_time({label_text, " width"}, $time - rise_ns, width_us * 1000);
        @(posedge pwm);
        check_time({label_text, " period"}, $time - rise_ns, 20_000_000);
    endtask

    task automatic start_home(output time rise_ns);
        @(negedge clk);
        rst_n = 0;
        angle_valid = 0;
        angle_deg = 0;
        repeat (3) @(negedge clk);
        if (pwm !== 1'b0) $fatal(1, "FAIL reset must force PWM low");
        rst_n = 1;
        @(posedge pwm);
        rise_ns = $time;
    endtask

    task automatic phase_case(input integer phase, input string label_text);
        time first_rise, boundary_rise;
        start_home(first_rise);
        if (phase == -1) begin
            // Accept at clock edge B-1, one edge before next PWM rising edge B.
            repeat (PERIOD_CYCLES - 2) @(posedge clk);
            @(negedge clk); angle_deg = 0; angle_valid = 1;
            @(negedge clk); angle_valid = 0;
            @(posedge pwm); boundary_rise = $time;
            check_time({label_text, " boundary"}, boundary_rise - first_rise, 20_000_000);
            expect_frame_from(boundary_rise, 500, label_text);
        end else if (phase == 0) begin
            // Accept on B; the B frame reads the old command, B+1 reads the new one.
            repeat (PERIOD_CYCLES - 1) @(posedge clk);
            @(negedge clk); angle_deg = 0; angle_valid = 1;
            @(posedge pwm); boundary_rise = $time;
            @(negedge clk); angle_valid = 0;
            check_time({label_text, " boundary"}, boundary_rise - first_rise, 20_000_000);
            expect_frame_from(boundary_rise, HOME_US, {label_text, " old"});
            expect_frame_from($time, 500, {label_text, " new"});
        end else if (phase == 1) begin
            // Accept at B+1; the already-started B frame stays unchanged.
            @(posedge pwm); boundary_rise = $time;
            @(negedge clk); angle_deg = 0; angle_valid = 1;
            @(negedge clk); angle_valid = 0;
            check_time({label_text, " boundary"}, boundary_rise - first_rise, 20_000_000);
            expect_frame_from(boundary_rise, HOME_US, {label_text, " old"});
            expect_frame_from($time, 500, {label_text, " new"});
        end else $fatal(1, "bad phase");
    endtask

    initial begin
        if (CLK_FREQ_HZ != 1_000_000 && CLK_FREQ_HZ != 100_000_000)
            $fatal(1, "TB supports 1 MHz or 100 MHz");
        if (MAX_ANGLE_DEG != 220 && MAX_ANGLE_DEG != 360)
            $fatal(1, "TB supports 220 or 360 degrees");

        phase_case(-1, "valid B-1");
        phase_case(0,  "valid B");
        phase_case(1,  "valid B+1");

        // Valid on first release edge: first pulse is reset position, next is command.
        @(negedge clk); rst_n = 0; angle_deg = 0; angle_valid = 1;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(posedge pwm); r0 = $time;
        @(negedge clk); angle_valid = 0;
        expect_frame_from(r0, HOME_US, "release+valid first");
        expect_frame_from($time, 500, "release+valid next");

        // Valid while reset is asserted must be discarded.
        @(negedge clk); rst_n = 0; angle_deg = 0; angle_valid = 1;
        repeat (3) @(negedge clk);
        angle_valid = 0; rst_n = 1;
        @(posedge pwm); r0 = $time;
        expect_frame_from(r0, HOME_US, "valid during reset first");
        expect_frame_from($time, HOME_US, "valid during reset hold");

        // Multiple accepted commands while valid stays high: latest wins at B.
        // They arrive during the high part of a pulse; current width must not shrink.
        start_home(r0);
        repeat (100 * CLKS_PER_US - 1) @(posedge clk);
        @(negedge clk); angle_valid = 1; angle_deg = 90;
        @(negedge clk); angle_deg = 0;
        @(negedge clk); angle_deg = MAX_ANGLE_DEG;
        @(negedge clk); angle_valid = 0;
        expect_frame_from(r0, HOME_US, "sustained valid current");
        expect_frame_from($time, 2500, "sustained valid latest");

        $display("PASS v2 targeted checks=%0d CLK_FREQ_HZ=%0d MAX_ANGLE_DEG=%0d", checks, CLK_FREQ_HZ, MAX_ANGLE_DEG);
        $finish;
    end

    initial begin
        #750_000_000;
        $fatal(1, "FAIL v2 targeted watchdog");
    end
endmodule
