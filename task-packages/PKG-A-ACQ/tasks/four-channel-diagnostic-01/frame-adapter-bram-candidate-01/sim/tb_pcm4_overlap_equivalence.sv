`timescale 1ns/1ps
// Legal-input, handshake-sequence equivalence check against the frozen
// asynchronous-read candidate. Timing is intentionally allowed to differ.
module tb_pcm4_overlap_equivalence;
    reg clk=0; always #5 clk=~clk;
    reg rst_n=0;
    integer cycle=0;

    reg o_start_valid=0, o_stop_valid=0, o_s_valid=0;
    reg [31:0] o_start_session_id=0, o_s_flags=0, o_s_reserved=0;
    reg [63:0] o_s_id=0;
    reg [127:0] o_s_pcm=0;
    reg o_s_integrity_error=0;
    reg [7:0] o_s_error_flags=0;
    reg o_m_ready=0, o_e_ready=0;
    wire o_start_ready, o_stop_ready, o_s_ready, o_m_valid, o_e_valid;
    wire [127:0] o_m_pcm;
    wire [63:0] o_m_id, o_m_first_id, o_m_last_id, o_e_id, o_e_prev_id;
    wire [3:0] o_m_flags;
    wire [31:0] o_m_session_id, o_m_frame_index, o_m_interval_index;
    wire [9:0] o_m_sample_index;
    wire o_m_reset_before, o_m_last;
    wire [2:0] o_e_code;
    wire [31:0] o_e_session_id, o_e_raw_flags, o_e_interval_index;
    wire [7:0] o_e_source_flags;
    wire [10:0] o_e_unused_tail;

    reg n_start_valid=0, n_stop_valid=0, n_s_valid=0;
    reg [31:0] n_start_session_id=0, n_s_flags=0, n_s_reserved=0;
    reg [63:0] n_s_id=0;
    reg [127:0] n_s_pcm=0;
    reg n_s_integrity_error=0;
    reg [7:0] n_s_error_flags=0;
    reg n_m_ready=0, n_e_ready=0;
    wire n_start_ready, n_stop_ready, n_s_ready, n_m_valid, n_e_valid;
    wire [127:0] n_m_pcm;
    wire [63:0] n_m_id, n_m_first_id, n_m_last_id, n_e_id, n_e_prev_id;
    wire [3:0] n_m_flags;
    wire [31:0] n_m_session_id, n_m_frame_index, n_m_interval_index;
    wire [9:0] n_m_sample_index;
    wire n_m_reset_before, n_m_last;
    wire [2:0] n_e_code;
    wire [31:0] n_e_session_id, n_e_raw_flags, n_e_interval_index;
    wire [7:0] n_e_source_flags;
    wire [10:0] n_e_unused_tail;

    pcm4_overlap_framer frozen (
        .clk(clk), .rst_n(rst_n),
        .start_valid(o_start_valid), .start_ready(o_start_ready),
        .start_session_id(o_start_session_id),
        .stop_valid(o_stop_valid), .stop_ready(o_stop_ready),
        .s_valid(o_s_valid), .s_ready(o_s_ready), .s_id(o_s_id),
        .s_pcm(o_s_pcm), .s_flags(o_s_flags), .s_reserved(o_s_reserved),
        .s_integrity_error(o_s_integrity_error), .s_error_flags(o_s_error_flags),
        .m_valid(o_m_valid), .m_ready(o_m_ready), .m_pcm(o_m_pcm), .m_id(o_m_id),
        .m_flags(o_m_flags), .m_session_id(o_m_session_id),
        .m_frame_index(o_m_frame_index), .m_interval_index(o_m_interval_index),
        .m_sample_index(o_m_sample_index), .m_first_id(o_m_first_id),
        .m_last_id(o_m_last_id), .m_reset_before(o_m_reset_before), .m_last(o_m_last),
        .e_valid(o_e_valid), .e_ready(o_e_ready), .e_code(o_e_code),
        .e_session_id(o_e_session_id), .e_id(o_e_id), .e_prev_id(o_e_prev_id),
        .e_raw_flags(o_e_raw_flags), .e_source_flags(o_e_source_flags),
        .e_unused_tail(o_e_unused_tail), .e_interval_index(o_e_interval_index)
    );

    pcm4_overlap_framer_bram candidate (
        .clk(clk), .rst_n(rst_n),
        .start_valid(n_start_valid), .start_ready(n_start_ready),
        .start_session_id(n_start_session_id),
        .stop_valid(n_stop_valid), .stop_ready(n_stop_ready),
        .s_valid(n_s_valid), .s_ready(n_s_ready), .s_id(n_s_id),
        .s_pcm(n_s_pcm), .s_flags(n_s_flags), .s_reserved(n_s_reserved),
        .s_integrity_error(n_s_integrity_error), .s_error_flags(n_s_error_flags),
        .m_valid(n_m_valid), .m_ready(n_m_ready), .m_pcm(n_m_pcm), .m_id(n_m_id),
        .m_flags(n_m_flags), .m_session_id(n_m_session_id),
        .m_frame_index(n_m_frame_index), .m_interval_index(n_m_interval_index),
        .m_sample_index(n_m_sample_index), .m_first_id(n_m_first_id),
        .m_last_id(n_m_last_id), .m_reset_before(n_m_reset_before), .m_last(n_m_last),
        .e_valid(n_e_valid), .e_ready(n_e_ready), .e_code(n_e_code),
        .e_session_id(n_e_session_id), .e_id(n_e_id), .e_prev_id(n_e_prev_id),
        .e_raw_flags(n_e_raw_flags), .e_source_flags(n_e_source_flags),
        .e_unused_tail(n_e_unused_tail), .e_interval_index(n_e_interval_index)
    );

    reg [431:0] expected_output [0:4095];
    reg [245:0] expected_event [0:31];
    integer old_outputs=0, new_outputs=0, old_events=0, new_events=0;

    function automatic [127:0] pcm_for(input integer id);
        reg signed [31:0] c0,c1,c2,c3;
        begin
            c0=(id%101)-50; c1=1000+(id%137);
            c2=-2000-(id%103); c3=3000+(id%89);
            pcm_for={c3,c2,c1,c0};
        end
    endfunction

    task automatic fail(input string why);
        begin $display("FAIL equivalence cycle=%0d: %s",cycle,why); $fatal(1); end
    endtask

    always @(negedge clk) begin
        cycle=cycle+1;
        o_m_ready=((cycle%7)!=0 && (cycle%11)!=0);
        o_e_ready=((cycle%5)!=0);
        n_m_ready=((cycle%13)!=0 && (cycle%17)!=0);
        n_e_ready=((cycle%6)!=0);
        if (cycle>300000) fail("timeout");
    end

    always @(posedge clk) if (rst_n) begin : capture_and_compare
        reg [431:0] out_record;
        reg [245:0] event_record;
        if (o_m_valid && o_m_ready) begin
            expected_output[old_outputs]={o_m_pcm,o_m_id,o_m_flags,o_m_session_id,
                o_m_frame_index,o_m_interval_index,o_m_sample_index,o_m_first_id,
                o_m_last_id,o_m_reset_before,o_m_last};
            old_outputs=old_outputs+1;
        end
        if (o_e_valid && o_e_ready) begin
            expected_event[old_events]={o_e_code,o_e_session_id,o_e_id,o_e_prev_id,
                o_e_raw_flags,o_e_source_flags,o_e_unused_tail,o_e_interval_index};
            old_events=old_events+1;
        end
        if (n_m_valid && n_m_ready) begin
            out_record={n_m_pcm,n_m_id,n_m_flags,n_m_session_id,
                n_m_frame_index,n_m_interval_index,n_m_sample_index,n_m_first_id,
                n_m_last_id,n_m_reset_before,n_m_last};
            if (new_outputs>=old_outputs) fail("candidate produced an extra output");
            if (out_record!==expected_output[new_outputs]) fail("output sequence differs from frozen candidate");
            new_outputs=new_outputs+1;
        end
        if (n_e_valid && n_e_ready) begin
            event_record={n_e_code,n_e_session_id,n_e_id,n_e_prev_id,
                n_e_raw_flags,n_e_source_flags,n_e_unused_tail,n_e_interval_index};
            if (new_events>=old_events) fail("candidate produced an extra event");
            if (event_record!==expected_event[new_events]) fail("event sequence differs from frozen candidate");
            new_events=new_events+1;
        end
    end

    task automatic start_old;
        begin
            @(negedge clk); while (!o_start_ready) @(negedge clk);
            o_start_session_id=32'd77; o_start_valid=1;
            @(negedge clk); o_start_valid=0;
        end
    endtask
    task automatic start_new;
        begin
            @(negedge clk); while (!n_start_ready) @(negedge clk);
            n_start_session_id=32'd77; n_start_valid=1;
            @(negedge clk); n_start_valid=0;
        end
    endtask
    task automatic push_old(input integer id);
        begin
            @(negedge clk); o_s_id=id; o_s_pcm=pcm_for(id);
            o_s_flags=id%16; o_s_reserved=0; o_s_valid=1;
            do @(posedge clk); while (!o_s_ready);
            @(negedge clk); o_s_valid=0;
        end
    endtask
    task automatic push_new(input integer id);
        begin
            @(negedge clk); n_s_id=id; n_s_pcm=pcm_for(id);
            n_s_flags=id%16; n_s_reserved=0; n_s_valid=1;
            do @(posedge clk); while (!n_s_ready);
            @(negedge clk); n_s_valid=0;
        end
    endtask
    task automatic stop_old;
        begin
            @(negedge clk); o_stop_valid=1;
            do @(posedge clk); while (!o_stop_ready);
            @(negedge clk); o_stop_valid=0;
            while (!o_start_ready) @(negedge clk);
        end
    endtask
    task automatic stop_new;
        begin
            @(negedge clk); n_stop_valid=1;
            do @(posedge clk); while (!n_stop_ready);
            @(negedge clk); n_stop_valid=0;
            while (!n_start_ready) @(negedge clk);
        end
    endtask

    integer i;
    initial begin
        repeat(5) @(negedge clk); rst_n=1;
        start_old();
        for (i=40000;i<42500;i=i+1) push_old(i);
        stop_old();
        if (old_outputs!=3072 || old_events!=1) fail("frozen reference count is unexpected");

        start_new();
        for (i=40000;i<42500;i=i+1) push_new(i);
        stop_new();
        repeat(10) @(negedge clk);
        if (new_outputs!=old_outputs || new_events!=old_events) fail("final sequence counts differ");
        $display("PASS BRAM_EQUIVALENCE outputs=%0d events=%0d; legal-input handshake sequence matches frozen candidate",new_outputs,new_events);
        $finish;
    end
endmodule
