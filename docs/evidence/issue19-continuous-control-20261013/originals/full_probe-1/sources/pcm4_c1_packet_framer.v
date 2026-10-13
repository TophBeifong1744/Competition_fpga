`timescale 1ns/1ps
// Private diagnostic slice. The source must support backpressure and must
// restore a genuine packet boundary before starting another session.
// No RUN/ABI coupling to the non-pausable C1 acquisition source is provided.
module pcm4_c1_packet_framer (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start_valid,
    output wire         start_ready,
    input  wire [31:0]  start_session_id,
    input  wire         stop_valid,
    output wire         stop_ready,
    input  wire         s_axis_tvalid,
    output wire         s_axis_tready,
    input  wire [31:0]  s_axis_tdata,
    input  wire [3:0]   s_axis_tkeep,
    input  wire         s_axis_tlast,
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
    output wire         session_active,
    output reg          closing,
    output reg          fault_latched,
    output reg          e_valid,
    input  wire         e_ready,
    output reg  [7:0]   e_code,
    output reg  [31:0]  e_session_id,
    output reg  [63:0]  e_id,
    output reg  [63:0]  e_prev_id,
    output reg          e_id_valid,
    output reg          e_prev_id_valid,
    output reg  [31:0]  e_raw_flags,
    output reg  [7:0]   e_source_flags,
    output reg  [10:0]  e_unused_tail,
    output reg  [31:0]  e_interval_index,
    output reg  [31:0]  e_packet_index,
    output reg  [10:0]  e_word_index,
    output reg  [10:0]  e_packet_words,
    output reg  [31:0]  e_tdata,
    output reg  [3:0]   e_tkeep,
    output reg          e_tlast,
    output reg  [7:0]   e_drop_buffered_groups,
    output reg  [7:0]   e_drop_verified_groups,
    output reg  [2:0]   e_framer_code,
    output reg  [10:0]  e_framer_error_tail,
    output reg          e_stop_truncated
);
    localparam [7:0] E_CLEAN_STOP       = 8'd1,
                     E_STOP_TRUNCATED   = 8'd2,
                     E_BAD_TKEEP        = 8'd3,
                     E_EARLY_TLAST      = 8'd4,
                     E_MISSING_TLAST    = 8'd5,
                     E_BAD_PCM          = 8'd6,
                     E_BAD_FLAGS        = 8'd7,
                     E_BAD_RESERVED     = 8'd8,
                     E_ID_DISCONTINUITY = 8'd9,
                     E_FRAMER_FAULT     = 8'd10;
    localparam [2:0] ST_IDLE       = 3'd0,
                     ST_CAPTURE    = 3'd1,
                     ST_REPLAY     = 3'd2,
                     ST_REPLAY_END = 3'd3,
                     ST_STOP_REQ   = 3'd4,
                     ST_WAIT_STOP  = 3'd5,
                     ST_EVENT      = 3'd6;
    localparam [2:0] F_E_STOP = 3'd1;

    // CAPTURE writes and REPLAY reads are mutually exclusive. No RAM reset.
    (* ram_style = "block" *) reg [195:0] packet_ram [0:249];
    reg [195:0] assembly;
    reg [195:0] holding;
    reg [2:0] state;
    reg [10:0] packet_word;
    reg [7:0] packet_groups;
    reg [31:0] packet_index;
    reg assembly_id_valid;
    reg [63:0] previous_id;
    reg previous_id_valid;
    // Next synchronous read address, including the exhausted sentinel 250.
    reg [8:0] replay_read_addr;
    reg holding_valid;
    reg [7:0] last_replay_index;
    reg last_replay_valid;
    reg framer_have_previous;
    reg last_replay_had_previous;

    wire f_start_ready;
    wire f_stop_ready;
    wire f_s_ready;
    wire f_e_valid;
    wire [2:0] f_e_code;
    wire [31:0] f_e_session_id;
    wire [63:0] f_e_id;
    wire [63:0] f_e_prev_id;
    wire [31:0] f_e_raw_flags;
    wire [7:0] f_e_source_flags;
    wire [10:0] f_e_unused_tail;
    wire [31:0] f_e_interval_index;

    wire start_fire = start_valid && start_ready;
    wire stop_fire = stop_valid && stop_ready;
    wire axis_fire = s_axis_tvalid && s_axis_tready;
    wire f_stop_valid = rst_n && state == ST_STOP_REQ;
    wire f_stop_fire = f_stop_valid && f_stop_ready;
    // An observed internal event stops the next group on that very edge.
    // Closing for an ordinary stop still allows the validated packet to drain.
    wire f_s_valid = rst_n && state == ST_REPLAY && holding_valid &&
                     !fault_latched && !f_e_valid;
    wire replay_fire = f_s_valid && f_s_ready;
    wire f_e_ready = rst_n &&
        ((f_e_code != F_E_STOP && state != ST_IDLE && state != ST_EVENT) ||
         (f_e_code == F_E_STOP && state == ST_WAIT_STOP));
    wire f_event_fire = f_e_valid && f_e_ready;
    wire replay_read = rst_n && state == ST_REPLAY && !fault_latched &&
                       !f_e_valid && (!holding_valid || replay_fire) &&
                       replay_read_addr < 9'd250;
    wire [8:0] held_index = replay_read_addr - 9'd1;
    wire [8:0] verified_drop = last_replay_valid ?
        (9'd250 - {1'b0, last_replay_index}) : 9'd250;

    assign session_active = state != ST_IDLE;
    assign start_ready = rst_n && state == ST_IDLE && f_start_ready;
    assign stop_ready = rst_n && !closing && !fault_latched &&
        (state == ST_CAPTURE || state == ST_REPLAY || state == ST_REPLAY_END);
    assign s_axis_tready = rst_n && state == ST_CAPTURE && !closing &&
                          !fault_latched && !stop_valid && !f_e_valid;

    wire [2:0] word_in_group = packet_word[2:0];
    wire [63:0] incoming_id = {s_axis_tdata, assembly[159:128]};
    wire discontinuous_id = previous_id_valid &&
        (previous_id == 64'hffffffffffffffff ||
         incoming_id != previous_id + 64'd1);
    wire bad_pcm = s_axis_tdata[31:24] != {8{s_axis_tdata[23]}};
    reg [7:0] field_issue;
    always @* begin
        field_issue = 8'd0;
        case (word_in_group)
            3'd1: if (discontinuous_id) field_issue = E_ID_DISCONTINUITY;
            3'd2, 3'd3, 3'd4, 3'd5:
                if (bad_pcm) field_issue = E_BAD_PCM;
            3'd6: if (s_axis_tdata[31:4] != 28'd0) field_issue = E_BAD_FLAGS;
            3'd7: if (s_axis_tdata != 32'd0) field_issue = E_BAD_RESERVED;
            default: field_issue = 8'd0;
        endcase
    end
    // Fixed same-edge first-error priority; never count a non-handshake beat.
    wire [7:0] input_issue = s_axis_tkeep != 4'hf ? E_BAD_TKEEP :
        (packet_word != 11'd1999 && s_axis_tlast) ? E_EARLY_TLAST :
        (packet_word == 11'd1999 && !s_axis_tlast) ? E_MISSING_TLAST :
        field_issue;
    // Word0 starts a fresh identity. A complete, correctly kept word1 can
    // locate its own error; a bad ID word cannot reuse stale assembly bits.
    wire issue_id_valid = word_in_group == 3'd0 ? 1'b0 :
        word_in_group == 3'd1 ? (s_axis_tkeep == 4'hf) : assembly_id_valid;
    wire [63:0] issue_id = !issue_id_valid ? 64'd0 :
        word_in_group == 3'd1 ? incoming_id : assembly[191:128];
    wire packet_write = axis_fire && input_issue == 8'd0 &&
                        word_in_group == 3'd7;

    pcm4_overlap_framer_bram u_framer (
        .clk(clk), .rst_n(rst_n),
        .start_valid(rst_n && state == ST_IDLE && start_valid),
        .start_ready(f_start_ready), .start_session_id(start_session_id),
        .stop_valid(f_stop_valid), .stop_ready(f_stop_ready),
        .s_valid(f_s_valid), .s_ready(f_s_ready),
        .s_id(holding[191:128]), .s_pcm(holding[127:0]),
        .s_flags({28'd0, holding[195:192]}), .s_reserved(32'd0),
        .s_integrity_error(1'b0), .s_error_flags(8'd0),
        .m_valid(m_valid), .m_ready(m_ready), .m_pcm(m_pcm), .m_id(m_id),
        .m_flags(m_flags), .m_session_id(m_session_id),
        .m_frame_index(m_frame_index), .m_interval_index(m_interval_index),
        .m_sample_index(m_sample_index), .m_first_id(m_first_id),
        .m_last_id(m_last_id), .m_reset_before(m_reset_before), .m_last(m_last),
        .e_valid(f_e_valid), .e_ready(f_e_ready), .e_code(f_e_code),
        .e_session_id(f_e_session_id), .e_id(f_e_id), .e_prev_id(f_e_prev_id),
        .e_raw_flags(f_e_raw_flags), .e_source_flags(f_e_source_flags),
        .e_unused_tail(f_e_unused_tail), .e_interval_index(f_e_interval_index)
    );

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            closing <= 1'b0; fault_latched <= 1'b0;
            packet_word <= 11'd0; packet_groups <= 8'd0; packet_index <= 32'd0;
            assembly <= 196'd0; assembly_id_valid <= 1'b0;
            previous_id <= 64'd0; previous_id_valid <= 1'b0;
            replay_read_addr <= 9'd0; holding_valid <= 1'b0;
            last_replay_index <= 8'd0; last_replay_valid <= 1'b0;
            framer_have_previous <= 1'b0; last_replay_had_previous <= 1'b0;
            e_valid <= 1'b0; e_code <= 8'd0; e_session_id <= 32'd0;
            e_id <= 64'd0; e_prev_id <= 64'd0;
            e_id_valid <= 1'b0; e_prev_id_valid <= 1'b0;
            e_raw_flags <= 32'd0; e_source_flags <= 8'd0;
            e_unused_tail <= 11'd0; e_interval_index <= 32'd0;
            e_packet_index <= 32'd0; e_word_index <= 11'd0;
            e_packet_words <= 11'd0; e_tdata <= 32'd0;
            e_tkeep <= 4'd0; e_tlast <= 1'b0;
            e_drop_buffered_groups <= 8'd0; e_drop_verified_groups <= 8'd0;
            e_framer_code <= 3'd0; e_framer_error_tail <= 11'd0;
            e_stop_truncated <= 1'b0;
        end else begin
            // One synchronous memory access. Valid, not stale RAM bytes,
            // controls visibility after reset, a bad packet, or a new session.
            if (packet_write)
                packet_ram[packet_groups] <= assembly;
            else if (replay_read)
                holding <= packet_ram[replay_read_addr];

            if (replay_read) begin
                replay_read_addr <= replay_read_addr + 9'd1;
                holding_valid <= 1'b1;
            end else if (replay_fire) begin
                holding_valid <= 1'b0;
            end
            if (replay_fire) begin
                last_replay_index <= held_index[7:0];
                last_replay_valid <= 1'b1;
                last_replay_had_previous <= framer_have_previous;
                framer_have_previous <= 1'b1;
            end

            // An internal error is acknowledged and captured before sending
            // stop. The legacy framer cannot open another interval here.
            if (f_event_fire && f_e_code != F_E_STOP) begin
                state <= ST_STOP_REQ;
                closing <= 1'b1; fault_latched <= 1'b1;
                holding_valid <= 1'b0;
                assembly_id_valid <= 1'b0;
                packet_word <= 11'd0; packet_groups <= 8'd0;
                if (!fault_latched) begin
                    e_code <= E_FRAMER_FAULT;
                    e_id <= last_replay_valid ? f_e_id : 64'd0;
                    e_id_valid <= last_replay_valid;
                    e_prev_id <= (last_replay_valid && last_replay_had_previous) ?
                                 f_e_prev_id : 64'd0;
                    e_prev_id_valid <= last_replay_valid && last_replay_had_previous;
                    e_raw_flags <= f_e_raw_flags;
                    e_source_flags <= f_e_source_flags;
                    e_interval_index <= f_e_interval_index;
                    e_packet_index <= packet_index;
                    e_word_index <= 11'd0; e_packet_words <= 11'd0;
                    e_tdata <= 32'd0; e_tkeep <= 4'd0; e_tlast <= 1'b0;
                    e_drop_buffered_groups <= 8'd0;
                    e_drop_verified_groups <= verified_drop[7:0];
                    e_framer_code <= f_e_code;
                    e_framer_error_tail <= f_e_unused_tail;
                    e_stop_truncated <= 1'b0;
                end
            end else if (f_event_fire && f_e_code == F_E_STOP) begin
                // Only WAIT_STOP accepts this final legacy event. Preserve
                // the first error interval and all first-error details.
                e_unused_tail <= f_e_unused_tail;
                if (e_code != E_FRAMER_FAULT)
                    e_interval_index <= f_e_interval_index;
                e_valid <= 1'b1;
                state <= ST_EVENT;
            end else begin
                // Ordinary control stop may be upgraded by a later real
                // framer fault, but can never overwrite a locked true error.
                if (stop_fire) begin
                    closing <= 1'b1;
                    e_code <= (state == ST_CAPTURE && packet_word != 11'd0) ?
                              E_STOP_TRUNCATED : E_CLEAN_STOP;
                    e_id <= 64'd0; e_id_valid <= 1'b0;
                    e_prev_id <= previous_id_valid ? previous_id : 64'd0;
                    e_prev_id_valid <= previous_id_valid;
                    e_raw_flags <= 32'd0; e_source_flags <= 8'd0;
                    e_packet_index <= packet_index;
                    e_word_index <= state == ST_CAPTURE ? packet_word : 11'd0;
                    e_packet_words <= state == ST_CAPTURE ? packet_word : 11'd0;
                    e_tdata <= 32'd0; e_tkeep <= 4'd0; e_tlast <= 1'b0;
                    e_drop_buffered_groups <= state == ST_CAPTURE ?
                                              packet_groups : 8'd0;
                    e_drop_verified_groups <= 8'd0;
                    e_framer_code <= 3'd0; e_framer_error_tail <= 11'd0;
                    e_stop_truncated <= state == ST_CAPTURE && packet_word != 11'd0;
                end

                case (state)
                    ST_IDLE: begin
                        if (start_fire) begin
                            state <= ST_CAPTURE;
                            closing <= 1'b0; fault_latched <= 1'b0;
                            packet_word <= 11'd0; packet_groups <= 8'd0;
                            packet_index <= 32'd0;
                            assembly <= 196'd0; assembly_id_valid <= 1'b0;
                            previous_id <= 64'd0; previous_id_valid <= 1'b0;
                            replay_read_addr <= 9'd0; holding_valid <= 1'b0;
                            last_replay_index <= 8'd0; last_replay_valid <= 1'b0;
                            framer_have_previous <= 1'b0;
                            last_replay_had_previous <= 1'b0;
                            e_valid <= 1'b0; e_code <= 8'd0;
                            e_session_id <= start_session_id;
                            e_id <= 64'd0; e_prev_id <= 64'd0;
                            e_id_valid <= 1'b0; e_prev_id_valid <= 1'b0;
                            e_raw_flags <= 32'd0; e_source_flags <= 8'd0;
                            e_unused_tail <= 11'd0; e_interval_index <= 32'd0;
                            e_packet_index <= 32'd0; e_word_index <= 11'd0;
                            e_packet_words <= 11'd0; e_tdata <= 32'd0;
                            e_tkeep <= 4'd0; e_tlast <= 1'b0;
                            e_drop_buffered_groups <= 8'd0;
                            e_drop_verified_groups <= 8'd0;
                            e_framer_code <= 3'd0; e_framer_error_tail <= 11'd0;
                            e_stop_truncated <= 1'b0;
                        end
                    end
                    ST_CAPTURE: begin
                        if (stop_fire) begin
                            // The ready gate makes axis_fire impossible on
                            // this edge, including a nominal last packet beat.
                            state <= ST_STOP_REQ;
                            packet_word <= 11'd0; packet_groups <= 8'd0;
                            assembly_id_valid <= 1'b0;
                        end else if (axis_fire) begin
                            if (input_issue != 8'd0) begin
                                state <= ST_STOP_REQ;
                                closing <= 1'b1; fault_latched <= 1'b1;
                                e_code <= input_issue;
                                e_id <= issue_id; e_id_valid <= issue_id_valid;
                                e_prev_id <= previous_id_valid ? previous_id : 64'd0;
                                e_prev_id_valid <= previous_id_valid;
                                e_raw_flags <= input_issue == E_BAD_FLAGS ?
                                               s_axis_tdata : 32'd0;
                                e_source_flags <= 8'd0;
                                e_packet_index <= packet_index;
                                e_word_index <= packet_word;
                                e_packet_words <= packet_word + 11'd1;
                                e_tdata <= s_axis_tdata; e_tkeep <= s_axis_tkeep;
                                e_tlast <= s_axis_tlast;
                                e_drop_buffered_groups <= packet_groups;
                                e_drop_verified_groups <= 8'd0;
                                e_framer_code <= 3'd0; e_framer_error_tail <= 11'd0;
                                e_stop_truncated <= 1'b0;
                                packet_word <= 11'd0; packet_groups <= 8'd0;
                                assembly_id_valid <= 1'b0;
                            end else begin
                                packet_word <= packet_word + 11'd1;
                                case (word_in_group)
                                    3'd0: begin
                                        assembly[159:128] <= s_axis_tdata;
                                        assembly[191:160] <= 32'd0;
                                        assembly_id_valid <= 1'b0;
                                    end
                                    3'd1: begin
                                        assembly[191:160] <= s_axis_tdata;
                                        assembly_id_valid <= 1'b1;
                                    end
                                    3'd2: assembly[31:0] <= s_axis_tdata;
                                    3'd3: assembly[63:32] <= s_axis_tdata;
                                    3'd4: assembly[95:64] <= s_axis_tdata;
                                    3'd5: assembly[127:96] <= s_axis_tdata;
                                    3'd6: assembly[195:192] <= s_axis_tdata[3:0];
                                    3'd7: begin
                                        previous_id <= assembly[191:128];
                                        previous_id_valid <= 1'b1;
                                        assembly_id_valid <= 1'b0;
                                        packet_groups <= packet_groups + 8'd1;
                                        if (packet_word == 11'd1999) begin
                                            // The same edge writes group249;
                                            // the first RAM read is next edge.
                                            state <= ST_REPLAY;
                                            packet_word <= 11'd0; packet_groups <= 8'd0;
                                            replay_read_addr <= 9'd0;
                                            holding_valid <= 1'b0;
                                            last_replay_index <= 8'd0;
                                            last_replay_valid <= 1'b0;
                                        end
                                    end
                                endcase
                            end
                        end
                    end
                    ST_REPLAY: begin
                        // Stop only locks closing; every validated group
                        // remains eligible until accepted by the old framer.
                        if (replay_fire && replay_read_addr == 9'd250) begin
                            holding_valid <= 1'b0;
                            state <= ST_REPLAY_END;
                        end
                    end
                    ST_REPLAY_END: begin
                        // Delayed errors from the final replay handshake are
                        // examined by the higher-priority event branch first.
                        if (closing || stop_fire) begin
                            state <= ST_STOP_REQ;
                        end else begin
                            packet_index <= packet_index + 32'd1;
                            state <= ST_CAPTURE;
                        end
                    end
                    ST_STOP_REQ: begin
                        if (f_stop_fire) state <= ST_WAIT_STOP;
                    end
                    ST_WAIT_STOP: begin
                        // Full legacy frames drain independently. There is
                        // no terminal publication until its STOP handshake.
                    end
                    ST_EVENT: begin
                        if (e_valid && e_ready) begin
                            e_valid <= 1'b0;
                            closing <= 1'b0;
                            state <= ST_IDLE;
                            // fault_latched clears only at reset/new start.
                        end
                    end
                    default: begin
                        // Corrupt private FSM: fail closed and request stop.
                        // If the legacy module is inactive, reset is required;
                        // never fabricate a terminal acknowledgement/restart.
                        state <= ST_STOP_REQ;
                        closing <= 1'b1; fault_latched <= 1'b1;
                        holding_valid <= 1'b0; assembly_id_valid <= 1'b0;
                        e_code <= E_FRAMER_FAULT;
                        e_id <= 64'd0; e_prev_id <= 64'd0;
                        e_id_valid <= 1'b0; e_prev_id_valid <= 1'b0;
                        e_raw_flags <= 32'd0; e_source_flags <= 8'd0;
                        e_interval_index <= 32'd0; e_packet_index <= packet_index;
                        e_word_index <= 11'd0; e_packet_words <= 11'd0;
                        e_tdata <= 32'd0; e_tkeep <= 4'd0; e_tlast <= 1'b0;
                        e_drop_buffered_groups <= 8'd0;
                        e_drop_verified_groups <= 8'd0;
                        e_framer_code <= 3'd0; e_framer_error_tail <= 11'd0;
                        e_stop_truncated <= 1'b0;
                    end
                endcase
            end
        end
    end
endmodule
