`timescale 1ns/1ps
module tb_pcm4_overlap_framer_bram;
    reg clk=0; always #5 clk=~clk;
    reg rst_n=0, start_valid=0, stop_valid=0, s_valid=0;
    reg [31:0] start_session_id=0, s_flags=0, s_reserved=0;
    reg [63:0] s_id=0;
    reg [127:0] s_pcm=0;
    reg s_integrity_error=0;
    reg [7:0] s_error_flags=0;
    reg m_ready=0, e_ready=0, force_ready=0;
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

    integer cycle=0, frame_number=0, event_number=0, accepted=0;
    integer first_out_cycle=-1, last_out_cycle=-1;
    integer pause_start=-1, pause_cycles=-1;
    reg perf_watch=0, previous_ready=0;
    reg stalled=0, event_stalled=0;
    reg [431:0] stalled_bus;
    reg [245:0] stalled_event;

    function automatic [127:0] pcm_for(input integer id);
        reg [31:0] c0,c1,c2,c3;
        begin
            c0=(id%101)-50; c1=1000+(id%137);
            c2=-2000-(id%103); c3=3000+(id%89);
            pcm_for={c3,c2,c1,c0};
        end
    endfunction

    task automatic fail(input string why);
        begin $display("FAIL cycle=%0d frame=%0d event=%0d: %s",cycle,frame_number,event_number,why); $fatal(1); end
    endtask

    always @(negedge clk) begin
        cycle=cycle+1;
        m_ready=force_ready ? 1'b1 : ((cycle%7)!=0 && (cycle%11)!=0);
        e_ready=((cycle%5)!=0);
        if (perf_watch) begin
            if (previous_ready && !s_ready && pause_start<0) pause_start=cycle;
            if (!previous_ready && s_ready && pause_start>=0 && pause_cycles<0)
                pause_cycles=cycle-pause_start;
        end
        previous_ready=s_ready;
        if (cycle>500000) fail("timeout");
    end

    always @(posedge clk) if (rst_n) begin : monitor
        integer first_id, expected_sess, expected_index, expected_interval;
        integer expected_flags;
        reg expected_reset;
        reg [431:0] output_bus;
        reg [245:0] event_bus;
        output_bus={m_pcm,m_id,m_flags,m_session_id,m_frame_index,
                    m_interval_index,m_sample_index,m_first_id,m_last_id,
                    m_reset_before,m_last};
        event_bus={e_code,e_session_id,e_id,e_prev_id,e_raw_flags,
                   e_source_flags,e_unused_tail,e_interval_index};
        if (stalled && (!m_valid || output_bus!==stalled_bus)) fail("output changed under backpressure");
        stalled=m_valid && !m_ready;
        if (stalled) stalled_bus=output_bus;
        if (event_stalled && (!e_valid || event_bus!==stalled_event)) fail("event changed under backpressure");
        event_stalled=e_valid && !e_ready;
        if (event_stalled) stalled_event=event_bus;

        if (m_valid && m_ready) begin
            case(frame_number)
                0: begin first_id=0; expected_sess=11; expected_index=0; expected_interval=0; expected_reset=1; expected_flags=-1; end
                1: begin first_id=512; expected_sess=11; expected_index=1; expected_interval=0; expected_reset=0; expected_flags=-1; end
                2: begin first_id=5000; expected_sess=22; expected_index=0; expected_interval=0; expected_reset=1; expected_flags=0; end
                3: begin first_id=20000; expected_sess=33; expected_index=0; expected_interval=6; expected_reset=1; expected_flags=0; end
                4: begin first_id=30000; expected_sess=44; expected_index=0; expected_interval=0; expected_reset=1; expected_flags=0; end
                default: fail("unexpected extra frame");
            endcase
            if (m_session_id!==expected_sess || m_frame_index!==expected_index ||
                m_interval_index!==expected_interval || m_reset_before!==expected_reset)
                fail("frame metadata mismatch");
            if (m_sample_index!==accepted || m_id!==(first_id+accepted) ||
                m_first_id!==first_id || m_last_id!==(first_id+1023)) fail("ID/order mismatch");
            if (m_pcm!==pcm_for(first_id+accepted)) fail("channel data mismatch or old RAM leaked");
            if (m_flags!==((expected_flags<0) ? ((first_id+accepted)%16) : expected_flags))
                fail("clip flags mismatch");
            if (m_last!==(accepted==1023)) fail("m_last is not tied to accepted sample 1024");
            if (expected_sess==44 && accepted==0) first_out_cycle=cycle;
            if (expected_sess==44 && accepted==1023) last_out_cycle=cycle;
            if (accepted==1023) begin accepted=0; frame_number=frame_number+1; end
            else accepted=accepted+1;
        end

        if (e_valid && e_ready) begin
            case(event_number)
                0: if (e_code!==1 || e_session_id!==11 || e_id!==1749 || e_unused_tail!==214 || e_interval_index!==0)
                       fail("session 11 stop event mismatch");
                1: if (e_code!==1 || e_session_id!==22 || e_id!==6023 || e_unused_tail!==0 || e_interval_index!==0)
                       fail("full-frame immediate stop did not drain first");
                2: if (e_code!==2 || e_session_id!==33 || e_id!==10010 || e_prev_id!==10009 || e_source_flags!==8'hA1 || e_unused_tail!==10 || e_interval_index!==0)
                       fail("upstream-bit event mismatch");
                3: if (e_code!==2 || e_id!==11010 || e_prev_id!==11009 || e_source_flags!==8'h04 || e_unused_tail!==10 || e_interval_index!==1)
                       fail("source-flags-only event mismatch");
                4: if (e_code!==3 || e_id!==12011 || e_prev_id!==12009 || e_unused_tail!==10 || e_interval_index!==2)
                       fail("ID gap event mismatch");
                5: if (e_code!==4 || e_id!==13010 || e_raw_flags!==32'h10 || e_unused_tail!==10 || e_interval_index!==3)
                       fail("illegal flags event mismatch");
                6: if (e_code!==4 || e_id!==14010 || e_raw_flags!==0 || e_unused_tail!==10 || e_interval_index!==4)
                       fail("reserved event mismatch");
                7: if (e_code!==5 || e_id!==15010 || e_unused_tail!==10 || e_interval_index!==5)
                       fail("signed24 range event mismatch");
                8: if (e_code!==1 || e_session_id!==33 || e_id!==21023 || e_unused_tail!==0 || e_interval_index!==6)
                       fail("session 33 stop event mismatch");
                9: if (e_code!==1 || e_session_id!==44 || e_id!==31023 || e_unused_tail!==0 || e_interval_index!==0)
                       fail("session 44 stop event mismatch");
                default: fail("unexpected extra event");
            endcase
            event_number=event_number+1;
        end
    end

    task automatic start_session(input [31:0] sid);
        begin
            @(negedge clk); while (!start_ready) @(negedge clk);
            start_session_id=sid; start_valid=1;
            @(negedge clk); start_valid=0;
        end
    endtask

    task automatic push_group(input integer id, input [31:0] flags,
                              input [31:0] reserved, input fault,
                              input [7:0] source, input bad_pcm);
        begin
            @(negedge clk);
            s_id=id; s_pcm=pcm_for(id); s_flags=flags; s_reserved=reserved;
            if (bad_pcm) s_pcm[31:0]=32'h00800000;
            s_integrity_error=fault; s_error_flags=source; s_valid=1;
            do @(posedge clk); while (!s_ready);
            @(negedge clk); s_valid=0;
        end
    endtask

    task automatic push_last_and_stop(input integer id);
        begin
            @(negedge clk);
            s_id=id; s_pcm=pcm_for(id); s_flags=0; s_reserved=0;
            s_integrity_error=0; s_error_flags=0; s_valid=1;
            do @(posedge clk); while (!s_ready);
            @(negedge clk); s_valid=0; stop_valid=1;
            do @(posedge clk); while (!stop_ready);
            @(negedge clk); stop_valid=0;
            while (!start_ready) @(negedge clk);
        end
    endtask

    task automatic request_stop;
        begin
            @(negedge clk); stop_valid=1;
            do @(posedge clk); while (!stop_ready);
            @(negedge clk); stop_valid=0;
            while (!start_ready) @(negedge clk);
        end
    endtask

    integer i;
    initial begin
        repeat(5) @(negedge clk); rst_n=1;
        start_session(11);
        for (i=0; i<1750; i=i+1) push_group(i,i%16,0,0,0,0);
        request_stop();

        start_session(22);
        for (i=5000; i<6023; i=i+1) push_group(i,0,0,0,0,0);
        push_last_and_stop(6023);

        start_session(33);
        for (i=10000; i<10010; i=i+1) push_group(i,0,0,0,0,0);
        push_group(10010,0,0,1,8'hA1,0);
        for (i=11000; i<11010; i=i+1) push_group(i,0,0,0,0,0);
        push_group(11010,0,0,0,8'h04,0);
        for (i=12000; i<12010; i=i+1) push_group(i,0,0,0,0,0);
        push_group(12011,0,0,0,0,0);
        for (i=13000; i<13010; i=i+1) push_group(i,0,0,0,0,0);
        push_group(13010,32'h10,0,0,0,0);
        for (i=14000; i<14010; i=i+1) push_group(i,0,0,0,0,0);
        push_group(14010,0,1,0,0,0);
        for (i=15000; i<15010; i=i+1) push_group(i,0,0,0,0,0);
        push_group(15010,0,0,0,0,1);
        for (i=20000; i<21024; i=i+1) push_group(i,0,0,0,0,0);
        request_stop();

        force_ready=1;
        start_session(44);
        for (i=30000; i<31024; i=i+1) begin
            if (i==31023) perf_watch=1;
            push_group(i,0,0,0,0,0);
        end
        while (pause_cycles<0 || last_out_cycle<0) @(negedge clk);
        request_stop();
        repeat(15) @(negedge clk);
        if (frame_number!=5 || event_number!=10 || accepted!=0) fail("missing output or event");
        if (last_out_cycle-first_out_cycle+1!=1024) fail("continuous-ready frame was not 1024 consecutive handshake cycles");
        if (pause_cycles!=1027) fail("unexpected synchronous-read input pause length");
        $display("PERF ready=1 output_handshake_span=1024 input_pause_cycles=%0d",pause_cycles);
        $display("PASS BRAM_FRAMER frames=%0d events=%0d; sync-prefetch, overlap, random backpressure, immediate-stop drain, errors, restart isolation",frame_number,event_number);
        $finish;
    end
endmodule
