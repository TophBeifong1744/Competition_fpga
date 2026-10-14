`timescale 1ns/1ps
`default_nettype none
// 中文用途：复用真实四麦/官方FFT和后端，接合同域非VIO命令、自动消费和既有双轴PWM。
module i17_continuous_top #(
    parameter WARMUP_SAMPLES=4096,
    parameter HANN_FILE="inputs/parent/inputs/a_numeric/inputs/b_np/hann-u18f17.mem"
)(
    input wire clk, rst_n,
    input wire cmd_valid, input wire [2:0] cmd_op,
    output wire cmd_ready, cmd_done, output wire [7:0] cmd_error,
    input wire stop_request,
    input wire [159:0] context_pending,
    input wire [95:0] map_pending, input wire [23:0] timeout_pending,
    output wire diag_valid, input wire diag_ready, output wire [31:0] diag_data,
    output wire [2:0] diag_bank, output wire [63:0] diag_sequence,
    output wire [5:0] diag_word, diag_words, output wire diag_last,
    output wire [63:0] reports_consumed, aborts_consumed, records_consumed,
    output wire result_valid, result_abort, result_eligible,
    output wire signed [17:0] result_angle_q8, output wire [8:0] result_angle_deg,
    output wire [724:0] result_identity,
    output wire [7:0] control_state, first_fault,
    output wire [31:0] core_status, output wire [255:0] ila_sample,
    input wire [3:0] mic_data,
    output wire [3:0] mic_clock,
    output wire pwm_horizontal, pwm_vertical
);
    wire [159:0] context_config;
    wire [95:0] map_config;
    wire config_valid, research_valid, map_valid, servo_enable, run_level, diag_start;
    wire warm_reset, stop_now, fault_now, fft_permit, arm_request, configured;
    wire [724:0] declared_tuple;
    wire [164:0] declared_context;
    wire [63:0] declared_generation;
    wire [7:0] controller_state;
    wire motion_open_request, report_ready, abort_ready;
    wire export_select, export_ack, export_abort;
    wire [2:0] export_select_bank;
    wire [63:0] export_ack_seq;
    wire [5:0] export_ack_word;
    wire horizontal_open, vertical_open, vertical_pwm;
    wire pdm_clk1;
    wire pdm_clk2;
    wire pdm_clk3;
    wire pdm_clk4;
    wire [31:0] status;
    wire [31:0] m_axis_tdata;
    wire [3:0] m_axis_tkeep;
    wire m_axis_tvalid;
    wire m_axis_tlast;
    wire ff_quiet;
    wire ff_session_aborted;
    wire ff_np_data_clear_valid;
    wire ff_np_data_clear_ready;
    wire ff_controlled_clear_valid;
    wire ff_controlled_clear_ready;
    wire ff_m_valid;
    wire [63:0] ff_m_token;
    wire [63:0] ff_m_generation;
    wire [164:0] ff_m_context;
    wire [431:0] ff_m_frame_first;
    wire ff_m_domain;
    wire [1:0] ff_m_channel;
    wire [9:0] ff_m_bin;
    wire signed [24:0] ff_m_real;
    wire signed [24:0] ff_m_imag;
    wire ff_m_numeric_valid;
    wire ff_m_ov_real;
    wire ff_m_ov_imag;
    wire ff_m_qualified;
    wire ff_terminal_valid;
    wire [63:0] ff_terminal_token;
    wire [63:0] ff_terminal_generation;
    wire [164:0] ff_terminal_context;
    wire [431:0] ff_terminal_frame_first;
    wire [63:0] ff_unit_state;
    wire [15:0] ff_hardware_started;
    wire [15:0] ff_physically_retired;
    wire [87:0] ff_fft_input_counts;
    wire [87:0] ff_fft_output_counts;
    wire [79:0] ff_fixed4_input_counts;
    wire [79:0] ff_fixed4_output_counts;
    wire [79:0] ff_fixed4_qualified_counts;
    wire [63:0] ff_fft_status_raw;
    wire [7:0] ff_fft_status_seen;
    wire [55:0] ff_fft_event_seen;
    wire [511:0] ff_fixed4_contexts;
    wire [279:0] ff_fixed4_cancel_causes_record;
    wire [79:0] ff_fixed4_terminal_n_record;
    wire [79:0] ff_fixed4_terminal_p_record;
    wire [79:0] ff_fixed4_cancelled_unsent_record;
    wire [79:0] ff_fixed4_terminal_t_bin_record;
    wire [7:0] ff_fixed4_terminal_t_record;
    wire [7:0] ff_fixed4_terminal_s_record;
    wire [7:0] ff_fixed4_cancel_saved;
    wire [7:0] ff_fixed4_retire_accepted;
    wire [13:0] ff_source_received;
    wire ff_transaction_cancelled;
    wire ff_protocol_error;
    wire ff_numeric_error;
    wire [7:0] ff_first_error_code;
    wire [7:0] ff_accumulated_cancel_causes;
    wire [2001:0] ff_source_report_record;
    wire [2079:0] ff_source_abort_record;
    wire ff_source_report_seen;
    wire ff_source_abort_seen;
    wire ff_abort_valid;
    wire [179:0] ff_abort_payload;
    wire ff_busy;
    wire ff_ip_obligation;
    wire ff_leaf_obligation;
    wire [3:0] ff_debug_state;
    wire ff_fft_audit_valid;
    wire ff_fft_audit_status;
    wire [2:0] ff_fft_audit_instance;
    wire [9:0] ff_fft_audit_bin;
    wire signed [28:0] ff_fft_audit_real;
    wire signed [28:0] ff_fft_audit_imag;
    wire [7:0] ff_fft_audit_status_raw;
    wire ff_fft_audit_last;
    wire ff_fft_audit_on_cancel;
    wire ff_np_busy;
    wire ff_np_read_pending;
    wire diag_frontend_ready;
    wire [3:0] diag_frontend_pv;
    wire [3:0] diag_frontend_clip;
    wire [95:0] diag_frontend_pcm;
    wire [63:0] diag_frontend_id;
    wire diag_m_valid;
    wire [431:0] diag_m_payload;
    wire diag_e_valid;
    wire [415:0] diag_e_payload;
    wire [415:0] diag_last_terminal;
    wire diag_last_terminal_valid;
    wire [31:0] diag_session_id;
    wire [31:0] diag_source_status;
    wire [31:0] diag_epoch;
    wire [223:0] diag_counts;
    wire [128:0] diag_ids;
    wire [31:0] diag_control;
    wire [176:0] diag_m_meta;
    wire [48:0] diag_e_meta;
    wire [147:0] diag_fault;
    wire [207:0] diag_terminal_lo;
    wire [207:0] diag_terminal_hi;
    wire diag_config_ready;
    wire diag_export_valid;
    wire [31:0] diag_export_data;
    wire [2:0] diag_export_bank;
    wire [63:0] diag_export_seq;
    wire [5:0] diag_export_word;
    wire [5:0] diag_export_words;
    wire diag_export_last;
    wire [31:0] diag_bank_counts;
    wire [7:0] diag_manager_state;
    wire diag_current_fault;
    wire [31:0] diag_local_error;
    wire [63:0] diag_cycle;
    wire [63:0] diag_capture_seq;
    wire doa_report_valid;
    wire doa_abort_valid;
    wire [724:0] doa_active_identity;
    wire signed [17:0] doa_raw_angle_q8;
    wire [8:0] doa_command_angle;
    wire doa_map_valid;
    wire doa_angle_numerical_valid;
    wire doa_angle_delivery_eligible;
    wire doa_qualified_delivery;
    wire [63:0] doa_report_policy_id;
    wire [6625:0] doa_frontend_terminal_record;
    wire doa_frontend_abort_seen;
    wire [724:0] doa_frontend_abort_identity_record;
    wire [179:0] doa_frontend_abort_record;
    wire [7:0] doa_first_error_code;
    wire doa_busy;
    wire doa_ip_obligation;
    wire [6:0] doa_official_events;
    wire diag_armed;
    wire diag_current_qualified;
    wire local_mismatched_abort;
    wire servo_pwm;
    wire servo_angle_valid;
    wire servo_accept_pulse;
    wire servo_reject_pulse;
    wire [3:0] servo_reject_reason;
    wire [8:0] servo_angle_deg;
    (* KEEP_HIERARCHY="yes" *) four_mic_live_loop #(
        .HANN_FILE(HANN_FILE),.WARMUP_SAMPLES(WARMUP_SAMPLES),
        .CONTINUOUS_WATCHDOG(1),.SERVO_CONFIGURED(1),.SIM_FIXTURE(0),
        .SERVO_CLK_FREQ_HZ(61440000),.SERVO_MAX_ANGLE_DEG(360),.SERVO_RESET_ANGLE_DEG(180)
    ) u_core (
        .aclk(clk),
        .aresetn(rst_n),
        .start(run_level),
        .pdm_data(mic_data),
        .pdm_clk1(pdm_clk1),
        .pdm_clk2(pdm_clk2),
        .pdm_clk3(pdm_clk3),
        .pdm_clk4(pdm_clk4),
        .status(status),
        .m_axis_tdata(m_axis_tdata),
        .m_axis_tkeep(m_axis_tkeep),
        .m_axis_tvalid(m_axis_tvalid),
        .m_axis_tready(1'b1),
        .m_axis_tlast(m_axis_tlast),
        .research_profile_valid(research_valid),
        .ff_quiet(ff_quiet),
        .ff_session_aborted(ff_session_aborted),
        .ff_np_data_clear_valid(ff_np_data_clear_valid),
        .ff_np_data_clear_ready(ff_np_data_clear_ready),
        .ff_cancel_now(1'b0),
        .ff_cancel_causes(8'd0),
        .ff_controlled_clear_valid(ff_controlled_clear_valid),
        .ff_controlled_clear_ready(ff_controlled_clear_ready),
        .ff_fft_output_permit(fft_permit),
        .ff_fft_status_permit(fft_permit),
        .ff_m_valid(ff_m_valid),
        .ff_m_token(ff_m_token),
        .ff_m_generation(ff_m_generation),
        .ff_m_context(ff_m_context),
        .ff_m_frame_first(ff_m_frame_first),
        .ff_m_domain(ff_m_domain),
        .ff_m_channel(ff_m_channel),
        .ff_m_bin(ff_m_bin),
        .ff_m_real(ff_m_real),
        .ff_m_imag(ff_m_imag),
        .ff_m_numeric_valid(ff_m_numeric_valid),
        .ff_m_ov_real(ff_m_ov_real),
        .ff_m_ov_imag(ff_m_ov_imag),
        .ff_m_qualified(ff_m_qualified),
        .ff_terminal_valid(ff_terminal_valid),
        .ff_terminal_token(ff_terminal_token),
        .ff_terminal_generation(ff_terminal_generation),
        .ff_terminal_context(ff_terminal_context),
        .ff_terminal_frame_first(ff_terminal_frame_first),
        .ff_unit_state(ff_unit_state),
        .ff_hardware_started(ff_hardware_started),
        .ff_physically_retired(ff_physically_retired),
        .ff_fft_input_counts(ff_fft_input_counts),
        .ff_fft_output_counts(ff_fft_output_counts),
        .ff_fixed4_input_counts(ff_fixed4_input_counts),
        .ff_fixed4_output_counts(ff_fixed4_output_counts),
        .ff_fixed4_qualified_counts(ff_fixed4_qualified_counts),
        .ff_fft_status_raw(ff_fft_status_raw),
        .ff_fft_status_seen(ff_fft_status_seen),
        .ff_fft_event_seen(ff_fft_event_seen),
        .ff_fixed4_contexts(ff_fixed4_contexts),
        .ff_fixed4_cancel_causes_record(ff_fixed4_cancel_causes_record),
        .ff_fixed4_terminal_n_record(ff_fixed4_terminal_n_record),
        .ff_fixed4_terminal_p_record(ff_fixed4_terminal_p_record),
        .ff_fixed4_cancelled_unsent_record(ff_fixed4_cancelled_unsent_record),
        .ff_fixed4_terminal_t_bin_record(ff_fixed4_terminal_t_bin_record),
        .ff_fixed4_terminal_t_record(ff_fixed4_terminal_t_record),
        .ff_fixed4_terminal_s_record(ff_fixed4_terminal_s_record),
        .ff_fixed4_cancel_saved(ff_fixed4_cancel_saved),
        .ff_fixed4_retire_accepted(ff_fixed4_retire_accepted),
        .ff_source_received(ff_source_received),
        .ff_transaction_cancelled(ff_transaction_cancelled),
        .ff_protocol_error(ff_protocol_error),
        .ff_numeric_error(ff_numeric_error),
        .ff_first_error_code(ff_first_error_code),
        .ff_accumulated_cancel_causes(ff_accumulated_cancel_causes),
        .ff_source_report_record(ff_source_report_record),
        .ff_source_abort_record(ff_source_abort_record),
        .ff_source_report_seen(ff_source_report_seen),
        .ff_source_abort_seen(ff_source_abort_seen),
        .ff_abort_valid(ff_abort_valid),
        .ff_abort_payload(ff_abort_payload),
        .ff_busy(ff_busy),
        .ff_ip_obligation(ff_ip_obligation),
        .ff_leaf_obligation(ff_leaf_obligation),
        .ff_debug_state(ff_debug_state),
        .ff_fft_audit_valid(ff_fft_audit_valid),
        .ff_fft_audit_status(ff_fft_audit_status),
        .ff_fft_audit_instance(ff_fft_audit_instance),
        .ff_fft_audit_bin(ff_fft_audit_bin),
        .ff_fft_audit_real(ff_fft_audit_real),
        .ff_fft_audit_imag(ff_fft_audit_imag),
        .ff_fft_audit_status_raw(ff_fft_audit_status_raw),
        .ff_fft_audit_last(ff_fft_audit_last),
        .ff_fft_audit_on_cancel(ff_fft_audit_on_cancel),
        .ff_np_busy(ff_np_busy),
        .ff_np_read_pending(ff_np_read_pending),
        .diag_reset(warm_reset),
        .diag_start(diag_start),
        .diag_stop(stop_now),
        .diag_frontend_ready(diag_frontend_ready),
        .diag_frontend_pv(diag_frontend_pv),
        .diag_frontend_clip(diag_frontend_clip),
        .diag_frontend_pcm(diag_frontend_pcm),
        .diag_frontend_id(diag_frontend_id),
        .diag_m_valid(diag_m_valid),
        .diag_m_payload(diag_m_payload),
        .diag_e_valid(diag_e_valid),
        .diag_e_payload(diag_e_payload),
        .diag_last_terminal(diag_last_terminal),
        .diag_last_terminal_valid(diag_last_terminal_valid),
        .diag_session_id(diag_session_id),
        .diag_source_status(diag_source_status),
        .diag_epoch(diag_epoch),
        .diag_counts(diag_counts),
        .diag_ids(diag_ids),
        .diag_control(diag_control),
        .diag_m_meta(diag_m_meta),
        .diag_e_meta(diag_e_meta),
        .diag_fault(diag_fault),
        .diag_terminal_lo(diag_terminal_lo),
        .diag_terminal_hi(diag_terminal_hi),
        .diag_config_valid(config_valid),
        .diag_config_ready(diag_config_ready),
        .diag_boot_valid(configured | config_valid),
        .diag_boot(context_config[159:96]),
        .diag_epoch_valid(configured | config_valid),
        .diag_decl_epoch(context_config[95:32]),
        .diag_sid_valid(configured | config_valid),
        .diag_decl_sid(context_config[31:0]),
        .diag_export_select(export_select),
        .diag_export_select_bank(export_select_bank),
        .diag_export_ack(export_ack),
        .diag_export_ack_seq(export_ack_seq),
        .diag_export_ack_word(export_ack_word),
        .diag_export_abort(export_abort),
        .diag_export_valid(diag_export_valid),
        .diag_export_data(diag_export_data),
        .diag_export_bank(diag_export_bank),
        .diag_export_seq(diag_export_seq),
        .diag_export_word(diag_export_word),
        .diag_export_words(diag_export_words),
        .diag_export_last(diag_export_last),
        .diag_bank_counts(diag_bank_counts),
        .diag_manager_state(diag_manager_state),.diag_current_fault(diag_current_fault),
        .diag_local_error(diag_local_error),
        .diag_cycle(diag_cycle),
        .diag_capture_seq(diag_capture_seq),
        .arm_request(arm_request),
        .fault_now(fault_now),
        .servo_enable(servo_enable),
        .declared_tuple(declared_tuple),
        .ff_cancel_identity(725'd0),
        .declared_context(declared_context),
        .declared_generation(declared_generation),
        .map_config_valid(map_valid),
        .map_offset_q8(map_config[23:0]),
        .map_direction(map_config[25:24]),
        .map_domain_min_q8(map_config[43:26]),
        .map_domain_max_q8(map_config[61:44]),
        .mechanical_min(map_config[70:62]),
        .mechanical_max(map_config[79:71]),
        .doa_report_ready(report_ready),
        .doa_abort_ready(abort_ready),
        .doa_report_valid(doa_report_valid),
        .doa_abort_valid(doa_abort_valid),
        .doa_active_identity(doa_active_identity),
        .doa_raw_angle_q8(doa_raw_angle_q8),
        .doa_command_angle(doa_command_angle),
        .doa_map_valid(doa_map_valid),
        .doa_angle_numerical_valid(doa_angle_numerical_valid),
        .doa_angle_delivery_eligible(doa_angle_delivery_eligible),
        .doa_qualified_delivery(doa_qualified_delivery),
        .doa_report_policy_id(doa_report_policy_id),
        .doa_frontend_terminal_record(doa_frontend_terminal_record),
        .doa_frontend_abort_seen(doa_frontend_abort_seen),
        .doa_frontend_abort_identity_record(doa_frontend_abort_identity_record),
        .doa_frontend_abort_record(doa_frontend_abort_record),
        .doa_first_error_code(doa_first_error_code),
        .doa_busy(doa_busy),
        .doa_ip_obligation(doa_ip_obligation),
        .doa_official_events(doa_official_events),
        .diag_armed(diag_armed),
        .diag_current_qualified(diag_current_qualified),
        .local_mismatched_abort(local_mismatched_abort),
        .servo_pwm(servo_pwm),
        .servo_angle_valid(servo_angle_valid),
        .servo_accept_pulse(servo_accept_pulse),
        .servo_reject_pulse(servo_reject_pulse),
        .servo_reject_reason(servo_reject_reason),
        .servo_angle_deg(servo_angle_deg)
    );

    assign mic_clock={pdm_clk4,pdm_clk3,pdm_clk2,pdm_clk1};
    wire [724:0] source_identity={ff_terminal_token,ff_terminal_generation,ff_terminal_context,ff_terminal_frame_first};
    wire consumer_idle;
    wire pipeline_quiet = ff_quiet && !ff_busy && !ff_ip_obligation && !ff_leaf_obligation &&
        !ff_np_busy && !ff_np_read_pending && !ff_m_valid && !ff_terminal_valid && !ff_abort_valid &&
        !doa_busy && !doa_ip_obligation && !doa_report_valid && !doa_abort_valid && consumer_idle;
    wire capture_drained = status[3] && !m_axis_tvalid;
    // 当前halt/状态传播；历史local_error跨warm保存，不能当新会话当前故障。
    wire source_fault = diag_current_fault || diag_manager_state>=6 ||
        ff_session_aborted || (ff_busy && (ff_protocol_error || ff_numeric_error)) || status[5] || status[2];
    assign report_ready = 1'b1;
    assign abort_ready = 1'b1;
    assign arm_request = 1'b0;
    assign declared_tuple = {128'd0,declared_context,432'd0};
    assign declared_generation = 64'd0;
    assign result_valid=doa_report_valid;
    assign result_abort=doa_abort_valid;
    assign result_eligible=doa_qualified_delivery;
    assign result_angle_q8=doa_raw_angle_q8;
    assign result_angle_deg=doa_command_angle;
    assign result_identity=doa_active_identity;
    assign control_state=controller_state;
    assign core_status=status;
    i17_continuous_control u_control (
        .clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_op(cmd_op),.cmd_ready(cmd_ready),
        .cmd_done(cmd_done),.cmd_error(cmd_error),.context_pending(context_pending),.map_pending(map_pending),
        .timeout_pending(timeout_pending),.stop_request(stop_request),.config_ready(diag_config_ready),
        .frontend_ready(diag_frontend_ready),.manager_state(diag_manager_state),
        .pipeline_quiet(pipeline_quiet),.capture_drained(capture_drained),
        .report_fire(doa_report_valid),.abort_fire(doa_abort_valid),.source_fault(source_fault),
        .context_config(context_config),.map_config(map_config),.declared_context(declared_context),
        .config_valid(config_valid),.configured(configured),.research_valid(research_valid),.map_valid(map_valid),
        .servo_enable(servo_enable),.motion_open_request(motion_open_request),.current_qualified(diag_current_qualified),
        .run_level(run_level),.stop_now(stop_now),.fault_now(fault_now),.fft_permit(fft_permit),
        .diag_start(diag_start),.warm_reset(warm_reset),.state(controller_state),.first_fault(first_fault),
        .report_count(reports_consumed),.abort_count(aborts_consumed));
    i17_diag_consumer u_consumer (
        .clk(clk),.rst_n(rst_n),.bank_counts(diag_bank_counts),
        .select_valid(export_select),.select_bank(export_select_bank),.ack_valid(export_ack),
        .ack_sequence(export_ack_seq),.ack_word(export_ack_word),
        .export_valid(diag_export_valid),.export_data(diag_export_data),.export_bank(diag_export_bank),
        .export_sequence(diag_export_seq),.export_word(diag_export_word),.export_words(diag_export_words),
        .export_last(diag_export_last),.m_valid(diag_valid),.m_ready(diag_ready),.m_data(diag_data),
        .m_bank(diag_bank),.m_sequence(diag_sequence),.m_word(diag_word),.m_words(diag_words),.m_last(diag_last),
        .idle(consumer_idle),.records_consumed(records_consumed));
    assign export_abort=1'b0;
    // 垂直固定既有 130 度；物理引脚仍受首次授权的低相门控。
    motor_drive #(.CLK_FREQ_HZ(61440000),.MAX_ANGLE_DEG(220),.RESET_ANGLE_DEG(130))
        u_vertical(.clk(clk),.rst_n(rst_n),.angle_deg_i(9'd130),.angle_valid_i(1'b0),.pwm_o(vertical_pwm));
    i17_pwm_gate u_horizontal_gate(.clk(clk),.rst_n(rst_n),.permit_open(motion_open_request),
        .internal_pwm(servo_pwm),.physical_pwm(pwm_horizontal),.opened(horizontal_open));
    i17_pwm_gate u_vertical_gate(.clk(clk),.rst_n(rst_n),.permit_open(motion_open_request),
        .internal_pwm(vertical_pwm),.physical_pwm(pwm_vertical),.opened(vertical_open));
    // 复用既有256位ILA宽度；采样clk=61.44MHz，A可连原生ILA，控制无JTAG依赖。
    assign ila_sample={reports_consumed,aborts_consumed,records_consumed,status,
        first_fault,diag_manager_state,controller_state,
        vertical_open,horizontal_open,diag_current_qualified,diag_armed,
        doa_report_valid,doa_abort_valid,servo_angle_valid,stop_now};
endmodule
`default_nettype wire
