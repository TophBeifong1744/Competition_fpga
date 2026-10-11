`timescale 1ns/1ps
// TEST_ONLY same-clock forward join. Original caller owns the sole window lease.
module forward_window_adapter #(
    parameter integer SOURCE_DEPTH=64, OTHER_DEPTH=8, WATCHDOG_BITS=23,
    parameter HANN_FILE="inputs/a_numeric/inputs/b_np/hann-u18f17.mem"
)(
    input wire clk, input wire cold_rst_n,
    // FF-1.0 full same-clock output boundary. No summary substitute or forced ACK.
    input wire research_profile_valid,
    output wire ff_quiet, ff_session_aborted,
    output wire ff_np_data_clear_valid, ff_np_data_clear_ready,
    input wire ff_cancel_now,
    input wire [7:0] ff_cancel_causes,
    output wire ff_controlled_clear_valid,
    output wire ff_controlled_clear_ready,
    input wire ff_fft_output_permit,
    input wire ff_fft_status_permit,
    output wire ff_m_valid,
    input wire ff_m_ready,
    output wire [63:0] ff_m_token,
    output wire [63:0] ff_m_generation,
    output wire [164:0] ff_m_context,
    output wire [431:0] ff_m_frame_first,
    output wire ff_m_domain,
    output wire [1:0] ff_m_channel,
    output wire [9:0] ff_m_bin,
    output wire signed [24:0] ff_m_real,
    output wire signed [24:0] ff_m_imag,
    output wire ff_m_numeric_valid,
    output wire ff_m_ov_real,
    output wire ff_m_ov_imag,
    output wire ff_m_qualified,
    output wire ff_terminal_valid,
    input wire ff_terminal_ready,
    output wire [63:0] ff_terminal_token,
    output wire [63:0] ff_terminal_generation,
    output wire [164:0] ff_terminal_context,
    output wire [431:0] ff_terminal_frame_first,
    output wire [63:0] ff_unit_state,
    output wire [15:0] ff_hardware_started,
    output wire [15:0] ff_physically_retired,
    output wire [87:0] ff_fft_input_counts,
    output wire [87:0] ff_fft_output_counts,
    output wire [79:0] ff_fixed4_input_counts,
    output wire [79:0] ff_fixed4_output_counts,
    output wire [79:0] ff_fixed4_qualified_counts,
    output wire [63:0] ff_fft_status_raw,
    output wire [7:0] ff_fft_status_seen,
    output wire [55:0] ff_fft_event_seen,
    output wire [511:0] ff_fixed4_contexts,
    output wire [279:0] ff_fixed4_cancel_causes_record,
    output wire [79:0] ff_fixed4_terminal_n_record,
    output wire [79:0] ff_fixed4_terminal_p_record,
    output wire [79:0] ff_fixed4_cancelled_unsent_record,
    output wire [79:0] ff_fixed4_terminal_t_bin_record,
    output wire [7:0] ff_fixed4_terminal_t_record,
    output wire [7:0] ff_fixed4_terminal_s_record,
    output wire [7:0] ff_fixed4_cancel_saved,
    output wire [7:0] ff_fixed4_retire_accepted,
    output wire [13:0] ff_source_received,
    output wire ff_transaction_cancelled,
    output wire ff_protocol_error,
    output wire ff_numeric_error,
    output wire [7:0] ff_first_error_code,
    output wire [7:0] ff_accumulated_cancel_causes,
    output wire [2001:0] ff_source_report_record,
    output wire [2079:0] ff_source_abort_record,
    output wire ff_source_report_seen,
    output wire ff_source_abort_seen,
    output wire ff_abort_valid,
    input wire ff_abort_ready,
    output wire [179:0] ff_abort_payload,
    output wire ff_busy,
    output wire ff_ip_obligation,
    output wire ff_leaf_obligation,
    output wire [3:0] ff_debug_state,
    output wire ff_fft_audit_valid,
    output wire ff_fft_audit_status,
    output wire [2:0] ff_fft_audit_instance,
    output wire [9:0] ff_fft_audit_bin,
    output wire signed [28:0] ff_fft_audit_real,
    output wire signed [28:0] ff_fft_audit_imag,
    output wire [7:0] ff_fft_audit_status_raw,
    output wire ff_fft_audit_last,
    output wire ff_fft_audit_on_cancel,
    output wire ff_np_busy,
    output wire ff_np_read_pending,
    input wire frontend_ready,
    input wire [3:0] pcm_valid, clipped,
    input wire [95:0] pcm, input wire [63:0] sample_id,
    input wire diag_reset, diag_start, diag_stop,
    input wire diag_config_valid, output wire diag_config_ready,
    input wire diag_boot_valid, input wire [63:0] diag_boot,
    input wire diag_epoch_valid, input wire [63:0] diag_decl_epoch,
    input wire diag_sid_valid, input wire [31:0] diag_decl_sid,
    input wire diag_export_select, input wire [2:0] diag_export_select_bank,
    input wire diag_export_ack, input wire [63:0] diag_export_ack_seq,
    input wire [5:0] diag_export_ack_word, input wire diag_export_abort,
    output wire diag_export_valid, output wire [31:0] diag_export_data,
    output wire [2:0] diag_export_bank, output wire [63:0] diag_export_seq,
    output wire [5:0] diag_export_word, diag_export_words,
    output wire diag_export_last,
    output wire [31:0] diag_bank_counts,
    output wire [7:0] diag_manager_state,
    output wire [31:0] diag_local_error,
    output wire [63:0] diag_cycle, diag_capture_seq,
    output wire diag_m_valid, output wire [431:0] diag_m_payload,
    output wire diag_e_valid, output wire [415:0] diag_e_payload,
    output reg [415:0] diag_last_terminal, output reg diag_last_terminal_valid,
    output wire [31:0] diag_session_id, diag_source_status, diag_epoch,
    output wire [223:0] diag_counts, output wire [128:0] diag_ids,
    output wire [31:0] diag_control,
    output wire [176:0] diag_m_meta, output wire [48:0] diag_e_meta,
    output wire [147:0] diag_fault,
    output wire [207:0] diag_terminal_lo, diag_terminal_hi
);
    wire  slice_rst_n;
    wire  start_req_valid;
    wire  start_req_ready;
    wire  decl_boot_valid;
    wire [63:0] decl_boot;
    wire  decl_epoch_valid;
    wire [63:0] decl_epoch;
    wire  decl_sid_valid;
    wire [31:0] decl_sid;
    wire  stop_req_valid;
    wire  stop_req_ready;
    wire  prepare_req_valid;
    wire  prepare_req_ready;
    wire  reset_req_valid;
    wire  reset_req_ready;
    wire  clear_req_valid;
    wire  clear_req_ready;
    wire [31:0] source_status;
    wire  session_active;
    wire  closing;
    wire  fault_latched;
    wire [7:0] fault_code;
    wire [7:0] fault_parent_code;
    wire [31:0] fault_session_id;
    wire [31:0] fault_source_status;
    wire  fault_session_valid;
    wire  fault_id_valid;
    wire  fault_after_terminal;
    wire [63:0] fault_id;
    wire  m_valid;
    wire  m_ready;
    wire  e_valid;
    wire  e_ready;
    wire  desc_valid;
    wire  desc_ready;
    wire [63:0] desc_token;
    wire [63:0] desc_generation;
    wire [431:0] desc_first;
    wire [164:0] desc_context;
    wire  rd_valid;
    wire  rd_ready;
    wire [63:0] rd_token;
    wire [63:0] rd_generation;
    wire [164:0] rd_context;
    wire [9:0] rd_index;
    wire  rd_rsp_valid;
    wire  rd_rsp_ready;
    wire [63:0] rd_rsp_token;
    wire [63:0] rd_rsp_generation;
    wire [164:0] rd_rsp_context;
    wire [9:0] rd_rsp_index;
    wire [1:0] rd_rsp_status;
    wire [431:0] rd_rsp_payload;
    wire  rd_rsp_origin;
    wire  reader_close_valid;
    wire  reader_close_ready;
    wire [63:0] reader_close_token;
    wire [63:0] reader_close_generation;
    wire  reader_no_future_access;
    wire  terminal_valid;
    wire  terminal_ready;
    wire [415:0] terminal_payload;
    wire [164:0] terminal_context;
    wire  terminal_binding_valid;
    wire [63:0] terminal_token;
    wire [63:0] terminal_generation;
    wire  binding_valid;
    wire [63:0] bound_token;
    wire [63:0] bound_generation;
    wire [164:0] current_context;
    wire  new_work_allowed;
    wire  source_save_valid;
    wire  source_save_ready;
    wire [1055:0] source_save_payload;
    wire  retire_save_valid;
    wire  retire_save_ready;
    wire [1183:0] retire_save_payload;
    wire  isolation_save_valid;
    wire  isolation_save_ready;
    wire [1080:0] isolation_save_payload;
    wire  local_cancel_now;
    wire  audit_capture_ready;
    wire  pending_cancel;
    wire  first_error_valid;
    wire [7:0] first_error_code;
    wire [2:0] lifecycle;
    wire  generation_exhausted;
    wire  source_revision_exhausted;
    wire  isolation_revision_exhausted;
    wire  reset_barrier;
    wire  token_exhausted;
    wire  slot_active;
    wire [63:0] slot_token;
    wire [10:0] slot_count;
    wire [2:0] slot_state;
    wire [3:0] slot_error;
    wire  slot_revoked;
    wire  command_pending;
    wire  command_wait_response;
    wire [1:0] command_op;
    wire [63:0] command_token;
    wire [7:0] command_reason;
    wire  command_fire;
    wire  command_response_fire;
    wire [2:0] command_response_status;
    wire  reset_request_accepted;
    wire  reset_candidate_authorized;
    wire  reset_guard_matches;
    wire  reset_abort;
    wire  slice_reset_executed;
    wire [1323:0] reset_candidate_cut;
    wire  source_run;
    wire [127:0] m_pcm;
    wire [63:0] m_id;
    wire [3:0] m_flags;
    wire [31:0] m_session_id;
    wire [31:0] m_frame_index;
    wire [31:0] m_interval_index;
    wire [9:0] m_sample_index;
    wire [63:0] m_first_id;
    wire [63:0] m_last_id;
    wire  m_reset_before;
    wire  m_last;
    wire [7:0] e_code;
    wire [7:0] e_parent_code;
    wire [31:0] e_source_status;
    wire  e_source_drained;
    wire [31:0] e_session_id;
    wire [63:0] e_id;
    wire [63:0] e_prev_id;
    wire  e_id_valid;
    wire  e_prev_id_valid;
    wire [31:0] e_raw_flags;
    wire [7:0] e_source_flags;
    wire [10:0] e_unused_tail;
    wire [31:0] e_interval_index;
    wire [31:0] e_packet_index;
    wire [10:0] e_word_index;
    wire [10:0] e_packet_words;
    wire [31:0] e_tdata;
    wire [3:0] e_tkeep;
    wire  e_tlast;
    wire [7:0] e_drop_buffered_groups;
    wire [7:0] e_drop_verified_groups;
    wire [2:0] e_framer_code;
    wire [10:0] e_framer_error_tail;
    wire  e_stop_truncated;
    wire  actual_start_valid;
    wire  actual_start_ready;
    wire  actual_stop_valid;
    wire  actual_stop_ready;
    wire bank_warning,bank_full,allocator_exhausted;
    wire halt_reader;
    // Busy halt creates real one-shot clear events through each module's ready.
    // Historical halt never drives the independent current kill; after cancel,
    // controlled_clear_ready drops so an already saved leaf can really retire.
    // Idle remains open for a cancelled historical descriptor's lease discharge.
    assign ff_np_data_clear_valid=cold_rst_n && halt_reader && ff_np_busy;
    assign ff_controlled_clear_valid=cold_rst_n && halt_reader && ff_busy;
    assign ff_quiet=!desc_valid && !ff_np_busy && !ff_np_read_pending && !ff_busy &&
        !ff_ip_obligation && !ff_leaf_obligation && !ff_m_valid &&
        !ff_terminal_valid && !ff_abort_valid;
    // Normal STOP must also retire caller and source-side obligations.
    // This is intentionally separate from warm reset/clear ff_quiet.
    wire normal_source_quiet=!m_valid && !e_valid && !slot_active &&
        !binding_valid && !command_pending && !command_wait_response &&
        !rd_rsp_valid && !reader_close_valid && !terminal_valid &&
        !source_save_valid && !retire_save_valid && !isolation_save_valid;
    wire config_present,terminal_seen,local_error_valid;
    wire [7:0] local_error_code,store_error_code;
    wire store_error;
    wire [31:0] frame_count;
    wire [63:0] start_count,stop_count,row_count,terminal_count;
    wire [709:0] terminal_record={terminal_payload,terminal_context,
        terminal_binding_valid,terminal_token,terminal_generation};
    wire terminal_copy=terminal_valid && terminal_ready;
    wire [431:0] m_payload={m_pcm,m_id,m_flags,m_session_id,m_frame_index,
        m_interval_index,m_sample_index,m_first_id,m_last_id,m_reset_before,m_last};
    wire [415:0] e_payload={e_code,e_parent_code,e_source_status,e_source_drained,
        e_session_id,e_id,e_prev_id,e_id_valid,e_prev_id_valid,e_raw_flags,e_source_flags,
        e_unused_tail,e_interval_index,e_packet_index,e_word_index,e_packet_words,e_tdata,
        e_tkeep,e_tlast,e_drop_buffered_groups,e_drop_verified_groups,e_framer_code,
        e_framer_error_tail,e_stop_truncated};
    pcm4_window_caller_entry u_entry (
        .clk(clk),
        .cold_rst_n(cold_rst_n),
        .slice_rst_n(slice_rst_n),
        .start_req_valid(start_req_valid),
        .start_req_ready(start_req_ready),
        .decl_boot_valid(decl_boot_valid),
        .decl_boot(decl_boot),
        .decl_epoch_valid(decl_epoch_valid),
        .decl_epoch(decl_epoch),
        .decl_sid_valid(decl_sid_valid),
        .decl_sid(decl_sid),
        .stop_req_valid(stop_req_valid),
        .stop_req_ready(stop_req_ready),
        .prepare_req_valid(prepare_req_valid),
        .prepare_req_ready(prepare_req_ready),
        .reset_req_valid(reset_req_valid),
        .reset_req_ready(reset_req_ready),
        .clear_req_valid(clear_req_valid),
        .clear_req_ready(clear_req_ready),
        .source_status(source_status),
        .session_active(session_active),
        .closing(closing),
        .fault_latched(fault_latched),
        .fault_code(fault_code),
        .fault_parent_code(fault_parent_code),
        .fault_session_id(fault_session_id),
        .fault_source_status(fault_source_status),
        .fault_session_valid(fault_session_valid),
        .fault_id_valid(fault_id_valid),
        .fault_after_terminal(fault_after_terminal),
        .fault_id(fault_id),
        .m_valid(m_valid),
        .m_ready(m_ready),
        .e_valid(e_valid),
        .e_ready(e_ready),
        .desc_valid(desc_valid),
        .desc_ready(desc_ready),
        .desc_token(desc_token),
        .desc_generation(desc_generation),
        .desc_first(desc_first),
        .desc_context(desc_context),
        .rd_valid(rd_valid),
        .rd_ready(rd_ready),
        .rd_token(rd_token),
        .rd_generation(rd_generation),
        .rd_context(rd_context),
        .rd_index(rd_index),
        .rd_rsp_valid(rd_rsp_valid),
        .rd_rsp_ready(rd_rsp_ready),
        .rd_rsp_token(rd_rsp_token),
        .rd_rsp_generation(rd_rsp_generation),
        .rd_rsp_context(rd_rsp_context),
        .rd_rsp_index(rd_rsp_index),
        .rd_rsp_status(rd_rsp_status),
        .rd_rsp_payload(rd_rsp_payload),
        .rd_rsp_origin(rd_rsp_origin),
        .reader_close_valid(reader_close_valid),
        .reader_close_ready(reader_close_ready),
        .reader_close_token(reader_close_token),
        .reader_close_generation(reader_close_generation),
        .reader_no_future_access(reader_no_future_access),
        .terminal_valid(terminal_valid),
        .terminal_ready(terminal_ready),
        .terminal_payload(terminal_payload),
        .terminal_context(terminal_context),
        .terminal_binding_valid(terminal_binding_valid),
        .terminal_token(terminal_token),
        .terminal_generation(terminal_generation),
        .binding_valid(binding_valid),
        .bound_token(bound_token),
        .bound_generation(bound_generation),
        .current_context(current_context),
        .new_work_allowed(new_work_allowed),
        .source_save_valid(source_save_valid),
        .source_save_ready(source_save_ready),
        .source_save_payload(source_save_payload),
        .retire_save_valid(retire_save_valid),
        .retire_save_ready(retire_save_ready),
        .retire_save_payload(retire_save_payload),
        .isolation_save_valid(isolation_save_valid),
        .isolation_save_ready(isolation_save_ready),
        .isolation_save_payload(isolation_save_payload),
        .local_cancel_now(local_cancel_now),
        .audit_capture_ready(audit_capture_ready),
        .pending_cancel(pending_cancel),
        .first_error_valid(first_error_valid),
        .first_error_code(first_error_code),
        .lifecycle(lifecycle),
        .generation_exhausted(generation_exhausted),
        .source_revision_exhausted(source_revision_exhausted),
        .isolation_revision_exhausted(isolation_revision_exhausted),
        .reset_barrier(reset_barrier),
        .token_exhausted(token_exhausted),
        .slot_active(slot_active),
        .slot_token(slot_token),
        .slot_count(slot_count),
        .slot_state(slot_state),
        .slot_error(slot_error),
        .slot_revoked(slot_revoked),
        .command_pending(command_pending),
        .command_wait_response(command_wait_response),
        .command_op(command_op),
        .command_token(command_token),
        .command_reason(command_reason),
        .command_fire(command_fire),
        .command_response_fire(command_response_fire),
        .command_response_status(command_response_status),
        .reset_request_accepted(reset_request_accepted),
        .reset_candidate_authorized(reset_candidate_authorized),
        .reset_guard_matches(reset_guard_matches),
        .reset_abort(reset_abort),
        .slice_reset_executed(slice_reset_executed),
        .reset_candidate_cut(reset_candidate_cut),
        .frontend_ready(frontend_ready),
        .pcm_valid(pcm_valid),
        .clipped(clipped),
        .pcm(pcm),
        .sample_id(sample_id),
        .source_run(source_run),
        .m_pcm(m_pcm),
        .m_id(m_id),
        .m_flags(m_flags),
        .m_session_id(m_session_id),
        .m_frame_index(m_frame_index),
        .m_interval_index(m_interval_index),
        .m_sample_index(m_sample_index),
        .m_first_id(m_first_id),
        .m_last_id(m_last_id),
        .m_reset_before(m_reset_before),
        .m_last(m_last),
        .e_code(e_code),
        .e_parent_code(e_parent_code),
        .e_source_status(e_source_status),
        .e_source_drained(e_source_drained),
        .e_session_id(e_session_id),
        .e_id(e_id),
        .e_prev_id(e_prev_id),
        .e_id_valid(e_id_valid),
        .e_prev_id_valid(e_prev_id_valid),
        .e_raw_flags(e_raw_flags),
        .e_source_flags(e_source_flags),
        .e_unused_tail(e_unused_tail),
        .e_interval_index(e_interval_index),
        .e_packet_index(e_packet_index),
        .e_word_index(e_word_index),
        .e_packet_words(e_packet_words),
        .e_tdata(e_tdata),
        .e_tkeep(e_tkeep),
        .e_tlast(e_tlast),
        .e_drop_buffered_groups(e_drop_buffered_groups),
        .e_drop_verified_groups(e_drop_verified_groups),
        .e_framer_code(e_framer_code),
        .e_framer_error_tail(e_framer_error_tail),
        .e_stop_truncated(e_stop_truncated),
        .actual_start_valid(actual_start_valid),
        .actual_start_ready(actual_start_ready),
        .actual_stop_valid(actual_stop_valid),
        .actual_stop_ready(actual_stop_ready)
    );
    pcm4_forward_fft_entry #(.HANN_FILE(HANN_FILE)) u_forward (
        .clk(clk),.cold_rst_n(cold_rst_n),.research_profile_valid(research_profile_valid),
        .desc_valid(desc_valid),.desc_ready(desc_ready),
        .desc_token(desc_token),.desc_generation(desc_generation),.desc_context(desc_context),.desc_first(desc_first),
        .rd_valid(rd_valid),.rd_ready(rd_ready),.rd_token(rd_token),.rd_generation(rd_generation),
        .rd_context(rd_context),.rd_index(rd_index),
        .rd_rsp_valid(rd_rsp_valid),.rd_rsp_ready(rd_rsp_ready),
        .rd_rsp_token(rd_rsp_token),.rd_rsp_generation(rd_rsp_generation),
        .rd_rsp_context(rd_rsp_context),.rd_rsp_index(rd_rsp_index),.rd_rsp_status(rd_rsp_status),
        .rd_rsp_origin(rd_rsp_origin),.rd_rsp_payload(rd_rsp_payload),
        .reader_close_valid(reader_close_valid),.reader_close_ready(reader_close_ready),
        .reader_close_token(reader_close_token),.reader_close_generation(reader_close_generation),
        .reader_no_future_access(reader_no_future_access),
        .binding_valid(binding_valid),.bound_token(bound_token),.bound_generation(bound_generation),
        .current_context(current_context),.new_work_allowed(new_work_allowed),
        .local_cancel_now(local_cancel_now),.pending_cancel(pending_cancel),
        .first_error_valid(first_error_valid),.caller_first_error_code(first_error_code),
        .data_clear_req_valid(ff_np_data_clear_valid),.data_clear_req_ready(ff_np_data_clear_ready),
        .cancel_now(ff_cancel_now),
        .cancel_causes(ff_cancel_causes),
        .controlled_clear_valid(ff_controlled_clear_valid),
        .controlled_clear_ready(ff_controlled_clear_ready),
        .fft_output_permit(ff_fft_output_permit),
        .fft_status_permit(ff_fft_status_permit),
        .m_valid(ff_m_valid),
        .m_ready(ff_m_ready),
        .m_token(ff_m_token),
        .m_generation(ff_m_generation),
        .m_context(ff_m_context),
        .m_frame_first(ff_m_frame_first),
        .m_domain(ff_m_domain),
        .m_channel(ff_m_channel),
        .m_bin(ff_m_bin),
        .m_real(ff_m_real),
        .m_imag(ff_m_imag),
        .m_numeric_valid(ff_m_numeric_valid),
        .m_ov_real(ff_m_ov_real),
        .m_ov_imag(ff_m_ov_imag),
        .m_qualified(ff_m_qualified),
        .terminal_valid(ff_terminal_valid),
        .terminal_ready(ff_terminal_ready),
        .terminal_token(ff_terminal_token),
        .terminal_generation(ff_terminal_generation),
        .terminal_context(ff_terminal_context),
        .terminal_frame_first(ff_terminal_frame_first),
        .unit_state(ff_unit_state),
        .hardware_started(ff_hardware_started),
        .physically_retired(ff_physically_retired),
        .fft_input_counts(ff_fft_input_counts),
        .fft_output_counts(ff_fft_output_counts),
        .fixed4_input_counts(ff_fixed4_input_counts),
        .fixed4_output_counts(ff_fixed4_output_counts),
        .fixed4_qualified_counts(ff_fixed4_qualified_counts),
        .fft_status_raw(ff_fft_status_raw),
        .fft_status_seen(ff_fft_status_seen),
        .fft_event_seen(ff_fft_event_seen),
        .fixed4_contexts(ff_fixed4_contexts),
        .fixed4_cancel_causes_record(ff_fixed4_cancel_causes_record),
        .fixed4_terminal_n_record(ff_fixed4_terminal_n_record),
        .fixed4_terminal_p_record(ff_fixed4_terminal_p_record),
        .fixed4_cancelled_unsent_record(ff_fixed4_cancelled_unsent_record),
        .fixed4_terminal_t_bin_record(ff_fixed4_terminal_t_bin_record),
        .fixed4_terminal_t_record(ff_fixed4_terminal_t_record),
        .fixed4_terminal_s_record(ff_fixed4_terminal_s_record),
        .fixed4_cancel_saved(ff_fixed4_cancel_saved),
        .fixed4_retire_accepted(ff_fixed4_retire_accepted),
        .source_received(ff_source_received),
        .transaction_cancelled(ff_transaction_cancelled),
        .protocol_error(ff_protocol_error),
        .numeric_error(ff_numeric_error),
        .first_error_code(ff_first_error_code),
        .accumulated_cancel_causes(ff_accumulated_cancel_causes),
        .source_report_record(ff_source_report_record),
        .source_abort_record(ff_source_abort_record),
        .source_report_seen(ff_source_report_seen),
        .source_abort_seen(ff_source_abort_seen),
        .abort_valid(ff_abort_valid),
        .abort_ready(ff_abort_ready),
        .abort_payload(ff_abort_payload),
        .busy(ff_busy),
        .ip_obligation(ff_ip_obligation),
        .leaf_obligation(ff_leaf_obligation),
        .debug_state(ff_debug_state),
        .fft_audit_valid(ff_fft_audit_valid),
        .fft_audit_status(ff_fft_audit_status),
        .fft_audit_instance(ff_fft_audit_instance),
        .fft_audit_bin(ff_fft_audit_bin),
        .fft_audit_real(ff_fft_audit_real),
        .fft_audit_imag(ff_fft_audit_imag),
        .fft_audit_status_raw(ff_fft_audit_status_raw),
        .fft_audit_last(ff_fft_audit_last),
        .fft_audit_on_cancel(ff_fft_audit_on_cancel),
        .np_busy(ff_np_busy),
        .np_read_pending(ff_np_read_pending)
    );
    diag_evidence_store #(.SOURCE_DEPTH(SOURCE_DEPTH),.OTHER_DEPTH(OTHER_DEPTH)) u_store (
        .clk(clk),.cold_rst_n(cold_rst_n),
        .source_valid(source_save_valid),.source_ready(source_save_ready),.source_payload(source_save_payload),
        .retire_valid(retire_save_valid),.retire_ready(retire_save_ready),.retire_payload(retire_save_payload),
        .isolation_valid(isolation_save_valid),.isolation_ready(isolation_save_ready),.isolation_payload(isolation_save_payload),
        .terminal_valid(terminal_valid),.terminal_ready(terminal_ready),.terminal_payload(terminal_record),
        .summary_valid(1'b0),.summary_ready(),.summary_payload(872'd0),
        .summary_reserved(1'b0),.summary_capacity(),
        .reserve_warning(bank_warning),.full(bank_full),.counts(diag_bank_counts),
        .local_cycle(diag_cycle),.next_sequence(diag_capture_seq),
        .select_valid(diag_export_select),.select_bank(diag_export_select_bank),
        .ack_valid(diag_export_ack),.ack_sequence(diag_export_ack_seq),.ack_word(diag_export_ack_word),
        .abort_valid(diag_export_abort),.export_valid(diag_export_valid),.export_data(diag_export_data),
        .export_bank(diag_export_bank),.export_sequence(diag_export_seq),
        .export_word(diag_export_word),.export_words(diag_export_words),.export_last(diag_export_last),
        .error_pulse(store_error),.error_code(store_error_code),.allocator_exhausted(allocator_exhausted)
    );
    forward_window_manager #(.WATCHDOG_BITS(WATCHDOG_BITS)) u_manager (
        .clk(clk),.cold_rst_n(cold_rst_n),
        .config_valid(diag_config_valid),.config_ready(diag_config_ready),
        .config_boot_valid(diag_boot_valid),.config_boot(diag_boot),
        .config_epoch_valid(diag_epoch_valid),.config_epoch(diag_decl_epoch),
        .config_sid_valid(diag_sid_valid),.config_sid(diag_decl_sid),
        .start_control(diag_start),.stop_control(diag_stop),.warm_control(diag_reset),
        .decl_boot_valid(decl_boot_valid),.decl_boot(decl_boot),
        .decl_epoch_valid(decl_epoch_valid),.decl_epoch(decl_epoch),
        .decl_sid_valid(decl_sid_valid),.decl_sid(decl_sid),
        .start_valid(start_req_valid),.start_ready(start_req_ready),
        .stop_valid(stop_req_valid),.stop_ready(stop_req_ready),
        .prepare_valid(prepare_req_valid),.prepare_ready(prepare_req_ready),
        .reset_valid(reset_req_valid),.reset_ready(reset_req_ready),
        .clear_valid(clear_req_valid),.clear_ready(clear_req_ready),
        .actual_start_fire(actual_start_valid && actual_start_ready),
        .actual_stop_fire(actual_stop_valid && actual_stop_ready),
        .m_fire(m_valid && m_ready),.m_last(m_last),
        .terminal_copy(terminal_copy),.terminal_drained(terminal_payload[367]),
        .source_status(source_status),.session_active(session_active),.fault_latched(fault_latched),
        .local_cancel(local_cancel_now || pending_cancel),.caller_lifecycle(lifecycle),
        .reset_abort(reset_abort),.reset_executed(slice_reset_executed),
        .bank_warning(bank_warning),.bank_full(bank_full),.allocator_exhausted(allocator_exhausted),
        .ff_quiet(ff_quiet),.normal_source_quiet(normal_source_quiet),
        .ff_abort(ff_abort_valid),.ff_session_aborted(ff_session_aborted),
        .store_error(store_error),.store_error_code(store_error_code),
        .caller_error(first_error_valid),.caller_error_code(first_error_code),
        .halt_reader(halt_reader),.config_present(config_present),.terminal_seen(terminal_seen),
        .state(diag_manager_state),.frame_count(frame_count),
        .actual_start_count(start_count),.actual_stop_count(stop_count),.m_count(row_count),.terminal_count(terminal_count),
        .error_valid(local_error_valid),.error_code(local_error_code)
    );
    assign diag_m_valid=m_valid;
    assign diag_m_payload=m_payload;
    assign diag_e_valid=e_valid;
    assign diag_e_payload=e_payload;
    assign diag_session_id=decl_sid;
    assign diag_source_status=source_status;
    assign diag_epoch=decl_epoch[31:0]; // observation only; full configured epoch lives in context
    assign diag_local_error={7'd0,store_error_code,first_error_code,local_error_code,local_error_valid};
    assign diag_counts={terminal_count[31:0],frame_count,row_count[31:0],32'd0,32'd0,stop_count[31:0],start_count[31:0]};
    reg ids_valid;
    reg [63:0] first_id,last_id;
    assign diag_ids={ids_valid,last_id,first_id};
    assign diag_control={15'd0,halt_reader,bank_full,bank_warning,ff_np_read_pending,
        terminal_seen,config_present,clear_req_ready,reset_req_ready,prepare_req_ready,
        stop_req_ready,start_req_ready,slice_rst_n,new_work_allowed,closing,session_active,
        source_run,frontend_ready};
    assign diag_m_meta={m_session_id,m_interval_index,m_frame_index,m_id,m_sample_index,m_flags,m_reset_before,m_last,m_valid};
    assign diag_e_meta={e_session_id,e_parent_code,e_code,e_source_drained};
    // Native typed layout is the B private fault148 definition, not the old C order.
    assign diag_fault={fault_latched,fault_code,fault_parent_code,fault_session_id,
        fault_source_status,fault_session_valid,fault_id_valid,fault_id,fault_after_terminal};
    assign diag_terminal_lo=diag_last_terminal[207:0];
    assign diag_terminal_hi=diag_last_terminal[415:208];
    always @(posedge clk) begin
        if(!cold_rst_n) begin
            diag_last_terminal<=0; diag_last_terminal_valid<=0;
            ids_valid<=0; first_id<=0; last_id<=0;
        end else begin
            if(terminal_copy) begin diag_last_terminal<=terminal_payload; diag_last_terminal_valid<=1; end
            if(m_valid && m_ready) begin
                if(!ids_valid) first_id<=m_id;
                last_id<=m_id; ids_valid<=1;
            end
        end
    end
endmodule
