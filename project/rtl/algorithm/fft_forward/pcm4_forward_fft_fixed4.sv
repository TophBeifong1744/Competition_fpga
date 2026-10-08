`timescale 1ns/1ps
// FF-1.0: detached NP snapshot -> actual serial AMD FFT -> unchanged fixed4.
// Single-clock manager. Reset is exclusively shared cold invalidation.
module pcm4_forward_fft_fixed4 (
    input logic clk, cold_rst_n,
    input logic source_begin_valid, output logic source_begin_ready,
    input logic [63:0] source_token, source_generation,
    input logic [164:0] source_context, input logic [431:0] source_frame_first,
    input logic np_fft_valid, output logic np_fft_ready,
    input logic np_fft_domain, input logic [1:0] np_fft_channel,
    input logic [9:0] np_fft_index,
    input logic signed [28:0] np_fft_real, np_fft_imag,
    input logic np_fft_numeric_valid, np_fft_overflow, np_fft_last,
    input logic [63:0] np_fft_token, np_fft_generation,
    input logic [164:0] np_fft_context,
    input logic [431:0] np_fft_frame_first,
    input logic np_report_valid, output logic np_report_ready,
    input logic [2001:0] np_report_payload,
    input logic np_abort_valid, output logic np_abort_ready,
    input logic [2079:0] np_abort_payload,
    // Explicit backend-scoped cancellation, NOT the caller's close feedback.
    input logic cancel_now, input logic [7:0] cancel_causes,
    input logic controlled_clear_valid, output logic controlled_clear_ready,
    // Explicit diagnostic permits; tie high only for an unstalled integrator.
    input logic fft_output_permit, fft_status_permit,
    output logic m_valid, input logic m_ready,
    output logic [63:0] m_token, m_generation,
    output logic [164:0] m_context, output logic [431:0] m_frame_first,
    output logic m_domain, output logic [1:0] m_channel,
    output logic [9:0] m_bin,
    output logic signed [24:0] m_real, m_imag,
    output logic m_numeric_valid, m_ov_real, m_ov_imag, m_qualified,
    output logic terminal_valid, input logic terminal_ready,
    output logic [63:0] terminal_token, terminal_generation,
    output logic [164:0] terminal_context,
    output logic [431:0] terminal_frame_first,
    output logic [63:0] unit_state,
    output logic [15:0] hardware_started, physically_retired,
    output logic [87:0] fft_input_counts, fft_output_counts,
    output logic [79:0] fixed4_input_counts, fixed4_output_counts,
    output logic [79:0] fixed4_qualified_counts,
    output logic [63:0] fft_status_raw, output logic [7:0] fft_status_seen,
    output logic [55:0] fft_event_seen,
    output logic [511:0] fixed4_contexts,
    output logic [279:0] fixed4_cancel_causes_record,
    output logic [79:0] fixed4_terminal_n_record, fixed4_terminal_p_record,
    output logic [79:0] fixed4_cancelled_unsent_record, fixed4_terminal_t_bin_record,
    output logic [7:0] fixed4_terminal_t_record, fixed4_terminal_s_record,
    output logic [7:0] fixed4_cancel_saved, fixed4_retire_accepted,
    output logic [13:0] source_received,
    output logic transaction_cancelled, protocol_error, numeric_error,
    output logic [7:0] first_error_code, accumulated_cancel_causes,
    output logic [2001:0] source_report_record,
    output logic [2079:0] source_abort_record,
    output logic source_report_seen, source_abort_seen,
    output logic abort_valid, input logic abort_ready,
    // Snapshot of strict-before-E facts + actual same-E physical transfers.
    // Original identity is in immutable terminal_* throughout this lease.
    output logic [179:0] abort_payload,
    output logic busy, ip_obligation, leaf_obligation,
    output logic [3:0] debug_state,
    // Physical FFT audit; pulses after an actual accepted output/status.
    output logic fft_audit_valid, fft_audit_status,
    output logic [2:0] fft_audit_instance,
    output logic [9:0] fft_audit_bin,
    output logic signed [28:0] fft_audit_real, fft_audit_imag,
    output logic [7:0] fft_audit_status_raw,
    output logic fft_audit_last, fft_audit_on_cancel
);
    localparam logic [3:0] IDLE=0, COLLECT=1, WAIT_NP=2, CONFIG=3,
        FEED=4, DRAIN=5, FFT_FINAL=6, LEAF_BEGIN=7, LEAF_RUN=8,
        LEAF_SAVE=9, LEAF_RETIRE=10, NEXT=11, FINISH=12, REPORT=13;
    localparam logic [3:0] PENDING=0, OK=1, CANCELLED=2,
        ERROR_PROTOCOL=3, ERROR_NUMERIC=4, NOT_RUN_NUMERIC=5;
    localparam logic [7:0] ERR_NONE=0, ERR_SOURCE_ORDER=1,
        ERR_SOURCE_ID=2, ERR_SOURCE_NUMERIC=3, ERR_NP_REPORT=4,
        ERR_NP_ABORT_ID=5, ERR_FFT_INDEX=6, ERR_FFT_LAST=7,
        ERR_FFT_STATUS=8, ERR_FFT_EVENT=9, ERR_FFT_OVERFLOW=10,
        ERR_FIXED4_OVERFLOW=11, ERR_FIXED4_PROTOCOL=12,
        ERR_CONTEXT_EXHAUSTED=13, ERR_FSM=14;
    logic [3:0] state;
    logic [57:0] input_ram [0:8191];
    logic [57:0] half_ram [0:512];
    logic [2:0] instance_id;
    logic [10:0] fft_in_n, fft_out_n;
    logic [9:0] leaf_in_n, leaf_out_n;
    logic [63:0] next_leaf_ctx, active_leaf_ctx;
    logic np_closed, fft_frame_numeric_error;
    logic np_source_fire, np_report_fire, np_abort_fire, clear_fire;
    logic source_bad, report_bad, abort_bad, ip_bad, leaf_bad;
    logic kill_now, external_kill;
    wire [7:0] reliable_causes_now=
        (cancel_now ? cancel_causes : 8'b0) |
        {3'b0,(source_bad||report_bad||abort_bad||ip_bad||leaf_bad),
         np_abort_valid,clear_fire,1'b0,cancel_now};
    wire [7:0] cancel_union_now=accumulated_cancel_causes | reliable_causes_now;
    logic [7:0] fault_now;
    wire cfg_valid, cfg_ready, ip_s_valid, ip_s_ready, ip_s_last;
    wire ip_m_valid, ip_m_ready, ip_m_last;
    wire signed [28:0] ip_s_real, ip_s_imag, ip_m_real, ip_m_imag;
    wire [9:0] ip_m_index;
    wire ip_status_valid, ip_status_ready;
    wire [7:0] ip_status_raw;
    wire [6:0] ip_events;
    wire cfg_fire=cfg_valid && cfg_ready;
    wire ip_in_fire=ip_s_valid && ip_s_ready;
    wire ip_out_fire=ip_m_valid && ip_m_ready;
    wire ip_status_fire=ip_status_valid && ip_status_ready;
    wire leaf_active, leaf_saved, leaf_begin_ready, leaf_s_ready;
    wire [63:0] leaf_ctx, leaf_m_ctx, leaf_terminal_ctx;
    wire leaf_m_valid, leaf_numeric, leaf_ov_re, leaf_ov_im;
    wire [9:0] leaf_m_bin;
    wire signed [24:0] leaf_m_re, leaf_m_im;
    wire leaf_done, leaf_overflow, leaf_cancelled, leaf_quiescent;
    wire leaf_protocol;
    wire [1:0] leaf_protocol_bits;
    wire [34:0] leaf_terminal_causes;
    wire [9:0] leaf_terminal_n, leaf_terminal_p, leaf_cancelled_unsent;
    wire leaf_terminal_t, leaf_terminal_s_transfer;
    wire [9:0] leaf_terminal_t_bin;
    wire leaf_begin_valid=(state==LEAF_BEGIN) && !transaction_cancelled &&
                          (next_leaf_ctx!=64'hffffffffffffffff);
    wire leaf_s_valid=(state==LEAF_RUN) && !transaction_cancelled &&
                     (leaf_in_n < 10'd513);
    wire leaf_input_fire=leaf_s_valid && leaf_s_ready;
    wire leaf_output_fire=leaf_m_valid && m_ready;
    // FF-PROTO-02: history alone permits retirement after save, but a current
    // reliable kill (including held/repeated kill) still reaches a saved leaf.
    wire leaf_cancel=leaf_active &&
                     (kill_now || (transaction_cancelled && !leaf_cancelled));
    wire [34:0] leaf_cause_now={leaf_cancel ? {24'b0,cancel_union_now} : 32'b0,
                              leaf_protocol_bits,leaf_cancel};
    wire leaf_ack=(state==LEAF_SAVE) && leaf_active && leaf_cancelled &&
                  leaf_quiescent && !leaf_m_valid && !leaf_saved;
    wire leaf_retire=(state==LEAF_RETIRE) && leaf_active && leaf_quiescent &&
                     !leaf_m_valid && (!leaf_cancelled || leaf_saved) && !kill_now;
    wire leaf_retire_safe=!ip_obligation && np_closed && !leaf_s_valid &&
                          !leaf_m_valid && leaf_quiescent;
    wire leaf_retire_fire=leaf_retire && leaf_retire_safe && !leaf_cancel &&
                          !leaf_protocol && (leaf_ctx==active_leaf_ctx);

    assign debug_state=state;
    assign busy=(state!=IDLE) || terminal_valid || abort_valid;
    assign source_begin_ready=cold_rst_n && !busy && !cancel_now &&
                              !controlled_clear_valid && !np_abort_valid;
    assign controlled_clear_ready=cold_rst_n && (state!=IDLE) &&
                                  (state!=REPORT) && !transaction_cancelled;
    assign clear_fire=controlled_clear_valid && controlled_clear_ready;
    assign np_fft_ready=cold_rst_n && (state==COLLECT) &&
                        (source_received < 14'd8192);
    assign np_report_ready=cold_rst_n && (state!=IDLE) &&
                           (state!=REPORT) && !source_report_seen;
    assign np_abort_ready=cold_rst_n && (state!=IDLE) &&
                          (state!=REPORT) && !source_abort_seen;
    assign np_source_fire=np_fft_valid && np_fft_ready;
    assign np_report_fire=np_report_valid && np_report_ready;
    assign np_abort_fire=np_abort_valid && np_abort_ready;
    assign external_kill=cancel_now || clear_fire ||
                         (np_abort_valid && (state!=IDLE) && (state!=REPORT));
    // FF-ARCH-01: an offered AXI config remains outstanding until actual ACK.
    // Cancel qualifies no new work, but cannot withdraw that physical offer.
    assign cfg_valid=cold_rst_n && (state==CONFIG);
    assign ip_s_valid=cold_rst_n && (state==FEED) && (fft_in_n<11'd1024);
    assign {ip_s_real,ip_s_imag}=input_ram[{instance_id,fft_in_n[9:0]}];
    assign ip_s_last=(fft_in_n==11'd1023);
    assign ip_m_ready=cold_rst_n && ip_obligation && fft_output_permit;
    assign ip_status_ready=cold_rst_n && ip_obligation && fft_status_permit;
    assign m_valid=cold_rst_n && leaf_m_valid;
    assign m_token=terminal_token;
    assign m_generation=terminal_generation;
    assign m_context=terminal_context;
    assign m_frame_first=terminal_frame_first;
    assign m_domain=instance_id[2];
    assign m_channel=instance_id[1:0];
    assign m_bin=leaf_m_bin;
    assign m_real=leaf_m_re;
    assign m_imag=leaf_m_im;
    assign m_numeric_valid=leaf_numeric;
    assign m_ov_real=leaf_ov_re;
    assign m_ov_imag=leaf_ov_im;
    assign m_qualified=m_valid && leaf_numeric && !transaction_cancelled &&
                       !kill_now;
    assign leaf_obligation=leaf_active;

    always_comb begin
        source_bad=1'b0; report_bad=1'b0; abort_bad=1'b0;
        ip_bad=1'b0; leaf_bad=1'b0; fault_now=ERR_NONE;
        if (np_source_fire) begin
            if ({np_fft_token,np_fft_generation,np_fft_context,np_fft_frame_first}
                !== {terminal_token,terminal_generation,terminal_context,terminal_frame_first}) begin
                source_bad=1; fault_now=ERR_SOURCE_ID;
            end else if ({np_fft_domain,np_fft_channel,np_fft_index}
                         !== source_received[12:0] ||
                         np_fft_last !== (source_received[9:0]==10'd1023)) begin
                source_bad=1; fault_now=ERR_SOURCE_ORDER;
            end else if (np_fft_numeric_valid !== 1'b1 || np_fft_overflow !== 1'b0) begin
                source_bad=1; fault_now=ERR_SOURCE_NUMERIC;
            end
        end
        if (np_report_fire) begin
            if (np_report_payload[2001:1277] !==
                {terminal_token,terminal_generation,terminal_context,terminal_frame_first} ||
                np_report_payload[878] !== 1'b1) begin
                report_bad=1;
            end else if (!transaction_cancelled && !external_kill &&
                (source_received!=14'd8192 ||
                 np_report_payload[1276:1241] !== {12{3'd1}} ||
                 np_report_payload[1144:1057] !== {8{11'd1024}} ||
                 np_report_payload[1056:1025] !== 32'd1024 ||
                 np_report_payload[1024:993] !== 32'd1024 ||
                 np_report_payload[992:961] !== 32'd1024 ||
                 np_report_payload[960:950] !== 11'd1024 ||
                 np_report_payload[949:936] !== 14'd8192 ||
                 np_report_payload[935:922] !== 14'd8192 ||
                 np_report_payload[921:880] !== 42'b0 ||
                 np_report_payload[879] !== 1'b0 ||
                 np_report_payload[877:876] !== 2'b0 ||
                 np_report_payload[875] !== 1'b1 ||
                 np_report_payload[874:859] !== 16'b0 ||
                 np_report_payload[849:838] !== 12'b0 ||
                 np_report_payload[858] !== 1'b0)) begin
                report_bad=1;
            end
            if (report_bad && fault_now==ERR_NONE) fault_now=ERR_NP_REPORT;
        end
        if (np_abort_fire && np_abort_payload[2079:1355] !==
            {terminal_token,terminal_generation,terminal_context,terminal_frame_first}) begin
            abort_bad=1;
            if (fault_now==ERR_NONE) fault_now=ERR_NP_ABORT_ID;
        end
        if (ip_out_fire) begin
            if (fft_out_n>=11'd1024 || ip_m_index !== fft_out_n[9:0]) begin
                ip_bad=1;
                if (fault_now==ERR_NONE) fault_now=ERR_FFT_INDEX;
            end else if (ip_m_last !== (fft_out_n==11'd1023)) begin
                ip_bad=1;
                if (fault_now==ERR_NONE) fault_now=ERR_FFT_LAST;
            end
        end
        if (ip_status_fire && fft_status_seen[instance_id]) begin
            ip_bad=1;
            if (fault_now==ERR_NONE) fault_now=ERR_FFT_STATUS;
        end
        if (ip_obligation && (ip_events[1] || ip_events[2])) begin
            ip_bad=1;
            if (fault_now==ERR_NONE) fault_now=ERR_FFT_EVENT;
        end
        if (leaf_protocol || (leaf_output_fire &&
            (leaf_m_ctx !== active_leaf_ctx || leaf_m_bin !== leaf_out_n))) begin
            leaf_bad=1;
            if (fault_now==ERR_NONE) fault_now=ERR_FIXED4_PROTOCOL;
        end
        if (state==LEAF_BEGIN && next_leaf_ctx==64'hffffffffffffffff) begin
            leaf_bad=1;
            if (fault_now==ERR_NONE) fault_now=ERR_CONTEXT_EXHAUSTED;
        end
    end
    assign kill_now=external_kill || source_bad || report_bad || abort_bad ||
                    ip_bad || leaf_bad;

    fft29_official fft (
        .clk(clk), .cold_rst_n(cold_rst_n),
        .config_valid(cfg_valid), .config_ready(cfg_ready),
        .data_valid(ip_s_valid), .data_ready(ip_s_ready),
        .data_real(ip_s_real), .data_imag(ip_s_imag), .data_last(ip_s_last),
        .out_valid(ip_m_valid), .out_ready(ip_m_ready), .out_real(ip_m_real),
        .out_imag(ip_m_imag), .out_index(ip_m_index), .out_last(ip_m_last),
        .status_valid(ip_status_valid), .status_ready(ip_status_ready),
        .status_raw(ip_status_raw), .events(ip_events)
    );
    fixed4_leaf fixed4 (
        .clk(clk), .cold_reset(!cold_rst_n), .ctx_active(leaf_active),
        .active_ctx(leaf_ctx), .terminal_saved(leaf_saved),
        .begin_valid(leaf_begin_valid), .begin_ready(leaf_begin_ready),
        .begin_ctx(next_leaf_ctx), .s_valid(leaf_s_valid), .s_ready(leaf_s_ready),
        .s_ctx(active_leaf_ctx), .s_bin(leaf_in_n),
        .s_re(half_ram[leaf_in_n][57:29]), .s_im(half_ram[leaf_in_n][28:0]),
        .m_valid(leaf_m_valid), .m_ready(m_ready), .m_ctx(leaf_m_ctx),
        .m_bin(leaf_m_bin), .m_re(leaf_m_re), .m_im(leaf_m_im),
        .m_numeric_valid(leaf_numeric), .m_ov_re(leaf_ov_re), .m_ov_im(leaf_ov_im),
        // FF-ARCH-02: leaf snapshot sees the same current-edge cause union.
        .cancel(leaf_cancel), .cancel_causes({24'b0,cancel_union_now}),
        .protocol_fault_now(leaf_protocol), .protocol_fault_bits_now(leaf_protocol_bits),
        .data_done(leaf_done), .sticky_numeric_overflow(leaf_overflow),
        .terminal_cancelled(leaf_cancelled), .terminal_ctx(leaf_terminal_ctx),
        .terminal_causes(leaf_terminal_causes), .terminal_n(leaf_terminal_n),
        .terminal_p(leaf_terminal_p), .terminal_t(leaf_terminal_t),
        .terminal_cancelled_untransferred(leaf_cancelled_unsent),
        .terminal_s_transfer(leaf_terminal_s_transfer), .terminal_t_bin(leaf_terminal_t_bin),
        .terminal_saved_ack(leaf_ack), .ack_ctx(active_leaf_ctx),
        .local_quiescent(leaf_quiescent), .retire_valid(leaf_retire),
        .retire_ctx(active_leaf_ctx), .retire_safe(leaf_retire_safe)
    );

    integer u;
    always_ff @(posedge clk) begin
        if (!cold_rst_n) begin
            state<=IDLE; instance_id<=0; next_leaf_ctx<=1; active_leaf_ctx<=0;
            terminal_valid<=0; abort_valid<=0; abort_payload<=0;
            terminal_token<=0; terminal_generation<=0; terminal_context<=0;
            terminal_frame_first<=0; unit_state<=0; hardware_started<=0;
            physically_retired<=0; fft_input_counts<=0; fft_output_counts<=0;
            fixed4_input_counts<=0; fixed4_output_counts<=0; fixed4_qualified_counts<=0;
            fft_status_raw<=0; fft_status_seen<=0; fft_event_seen<=0;
            fixed4_contexts<=0; source_received<=0; transaction_cancelled<=0;
            fixed4_cancel_causes_record<=0; fixed4_terminal_n_record<=0;
            fixed4_terminal_p_record<=0; fixed4_cancelled_unsent_record<=0;
            fixed4_terminal_t_bin_record<=0; fixed4_terminal_t_record<=0;
            fixed4_terminal_s_record<=0; fixed4_cancel_saved<=0;
            fixed4_retire_accepted<=0;
            protocol_error<=0; numeric_error<=0; first_error_code<=0;
            accumulated_cancel_causes<=0; source_report_record<=0; source_abort_record<=0;
            source_report_seen<=0; source_abort_seen<=0; np_closed<=0;
            ip_obligation<=0; fft_frame_numeric_error<=0;
            fft_in_n<=0; fft_out_n<=0; leaf_in_n<=0; leaf_out_n<=0;
            fft_audit_valid<=0; fft_audit_status<=0; fft_audit_instance<=0;
            fft_audit_bin<=0; fft_audit_real<=0; fft_audit_imag<=0;
            fft_audit_status_raw<=0; fft_audit_last<=0; fft_audit_on_cancel<=0;
        end else begin
            fft_audit_valid<=0; fft_audit_status<=0;
            if (abort_valid && abort_ready) abort_valid<=0;
            if (terminal_valid && terminal_ready) terminal_valid<=0;
            if (state!=IDLE && state!=REPORT) begin
                if (np_source_fire) begin
                    input_ram[source_received[12:0]]<={np_fft_real,np_fft_imag};
                    source_received<=source_received+14'd1;
                end
                if (np_report_fire) begin
                    source_report_record<=np_report_payload;
                    source_report_seen<=1;
                    if (np_report_payload[876]) numeric_error<=1;
                    if (np_report_payload[877]) protocol_error<=1;
                    if (np_report_payload[2001:1277] ===
                        {terminal_token,terminal_generation,terminal_context,terminal_frame_first} &&
                        np_report_payload[878] === 1'b1) np_closed<=1;
                end
                if (np_abort_fire) begin
                    source_abort_record<=np_abort_payload; source_abort_seen<=1;
                    if (np_abort_payload[954]) numeric_error<=1;
                    if (np_abort_payload[955]) protocol_error<=1;
                end
                if (ip_obligation) fft_event_seen[instance_id*7+:7]<=
                    fft_event_seen[instance_id*7+:7] | ip_events;
                if (ip_in_fire) begin
                    fft_in_n<=fft_in_n+11'd1;
                    fft_input_counts[instance_id*11+:11]<=fft_in_n+11'd1;
                end
                if (ip_out_fire) begin
                    if (fft_out_n<11'd1024) fft_out_n<=fft_out_n+11'd1;
                    fft_output_counts[instance_id*11+:11]<=
                        (fft_out_n<11'd1024) ? fft_out_n+11'd1 : fft_out_n;
                    if (fft_out_n<11'd513 && !transaction_cancelled && !kill_now)
                        half_ram[fft_out_n[9:0]]<={ip_m_real,ip_m_imag};
                    fft_audit_valid<=1; fft_audit_instance<=instance_id;
                    fft_audit_bin<=ip_m_index; fft_audit_real<=ip_m_real;
                    fft_audit_imag<=ip_m_imag; fft_audit_last<=ip_m_last;
                    fft_audit_on_cancel<=transaction_cancelled || kill_now;
                end
                if (ip_status_fire) begin
                    // First actual status payload is never overwritten by a duplicate.
                    if (!fft_status_seen[instance_id])
                        fft_status_raw[instance_id*8+:8]<=ip_status_raw;
                    fft_status_seen[instance_id]<=1;
                    fft_audit_status<=1; fft_audit_status_raw<=ip_status_raw;
                    fft_audit_instance<=instance_id;
                    if (ip_status_raw[0] !== 1'b0) begin
                        fft_frame_numeric_error<=1; numeric_error<=1;
                        if (first_error_code==ERR_NONE && fault_now==ERR_NONE)
                            first_error_code<=ERR_FFT_OVERFLOW;
                    end
                end
                if (ip_obligation && ip_events[6]) begin
                    fft_frame_numeric_error<=1; numeric_error<=1;
                    if (first_error_code==ERR_NONE && fault_now==ERR_NONE)
                        first_error_code<=ERR_FFT_OVERFLOW;
                end
                if (leaf_input_fire) begin
                    leaf_in_n<=leaf_in_n+10'd1;
                    fixed4_input_counts[instance_id*10+:10]<=leaf_in_n+10'd1;
                end
                if (leaf_ack) begin
                    fixed4_terminal_n_record[instance_id*10+:10]<=leaf_terminal_n;
                    fixed4_terminal_p_record[instance_id*10+:10]<=leaf_terminal_p;
                    fixed4_cancelled_unsent_record[instance_id*10+:10]<=leaf_cancelled_unsent;
                    fixed4_terminal_t_bin_record[instance_id*10+:10]<=leaf_terminal_t_bin;
                    fixed4_terminal_t_record[instance_id]<=leaf_terminal_t;
                    fixed4_terminal_s_record[instance_id]<=leaf_terminal_s_transfer;
                    fixed4_cancel_saved[instance_id]<=1;
                end
                // Initial N/P/T/identity remain untouched; the cause field is
                // the old leaf's documented monotonic late-cause audit union.
                // Include E before the leaf's registered union becomes visible,
                // and persist it before any later real retirement clears it.
                if (leaf_active && leaf_cancelled && (leaf_saved || leaf_ack))
                    fixed4_cancel_causes_record[instance_id*35+:35]<=
                        fixed4_cancel_causes_record[instance_id*35+:35] |
                        leaf_terminal_causes | leaf_cause_now;
                if (leaf_retire_fire) fixed4_retire_accepted[instance_id]<=1;
                if (leaf_output_fire) begin
                    leaf_out_n<=leaf_out_n+10'd1;
                    fixed4_output_counts[instance_id*10+:10]<=leaf_out_n+10'd1;
                    if (m_qualified) fixed4_qualified_counts[instance_id*10+:10]<=
                        fixed4_qualified_counts[instance_id*10+:10]+10'd1;
                    if (!leaf_numeric) begin
                        numeric_error<=1;
                        if (first_error_code==ERR_NONE && fault_now==ERR_NONE)
                            first_error_code<=ERR_FIXED4_OVERFLOW;
                    end
                end
                if (kill_now) begin
                    transaction_cancelled<=1;
                    accumulated_cancel_causes<=cancel_union_now;
                    if (source_bad || report_bad || abort_bad || ip_bad || leaf_bad) begin
                        protocol_error<=1;
                        if (first_error_code==ERR_NONE) first_error_code<=fault_now;
                    end
                    if (source_bad && fault_now==ERR_SOURCE_NUMERIC) numeric_error<=1;
                    for (u=0;u<16;u=u+1)
                        if (unit_state[u*4+:4]==PENDING) unit_state[u*4+:4]<=CANCELLED;
                    if (ip_bad && unit_state[instance_id*4+:4]==PENDING)
                        unit_state[instance_id*4+:4]<=ERROR_PROTOCOL;
                    if (leaf_bad && unit_state[(instance_id+8)*4+:4]==PENDING)
                        unit_state[(instance_id+8)*4+:4]<=ERROR_PROTOCOL;
                    if (!transaction_cancelled) begin
                        abort_valid<=1;
                        abort_payload<={unit_state,hardware_started,physically_retired,
                            source_received,fft_in_n,fft_out_n,leaf_in_n,leaf_out_n,
                            instance_id,(first_error_code!=0 ? first_error_code : fault_now),
                            reliable_causes_now,{np_source_fire,cfg_fire,ip_in_fire,ip_out_fire,
                                           leaf_input_fire,leaf_output_fire},
                            !np_closed,ip_obligation,leaf_active};
                    end
                end
            end
            case (state)
                IDLE: if (source_begin_valid && source_begin_ready) begin
                    terminal_token<=source_token; terminal_generation<=source_generation;
                    terminal_context<=source_context; terminal_frame_first<=source_frame_first;
                    unit_state<=0; hardware_started<=0; physically_retired<=0;
                    fft_input_counts<=0; fft_output_counts<=0; fixed4_input_counts<=0;
                    fixed4_output_counts<=0; fixed4_qualified_counts<=0;
                    fft_status_raw<=0; fft_status_seen<=0; fft_event_seen<=0;
                    fixed4_contexts<=0; source_received<=0; transaction_cancelled<=0;
                    fixed4_cancel_causes_record<=0; fixed4_terminal_n_record<=0;
                    fixed4_terminal_p_record<=0; fixed4_cancelled_unsent_record<=0;
                    fixed4_terminal_t_bin_record<=0; fixed4_terminal_t_record<=0;
                    fixed4_terminal_s_record<=0; fixed4_cancel_saved<=0;
                    fixed4_retire_accepted<=0;
                    protocol_error<=0; numeric_error<=0; first_error_code<=0;
                    accumulated_cancel_causes<=0; source_report_record<=0;
                    source_abort_record<=0; source_report_seen<=0; source_abort_seen<=0;
                    np_closed<=0; instance_id<=0; fft_in_n<=0; fft_out_n<=0;
                    leaf_in_n<=0; leaf_out_n<=0; fft_frame_numeric_error<=0;
                    state<=COLLECT;
                end
                COLLECT: begin
                    if (np_source_fire && source_received==14'd8191) state<=WAIT_NP;
                    if ((transaction_cancelled || kill_now) && np_closed) state<=FINISH;
                end
                WAIT_NP: if (np_closed) begin
                    if (transaction_cancelled || kill_now) state<=FINISH;
                    else state<=CONFIG;
                end
                CONFIG: begin
                    if (cfg_fire) begin
                        ip_obligation<=1; hardware_started[instance_id]<=1;
                        fft_in_n<=0; fft_out_n<=0; fft_frame_numeric_error<=0;
                        state<=FEED;
                    end
                end
                FEED: if (ip_in_fire && fft_in_n==11'd1023) state<=DRAIN;
                DRAIN: if (fft_in_n==11'd1024 && fft_out_n==11'd1024 &&
                           fft_status_seen[instance_id]) begin
                    // A separate edge closes the real full-output/status obligation.
                    ip_obligation<=0; physically_retired[instance_id]<=1;
                    state<=FFT_FINAL;
                end
                FFT_FINAL: begin
                    if (transaction_cancelled || kill_now) state<=FINISH;
                    else if (fft_frame_numeric_error) begin
                        unit_state[instance_id*4+:4]<=ERROR_NUMERIC;
                        unit_state[(instance_id+8)*4+:4]<=NOT_RUN_NUMERIC;
                        physically_retired[instance_id+8]<=1;
                        state<=NEXT;
                    end else begin
                        unit_state[instance_id*4+:4]<=OK;
                        leaf_in_n<=0; leaf_out_n<=0; state<=LEAF_BEGIN;
                    end
                end
                LEAF_BEGIN: begin
                    if (leaf_begin_valid && leaf_begin_ready) begin
                        active_leaf_ctx<=next_leaf_ctx;
                        fixed4_contexts[instance_id*64+:64]<=next_leaf_ctx;
                        next_leaf_ctx<=next_leaf_ctx+64'd1;
                        hardware_started[instance_id+8]<=1;
                        state<=LEAF_RUN;
                    end else if (transaction_cancelled || kill_now) state<=FINISH;
                end
                LEAF_RUN: begin
                    if (leaf_cancelled) state<=LEAF_SAVE;
                    else if (leaf_done && !kill_now && !transaction_cancelled) begin
                        unit_state[(instance_id+8)*4+:4]<=leaf_overflow ? ERROR_NUMERIC : OK;
                        state<=LEAF_RETIRE;
                    end
                end
                LEAF_SAVE: if (leaf_saved) state<=LEAF_RETIRE;
                LEAF_RETIRE: begin
                    if (leaf_cancelled && !leaf_saved) state<=LEAF_SAVE;
                    else if (!leaf_active) begin
                        physically_retired[instance_id+8]<=1;
                        if (transaction_cancelled || kill_now) state<=FINISH;
                        else state<=NEXT;
                    end
                end
                NEXT: begin
                    if (transaction_cancelled || kill_now || instance_id==3'd7) state<=FINISH;
                    else begin instance_id<=instance_id+3'd1; state<=CONFIG; end
                end
                FINISH: if (np_closed && !ip_obligation && !leaf_active) begin
                    for (u=0;u<16;u=u+1) begin
                        if (!hardware_started[u]) physically_retired[u]<=1;
                        if (unit_state[u*4+:4]==PENDING) unit_state[u*4+:4]<=CANCELLED;
                    end
                    terminal_valid<=1; state<=REPORT;
                end
                REPORT: if (!terminal_valid && !abort_valid) state<=IDLE;
                default: begin
                    protocol_error<=1; transaction_cancelled<=1;
                    if (first_error_code==ERR_NONE) first_error_code<=ERR_FSM;
                    // Unknown FSM cannot certify IP drain; hold isolation.
                    state<=DRAIN;
                end
            endcase
        end
    end
endmodule
