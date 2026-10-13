`timescale 1ns/1ps
// Private diagnostic lifecycle slice; all controls use clk. The source and
// packet/framer dependencies are frozen separately and remain unmodified.
module pcm4_c1_lifecycle (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         frontend_ready,
    input  wire [3:0]   pcm_valid,
    input  wire [3:0]   clipped,
    input  wire [95:0]  pcm,
    input  wire [63:0]  sample_id,
    input  wire         start_valid,
    output wire         start_ready,
    input  wire [31:0]  start_session_id,
    input  wire         stop_valid,
    output wire         stop_ready,
    output wire         source_run,
    output wire [31:0]  source_status,
    output wire         session_active,
    output wire         closing,
    output wire         fault_latched,
    output wire [7:0]   fault_code,
    output wire [7:0]   fault_parent_code,
    output wire [31:0]  fault_session_id,
    output wire [31:0]  fault_source_status,
    output wire         fault_session_valid,
    output wire         fault_id_valid,
    output wire         fault_after_terminal,
    output wire [63:0]  fault_id,
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
    output wire         e_valid,
    input  wire         e_ready,
    output wire [7:0]   e_code,
    output wire [7:0]   e_parent_code,
    output wire [31:0]  e_source_status,
    output wire         e_source_drained,
    output wire [31:0]  e_session_id,
    output wire [63:0]  e_id,
    output wire [63:0]  e_prev_id,
    output wire         e_id_valid,
    output wire         e_prev_id_valid,
    output wire [31:0]  e_raw_flags,
    output wire [7:0]   e_source_flags,
    output wire [10:0]  e_unused_tail,
    output wire [31:0]  e_interval_index,
    output wire [31:0]  e_packet_index,
    output wire [10:0]  e_word_index,
    output wire [10:0]  e_packet_words,
    output wire [31:0]  e_tdata,
    output wire [3:0]   e_tkeep,
    output wire         e_tlast,
    output wire [7:0]   e_drop_buffered_groups,
    output wire [7:0]   e_drop_verified_groups,
    output wire [2:0]   e_framer_code,
    output wire [10:0]  e_framer_error_tail,
    output wire         e_stop_truncated
);
    localparam [3:0] ST_IDLE         = 4'd0,
                     ST_SOURCE_ARM   = 4'd1,
                     ST_ACTIVE       = 4'd2,
                     ST_DRAIN_SOURCE = 4'd3,
                     ST_STOP_PARENT  = 4'd4,
                     ST_WAIT_PARENT  = 4'd5,
                     ST_EVENT        = 4'd6,
                     ST_FAULT_HOLD   = 4'd7;
    // Code0 is UNKNOWN_OR_NONE; fault_latched distinguishes an unclassified
    // illegal-control-state fault from the initial absence of a fault.
    localparam [7:0] E_NORMAL_STOP    = 8'd1,
                     E_SOURCE_SYNC   = 8'd2,
                     E_SOURCE_FULL   = 8'd3,
                     E_PARENT_FAULT  = 8'd4,
                     E_ARM_WARM_LOST = 8'd5;

    reg [3:0] state;
    reg [31:0] last_session_id;
    reg last_session_valid;
    reg terminal_published;
    reg fault_latched_r;
    reg [7:0] fault_code_r;
    reg [7:0] fault_parent_code_r;
    reg [31:0] fault_session_id_r;
    reg [31:0] fault_source_status_r;
    reg fault_session_valid_r;
    reg fault_id_valid_r;
    reg fault_after_terminal_r;
    reg [63:0] fault_id_r;
    reg [7:0] event_code;
    reg [31:0] event_source_status;
    reg event_source_drained;

    wire [31:0] axis_data;
    wire [3:0] axis_keep;
    wire axis_valid, axis_last, axis_ready;
    wire parent_start_ready, parent_stop_ready;
    wire parent_session_active, parent_closing, parent_fault;
    wire parent_e_valid;
    wire mismatch = (|pcm_valid) && !(&pcm_valid);
    wire source_normal_empty = source_status[31:24] == 8'hc1 &&
        !source_status[5] && !source_status[2] && source_status[3] &&
        !source_status[0] && !source_status[6] && !source_status[7];
    wire arm_warm_lost = state == ST_SOURCE_ARM &&
        !source_status[0] && !frontend_ready;
    // Only the source's registered sticky fatal bits classify source errors.
    // Raw mismatch prevents start but is not substituted for their F snapshot.
    wire [7:0] current_fault_code = source_status[5] ? E_SOURCE_SYNC :
        source_status[2] ? E_SOURCE_FULL :
        parent_fault ? E_PARENT_FAULT :
        arm_warm_lost ? E_ARM_WARM_LOST : 8'd0;
    wire current_fault = current_fault_code != 8'd0;
    wire start_fire = start_valid && start_ready;
    wire stop_fire = stop_valid && stop_ready;
    wire parent_stop_valid = rst_n && state == ST_STOP_PARENT &&
        !parent_closing && !parent_fault;
    wire parent_stop_fire = parent_stop_valid && parent_stop_ready;
    wire parent_e_ready = rst_n && state == ST_EVENT && e_ready;

    assign start_ready = rst_n && state == ST_IDLE && !fault_latched_r &&
        !current_fault && !mismatch && frontend_ready &&
        source_normal_empty && parent_start_ready;
    assign stop_ready = rst_n && state == ST_ACTIVE &&
        !fault_latched_r && !current_fault;
    // A normal stop accepted at D reaches the original source at that same D
    // edge. Parent stop remains low throughout SOURCE_ARM/ACTIVE/DRAIN_SOURCE.
    assign source_run = rst_n &&
        (state == ST_SOURCE_ARM || state == ST_ACTIVE) &&
        !fault_latched_r && !current_fault && !stop_fire;
    assign session_active = rst_n &&
        (state == ST_SOURCE_ARM || state == ST_ACTIVE ||
         state == ST_DRAIN_SOURCE || state == ST_STOP_PARENT ||
         state == ST_WAIT_PARENT || state == ST_EVENT);
    assign closing = rst_n &&
        (state == ST_DRAIN_SOURCE || state == ST_STOP_PARENT ||
         state == ST_WAIT_PARENT || state == ST_EVENT ||
         (session_active && current_fault));
    assign fault_latched = fault_latched_r;
    assign fault_code = fault_code_r;
    assign fault_parent_code = fault_parent_code_r;
    assign fault_session_id = fault_session_id_r;
    assign fault_source_status = fault_source_status_r;
    assign fault_session_valid = fault_session_valid_r;
    assign fault_id_valid = fault_id_valid_r;
    assign fault_after_terminal = fault_after_terminal_r;
    assign fault_id = fault_id_r;
    assign e_valid = rst_n && state == ST_EVENT && parent_e_valid;
    assign e_code = event_code;
    assign e_source_status = event_source_status;
    assign e_source_drained = event_source_drained;

    pcm4_continuous_axis #(
        .SAMPLES_PER_PACKET(250), .FIFO_LOG2(10)
    ) u_source (
        .clk(clk), .rst_n(rst_n), .run(source_run), .ready(frontend_ready),
        .pcm_valid(pcm_valid), .pcm(pcm), .clipped(clipped),
        .sample_id(sample_id), .m_axis_tdata(axis_data),
        .m_axis_tkeep(axis_keep), .m_axis_tvalid(axis_valid),
        .m_axis_tlast(axis_last), .m_axis_tready(axis_ready),
        .status(source_status)
    );

    // Data and held parent terminal payloads are transparent. The wrapper
    // delays only terminal visibility/ack and adds its three frozen fields.
    pcm4_c1_packet_framer u_parent (
        .clk(clk), .rst_n(rst_n),
        .start_valid(start_fire), .start_ready(parent_start_ready),
        .start_session_id(start_session_id),
        .stop_valid(parent_stop_valid), .stop_ready(parent_stop_ready),
        .s_axis_tvalid(axis_valid), .s_axis_tready(axis_ready),
        .s_axis_tdata(axis_data), .s_axis_tkeep(axis_keep),
        .s_axis_tlast(axis_last),
        .m_valid(m_valid), .m_ready(m_ready), .m_pcm(m_pcm), .m_id(m_id),
        .m_flags(m_flags), .m_session_id(m_session_id),
        .m_frame_index(m_frame_index), .m_interval_index(m_interval_index),
        .m_sample_index(m_sample_index), .m_first_id(m_first_id),
        .m_last_id(m_last_id), .m_reset_before(m_reset_before), .m_last(m_last),
        .session_active(parent_session_active), .closing(parent_closing),
        .fault_latched(parent_fault),
        .e_valid(parent_e_valid), .e_ready(parent_e_ready),
        .e_code(e_parent_code), .e_session_id(e_session_id),
        .e_id(e_id), .e_prev_id(e_prev_id), .e_id_valid(e_id_valid),
        .e_prev_id_valid(e_prev_id_valid), .e_raw_flags(e_raw_flags),
        .e_source_flags(e_source_flags), .e_unused_tail(e_unused_tail),
        .e_interval_index(e_interval_index), .e_packet_index(e_packet_index),
        .e_word_index(e_word_index), .e_packet_words(e_packet_words),
        .e_tdata(e_tdata), .e_tkeep(e_tkeep), .e_tlast(e_tlast),
        .e_drop_buffered_groups(e_drop_buffered_groups),
        .e_drop_verified_groups(e_drop_verified_groups),
        .e_framer_code(e_framer_code), .e_framer_error_tail(e_framer_error_tail),
        .e_stop_truncated(e_stop_truncated)
    );

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            last_session_id <= 32'd0;
            last_session_valid <= 1'b0;
            terminal_published <= 1'b0;
            fault_latched_r <= 1'b0;
            fault_code_r <= 8'd0;
            fault_parent_code_r <= 8'd0;
            fault_session_id_r <= 32'd0;
            fault_source_status_r <= 32'd0;
            fault_session_valid_r <= 1'b0;
            fault_id_valid_r <= 1'b0;
            fault_after_terminal_r <= 1'b0;
            fault_id_r <= 64'd0;
            event_code <= 8'd0;
            event_source_status <= 32'd0;
            event_source_drained <= 1'b0;
        end else begin
            // Fault ownership is independent of event publication. A late
            // fault can block restart without rewriting already held history.
            if (!fault_latched_r && current_fault) begin
                fault_latched_r <= 1'b1;
                fault_code_r <= current_fault_code;
                fault_parent_code_r <= parent_e_valid ? e_parent_code : 8'd0;
                fault_session_id_r <= last_session_valid ?
                                      last_session_id : 32'd0;
                fault_source_status_r <= source_status;
                fault_session_valid_r <= last_session_valid;
                fault_id_valid_r <= current_fault_code == E_PARENT_FAULT &&
                                    parent_e_valid && e_id_valid;
                fault_id_r <= (current_fault_code == E_PARENT_FAULT &&
                               parent_e_valid && e_id_valid) ? e_id : 64'd0;
                fault_after_terminal_r <= terminal_published;
            end

            case (state)
                ST_IDLE: begin
                    if (fault_latched_r || current_fault) begin
                        // No session means no fabricated terminal event.
                        state <= ST_FAULT_HOLD;
                    end else if (start_fire) begin
                        state <= ST_SOURCE_ARM;
                        last_session_id <= start_session_id;
                        last_session_valid <= 1'b1;
                        terminal_published <= 1'b0;
                    end
                end
                ST_SOURCE_ARM: begin
                    if (fault_latched_r || current_fault) begin
                        state <= (parent_closing || parent_fault) ?
                                 ST_WAIT_PARENT : ST_STOP_PARENT;
                    end else if (source_status[0]) begin
                        // ACTIVE proves startup; initial empty/drained can
                        // never bypass this observation into a normal stop.
                        state <= ST_ACTIVE;
                    end
                end
                ST_ACTIVE: begin
                    if (fault_latched_r || current_fault) begin
                        state <= (parent_closing || parent_fault) ?
                                 ST_WAIT_PARENT : ST_STOP_PARENT;
                    end else if (stop_fire) begin
                        state <= ST_DRAIN_SOURCE;
                    end
                end
                ST_DRAIN_SOURCE: begin
                    if (fault_latched_r || current_fault) begin
                        // A source fatal can leave fragments forever; stop
                        // the parent rather than waiting for false drained.
                        state <= (parent_closing || parent_fault) ?
                                 ST_WAIT_PARENT : ST_STOP_PARENT;
                    end else if (source_normal_empty) begin
                        state <= ST_STOP_PARENT;
                    end
                end
                ST_STOP_PARENT: begin
                    if (parent_closing || parent_fault || parent_stop_fire)
                        state <= ST_WAIT_PARENT;
                end
                ST_WAIT_PARENT: begin
                    if (parent_e_valid) begin
                        // Q includes a newly visible fault on this edge;
                        // subsequent faults cannot mutate these registers.
                        event_code <= fault_latched_r ? fault_code_r :
                                      current_fault ? current_fault_code :
                                      E_NORMAL_STOP;
                        event_source_status <= source_status;
                        event_source_drained <= source_normal_empty;
                        terminal_published <= 1'b1;
                        state <= ST_EVENT;
                    end
                end
                ST_EVENT: begin
                    if (parent_e_valid && e_ready) begin
                        state <= (fault_latched_r || current_fault) ?
                                 ST_FAULT_HOLD : ST_IDLE;
                    end
                end
                ST_FAULT_HOLD: begin
                    // Only the shared synchronous reset permits recovery.
                end
                default: begin
                    // Unclassified wrapper-control corruption fails closed.
                    // Real same-edge source/parent faults retain priority.
                    state <= ST_FAULT_HOLD;
                    if (!fault_latched_r && !current_fault) begin
                        fault_latched_r <= 1'b1;
                        fault_code_r <= 8'd0;
                        fault_parent_code_r <= 8'd0;
                        fault_session_id_r <= last_session_valid ?
                                              last_session_id : 32'd0;
                        fault_source_status_r <= source_status;
                        fault_session_valid_r <= last_session_valid;
                        fault_id_valid_r <= 1'b0;
                        fault_id_r <= 64'd0;
                        fault_after_terminal_r <= terminal_published;
                    end
                end
            endcase
        end
    end
endmodule
