`timescale 1ns/1ps
// Private same-clk sidecar. Connect only the public lifecycle ports below.
// The caller gates actual A start_valid with !local_cancel_now and excludes
// clear_preserved_i. Illegal accepted starts are ignored locally so old audit
// cannot be replaced; this does not repair the caller's actual A handshake.
// observer_cold_reset_i is synchronous cold initialization, never the routine
// slice reset. Preserve A audit AND B's old identity/reader obligations before
// either kind of later reset. No output here proves physical reader retirement.
module pcm4_source_cancel_observer (
    input  wire         clk,
    input  wire         slice_rst_n,
    input  wire         observer_cold_reset_i,
    input  wire         prepare_reset_i,
    input  wire         clear_preserved_i,
    input  wire         start_valid,
    input  wire         start_ready,
    input  wire [31:0]  start_session_id,
    input  wire         stop_valid,
    input  wire         stop_ready,
    input  wire [31:0]  source_status,
    input  wire         session_active,
    input  wire         closing,
    input  wire         e_valid,
    input  wire         fault_latched,
    input  wire [7:0]   fault_code,
    input  wire [7:0]   fault_parent_code,
    input  wire [31:0]  fault_session_id,
    input  wire [31:0]  fault_source_status,
    input  wire         fault_session_valid,
    input  wire         fault_id_valid,
    input  wire         fault_after_terminal,
    input  wire [63:0]  fault_id,
    output wire         local_cancel_now,
    output wire         audit_capture_ready,
    output wire         clear_preserved_ready,
    output reg          cancellation_pending,
    output reg          tracked_session_valid,
    output reg  [31:0]  tracked_session_id,
    output reg          accepted_stop_seen,
    output reg          first_observation_valid,
    output reg  [4:0]   first_observation_mask,
    output reg  [4:0]   accumulated_observation_mask,
    output reg  [31:0]  first_source_status,
    output reg          first_session_valid,
    output reg  [31:0]  first_session_id,
    output reg          fault_audit_valid,
    output reg  [147:0] fault_audit_snapshot,
    output wire [7:0]   fault_audit_code,
    output wire [7:0]   fault_audit_parent_code,
    output wire [31:0]  fault_audit_session_id,
    output wire [31:0]  fault_audit_source_status,
    output wire         fault_audit_session_valid,
    output wire         fault_audit_id_valid,
    output wire         fault_audit_after_terminal,
    output wire [63:0]  fault_audit_id
);
    // Private observed-fact bits, NOT the original fault-code namespace.
    localparam [4:0] SOURCE_SYNC_OBS      = 5'b00001,
                     SOURCE_FULL_OBS      = 5'b00010,
                     PUBLISHED_FAULT_OBS  = 5'b00100,
                     UNEXPECTED_CLOSE_OBS = 5'b01000,
                     CONTROLLED_RESET_OBS = 5'b10000;

    wire start_fire = start_valid && start_ready;
    wire stop_fire = stop_valid && stop_ready;
    // 真实lifecycle的closing必使stop_ready为0；去掉冗余STOP项以断即时取消反馈。
    // 仅限同源生命周期接线，合法STOP接受前closing为0，接受后由记录保留。
    wire unexpected_close = tracked_session_valid && session_active &&
        closing && !accepted_stop_seen;
    // The same normal-empty definition/signature used by the frozen A source.
    // Warm/clip-ever/rejected are independent facts, not empty/fatal flags.
    wire source_normal_empty = source_status[31:24] == 8'hc1 &&
        !source_status[5] && !source_status[2] && source_status[3] &&
        !source_status[0] && !source_status[6] && !source_status[7];
    // Initial slice reset after cold init is only a gate, not an old-session
    // audit. A later slice reset with a tracked sid preserves a RESET fact.
    wire observed_reset = prepare_reset_i ||
        (!slice_rst_n && tracked_session_valid);
    wire [4:0] observation_mask =
        (source_status[5] ? SOURCE_SYNC_OBS : 5'b00000) |
        (source_status[2] ? SOURCE_FULL_OBS : 5'b00000) |
        (fault_latched ? PUBLISHED_FAULT_OBS : 5'b00000) |
        (unexpected_close ? UNEXPECTED_CLOSE_OBS : 5'b00000) |
        (observed_reset ? CONTROLLED_RESET_OBS : 5'b00000);
    wire nonreset_observed = (|accumulated_observation_mask[3:0]) ||
        (|observation_mask[3:0]);

    // Use these stable pre-E facts in the E arbiter. The audit registers below
    // update after E and must never become the sole trigger for that edge.
    assign local_cancel_now = source_status[5] || source_status[2] ||
        fault_latched || unexpected_close || prepare_reset_i ||
        cancellation_pending || !slice_rst_n || observer_cold_reset_i;
    // A newly visible non-reset fact also closes ready until the first native
    // fault copy is valid. Do not reset A early and erase that delayed cause.
    assign audit_capture_ready = first_observation_valid &&
        !observer_cold_reset_i && !clear_preserved_i &&
        (!nonreset_observed || fault_audit_valid);
    assign clear_preserved_ready = slice_rst_n && !observer_cold_reset_i &&
        !prepare_reset_i && !start_valid && !session_active && !e_valid &&
        !fault_latched && source_normal_empty;

    // Private 148-bit vector, matching the old TB f_bus field order only;
    // this is NOT the C diag_fault packed ABI. No code/parent translation:
    // [147] latched, [146:139] code, [138:131] parent, [130:99] sid,
    // [98:67] source, [66] sid-valid, [65] id-valid, [64:1] id,
    // [0] after-terminal. fault_audit_valid belongs to this private copy.
    assign fault_audit_code = fault_audit_snapshot[146:139];
    assign fault_audit_parent_code = fault_audit_snapshot[138:131];
    assign fault_audit_session_id = fault_audit_snapshot[130:99];
    assign fault_audit_source_status = fault_audit_snapshot[98:67];
    assign fault_audit_session_valid = fault_audit_snapshot[66];
    assign fault_audit_id_valid = fault_audit_snapshot[65];
    assign fault_audit_after_terminal = fault_audit_snapshot[0];
    assign fault_audit_id = fault_audit_snapshot[64:1];

    always @(posedge clk) begin
        if (observer_cold_reset_i) begin
            cancellation_pending <= 1'b0;
            tracked_session_valid <= 1'b0;
            tracked_session_id <= 32'd0;
            accepted_stop_seen <= 1'b0;
            first_observation_valid <= 1'b0;
            first_observation_mask <= 5'b00000;
            accumulated_observation_mask <= 5'b00000;
            first_source_status <= 32'd0;
            first_session_valid <= 1'b0;
            first_session_id <= 32'd0;
            fault_audit_valid <= 1'b0;
            fault_audit_snapshot <= 148'd0;
        end else if (clear_preserved_i && clear_preserved_ready) begin
            // Caller already copied the audit. This clears only local state;
            // no B lease/reader/generation result follows from this edge.
            cancellation_pending <= 1'b0;
            tracked_session_valid <= 1'b0;
            tracked_session_id <= 32'd0;
            accepted_stop_seen <= 1'b0;
            first_observation_valid <= 1'b0;
            first_observation_mask <= 5'b00000;
            accumulated_observation_mask <= 5'b00000;
            first_source_status <= 32'd0;
            first_session_valid <= 1'b0;
            first_session_id <= 32'd0;
            fault_audit_valid <= 1'b0;
            fault_audit_snapshot <= 148'd0;
        end else begin
            // No slice-reset branch: the old audit and sid survive R.
            if (start_fire && !local_cancel_now && !clear_preserved_i) begin
                tracked_session_valid <= 1'b1;
                tracked_session_id <= start_session_id;
                accepted_stop_seen <= 1'b0;
            end else if (stop_fire && tracked_session_valid) begin
                accepted_stop_seen <= 1'b1;
            end

            if (|observation_mask) begin
                cancellation_pending <= 1'b1;
                accumulated_observation_mask <=
                    accumulated_observation_mask | observation_mask;
                if (!first_observation_valid) begin
                    first_observation_valid <= 1'b1;
                    first_observation_mask <= observation_mask;
                    first_source_status <= source_status;
                    first_session_valid <= tracked_session_valid;
                    first_session_id <= tracked_session_valid ?
                                        tracked_session_id : 32'd0;
                end
            end

            // A published fault may follow source/closing observation. Copy
            // it once without changing the earlier private first-fact tuple.
            if (fault_latched && !fault_audit_valid) begin
                fault_audit_valid <= 1'b1;
                fault_audit_snapshot <= {fault_latched, fault_code,
                    fault_parent_code, fault_session_id, fault_source_status,
                    fault_session_valid, fault_id_valid, fault_id,
                    fault_after_terminal};
            end
        end
    end
endmodule
