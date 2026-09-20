`timescale 1ns/1ps
// Isolated BRAM-friendly candidate. Input is one already-validated four-mic group.
// The source MUST be backpressure-capable (for example a DDR reader), never raw PDM/CIC.
module pcm4_overlap_framer_bram (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start_valid,
    output wire         start_ready,
    input  wire [31:0]  start_session_id,
    input  wire         stop_valid,
    output wire         stop_ready,
    input  wire         s_valid,
    output wire         s_ready,
    input  wire [63:0]  s_id,
    input  wire [127:0] s_pcm,       // {mic3,mic2,mic1,mic0}, signed24 extended to int32
    input  wire [31:0]  s_flags,     // [3:0] clip indicators; all other bits forbidden
    input  wire [31:0]  s_reserved,
    input  wire         s_integrity_error,
    input  wire [7:0]   s_error_flags,
    output wire         m_valid,
    input  wire         m_ready,
    output wire [127:0] m_pcm,
    output wire [63:0]  m_id,
    output wire [3:0]   m_flags,
    output wire [31:0]  m_session_id,
    output wire [31:0]  m_frame_index,
    output wire [31:0]  m_interval_index,
    output wire [9:0]   m_sample_index,
    output wire [63:0]  m_first_id,
    output wire [63:0]  m_last_id,
    output wire         m_reset_before,
    output wire         m_last,
    output reg          e_valid,
    input  wire         e_ready,
    output reg  [2:0]   e_code,
    output reg  [31:0]  e_session_id,
    output reg  [63:0]  e_id,
    output reg  [63:0]  e_prev_id,
    output reg  [31:0]  e_raw_flags,
    output reg  [7:0]   e_source_flags,
    output reg  [10:0]  e_unused_tail,
    output reg  [31:0]  e_interval_index
);
    localparam [2:0] E_STOP=3'd1, E_UPSTREAM=3'd2, E_ID=3'd3,
                     E_FLAGS=3'd4, E_RANGE=3'd5;

    // No memory reset. One address is used per cycle; read data is synchronous.
    (* ram_style = "block" *) reg [195:0] groups [0:1023];
    reg [195:0] out_group;
    reg [9:0] wr_ptr, frame_start, fetch_ptr, out_index;
    reg [10:0] fill_count, new_count, fetch_count;
    reg [31:0] session_id, frame_index, interval_index;
    reg [63:0] last_input_id, frame_first_id, frame_last_id;
    reg active, emitting, stop_pending, have_prev, have_frame, reset_next;
    reg frame_reset, out_valid, first_pending;

    wire start_fire=start_valid && start_ready;
    wire stop_fire=stop_valid && stop_ready;
    wire s_fire=s_valid && s_ready;
    wire m_fire=m_valid && m_ready;
    wire bad_range=
        (s_pcm[31:24]   != {8{s_pcm[23]}})  ||
        (s_pcm[63:56]   != {8{s_pcm[55]}})  ||
        (s_pcm[95:88]   != {8{s_pcm[87]}})  ||
        (s_pcm[127:120] != {8{s_pcm[119]}});
    wire bad_id=have_prev &&
        (last_input_id==64'hffffffffffffffff || s_id!=last_input_id+64'd1);
    wire [2:0] input_issue=(s_integrity_error || s_error_flags!=0) ? E_UPSTREAM :
                           bad_id ? E_ID :
                           ((s_flags[31:4]!=0) || (s_reserved!=0)) ? E_FLAGS :
                           bad_range ? E_RANGE : 3'd0;
    wire ram_write=s_fire && input_issue==0;
    wire first_read=emitting && !out_valid && !first_pending && fetch_count==0;
    wire advance_read=emitting && out_valid && m_ready && fetch_count<11'd1024;
    wire ram_read=first_read || advance_read;

    assign start_ready=!active && !emitting && !stop_pending && !e_valid;
    assign stop_ready=active && !stop_pending && !e_valid;
    assign s_ready=active && !emitting && !stop_pending && !stop_valid &&
                   !e_valid && fill_count<11'd1024;
    assign m_valid=out_valid;
    assign m_pcm=out_group[127:0];
    assign m_id=out_group[191:128];
    assign m_flags=out_group[195:192];
    assign m_session_id=session_id;
    assign m_frame_index=frame_index;
    assign m_interval_index=interval_index;
    assign m_sample_index=out_index;
    assign m_first_id=frame_first_id;
    assign m_last_id=frame_last_id;
    assign m_reset_before=frame_reset;
    assign m_last=out_valid && out_index==10'd1023;

    always @(posedge clk) begin
        if (!rst_n) begin
            wr_ptr<=0; frame_start<=0; fetch_ptr<=0; out_index<=0;
            fill_count<=0; new_count<=0; fetch_count<=0;
            session_id<=0; frame_index<=0; interval_index<=0;
            last_input_id<=0; frame_first_id<=0; frame_last_id<=0;
            active<=0; emitting<=0; stop_pending<=0; have_prev<=0;
            have_frame<=0; reset_next<=1; frame_reset<=0;
            out_valid<=0; first_pending<=0;
            e_valid<=0; e_code<=0; e_session_id<=0; e_id<=0; e_prev_id<=0;
            e_raw_flags<=0; e_source_flags<=0; e_unused_tail<=0; e_interval_index<=0;
        end else begin
            // Single memory access per clock. The array itself is never reset.
            if (ram_write)
                groups[wr_ptr]<={s_flags[3:0],s_id,s_pcm};
            else if (ram_read)
                out_group<=groups[fetch_ptr];

            if (e_valid && e_ready) e_valid<=0;
            if (stop_fire) stop_pending<=1;

            if (start_fire) begin
                active<=1; stop_pending<=0; session_id<=start_session_id;
                frame_index<=0; interval_index<=0;
                wr_ptr<=0; frame_start<=0; fetch_ptr<=0; out_index<=0;
                fill_count<=0; new_count<=0; fetch_count<=0;
                have_prev<=0; have_frame<=0; reset_next<=1;
                emitting<=0; out_valid<=0; first_pending<=0;
            end else if (s_fire) begin
                if (input_issue!=0) begin
                    e_valid<=1; e_code<=input_issue; e_session_id<=session_id;
                    e_id<=s_id; e_prev_id<=have_prev ? last_input_id : 64'd0;
                    e_raw_flags<=s_flags; e_source_flags<=s_error_flags;
                    e_unused_tail<=have_frame ? new_count : fill_count;
                    e_interval_index<=interval_index;
                    interval_index<=interval_index+1'b1;
                    wr_ptr<=0; frame_start<=0; fetch_ptr<=0;
                    fill_count<=0; new_count<=0; fetch_count<=0;
                    have_prev<=0; have_frame<=0; reset_next<=1;
                    emitting<=0; out_valid<=0; first_pending<=0;
                end else begin
                    wr_ptr<=wr_ptr+1'b1;
                    fill_count<=fill_count+1'b1;
                    new_count<=new_count+1'b1;
                    last_input_id<=s_id; have_prev<=1;
                end
            end else if (!emitting && fill_count==11'd1024) begin
                emitting<=1; fetch_ptr<=frame_start; fetch_count<=0;
                out_index<=0; out_valid<=0; first_pending<=0;
                frame_last_id<=last_input_id; frame_reset<=reset_next;
            end else if (first_read) begin
                fetch_ptr<=fetch_ptr+1'b1;
                fetch_count<=11'd1;
                out_index<=0;
                first_pending<=1;
            end else if (first_pending) begin
                frame_first_id<=out_group[191:128];
                first_pending<=0;
                out_valid<=1;
            end else if (advance_read) begin
                fetch_ptr<=fetch_ptr+1'b1;
                out_index<=fetch_count[9:0];
                fetch_count<=fetch_count+1'b1;
                out_valid<=1;
            end else if (m_fire) begin
                if (out_index==10'd1023) begin
                    emitting<=0; out_valid<=0; first_pending<=0;
                    frame_index<=frame_index+1'b1;
                    frame_start<=frame_start+10'd512;
                    fill_count<=11'd512; new_count<=0;
                    have_frame<=1; reset_next<=0;
                end else begin
                    // Defensive only: normal non-tail handshakes also issue the next read.
                    out_valid<=0;
                end
            end else if (stop_pending && !emitting && !e_valid) begin
                e_valid<=1; e_code<=E_STOP; e_session_id<=session_id;
                e_id<=have_prev ? last_input_id : 64'd0;
                e_prev_id<=have_prev ? last_input_id : 64'd0;
                e_raw_flags<=0; e_source_flags<=0;
                e_unused_tail<=have_frame ? new_count : fill_count;
                e_interval_index<=interval_index;
                active<=0; stop_pending<=0;
                fill_count<=0; new_count<=0; fetch_count<=0;
                have_prev<=0; have_frame<=0;
                out_valid<=0; first_pending<=0;
            end
        end
    end
endmodule
