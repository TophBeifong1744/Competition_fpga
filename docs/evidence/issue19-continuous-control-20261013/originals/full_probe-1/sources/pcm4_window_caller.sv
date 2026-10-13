`timescale 1ns/1ps
// CALLER-1.0-R3: private same-clk lifecycle join. No numerical backend/public ABI.
module pcm4_window_caller #(
    parameter logic [63:0] TOKEN_LIMIT = 64'hffff_ffff_ffff_ffff,
    parameter logic [63:0] GENERATION_LIMIT = 64'hffff_ffff_ffff_ffff
) (
    input wire clk, cold_rst_n,
    output wire slice_rst_n,
    input wire start_req_valid, output wire start_req_ready,
    input wire decl_boot_valid, input wire [63:0] decl_boot,
    input wire decl_epoch_valid, input wire [63:0] decl_epoch,
    input wire decl_sid_valid, input wire [31:0] decl_sid,
    input wire stop_req_valid, output wire stop_req_ready,
    input wire prepare_req_valid, output wire prepare_req_ready,
    input wire reset_req_valid, output wire reset_req_ready,
    input wire clear_req_valid, output wire clear_req_ready,
    output wire a_start_valid, input wire a_start_ready,
    output wire [31:0] a_start_session_id,
    output wire a_stop_valid, input wire a_stop_ready,
    input wire [31:0] source_status,
    input wire session_active, closing,
    input wire fault_latched,
    input wire [7:0] fault_code, fault_parent_code,
    input wire [31:0] fault_session_id, fault_source_status,
    input wire fault_session_valid, fault_id_valid, fault_after_terminal,
    input wire [63:0] fault_id,
    input wire m_valid, output wire m_ready, input wire [431:0] m_payload,
    input wire e_valid, output wire e_ready, input wire [415:0] e_payload,
    output wire desc_valid, input wire desc_ready,
    output wire [63:0] desc_token, desc_generation,
    output wire [431:0] desc_first, output wire [164:0] desc_context,
    input wire rd_valid, output wire rd_ready,
    input wire [63:0] rd_token, rd_generation,
    input wire [164:0] rd_context, input wire [9:0] rd_index,
    output wire rd_rsp_valid, input wire rd_rsp_ready,
    output wire [63:0] rd_rsp_token, rd_rsp_generation,
    output wire [164:0] rd_rsp_context, output wire [9:0] rd_rsp_index,
    output wire [1:0] rd_rsp_status,
    output wire [431:0] rd_rsp_payload, output wire rd_rsp_origin,
    input wire reader_close_valid, output wire reader_close_ready,
    input wire [63:0] reader_close_token, reader_close_generation,
    input wire reader_no_future_access,
    output wire terminal_valid, input wire terminal_ready,
    output wire [415:0] terminal_payload,
    output wire [164:0] terminal_context,
    output wire terminal_binding_valid,
    output wire [63:0] terminal_token, terminal_generation,
    output wire binding_valid,
    output wire [63:0] bound_token, bound_generation,
    output wire [164:0] current_context,
    output wire new_work_allowed,
    output wire source_save_valid, input wire source_save_ready,
    output wire [1055:0] source_save_payload,
    output wire retire_save_valid, input wire retire_save_ready,
    output wire [1183:0] retire_save_payload,
    output wire isolation_save_valid, input wire isolation_save_ready,
    output wire [1080:0] isolation_save_payload,
    output wire local_cancel_now, audit_capture_ready,
    output wire pending_cancel,
    output wire first_error_valid, output wire [7:0] first_error_code,
    output wire [2:0] lifecycle,
    output wire generation_exhausted, source_revision_exhausted,
    output wire isolation_revision_exhausted,
    output wire reset_barrier, token_exhausted, slot_active,
    output wire [63:0] slot_token,
    output wire [10:0] slot_count,
    output wire [2:0] slot_state,
    output wire [3:0] slot_error, output wire slot_revoked,
    output wire command_pending, command_wait_response,
    output wire [1:0] command_op,
    output wire [63:0] command_token,
    output wire [7:0] command_reason,
    output wire command_fire, command_response_fire,
    output wire [2:0] command_response_status,
    output wire reset_request_accepted, reset_candidate_authorized,
    output wire reset_guard_matches, reset_abort, slice_reset_executed,
    output wire [1323:0] reset_candidate_cut
);
    localparam [2:0] IDLE=0, RUN=1, PREPARING=2, WAIT_RETIRE=3,
        WAIT_SAVES=4, RESET_RECOVERY=5, WAIT_CLEAR=6, BLOCKED=7;
    localparam [1:0] RELEASE=0, REVOKE=1, WARM_RESET=2;
    localparam [7:0] SOURCE_CANCEL=8'ha1, CONTROLLED_PREPARE=8'ha2,
        IDENTITY_CONFLICT=8'ha3, CALLER_PROTOCOL_ERROR=8'ha4,
        INPUT_TRANSPORT_ERROR=8'ha5;
    localparam [7:0] IDENTITY_MISSING=1, SID_CONFLICT=2,
        BINDING_CONFLICT=3, COMMAND_ECHO=4, COMMAND_STATUS=5,
        AUDIT_CONFLICT=6, SOURCE_REVISION_LIMIT=7,
        ISOLATION_REVISION_LIMIT=8, SOURCE_HOLD=9,
        INPUT_ERROR=10, READ_RESPONSE_ERROR=11;

    // MSB first, a private record with explicit DECLARED/UNBOUND status.
    typedef struct packed {
        logic [1:0] status;
        logic boot_valid; logic [63:0] boot;
        logic epoch_valid; logic [63:0] epoch;
        logic sid_valid; logic [31:0] sid;
    } context_t;
    typedef struct packed {
        context_t context_tag;
        logic [31:0] status;
        logic first_valid; logic [4:0] first_mask, accumulated_mask;
        logic [31:0] first_source;
        logic first_sid_valid; logic [31:0] first_sid;
        logic native_valid; logic [147:0] native_fault;
        logic cancel; logic error_valid; logic [7:0] error_code;
        logic [431:0] first_row;
        logic [63:0] token, generation;
    } source_t;
    typedef struct packed {
        context_t context_tag;
        logic m_valid; logic [431:0] m;
        logic e_valid; logic [415:0] e;
        logic m_accepted, e_accepted;
    } isolation_t;
    typedef struct packed {
        context_t context_tag;
        logic [63:0] generation;
        logic [63:0] token;
        logic [10:0] count;
        logic [431:0] first;
        logic bad_valid; logic [431:0] bad;
        logic [3:0] error;
        logic revoked; logic [7:0] reason;
        logic [1:0] retire_op;
    } retire_t;
    // R3 H cut: raw guard fields are independent of A's slice reset gate.
    typedef struct packed {
        context_t context_tag;
        logic [31:0] source;
        logic native_valid; logic [147:0] native_fault;
        logic m_valid; logic [431:0] m;
        logic e_valid; logic [415:0] e;
        logic [63:0] source_revision, isolation_revision;
    } reset_cut_t;

    logic [2:0] state_q;
    context_t context_q, declared_context;
    logic binding_q, bind_wait_q;
    logic [63:0] token_q, generation_q, next_generation_q;
    logic [431:0] first_q;
    logic gen_exhausted_q, cancel_q;
    logic [7:0] cancel_reason_q;
    logic error_q, hard_failure_q;
    logic hard_error_now;
    logic [7:0] error_code_q;
    logic lease_q, reader_closed_q, read_outstanding_q;
    logic local_rsp_q;
    logic [63:0] request_token_q, request_generation_q;
    context_t request_context_q;
    logic [9:0] request_index_q;
    logic retire_phase_q, retired_q, retire_audit_seen_q;
    logic retired_active_q;
    logic [1:0] retired_op_q;
    logic cmd_offer_q, cmd_wait_q;
    logic [1:0] cmd_op_q;
    logic [63:0] cmd_token_q;
    logic [7:0] cmd_reason_q;
    context_t terminal_context_q;
    logic terminal_bound_q;
    logic [63:0] terminal_token_q, terminal_generation_q;
    logic [2:0] observed_slot_state_q;
    logic [10:0] observed_slot_count_q;
    logic prior_m_fire_q, prior_command_fire_q;
    logic reset_request_q, reset_candidate_q, reset_abort_q, reset_executed_q;
    reset_cut_t reset_cut_q;

    wire b_m_ready, b_e_ready, b_desc_valid;
    wire [63:0] b_desc_token;
    wire [431:0] b_desc_first;
    wire b_rd_ready, b_rsp_valid;
    wire [63:0] b_rsp_token;
    wire [9:0] b_rsp_index;
    wire [1:0] b_rsp_status;
    wire [431:0] b_rsp_payload;
    wire b_cmd_ready, b_cmd_rsp_valid;
    wire [63:0] b_cmd_rsp_token;
    wire [2:0] b_cmd_rsp_status;
    wire b_audit_valid;
    wire [63:0] b_audit_token;
    wire [10:0] b_audit_count;
    wire [431:0] b_audit_first, b_audit_bad;
    wire b_audit_bad_valid, b_audit_revoked;
    wire [3:0] b_audit_error;
    wire [7:0] b_audit_reason;
    wire [1:0] b_audit_op;
    wire b_terminal_valid;
    wire [415:0] b_terminal_payload;
    wire observer_pending, tracked_valid, accepted_stop_seen;
    wire [31:0] tracked_sid;
    wire first_observation_valid, first_session_valid, fault_audit_valid;
    wire [4:0] first_mask, accumulated_mask;
    wire [31:0] first_source, first_sid;
    wire [147:0] native_snapshot;
    wire observer_clear_ready;

    source_t source_now, source_mirror_q, source_front_q;
    isolation_t isolation_now, isolation_mirror_q, isolation_front_q;
    retire_t retire_front_q;
    logic source_front_valid_q, isolation_front_valid_q, retire_front_valid_q;
    logic [63:0] source_revision_q, source_front_revision_q, source_saved_revision_q;
    logic [63:0] isolation_revision_q, isolation_front_revision_q, isolation_saved_revision_q;
    logic source_exhausted_q, isolation_exhausted_q;
    logic isolation_observed_q;

    wire preparing = state_q==PREPARING || state_q==WAIT_RETIRE || state_q==WAIT_SAVES ||
        (state_q==RESET_RECOVERY && reset_request_q);
    wire prepare_fire = prepare_req_valid && prepare_req_ready;
    wire clear_fire = clear_req_valid && clear_req_ready;
    wire reset_fire = reset_req_valid && reset_req_ready;
    wire [147:0] raw_native_fault = {fault_latched, fault_code, fault_parent_code,
        fault_session_id, fault_source_status, fault_session_valid, fault_id_valid,
        fault_id, fault_after_terminal};
    // No e/session/closing/source_run/observer or slice-gated fact in this cone.
    wire raw_reset_guard = source_status==reset_cut_q.source &&
        fault_latched==reset_cut_q.native_valid &&
        (!fault_latched || raw_native_fault==reset_cut_q.native_fault) &&
        m_valid==reset_cut_q.m_valid && (!m_valid || m_payload==reset_cut_q.m);
    wire reset_candidate_live = reset_request_q && reset_candidate_q;
    wire reset_execute_now = reset_candidate_live && raw_reset_guard;
    // Authorized H hides A e until R; that gate is not a new isolation fact.
    wire isolation_observe = preparing && !reset_candidate_live;
    wire observer_prepare = preparing || prepare_fire;
    wire declarations_valid = decl_boot_valid && decl_epoch_valid && decl_sid_valid;
    wire source_watch = context_q.status!=0 || error_q || preparing || state_q==WAIT_CLEAR;
    wire source_current = !source_front_valid_q &&
        source_saved_revision_q==source_revision_q && source_mirror_q==source_now && !source_exhausted_q;
    wire isolation_current = isolation_observed_q && !isolation_front_valid_q &&
        isolation_saved_revision_q==isolation_revision_q &&
        isolation_mirror_q==isolation_now && !isolation_exhausted_q;
    wire saves_quiet = !retire_front_valid_q && !b_audit_valid && source_current;
    wire no_reader_work = !read_outstanding_q && !local_rsp_q && !b_rsp_valid;
    wire no_control_work = !cmd_offer_q && !cmd_wait_q;
    wire b_closed = !slot_active && !b_desc_valid && !lease_q && no_reader_work && no_control_work;
    // H may inspect slice-gated observation inputs while slice is still high.
    // A new P-post closing/fault mask bit must reach the real observer/save
    // before H authorization, even when the first native fault was saved earlier.
    wire observed_unexpected_close = tracked_valid && session_active && closing &&
        !accepted_stop_seen && !(a_stop_valid && a_stop_ready);
    wire [4:0] current_observation_mask = {observer_prepare,
        observed_unexpected_close, fault_latched, source_status[2], source_status[5]};
    wire observer_facts_captured = (accumulated_mask | current_observation_mask)==accumulated_mask;
    wire closure = b_closed && retired_q &&
        (!retired_active_q || retire_audit_seen_q) && saves_quiet &&
        audit_capture_ready && observer_facts_captured && isolation_current && !hard_failure_q;
    wire sid_conflict = context_q.status==1 &&
        ((tracked_valid && tracked_sid!=context_q.sid) ||
         (m_valid && m_payload[235:204]!=context_q.sid) ||
         (fault_latched && fault_session_valid && fault_session_id!=context_q.sid));
    wire binding_conflict = slot_state>3'd4 || slot_count>11'd1024 ||
        (binding_q && !prior_m_fire_q && !prior_command_fire_q &&
         (slot_state!=observed_slot_state_q || slot_count!=observed_slot_count_q)) ||
        (bind_wait_q && (!slot_active || slot_token==0 ||
        b_desc_first!=first_q || first_q[235:204]!=context_q.sid)) ||
        (binding_q && slot_active && slot_token!=token_q) ||
        (binding_q && b_desc_valid && (b_desc_token!=token_q || b_desc_first!=first_q)) ||
        (binding_q && !slot_active && !retired_q &&
         !(cmd_wait_q && cmd_op_q!=REVOKE));
    wire cancellation_now = cancel_q || local_cancel_now || prepare_fire ||
        sid_conflict || binding_conflict || slot_error!=0 || slot_revoked || error_q;
    wire forward_m = cold_rst_n && state_q==RUN && !prepare_fire && !retire_phase_q &&
        !hard_failure_q && !sid_conflict && !binding_conflict &&
        (slot_active || (!cancellation_now && !gen_exhausted_q && !retire_front_valid_q && !b_audit_valid));
    wire forward_e = cold_rst_n && state_q==RUN && !prepare_fire && !retire_phase_q && !hard_failure_q;
    wire m_fire = m_valid && m_ready;
    wire e_fire = e_valid && e_ready;
    wire desc_fire = desc_valid && desc_ready;
    wire live_read = binding_q && lease_q && !reader_closed_q && slot_active &&
        rd_token==token_q && rd_generation==generation_q && rd_context==context_q;
    wire rd_fire = rd_valid && rd_ready;
    wire response_fire = rd_rsp_valid && rd_rsp_ready;
    wire close_fire = reader_close_valid && reader_close_ready;
    wire audit_ready = cold_rst_n && !retire_front_valid_q && retired_q && retired_active_q && !hard_failure_q;
    wire audit_fire = b_audit_valid && audit_ready;
    wire hold_violation = isolation_observe && isolation_observed_q &&
        ((isolation_mirror_q.m_valid && (!m_valid || m_payload!=isolation_mirror_q.m)) ||
         (isolation_mirror_q.e_valid && (!e_valid || e_payload!=isolation_mirror_q.e)));
    wire command_bad_echo = command_response_fire && b_cmd_rsp_token!=cmd_token_q;
    wire read_response_error = b_rsp_valid &&
        (!read_outstanding_q || b_rsp_token!=request_token_q ||
         b_rsp_index!=request_index_q || b_rsp_status==2'd3);
    wire command_bad_status = command_response_fire &&
        (b_cmd_rsp_status>3 || b_cmd_rsp_status==1 ||
         (cmd_op_q==REVOKE && b_cmd_rsp_status!=0));
    wire audit_conflict = audit_fire &&
        (b_audit_token!=token_q || b_audit_op!=retired_op_q ||
         b_audit_first!=first_q || !binding_q || context_q.status!=1);

    always_comb begin
        declared_context.status=declarations_valid ? 2'd1 : 2'd0;
        declared_context.boot_valid=decl_boot_valid;
        declared_context.boot=decl_boot;
        declared_context.epoch_valid=decl_epoch_valid;
        declared_context.epoch=decl_epoch;
        declared_context.sid_valid=decl_sid_valid;
        declared_context.sid=decl_sid;
        source_now.context_tag=context_q;
        source_now.status=source_status;
        source_now.first_valid=first_observation_valid;
        source_now.first_mask=first_mask;
        source_now.accumulated_mask=accumulated_mask;
        source_now.first_source=first_source;
        source_now.first_sid_valid=first_session_valid;
        source_now.first_sid=first_sid;
        source_now.native_valid=fault_audit_valid;
        source_now.native_fault=native_snapshot;
        source_now.cancel=cancel_q || observer_pending;
        source_now.error_valid=error_q;
        source_now.error_code=error_code_q;
        source_now.first_row=first_q;
        source_now.token=token_q;
        source_now.generation=generation_q;
        isolation_now.context_tag=context_q;
        isolation_now.m_valid=m_valid;
        isolation_now.m=m_valid ? m_payload : 432'd0;
        isolation_now.e_valid=e_valid;
        isolation_now.e=e_valid ? e_payload : 416'd0;
        isolation_now.m_accepted=1'b0;
        isolation_now.e_accepted=1'b0;
    end

    assign lifecycle=state_q;
    assign slice_rst_n=cold_rst_n && !reset_execute_now;
    assign current_context=context_q;
    assign binding_valid=binding_q;
    assign bound_token=token_q;
    assign bound_generation=generation_q;
    assign pending_cancel=cancel_q || observer_pending;
    assign first_error_valid=error_q;
    assign first_error_code=error_code_q;
    assign generation_exhausted=gen_exhausted_q;
    assign source_revision_exhausted=source_exhausted_q;
    assign isolation_revision_exhausted=isolation_exhausted_q;
    assign prepare_req_ready=cold_rst_n && (state_q==RUN || state_q==IDLE) &&
        !hard_failure_q && no_control_work && !reset_req_valid && !clear_req_valid;
    assign start_req_ready=cold_rst_n && state_q==IDLE && !error_q && !local_cancel_now &&
        !prepare_req_valid && !clear_req_valid && !reset_req_valid && b_closed &&
        !retire_front_valid_q && !b_audit_valid && !source_front_valid_q &&
        !isolation_front_valid_q && !gen_exhausted_q && !token_exhausted &&
        (!declarations_valid || a_start_ready);
    assign a_start_valid=start_req_valid && cold_rst_n && state_q==IDLE &&
        declarations_valid && !error_q && !local_cancel_now &&
        !prepare_req_valid && !clear_req_valid && !reset_req_valid && b_closed &&
        !retire_front_valid_q && !b_audit_valid && !source_front_valid_q &&
        !isolation_front_valid_q && !gen_exhausted_q && !token_exhausted;
    assign a_start_session_id=decl_sid;
    assign a_stop_valid=stop_req_valid && cold_rst_n && state_q==RUN &&
        !prepare_req_valid && !reset_req_valid && !clear_req_valid;
    assign stop_req_ready=cold_rst_n && state_q==RUN && !prepare_req_valid &&
        !reset_req_valid && !clear_req_valid && a_stop_ready;
    assign reset_req_ready=cold_rst_n && state_q==WAIT_SAVES && closure && !clear_req_valid && !start_req_valid;
    assign clear_req_ready=cold_rst_n && state_q==WAIT_CLEAR && observer_clear_ready &&
        b_closed && saves_quiet && !hard_failure_q && !start_req_valid && !reset_req_valid;
    assign new_work_allowed=cold_rst_n && slice_rst_n && state_q==RUN && binding_q &&
        slot_active && slot_token==token_q && context_q.status==1 &&
        !cancellation_now && !hard_error_now && !reader_closed_q && !close_fire &&
        !retire_phase_q && !clear_req_valid && !reset_req_valid;
    assign m_ready=forward_m && b_m_ready;
    assign e_ready=forward_e && b_e_ready;
    assign desc_valid=cold_rst_n && b_desc_valid && binding_q;
    assign desc_token=b_desc_token;
    assign desc_first=b_desc_first;
    assign desc_generation=generation_q;
    assign desc_context=context_q;
    assign rd_ready=cold_rst_n && !read_outstanding_q && !local_rsp_q && !b_rsp_valid &&
        !hard_failure_q && !retire_phase_q && !prepare_fire && !reset_fire && !clear_fire &&
        state_q!=RESET_RECOVERY && (live_read ? b_rd_ready : 1'b1);
    assign rd_rsp_valid=cold_rst_n && (local_rsp_q || (read_outstanding_q && b_rsp_valid));
    assign rd_rsp_token=local_rsp_q ? request_token_q : b_rsp_token;
    assign rd_rsp_index=local_rsp_q ? request_index_q : b_rsp_index;
    assign rd_rsp_status=local_rsp_q ? 2'd1 : b_rsp_status;
    assign rd_rsp_payload=local_rsp_q ? 432'd0 : b_rsp_payload;
    assign rd_rsp_generation=request_generation_q;
    assign rd_rsp_context=request_context_q;
    assign rd_rsp_origin=local_rsp_q; // 0=B, 1=LOCAL_STALE
    assign reader_close_ready=cold_rst_n && lease_q && binding_q && !reader_closed_q &&
        reader_close_token==token_q && reader_close_generation==generation_q && reader_no_future_access && !hard_failure_q;
    assign terminal_valid=b_terminal_valid;
    assign terminal_payload=b_terminal_payload;
    assign terminal_context=terminal_context_q;
    assign terminal_binding_valid=terminal_bound_q;
    assign terminal_token=terminal_token_q;
    assign terminal_generation=terminal_generation_q;
    assign source_save_valid=cold_rst_n && source_front_valid_q;
    assign source_save_payload={source_front_revision_q,source_front_q};
    assign isolation_save_valid=cold_rst_n && isolation_front_valid_q;
    assign isolation_save_payload={isolation_front_revision_q,isolation_front_q};
    assign retire_save_valid=cold_rst_n && retire_front_valid_q;
    assign retire_save_payload=retire_front_q;
    assign command_pending=cmd_offer_q;
    assign command_wait_response=cmd_wait_q;
    assign command_op=cmd_op_q;
    assign command_token=cmd_token_q;
    assign command_reason=cmd_reason_q;
    assign command_fire=cold_rst_n && cmd_offer_q && b_cmd_ready;
    assign command_response_fire=cold_rst_n && cmd_wait_q && b_cmd_rsp_valid;
    assign command_response_status=b_cmd_rsp_status;
    assign reset_request_accepted=reset_fire;
    assign reset_candidate_authorized=cold_rst_n && reset_candidate_live;
    assign reset_guard_matches=cold_rst_n && reset_candidate_live && raw_reset_guard;
    assign reset_abort=cold_rst_n && reset_abort_q;
    assign slice_reset_executed=cold_rst_n && reset_executed_q;
    assign reset_candidate_cut=reset_cut_q;

    // CALLER-1.0-R3 phase H. Only these registers have a negedge writer.
    // P-after offers are visible here before candidate assertion hides e.
    always_ff @(negedge clk) begin
        if (!cold_rst_n) begin
            reset_candidate_q<=0; reset_cut_q<='0;
        end else begin
            reset_candidate_q<=0;
            if (state_q==RESET_RECOVERY && reset_request_q && closure &&
                !hard_error_now && !clear_req_valid && !start_req_valid) begin
                reset_candidate_q<=1;
                reset_cut_q.context_tag<=context_q;
                reset_cut_q.source<=source_status;
                reset_cut_q.native_valid<=fault_latched;
                reset_cut_q.native_fault<=fault_latched ? raw_native_fault : 148'd0;
                reset_cut_q.m_valid<=m_valid;
                reset_cut_q.m<=m_valid ? m_payload : 432'd0;
                reset_cut_q.e_valid<=e_valid;
                reset_cut_q.e<=e_valid ? e_payload : 416'd0;
                reset_cut_q.source_revision<=source_saved_revision_q;
                reset_cut_q.isolation_revision<=isolation_saved_revision_q;
            end
        end
    end

    pcm4_source_cancel_observer u_observer (
        .clk(clk), .slice_rst_n(slice_rst_n), .observer_cold_reset_i(!cold_rst_n),
        .prepare_reset_i(observer_prepare), .clear_preserved_i(clear_fire),
        .start_valid(a_start_valid), .start_ready(a_start_ready), .start_session_id(a_start_session_id),
        .stop_valid(a_stop_valid), .stop_ready(a_stop_ready),
        .source_status(source_status), .session_active(session_active), .closing(closing), .e_valid(e_valid),
        .fault_latched(fault_latched), .fault_code(fault_code), .fault_parent_code(fault_parent_code),
        .fault_session_id(fault_session_id), .fault_source_status(fault_source_status),
        .fault_session_valid(fault_session_valid), .fault_id_valid(fault_id_valid),
        .fault_after_terminal(fault_after_terminal), .fault_id(fault_id),
        .local_cancel_now(local_cancel_now), .audit_capture_ready(audit_capture_ready),
        .clear_preserved_ready(observer_clear_ready), .cancellation_pending(observer_pending),
        .tracked_session_valid(tracked_valid), .tracked_session_id(tracked_sid),
        .accepted_stop_seen(accepted_stop_seen), .first_observation_valid(first_observation_valid),
        .first_observation_mask(first_mask), .accumulated_observation_mask(accumulated_mask),
        .first_source_status(first_source), .first_session_valid(first_session_valid),
        .first_session_id(first_sid), .fault_audit_valid(fault_audit_valid), .fault_audit_snapshot(native_snapshot),
        .fault_audit_code(), .fault_audit_parent_code(), .fault_audit_session_id(),
        .fault_audit_source_status(), .fault_audit_session_valid(), .fault_audit_id_valid(),
        .fault_audit_after_terminal(), .fault_audit_id()
    );
    pcm4_window_consumer #(.TOKEN_LIMIT(TOKEN_LIMIT)) u_consumer (
        .clk(clk), .rst_n(cold_rst_n), .m_valid(m_valid && forward_m), .m_ready(b_m_ready), .m_payload(m_payload),
        .e_valid(e_valid && forward_e), .e_ready(b_e_ready), .e_payload(e_payload),
        .terminal_valid(b_terminal_valid), .terminal_ready(terminal_ready), .terminal_payload(b_terminal_payload),
        .desc_valid(b_desc_valid), .desc_ready(desc_ready && binding_q), .desc_token(b_desc_token), .desc_first(b_desc_first),
        .rd_valid(rd_valid && rd_ready && live_read), .rd_ready(b_rd_ready), .rd_token(rd_token), .rd_index(rd_index),
        .rd_rsp_valid(b_rsp_valid), .rd_rsp_ready(rd_rsp_ready && read_outstanding_q && !local_rsp_q),
        .rd_rsp_token(b_rsp_token), .rd_rsp_index(b_rsp_index), .rd_rsp_status(b_rsp_status), .rd_rsp_payload(b_rsp_payload),
        .cmd_valid(cmd_offer_q && cold_rst_n), .cmd_ready(b_cmd_ready), .cmd_op(cmd_op_q), .cmd_token(cmd_token_q),
        .cmd_reason(cmd_reason_q), .cmd_rsp_valid(b_cmd_rsp_valid), .cmd_rsp_ready(cmd_wait_q),
        .cmd_rsp_token(b_cmd_rsp_token), .cmd_rsp_status(b_cmd_rsp_status),
        .audit_valid(b_audit_valid), .audit_ready(audit_ready), .audit_token(b_audit_token), .audit_count(b_audit_count),
        .audit_first(b_audit_first), .audit_bad_valid(b_audit_bad_valid), .audit_bad(b_audit_bad),
        .audit_error(b_audit_error), .audit_revoked(b_audit_revoked), .audit_reason(b_audit_reason), .audit_retire_op(b_audit_op),
        .reset_barrier(reset_barrier), .token_exhausted(token_exhausted), .slot_active(slot_active), .slot_token(slot_token),
        .slot_count(slot_count), .slot_state(slot_state), .slot_error(slot_error), .slot_revoked(slot_revoked)
    );

    // One prioritized first error. Later A mask/native facts remain independent.
    logic [7:0] error_now;
    always_comb begin
        error_now=0; hard_error_now=1'b0;
        if (command_bad_echo) begin error_now=COMMAND_ECHO; hard_error_now=1'b1; end
        else if (command_bad_status) begin error_now=COMMAND_STATUS; hard_error_now=1'b1; end
        else if (audit_conflict) begin error_now=AUDIT_CONFLICT; hard_error_now=1'b1; end
        else if (binding_conflict) begin error_now=BINDING_CONFLICT; hard_error_now=1'b1; end
        else if (read_response_error) begin error_now=READ_RESPONSE_ERROR; hard_error_now=1'b1; end
        else if (hold_violation) begin error_now=SOURCE_HOLD; hard_error_now=1'b1; end
        else if (source_exhausted_q) begin error_now=SOURCE_REVISION_LIMIT; hard_error_now=1'b1; end
        else if (isolation_exhausted_q) begin error_now=ISOLATION_REVISION_LIMIT; hard_error_now=1'b1; end
        else if (sid_conflict) error_now=SID_CONFLICT;
        else if (slot_error!=0) error_now=INPUT_ERROR;
        else if (start_req_valid && start_req_ready && !declarations_valid) error_now=IDENTITY_MISSING;
    end

    always_ff @(posedge clk) begin
        if (!cold_rst_n) begin
            state_q<=IDLE; context_q<='0;
            binding_q<=0; bind_wait_q<=0; token_q<=0; generation_q<=0; first_q<=0;
            next_generation_q<=64'd1; gen_exhausted_q<=(GENERATION_LIMIT==0);
            cancel_q<=0; cancel_reason_q<=0; error_q<=0; error_code_q<=0; hard_failure_q<=0;
            lease_q<=0; reader_closed_q<=0; read_outstanding_q<=0; local_rsp_q<=0;
            request_token_q<=0; request_generation_q<=0; request_context_q<='0; request_index_q<=0;
            retire_phase_q<=0; retired_q<=0; retired_active_q<=0; retire_audit_seen_q<=0; retired_op_q<=WARM_RESET;
            cmd_offer_q<=0; cmd_wait_q<=0; cmd_op_q<=WARM_RESET; cmd_token_q<=0; cmd_reason_q<=0;
            terminal_context_q<='0; terminal_bound_q<=0; terminal_token_q<=0; terminal_generation_q<=0;
            observed_slot_state_q<=0; observed_slot_count_q<=0;
            prior_m_fire_q<=0; prior_command_fire_q<=0;
            reset_request_q<=0; reset_abort_q<=0; reset_executed_q<=0;
            source_mirror_q<='0; source_front_q<='0; source_front_valid_q<=0;
            source_revision_q<=0; source_front_revision_q<=0; source_saved_revision_q<=0; source_exhausted_q<=0;
            isolation_mirror_q<='0; isolation_front_q<='0; isolation_front_valid_q<=0;
            isolation_revision_q<=0; isolation_front_revision_q<=0; isolation_saved_revision_q<=0;
            isolation_exhausted_q<=0; isolation_observed_q<=0;
            retire_front_q<='0; retire_front_valid_q<=0;
        end else begin
            reset_abort_q<=0; reset_executed_q<=0;
            observed_slot_state_q<=slot_state; observed_slot_count_q<=slot_count;
            prior_m_fire_q<=m_fire; prior_command_fire_q<=command_fire;
            // Every ACK releases only an existing entry; it cannot refill that E.
            if (source_front_valid_q && source_save_ready) begin
                source_front_valid_q<=0;
                source_saved_revision_q<=source_front_revision_q;
            end
            if (source_watch && source_now!=source_mirror_q) begin
                if (&source_revision_q) source_exhausted_q<=1;
                else begin source_mirror_q<=source_now; source_revision_q<=source_revision_q+64'd1; end
            end
            if (!source_front_valid_q && source_saved_revision_q!=source_revision_q) begin
                source_front_valid_q<=1; source_front_q<=source_mirror_q; source_front_revision_q<=source_revision_q;
            end
            if (isolation_front_valid_q && isolation_save_ready) begin
                isolation_front_valid_q<=0; isolation_saved_revision_q<=isolation_front_revision_q;
            end
            if (isolation_observe && (!isolation_observed_q || isolation_now!=isolation_mirror_q)) begin
                if (&isolation_revision_q) isolation_exhausted_q<=1;
                else begin
                    isolation_mirror_q<=isolation_now; isolation_revision_q<=isolation_revision_q+64'd1;
                    isolation_observed_q<=1;
                end
            end
            if (!isolation_front_valid_q && isolation_saved_revision_q!=isolation_revision_q) begin
                isolation_front_valid_q<=1; isolation_front_q<=isolation_mirror_q;
                isolation_front_revision_q<=isolation_revision_q;
            end
            if (retire_front_valid_q && retire_save_ready) retire_front_valid_q<=0;
            if (audit_fire) begin
                retire_front_valid_q<=1; retire_audit_seen_q<=1;
                retire_front_q.context_tag<=context_q; retire_front_q.generation<=generation_q;
                retire_front_q.token<=b_audit_token; retire_front_q.count<=b_audit_count;
                retire_front_q.first<=b_audit_first; retire_front_q.bad_valid<=b_audit_bad_valid;
                retire_front_q.bad<=b_audit_bad; retire_front_q.error<=b_audit_error;
                retire_front_q.revoked<=b_audit_revoked; retire_front_q.reason<=b_audit_reason;
                retire_front_q.retire_op<=b_audit_op;
            end
            if (error_now!=0) begin
                if (!error_q) begin error_q<=1; error_code_q<=error_now; end
                if (hard_error_now) begin hard_failure_q<=1; state_q<=BLOCKED; end
            end
            if (cancellation_now && !cancel_q) begin
                cancel_q<=1;
                if (sid_conflict || binding_conflict) cancel_reason_q<=IDENTITY_CONFLICT;
                else if (slot_error!=0) cancel_reason_q<=INPUT_TRANSPORT_ERROR;
                else if (prepare_fire) cancel_reason_q<=CONTROLLED_PREPARE;
                else if (error_q) cancel_reason_q<=CALLER_PROTOCOL_ERROR;
                else cancel_reason_q<=SOURCE_CANCEL;
            end
            if (start_req_valid && start_req_ready) begin
                if (declarations_valid) begin context_q<=declared_context; state_q<=RUN; end
                // Illegal declaration is retained exactly, with UNBOUND status.
                else begin context_q<=declared_context; cancel_q<=1; cancel_reason_q<=IDENTITY_CONFLICT; end
            end
            if (m_fire && !slot_active) begin
                first_q<=m_payload; generation_q<=next_generation_q;
                if (next_generation_q==GENERATION_LIMIT) gen_exhausted_q<=1;
                else next_generation_q<=next_generation_q+64'd1;
                bind_wait_q<=1; binding_q<=0; token_q<=0;
            end
            if (bind_wait_q) begin
                bind_wait_q<=0;
                if (slot_active && slot_token!=0 && first_q[235:204]==context_q.sid &&
                    b_desc_first==first_q && !binding_conflict) begin
                    token_q<=slot_token; binding_q<=1;
                end
            end
            if (desc_fire) begin lease_q<=1; reader_closed_q<=0; end
            if (rd_fire) begin
                request_token_q<=rd_token; request_generation_q<=rd_generation;
                request_context_q<=rd_context; request_index_q<=rd_index;
                if (live_read) read_outstanding_q<=1; else local_rsp_q<=1;
            end
            if (response_fire) begin read_outstanding_q<=0; local_rsp_q<=0; end
            if (close_fire) reader_closed_q<=1;
            if (e_fire) begin
                terminal_context_q<=context_q; terminal_bound_q<=binding_q;
                terminal_token_q<=binding_q ? token_q : 64'd0;
                terminal_generation_q<=binding_q ? generation_q : 64'd0;
            end
            if (prepare_fire) begin
                state_q<=PREPARING; retire_phase_q<=1; isolation_observed_q<=0;
                if (!retire_phase_q) begin
                    retired_q<=0; retired_active_q<=0; retire_audit_seen_q<=0;
                end
            end
            if (state_q==PREPARING) state_q<=WAIT_RETIRE;
            if (state_q==RUN && slot_active &&
                ((lease_q && reader_closed_q) || slot_state==3)) retire_phase_q<=1;

            // Own one stable management transaction from offer through response.
            if (command_fire) begin cmd_offer_q<=0; cmd_wait_q<=1; end
            if (command_response_fire) begin
                cmd_wait_q<=0;
                if (!command_bad_echo && !command_bad_status && b_cmd_rsp_status==0 && cmd_op_q!=REVOKE) begin
                    retired_q<=1; retired_active_q<=binding_q; retired_op_q<=cmd_op_q;
                    lease_q<=0;
                end
                // BUSY/AUDIT_FULL leave the logical retire request latched.
                // The next offer is only formed on a later edge, after closure.
            end
            if (!cmd_offer_q && !cmd_wait_q && !hard_failure_q && !hard_error_now && state_q!=BLOCKED) begin
                if (cancellation_now && binding_q && slot_active && !slot_revoked) begin
                    cmd_offer_q<=1; cmd_op_q<=REVOKE; cmd_token_q<=token_q;
                    cmd_reason_q<=cancel_q ? cancel_reason_q :
                        (sid_conflict ? IDENTITY_CONFLICT : (slot_error!=0 ? INPUT_TRANSPORT_ERROR :
                         (prepare_fire ? CONTROLLED_PREPARE : SOURCE_CANCEL)));
                end else if (retire_phase_q && !retired_q && !b_desc_valid && no_reader_work &&
                             (!lease_q || reader_closed_q) && !retire_front_valid_q && !b_audit_valid &&
                             (!slot_active || binding_q) && (!cancellation_now || !slot_active || slot_revoked)) begin
                    cmd_offer_q<=1; cmd_op_q<=lease_q ? RELEASE : WARM_RESET;
                    cmd_token_q<=slot_active ? token_q : 64'd0;
                    cmd_reason_q<=cancel_reason_q;
                end
            end
            if (state_q==WAIT_RETIRE && b_closed && retired_q &&
                (!retired_active_q || retire_audit_seen_q) && !retire_front_valid_q && !b_audit_valid)
                state_q<=WAIT_SAVES;
            // A normal window can retire without resetting its continuing A session.
            if (state_q==RUN && !prepare_fire && retire_phase_q && b_closed && retired_q &&
                (!retired_active_q || retire_audit_seen_q) && !retire_front_valid_q && !b_audit_valid && source_current) begin
                retire_phase_q<=0; retired_q<=0; retired_active_q<=0; retire_audit_seen_q<=0;
                binding_q<=0; token_q<=0; generation_q<=0; first_q<=0; reader_closed_q<=0;
            end
            if (reset_fire) begin
                state_q<=RESET_RECOVERY; reset_request_q<=1;
            end
            if (state_q==RESET_RECOVERY && reset_request_q) begin
                reset_request_q<=0;
                if (reset_execute_now) begin
                    reset_executed_q<=1; state_q<=WAIT_CLEAR;
                end else begin
                    reset_abort_q<=1; state_q<=WAIT_SAVES;
                end
                // Post-R changes cannot be reclassified as an abort: request
                // is cleared at R and the H cut is not overwritten here.
            end
            if (clear_fire) begin
                state_q<=IDLE; context_q<='0; binding_q<=0; bind_wait_q<=0;
                token_q<=0; generation_q<=0; first_q<=0;
                cancel_q<=0; cancel_reason_q<=0; error_q<=0; error_code_q<=0;
                reader_closed_q<=0; retire_phase_q<=0; retired_q<=0;
                retired_active_q<=0; retire_audit_seen_q<=0; isolation_observed_q<=0;
                // All allocators, terminal and immutable save histories survive.
            end
            // Hard control/hold errors dominate all normal transitions.
            if (hard_error_now || hard_failure_q) state_q<=BLOCKED;
        end
    end
endmodule
