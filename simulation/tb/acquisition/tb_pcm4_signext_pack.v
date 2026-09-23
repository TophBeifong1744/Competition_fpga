`timescale 1ns/1ps

// Verilog testbench. Independent integer oracle, no floating-point arithmetic.
module pcm4_width_test #(parameter W = 24) (output reg done);
    reg [W-1:0] samples [0:3];
    wire [127:0] packed_out;
    reg [127:0] expected, before_out;
    reg [W-1:0] boundaries [0:5];
    reg [W-1:0] sign_mask;
    reg [31:0] rng;
    integer channel, bit_index, pattern, k, a, b, c, d;
    integer comparisons;

    generate
        if (W == 24) begin : default_width
            // Intentionally leave the DUT's default parameter untouched.
            pcm4_signext_pack dut (
                .mic0_in(samples[0]), .mic1_in(samples[1]),
                .mic2_in(samples[2]), .mic3_in(samples[3]), .pcm_packed(packed_out));
        end else begin : configured_width
            pcm4_signext_pack #(.SAMPLE_WIDTH(W)) dut (
                .mic0_in(samples[0]), .mic1_in(samples[1]),
                .mic2_in(samples[2]), .mic3_in(samples[3]), .pcm_packed(packed_out));
        end
    endgenerate

    function [31:0] reference_word;
        input [W-1:0] raw;
        reg signed [63:0] value, modulus;
        begin
            value = 0;
            value = raw; // Unsigned raw code is zero-extended into 64 bits.
            modulus = 64'd1 << W;
            if (raw[W-1]) value = value - modulus;
            reference_word = value; // Low 32 bits of the mathematical integer.
        end
    endfunction

    task check;
        integer slot;
        begin
            #1; // Allow continuous assignments to settle after every stimulus.
            for (slot = 0; slot < 4; slot = slot + 1)
                expected[slot*32 +: 32] = reference_word(samples[slot]);
            if (packed_out !== expected) begin
                $display("FAIL W=%0d input=%h/%h/%h/%h expected=%h actual=%h",
                    W, samples[0], samples[1], samples[2], samples[3], expected, packed_out);
                $fatal(1, "PCM comparison failed");
            end
            comparisons = comparisons + 1;
        end
    endtask

    task baseline;
        begin
            samples[0] = 0; samples[1] = 1;
            samples[2] = 2; samples[3] = 3;
        end
    endtask

    // Check single-channel updates explicitly, in addition to the full oracle.
    task check_isolation;
        input integer changed;
        integer slot;
        begin
            check;
            for (slot = 0; slot < 4; slot = slot + 1)
                if ((slot != changed) &&
                    (packed_out[slot*32 +: 32] !== before_out[slot*32 +: 32])) begin
                    $display("FAIL isolation W=%0d changed=%0d slot=%0d input=%h/%h/%h/%h expected=%h actual=%h",
                        W, changed, slot, samples[0], samples[1], samples[2], samples[3], expected, packed_out);
                    $fatal(1, "Unchanged channel moved");
                end
        end
    endtask

    task random_step;
        begin
            // Explicit xorshift32 algorithm makes the sequence reproducible.
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 17);
            rng = rng ^ (rng << 5);
        end
    endtask

    initial begin
        done = 0; comparisons = 0;
        rng = 32'h13579bdf ^ W;
        sign_mask = {W{1'b0}};
        sign_mask[W-1] = 1'b1;
        boundaries[0] = 0;
        boundaries[1] = 1;
        boundaries[2] = {W{1'b1}};
        boundaries[3] = sign_mask - 1'b1;
        boundaries[4] = sign_mask;
        boundaries[5] = sign_mask + 1'b1;

        if (W == 24) begin
            samples[0] = 0; samples[1] = 1;
            samples[2] = -1; samples[3] = -8388608;
            check;
            if (packed_out !== 128'hFF800000_FFFFFFFF_00000001_00000000)
                $fatal(1, "README example 1 failed");
            samples[0] = 8388607; samples[1] = -2;
            samples[2] = 2; samples[3] = 0;
            check;
            if (packed_out !== 128'h00000000_00000002_FFFFFFFE_007FFFFF)
                $fatal(1, "README example 2 failed");
            $display("COVER W=24 README examples=2 PASS");
        end

        baseline; check;
        for (channel = 0; channel < 4; channel = channel + 1) begin
            baseline; check;
            for (k = 0; k < 6; k = k + 1) begin
                before_out = packed_out;
                samples[channel] = boundaries[k];
                check_isolation(channel);
            end
        end
        $display("COVER W=%0d boundaries=24 channel_order isolation PASS", W);

        for (pattern = 0; pattern < 16; pattern = pattern + 1) begin
            for (channel = 0; channel < 4; channel = channel + 1) begin
                samples[channel] = channel;
                samples[channel][W-1] = (pattern >> channel) & 1;
            end
            check;
        end
        $display("COVER W=%0d sign_combinations=16 PASS", W);

        for (channel = 0; channel < 4; channel = channel + 1) begin
            baseline; check;
            for (bit_index = 0; bit_index < W; bit_index = bit_index + 1) begin
                before_out = packed_out;
                samples[channel] = 0;
                samples[channel][bit_index] = 1'b1;
                check_isolation(channel);
                before_out = packed_out;
                samples[channel] = {W{1'b1}};
                samples[channel][bit_index] = 1'b0;
                check_isolation(channel);
            end
        end
        $display("COVER W=%0d walking_one_zero=%0d combinational_updates PASS", W, 8*W);

        if (W == 2) begin
            for (a = 0; a < 4; a = a + 1)
                for (b = 0; b < 4; b = b + 1)
                    for (c = 0; c < 4; c = c + 1)
                        for (d = 0; d < 4; d = d + 1) begin
                            samples[0] = a; samples[1] = b;
                            samples[2] = c; samples[3] = d;
                            check;
                        end
            $display("COVER W=2 exhaustive=256 PASS");
        end
        if (W >= 16) begin
            $display("RANDOM W=%0d seed=%h groups=256", W, rng);
            for (k = 0; k < 256; k = k + 1) begin
                for (channel = 0; channel < 4; channel = channel + 1) begin
                    random_step;
                    samples[channel] = rng;
                end
                check;
            end
            $display("COVER W=%0d random=256 PASS", W);
        end
        $display("WIDTH PASS W=%0d comparisons=%0d time=%0t", W, comparisons, $time);
        done = 1;
    end
endmodule

module tb_pcm4_signext_pack;
    wire done2, done3, done16, done24, done32;
    pcm4_width_test #(.W(2)) test2(done2);
    pcm4_width_test #(.W(3)) test3(done3);
    pcm4_width_test #(.W(16)) test16(done16);
    pcm4_width_test test24(done24);
    pcm4_width_test #(.W(32)) test32(done32);
    initial begin
        wait (done2 && done3 && done16 && done24 && done32);
        $display("ALL TESTS PASS time=%0t", $time);
        $finish;
    end
    initial begin
        #100000;
        $fatal(1, "TIMEOUT: not all width tests completed");
    end
endmodule
