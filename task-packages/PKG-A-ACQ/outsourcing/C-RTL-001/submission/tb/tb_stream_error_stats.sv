`timescale 1ns / 1ps

// Self-checking simulation top. Run until ALL TESTS PASS or $fatal.
module tb_stream_error_stats;
    wire done_1, done_3, done_32, done_64;

    stream_error_stats_checker #(.WIDTH(1))  check_1  (.done(done_1));
    stream_error_stats_checker #(.WIDTH(3))  check_3  (.done(done_3));
    // WIDTH=32 deliberately instantiates the DUT without a parameter override.
    stream_error_stats_checker #(.WIDTH(32)) check_32 (.done(done_32));
    stream_error_stats_checker #(.WIDTH(64)) check_64 (.done(done_64));

    initial begin
        wait (done_1 && done_3 && done_32 && done_64);
        $display("ALL TESTS PASS: COUNT_WIDTH=1,3,default32,64");
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "FAIL: global test timeout (100 us)");
    end
endmodule

module stream_error_stats_checker #(
    parameter integer WIDTH = 3
) (
    output logic done = 1'b0
);
    logic clk = 1'b0;
    logic rst_n = 1'b1;
    logic clear = 1'b0;
    logic overflow_event = 1'b0;
    logic drop_event = 1'b0;
    wire [WIDTH-1:0] overflow_count, drop_count;
    wire overflow_sticky, drop_sticky;

    // A 65-bit reference value avoids overflow even for the 64-bit DUT.
    localparam logic [64:0] LIMIT = (65'd1 << WIDTH) - 65'd1;
    logic [64:0] ref_overflow = '0;
    logic [64:0] ref_drop = '0;
    logic ref_overflow_sticky = 1'b0;
    logic ref_drop_sticky = 1'b0;
    integer checks = 0;
    integer i, a, b;
    string active_case = "startup";

    generate
        if (WIDTH == 32) begin : default_parameter
            stream_error_stats dut (
                .clk(clk), .rst_n(rst_n), .clear(clear),
                .overflow_event(overflow_event), .drop_event(drop_event),
                .overflow_count(overflow_count), .drop_count(drop_count),
                .overflow_sticky(overflow_sticky), .drop_sticky(drop_sticky)
            );
        end else begin : explicit_parameter
            stream_error_stats #(.COUNT_WIDTH(WIDTH)) dut (
                .clk(clk), .rst_n(rst_n), .clear(clear),
                .overflow_event(overflow_event), .drop_event(drop_event),
                .overflow_count(overflow_count), .drop_count(drop_count),
                .overflow_sticky(overflow_sticky), .drop_sticky(drop_sticky)
            );
        end
    endgenerate

    always #5 clk = ~clk;

    // Compare all four outputs; !== also catches unexpected X/Z values.
    task automatic compare_outputs(input string case_name);
        begin
            checks = checks + 1;
            if ((overflow_count !== ref_overflow[WIDTH-1:0]) ||
                (drop_count !== ref_drop[WIDTH-1:0]) ||
                (overflow_sticky !== ref_overflow_sticky) ||
                (drop_sticky !== ref_drop_sticky)) begin
                $display("FAIL width=%0d case=%s time=%0t", WIDTH, case_name, $time);
                $display("expected: overflow=%0d drop=%0d sticky=%b/%b",
                    ref_overflow, ref_drop, ref_overflow_sticky, ref_drop_sticky);
                $display("actual:   overflow=%0d drop=%0d sticky=%b/%b",
                    overflow_count, drop_count, overflow_sticky, drop_sticky);
                $fatal(1, "Output mismatch");
            end
        end
    endtask

    // Drive inputs on falling edges, check one ns after rising edges.
    // This avoids reading outputs before DUT nonblocking assignments settle.
    task automatic step(
        input string case_name,
        input bit reset_value,
        input bit clear_value,
        input bit overflow_value,
        input bit drop_value
    );
        begin
            active_case = case_name;
            @(negedge clk);
            rst_n = reset_value;
            clear = clear_value;
            overflow_event = overflow_value;
            drop_event = drop_value;

            @(posedge clk);
            // Reference model: discard history if requested, add events,
            // then clamp the widened mathematical totals to the limit.
            if (!reset_value || clear_value) begin
                ref_overflow = 0;
                ref_drop = 0;
                ref_overflow_sticky = 0;
                ref_drop_sticky = 0;
            end
            if (reset_value) begin
                ref_overflow = ref_overflow + overflow_value;
                ref_drop = ref_drop + drop_value;
                if (ref_overflow > LIMIT) ref_overflow = LIMIT;
                if (ref_drop > LIMIT) ref_drop = LIMIT;
                ref_overflow_sticky = ref_overflow_sticky | overflow_value;
                ref_drop_sticky = ref_drop_sticky | drop_value;
            end
            #1;
            compare_outputs(case_name);
        end
    endtask

    initial begin
        step("initial reset",          0, 0, 0, 0);
        step("idle after reset",       1, 0, 0, 0);
        step("overflow only",          1, 0, 1, 0);
        step("overflow sticky hold",   1, 0, 0, 0);
        step("drop only",              1, 0, 0, 1);
        step("both sticky hold",       1, 0, 0, 0);
        step("ordinary clear",         1, 1, 0, 0);
        repeat (3) step("three consecutive overflow events", 1, 0, 1, 0);
        step("ordinary clear",         1, 1, 0, 0);
        repeat (3) step("three consecutive drop events", 1, 0, 0, 1);
        step("both events same edge",  1, 0, 1, 1);
        step("reset wins over all",    0, 1, 1, 1);
        step("clear plus overflow",    1, 1, 1, 0);
        step("clear plus drop",        1, 1, 0, 1);
        step("clear plus both",        1, 1, 1, 1);
        repeat (3) step("continuous clear plus events", 1, 1, 1, 1);
        step("resume after clear",     1, 0, 1, 1);
        step("idle preserves state",   1, 0, 0, 0);

        // Reset assertion between rising edges must NOT immediately clear.
        active_case = "synchronous reset between edges";
        @(negedge clk);
        rst_n = 0;
        clear = 1;
        overflow_event = 1;
        drop_event = 1;
        #1;
        compare_outputs(active_case);
        @(posedge clk);
        ref_overflow = 0;
        ref_drop = 0;
        ref_overflow_sticky = 0;
        ref_drop_sticky = 0;
        #1;
        compare_outputs("synchronous reset at rising edge");

        step("reload before sync clear", 1, 0, 1, 1);
        active_case = "synchronous clear between edges";
        @(negedge clk);
        clear = 1;
        overflow_event = 0;
        drop_event = 0;
        #1;
        compare_outputs(active_case);
        @(posedge clk);
        ref_overflow = 0;
        ref_drop = 0;
        ref_overflow_sticky = 0;
        ref_drop_sticky = 0;
        #1;
        compare_outputs("synchronous clear at rising edge");

        // Reach saturation using real input cycles only; never force DUT state.
        if (WIDTH <= 3) begin
            step("clear before saturation", 1, 1, 0, 0);
            for (i = 0; i < (1 << WIDTH) + 2; i = i + 1)
                step("overflow saturation", 1, 0, 1, 0);
            step("drop while overflow saturated", 1, 0, 0, 1);
            for (i = 0; i < (1 << WIDTH) + 2; i = i + 1)
                step("both saturation", 1, 0, 1, 1);
            step("saturated idle", 1, 0, 0, 0);
            step("saturated clear plus overflow", 1, 1, 1, 0);
            for (i = 0; i < (1 << WIDTH) + 2; i = i + 1)
                step("drop saturation independently", 1, 0, 0, 1);
            step("overflow while drop saturated", 1, 0, 1, 0);
            step("saturated reset priority", 0, 1, 1, 1);
            step("recount after reset", 1, 0, 1, 1);
            step("clear saturated width1", 1, 1, 0, 0);
        end

        // Exercise every pair of the 16 possible control-input combinations.
        for (a = 0; a < 16; a = a + 1) begin
            for (b = 0; b < 16; b = b + 1) begin
                step($sformatf("control pair %0d/%0d first", a, b),
                    a[3], a[2], a[1], a[0]);
                step($sformatf("control pair %0d/%0d second", a, b),
                    b[3], b[2], b[1], b[0]);
            end
        end
        $display("PASS COUNT_WIDTH=%0d checks=%0d", WIDTH, checks);
        done = 1'b1;
    end
endmodule
