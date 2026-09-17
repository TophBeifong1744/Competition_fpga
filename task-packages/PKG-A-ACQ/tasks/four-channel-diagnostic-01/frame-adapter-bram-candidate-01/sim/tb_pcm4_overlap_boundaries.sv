`timescale 1ns/1ps
module tb_pcm4_overlap_boundaries;
    reg clk=0; always #5 clk=~clk;
    reg rst_n=0, start_valid=0, stop_valid=0, s_valid=0;
    reg [31:0] start_session_id=0, s_flags=0, s_reserved=0;
    reg [63:0] s_id=0;
    reg [127:0] s_pcm=0;
    reg s_integrity_error=0;
    reg [7:0] s_error_flags=0;
    reg m_ready=0, e_ready=0;
    wire start_ready, stop_ready, s_ready, m_valid, e_valid, m_reset_before, m_last;
    wire [127:0] m_pcm;
    wire [63:0] m_id, m_first_id, m_last_id, e_id, e_prev_id;
    wire [3:0] m_flags;
    wire [31:0] m_session_id, m_frame_index, m_interval_index;
    wire [9:0] m_sample_index;
    wire [2:0] e_code;
    wire [31:0] e_session_id, e_raw_flags, e_interval_index;
    wire [7:0] e_source_flags;
    wire [10:0] e_unused_tail;

    pcm4_overlap_framer_bram dut(.*);

    integer cycle=0, active_base=0, expected_frames=0;
    integer session_outputs=0, session_events=0;

    function automatic [127:0] pcm_for(input integer id);
        reg signed [31:0] c0,c1,c2,c3;
        begin
            c0=(id%101)-50; c1=1000+(id%137);
            c2=-2000-(id%103); c3=3000+(id%89);
            pcm_for={c3,c2,c1,c0};
        end
    endfunction

    task automatic fail(input string why);
        begin $display("FAIL boundary cycle=%0d session=%0d: %s",cycle,start_session_id,why); $fatal(1); end
    endtask

    always @(negedge clk) begin
        cycle=cycle+1;
        m_ready=((cycle%7)!=0 && (cycle%11)!=0);
        e_ready=((cycle%5)!=0);
        if (cycle>500000) fail("timeout");
    end

    always @(posedge clk) if (rst_n) begin : monitor
        integer frame_no, sample_no, expected_id;
        if (m_valid && m_ready) begin
            frame_no=session_outputs/1024;
            sample_no=session_outputs%1024;
            expected_id=active_base+frame_no*512+sample_no;
            if (frame_no>=expected_frames) fail("unexpected extra frame");
            if (m_session_id!==start_session_id || m_frame_index!==frame_no ||
                m_interval_index!==0 || m_sample_index!==sample_no)
                fail("metadata mismatch");
            if (m_id!==expected_id || m_first_id!==(active_base+frame_no*512) ||
                m_last_id!==(active_base+frame_no*512+1023)) fail("ID mismatch");
            if (m_pcm!==pcm_for(expected_id) || m_flags!==(expected_id%16))
                fail("payload mismatch or stale BRAM content leaked");
            if (m_reset_before!==(frame_no==0) || m_last!==(sample_no==1023))
                fail("frame boundary metadata mismatch");
            session_outputs=session_outputs+1;
        end
        if (e_valid && e_ready) session_events=session_events+1;
    end

    task automatic run_case(input integer count, input integer sid,
                            input integer frames, input integer expected_tail);
        integer i, base;
        begin
            base=sid*100000;
            active_base=base; expected_frames=frames;
            session_outputs=0; session_events=0;
            @(negedge clk); while (!start_ready) @(negedge clk);
            start_session_id=sid; start_valid=1;
            @(negedge clk); start_valid=0;
            for (i=0;i<count;i=i+1) begin
                @(negedge clk); s_id=base+i; s_pcm=pcm_for(base+i);
                s_flags=(base+i)%16; s_reserved=0; s_valid=1;
                do @(posedge clk); while (!s_ready);
                @(negedge clk); s_valid=0;
            end
            @(negedge clk); stop_valid=1;
            do @(posedge clk); while (!stop_ready);
            @(negedge clk); stop_valid=0;
            while (!e_valid) @(negedge clk);
            if (e_code!==1 || e_session_id!==sid || e_unused_tail!==expected_tail ||
                e_interval_index!==0) fail("stop event mismatch");
            while (!start_ready) @(negedge clk);
            if (session_outputs!=frames*1024 || session_events!=1)
                fail("frame or event count mismatch");
            $display("BOUNDARY_PASS groups=%0d frames=%0d tail=%0d",count,frames,expected_tail);
        end
    endtask

    initial begin
        repeat(5) @(negedge clk); rst_n=1;
        run_case(0,     1, 0,    0);
        run_case(1023,  2, 0, 1023);
        run_case(1024,  3, 1,    0);
        run_case(1535,  4, 1,  511);
        run_case(1536,  5, 2,    0);
        run_case(2048,  6, 3,    0);
        $display("PASS BRAM_BOUNDARIES cases=6 groups=0,1023,1024,1535,1536,2048");
        $finish;
    end
endmodule
