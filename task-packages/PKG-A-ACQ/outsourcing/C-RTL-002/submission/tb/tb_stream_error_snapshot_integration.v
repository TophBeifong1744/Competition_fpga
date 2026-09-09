`timescale 1ns/1ps
module tb_stream_error_snapshot_integration;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0, clear = 0, overflow_event = 0, drop_event = 0;
    reg snapshot_req = 0;
    wire [2:0] live_overflow_count, live_drop_count;
    wire live_overflow_sticky, live_drop_sticky;
    wire [2:0] snapshot_overflow_count, snapshot_drop_count;
    wire snapshot_overflow_sticky, snapshot_drop_sticky, snapshot_valid;
    stream_error_stats #(.COUNT_WIDTH(3)) stats (
        .clk(clk), .rst_n(rst_n), .clear(clear),
        .overflow_event(overflow_event), .drop_event(drop_event),
        .overflow_count(live_overflow_count), .drop_count(live_drop_count),
        .overflow_sticky(live_overflow_sticky), .drop_sticky(live_drop_sticky)
    );
    stream_error_snapshot #(.COUNT_WIDTH(3)) dut (.clk(clk), .rst_n(rst_n), .snapshot_req(snapshot_req),
                .live_overflow_count(live_overflow_count), .live_drop_count(live_drop_count),
                .live_overflow_sticky(live_overflow_sticky), .live_drop_sticky(live_drop_sticky),
                .snapshot_overflow_count(snapshot_overflow_count), .snapshot_drop_count(snapshot_drop_count),
                .snapshot_overflow_sticky(snapshot_overflow_sticky), .snapshot_drop_sticky(snapshot_drop_sticky),
                .snapshot_valid(snapshot_valid));
    integer checks = 0;
    integer i;

    // Explicit expected values, independent of DUT outputs.
    task step;
        input [8*96-1:0] name;
        input rn, cl, oe, de, req;
        input [2:0] snap_o, snap_d;
        input so, sd, valid;
        input [2:0] live_o, live_d;
        input lo, ld;
        reg [8:0] expected, actual;
        reg [7:0] expected_live, actual_live;
        begin
            @(negedge clk);
            rst_n = rn; clear = cl; overflow_event = oe; drop_event = de;
            snapshot_req = req;
            @(posedge clk); #1;
            expected = {snap_o, snap_d, so, sd, valid};
            actual = {snapshot_overflow_count, snapshot_drop_count,
                      snapshot_overflow_sticky, snapshot_drop_sticky, snapshot_valid};
            expected_live = {live_o, live_d, lo, ld};
            actual_live = {live_overflow_count, live_drop_count, live_overflow_sticky, live_drop_sticky};
            checks = checks + 1;
            if (actual !== expected || actual_live !== expected_live) begin
                $display("FAIL W=3 case=%0s expected=%h actual=%h expected_live=%h actual_live=%h",
                         name, expected, actual, expected_live, actual_live);
                $fatal(1, "integration mismatch");
            end
            $display("PASS integration case=%0s snapshot=%0d/%0d valid=%b live=%0d/%0d",
                     name, snapshot_overflow_count, snapshot_drop_count, snapshot_valid,
                     live_overflow_count, live_drop_count);
        end
    endtask
    initial begin
        step("reset wins",              0,1,1,1,1, 0,0,0,0,0, 0,0,0,0);
        step("first event plus req",    1,0,1,0,1, 0,0,0,0,1, 1,0,1,0);
        step("next req sees event",     1,0,0,0,1, 1,0,1,0,1, 1,0,1,0);
        step("both events plus req",    1,0,1,1,1, 1,0,1,0,1, 2,1,1,1);
        step("next req sees both",      1,0,0,0,1, 2,1,1,1,1, 2,1,1,1);
        step("live advances no req",    1,0,1,1,0, 2,1,1,1,0, 3,2,1,1);
        step("clear plus req old data", 1,1,0,0,1, 3,2,1,1,1, 0,0,0,0);
        step("next req sees cleared",   1,0,0,0,1, 0,0,0,0,1, 0,0,0,0);
        step("repopulate stats",        1,0,1,1,0, 0,0,0,0,0, 1,1,1,1);
        step("clear event req old",     1,1,0,1,1, 1,1,1,1,1, 0,1,0,1);
        step("next sees clear event",   1,0,0,0,1, 0,1,0,1,1, 0,1,0,1);
        step("joint reset",             0,0,1,1,1, 0,0,0,0,0, 0,0,0,0);
        step("recovery event req",      1,0,1,1,1, 0,0,0,0,1, 1,1,1,1);
        step("recovery next req",       1,0,0,0,1, 1,1,1,1,1, 1,1,1,1);
        step("final idle",              1,0,0,0,0, 1,1,1,1,0, 1,1,1,1);

        // Reach and hold saturation via real 001 event inputs; never force state.
        for (i = 2; i <= 7; i = i + 1)
            step("count toward saturation plus req", 1,0,1,1,1, i-1,i-1,1,1,1, i,i,1,1);
        for (i = 0; i < 4; i = i + 1)
            step("saturated event plus req", 1,0,1,1,1, 7,7,1,1,1, 7,7,1,1);
        step("clear saturated overflow event req",1,1,1,0,1, 7,7,1,1,1, 1,0,1,0);
        step("next sees overflow clear event",    1,0,0,0,1, 1,0,1,0,1, 1,0,1,0);
        step("drop-only event plus req",         1,0,0,1,1, 1,0,1,0,1, 1,1,1,1);
        step("clear both events plus req",       1,1,1,1,1, 1,1,1,1,1, 1,1,1,1);
        step("repeated clear both events req",   1,1,1,1,1, 1,1,1,1,1, 1,1,1,1);
        step("clear without req snapshot holds", 1,1,0,0,0, 1,1,1,1,0, 0,0,0,0);
        step("next request sees zero",           1,0,0,0,1, 0,0,0,0,1, 0,0,0,0);

        $display("ALL TESTS PASS: integration COUNT_WIDTH=3 checks=%0d", checks);
        $finish;
    end
    initial begin #100000; $fatal(1, "TIMEOUT: integration tests"); end
endmodule
