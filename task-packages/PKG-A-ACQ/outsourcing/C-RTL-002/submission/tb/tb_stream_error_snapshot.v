`timescale 1ns/1ps
module snapshot_checker #(parameter integer W = 3)(output reg done);
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0, snapshot_req = 0;
    reg [W-1:0] live_overflow_count = 0, live_drop_count = 0;
    reg live_overflow_sticky = 0, live_drop_sticky = 0;
    wire [W-1:0] snapshot_overflow_count, snapshot_drop_count;
    wire snapshot_overflow_sticky, snapshot_drop_sticky, snapshot_valid;
    generate
        if (W == 32) begin : default_width
            // No override: test the published default parameter.
            stream_error_snapshot dut (.clk(clk), .rst_n(rst_n), .snapshot_req(snapshot_req),
                .live_overflow_count(live_overflow_count), .live_drop_count(live_drop_count),
                .live_overflow_sticky(live_overflow_sticky), .live_drop_sticky(live_drop_sticky),
                .snapshot_overflow_count(snapshot_overflow_count), .snapshot_drop_count(snapshot_drop_count),
                .snapshot_overflow_sticky(snapshot_overflow_sticky), .snapshot_drop_sticky(snapshot_drop_sticky),
                .snapshot_valid(snapshot_valid));
        end else begin : explicit_width
            stream_error_snapshot #(.COUNT_WIDTH(W)) dut (.clk(clk), .rst_n(rst_n), .snapshot_req(snapshot_req),
                .live_overflow_count(live_overflow_count), .live_drop_count(live_drop_count),
                .live_overflow_sticky(live_overflow_sticky), .live_drop_sticky(live_drop_sticky),
                .snapshot_overflow_count(snapshot_overflow_count), .snapshot_drop_count(snapshot_drop_count),
                .snapshot_overflow_sticky(snapshot_overflow_sticky), .snapshot_drop_sticky(snapshot_drop_sticky),
                .snapshot_valid(snapshot_valid));
        end
    endgenerate

    reg [2*W+1:0] saved = 0;
    reg expected_valid = 0;
    reg initialized = 0;
    integer checks = 0;
    reg [8*96-1:0] case_name = "initial reset";
    localparam [W-1:0] MAX_VALUE = {W{1'b1}};
    localparam [W-1:0] MSB_VALUE = {1'b1, {(W-1){1'b0}}};
    reg [W-1:0] alternating;
    integer b, i, s, ov_i, dr_i;
    reg [W-1:0] walking;
    reg [63:0] rng, random_ov;


    // Also reject any output transition outside the sampling edge, including
    // short glitches that periodic #1 comparisons alone could miss.
    realtime last_rising_edge = -1.0;
    always @(posedge clk) last_rising_edge = $realtime;
    always @(snapshot_overflow_count or snapshot_drop_count or
             snapshot_overflow_sticky or snapshot_drop_sticky or snapshot_valid) begin
        if (initialized && $realtime != last_rising_edge) begin
            $display("FAIL W=%0d case=%0s asynchronous output transition expected=%h actual=%h",
                     W, case_name, {saved, expected_valid},
                     {snapshot_overflow_count, snapshot_drop_count,
                      snapshot_overflow_sticky, snapshot_drop_sticky, snapshot_valid});
            $fatal(1, "output changed outside rising edge");
        end
    end

    task compare_outputs;
        input [8*64-1:0] phase_name;
        reg [2*W+2:0] actual, expected;
        begin
            actual = {snapshot_overflow_count, snapshot_drop_count,
                      snapshot_overflow_sticky, snapshot_drop_sticky, snapshot_valid};
            expected = {saved, expected_valid};
            checks = checks + 1;
            if (actual !== expected) begin
                $display("FAIL W=%0d case=%0s phase=%0s expected=%h actual=%h",
                         W, case_name, phase_name, expected, actual);
                $fatal(1, "snapshot mismatch");
            end
        end
    endtask

    // Packed reference register; no dependency on DUT internal state.
    always @(posedge clk) begin
        case ({rst_n, snapshot_req})
            2'b00, 2'b01: begin saved = 0; expected_valid = 0; end
            2'b10: expected_valid = 0;
            2'b11: begin
                saved = {live_overflow_count, live_drop_count,
                         live_overflow_sticky, live_drop_sticky};
                expected_valid = 1;
            end
            default: $fatal(1, "unknown stimulus");
        endcase
        #1;
        initialized = 1;
        compare_outputs("after rising edge");
    end

    task step;
        input [8*96-1:0] label_text;
        input reset_value, request_value;
        input [W-1:0] ov, dr;
        input os, ds;
        begin
            @(negedge clk);
            case_name = label_text;
            rst_n = reset_value;
            snapshot_req = request_value;
            live_overflow_count = ov;
            live_drop_count = dr;
            live_overflow_sticky = os;
            live_drop_sticky = ds;
            #1;
            if (initialized) compare_outputs("between edges: outputs must hold");
            @(posedge clk); #2;
        end
    endtask

    initial begin
        done = 0;
        alternating = 0;
        for (b = 0; b < W; b = b + 1) alternating[b] = (b % 2 == 0);
        step("reset wins over request", 0, 1, MAX_VALUE, MAX_VALUE, 1, 1);
        for (i = 0; i < 8; i = i + 1)
            step("initial idle changing live", 1, 0, i, ~i, i[0], i[1]);
        step("single request", 1, 1, MSB_VALUE, MAX_VALUE, 1, 0);
        step("valid deasserts data holds", 1, 0, 0, 0, 0, 1);
        for (i = 0; i < 32; i = i + 1)
            step("long idle changing live", 1, 0, i, ~i, i[0], i[1]);
        for (i = 0; i < 16; i = i + 1)
            step("consecutive requests", 1, 1, i, ~i, i[0], ~i[0]);
        for (s = 0; s < 4; s = s + 1) begin
            step("zero boundary sticky combinations", 1, 1, 0, 0, s[1], s[0]);
            step("all ones sticky combinations", 1, 1, MAX_VALUE, MAX_VALUE, s[1], s[0]);
            step("highest bit sticky combinations", 1, 1, MSB_VALUE, MSB_VALUE, s[1], s[0]);
            step("alternating bits sticky combinations", 1, 1, alternating, ~alternating, s[1], s[0]);
        end
        step("prepare nonzero synchronous reset", 1, 1, MAX_VALUE, MAX_VALUE, 1, 1);
        step("assert reset between edges", 0, 1, MSB_VALUE, 0, 0, 1);
        step("request after reset", 1, 1, MSB_VALUE, MAX_VALUE, 0, 0);
        step("hold after recovery", 1, 0, 0, 0, 1, 1);
        // A pulse wholly between rising edges must not reset/capture.
        @(negedge clk);
        case_name = "between-edge request live reset pulses";
        snapshot_req = 1;
        live_overflow_count = 0;
        live_drop_count = 0;
        rst_n = 0;
        #1; compare_outputs("pulse asserted");
        rst_n = 1;
        snapshot_req = 0;
        #1; compare_outputs("pulse removed");
        @(posedge clk); #2;

        // Each individual data bit on each lane, with no relation to sticky.
        for (b = 0; b < W; b = b + 1) begin
            walking = {{(W-1){1'b0}}, 1'b1} << b;
            step("walking one overflow only", 1, 1, walking, 0, 0, 1);
            step("walking one drop only", 1, 1, 0, walking, 1, 0);
            step("walking zero overflow only", 1, 1, ~walking, MAX_VALUE, 0, 0);
            step("walking zero drop only", 1, 1, MAX_VALUE, ~walking, 1, 1);
        end
        // Exhaust all live data and sticky combinations for small widths.
        // This is an input sweep, not an exhaustive sequential-state proof.
        if (W <= 3) begin
            for (ov_i = 0; ov_i < (1 << W); ov_i = ov_i + 1)
                for (dr_i = 0; dr_i < (1 << W); dr_i = dr_i + 1)
                    for (s = 0; s < 4; s = s + 1) begin
                        step("small-width exhaustive capture", 1, 1, ov_i, dr_i, s[1], s[0]);
                        step("small-width exhaustive hold", 1, 0, ~ov_i, ~dr_i, ~s[1], ~s[0]);
                    end
        end
        // Fixed-seed xorshift64 stimulus fills upper bits as well as lower bits.
        rng = 64'hd1b54a32d192ed03;
        for (i = 0; i < 256; i = i + 1) begin
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 7);
            rng = rng ^ (rng << 17);
            random_ov = rng;
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 7);
            rng = rng ^ (rng << 17);
            step("fixed-seed reset request live mix", (i % 17 != 0),
                 rng[2], random_ov, rng, rng[4], rng[5]);
        end
        step("prepare reset without request", 1, 1, MAX_VALUE, MAX_VALUE, 1, 1);
        step("reset without request", 0, 0, MSB_VALUE, MAX_VALUE, 1, 1);
        step("prepare standalone request pulse", 1, 0, 0, 0, 0, 0);
        @(negedge clk);
        case_name = "request-only pulse between rising edges";
        snapshot_req = 1;
        live_overflow_count = MAX_VALUE;
        live_drop_count = MAX_VALUE;
        #1; compare_outputs("request pulse high");
        snapshot_req = 0;
        #1; compare_outputs("request pulse low");
        @(posedge clk); #2;
        step("prepare data-only pulse", 1, 1, MSB_VALUE, MAX_VALUE, 1, 0);
        @(negedge clk);
        case_name = "data-only pulse while request stays high";
        live_overflow_count = 0; live_drop_count = 0;
        live_overflow_sticky = 0; live_drop_sticky = 1;
        #1; compare_outputs("data pulse changed");
        live_overflow_count = MSB_VALUE; live_drop_count = MAX_VALUE;
        live_overflow_sticky = 1; live_drop_sticky = 0;
        #1; compare_outputs("data pulse restored");
        @(posedge clk); #2;
        step("prepare reset-only pulse", 1, 0, 0, 0, 0, 0);
        @(negedge clk);
        case_name = "reset-only pulse between rising edges";
        rst_n = 0;
        #1; compare_outputs("reset pulse asserted");
        rst_n = 1;
        #1; compare_outputs("reset pulse released");
        @(posedge clk); #2;

        step("final request", 1, 1, MAX_VALUE, MSB_VALUE, 1, 0);
        step("final hold", 1, 0, 0, 0, 0, 0);
        $display("PASS COUNT_WIDTH=%0d checks=%0d", W, checks);
        done = 1;
    end
endmodule

module tb_stream_error_snapshot;
    wire d3, d1, d32, d64;
    snapshot_checker #(3) test3(d3);
    snapshot_checker #(1) test1(d1);
    snapshot_checker #(32) test32(d32);
    snapshot_checker #(64) test64(d64);
    initial begin
        wait (d3 && d1 && d32 && d64);
        $display("ALL TESTS PASS: COUNT_WIDTH=1,3,default32,64");
        $finish;
    end
    initial begin #100000; $fatal(1, "TIMEOUT: snapshot unit tests"); end
endmodule

module tb_stream_error_snapshot_all_widths;
    wire [64:1] done;
    genvar width_index;
    generate
        for (width_index = 1; width_index <= 64; width_index = width_index + 1) begin : widths
            snapshot_checker #(.W(width_index)) check_width(.done(done[width_index]));
        end
    endgenerate
    initial begin
        wait (&done);
        $display("ALL TESTS PASS: every COUNT_WIDTH from 1 through 64");
        $finish;
    end
    initial begin #100000; $fatal(1, "TIMEOUT: all-width sweep"); end
endmodule
