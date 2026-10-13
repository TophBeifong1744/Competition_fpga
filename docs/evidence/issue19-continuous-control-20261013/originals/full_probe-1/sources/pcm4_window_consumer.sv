`timescale 1ns/1ps
// WC-1.1: bounded same-clock transport storage, one development reader.
// INPUT_COMPLETE is an input fact; this module creates no algorithm result.
module pcm4_window_consumer #(
    parameter logic [63:0] TOKEN_LIMIT = 64'hffff_ffff_ffff_ffff
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         m_valid,
    output wire         m_ready,
    input  wire [431:0] m_payload,
    input  wire         e_valid,
    output wire         e_ready,
    input  wire [415:0] e_payload,
    output wire         terminal_valid,
    input  wire         terminal_ready,
    output logic [415:0] terminal_payload,
    output wire         desc_valid,
    input  wire         desc_ready,
    output wire [63:0]  desc_token,
    output wire [431:0] desc_first,
    input  wire         rd_valid,
    output wire         rd_ready,
    input  wire [63:0]  rd_token,
    input  wire [9:0]   rd_index,
    output wire         rd_rsp_valid,
    input  wire         rd_rsp_ready,
    output logic [63:0] rd_rsp_token,
    output logic [9:0]  rd_rsp_index,
    output logic [1:0]  rd_rsp_status,
    output logic [431:0] rd_rsp_payload,
    input  wire         cmd_valid,
    output wire         cmd_ready,
    input  wire [1:0]   cmd_op,
    input  wire [63:0]  cmd_token,
    input  wire [7:0]   cmd_reason,
    output wire         cmd_rsp_valid,
    input  wire         cmd_rsp_ready,
    output logic [63:0] cmd_rsp_token,
    output logic [2:0]  cmd_rsp_status,
    output wire         audit_valid,
    input  wire         audit_ready,
    output logic [63:0] audit_token,
    output logic [10:0] audit_count,
    output logic [431:0] audit_first,
    output logic        audit_bad_valid,
    output logic [431:0] audit_bad,
    output logic [3:0]  audit_error,
    output logic        audit_revoked,
    output logic [7:0]  audit_reason,
    output logic [1:0]  audit_retire_op,
    output logic        reset_barrier,
    output wire         token_exhausted,
    output wire         slot_active,
    output wire [63:0]  slot_token,
    output wire [10:0]  slot_count,
    output wire [2:0]   slot_state,
    output wire [3:0]   slot_error,
    output wire         slot_revoked
);
    localparam logic [2:0] EMPTY       = 3'd0;
    localparam logic [2:0] RECEIVING   = 3'd1;
    localparam logic [2:0] DRAIN       = 3'd2;
    localparam logic [2:0] QUARANTINED = 3'd3;
    localparam logic [2:0] COMPLETE    = 3'd4;

    localparam logic [3:0] ERR_NONE     = 4'd0;
    localparam logic [3:0] ERR_INDEX    = 4'd1;
    localparam logic [3:0] ERR_ID_RANGE = 4'd2;
    localparam logic [3:0] ERR_IDENTITY = 4'd3;
    localparam logic [3:0] ERR_LAST     = 4'd4;
    localparam logic [3:0] ERR_PCM      = 4'd5;

    localparam logic [1:0] READ_OK      = 2'd0;
    localparam logic [1:0] READ_STALE   = 2'd1;
    localparam logic [1:0] READ_REVOKED = 2'd2;
    localparam logic [1:0] RELEASE     = 2'd0;
    localparam logic [1:0] REVOKE      = 2'd1;
    localparam logic [1:0] WARM_RESET  = 2'd2;
    localparam logic [2:0] CMD_OK         = 3'd0;
    localparam logic [2:0] CMD_STALE      = 3'd1;
    localparam logic [2:0] CMD_BUSY       = 3'd2;
    localparam logic [2:0] CMD_AUDIT_FULL = 3'd3;
    localparam logic [2:0] CMD_BAD_OP     = 3'd4;

    // Raw storage is never reset. Only COMPLETE + a live lease grants access.
    logic [431:0] record_ram [0:1023];
    logic [2:0] state_q;
    logic [10:0] count_q;
    logic [63:0] token_q, next_token_q;
    logic [431:0] first_q, bad_q;
    logic [3:0] error_q;
    logic bad_valid_q, revoked_q, reader_owned_q;
    logic [7:0] reason_q;
    logic exhausted_q;
    logic terminal_valid_q, desc_valid_q, rd_rsp_valid_q;
    logic cmd_rsp_valid_q, audit_valid_q;
    logic [3:0] row_error;
    logic [2:0] command_status;

    wire active = (state_q != EMPTY);
    wire [64:0] advertised_end = {1'b0, m_payload[129:66]} + 65'd1023;
    wire [64:0] advertised_id  = {1'b0, m_payload[129:66]} + {54'd0, count_q};
    wire expected_last = (count_q == 11'd1023);
    wire cmd_fire = cmd_valid && cmd_ready;
    wire warm_offered = cmd_fire && (cmd_op == WARM_RESET);
    wire revoke_now = cmd_fire && (command_status == CMD_OK) && (cmd_op == REVOKE);
    wire retire_now = cmd_fire && (command_status == CMD_OK) &&
                      ((cmd_op == RELEASE) || (cmd_op == WARM_RESET));
    wire m_fire = m_valid && m_ready;

    // No lookthrough on any one-entry output. All predicates are pre-edge.
    assign terminal_valid = rst_n && terminal_valid_q;
    assign desc_valid = rst_n && desc_valid_q;
    assign rd_rsp_valid = rst_n && rd_rsp_valid_q;
    assign cmd_rsp_valid = rst_n && cmd_rsp_valid_q;
    assign audit_valid = rst_n && audit_valid_q;
    assign e_ready = rst_n && !terminal_valid_q;
    assign cmd_ready = rst_n && !cmd_rsp_valid_q;
    assign rd_ready = rst_n && !rd_rsp_valid_q && !cmd_valid;
    assign m_ready = rst_n && !warm_offered &&
                     (((state_q == EMPTY) && !exhausted_q) ||
                      (((state_q == RECEIVING) || (state_q == DRAIN)) &&
                       (count_q < 11'd1024)));
    assign desc_token = token_q;
    assign desc_first = first_q;
    assign token_exhausted = exhausted_q;
    assign slot_active = active;
    assign slot_token = active ? token_q : 64'd0;
    assign slot_count = active ? count_q : 11'd0;
    assign slot_state = state_q;
    assign slot_error = active ? error_q : ERR_NONE;
    assign slot_revoked = active && revoked_q;

    function automatic logic pcm_extension_ok(input logic [127:0] pcm);
        integer lane;
        begin
            pcm_extension_ok = 1'b1;
            for (lane = 0; lane < 4; lane = lane + 1)
                if (pcm[lane*32+24 +: 8] != {8{pcm[lane*32+23]}})
                    pcm_extension_ok = 1'b0;
        end
    endfunction

    // Validate arithmetic at 65 bits; no ID truncation or wrap is legal.
    // Identity excludes flags and sample index, which have separate meanings.
    always_comb begin
        row_error = ERR_NONE;
        if ({1'b0, m_payload[139:130]} != count_q)
            row_error = ERR_INDEX;
        else if (advertised_end[64] ||
                 (advertised_end[63:0] != m_payload[65:2]) ||
                 (advertised_id != {1'b0, m_payload[303:240]}))
            row_error = ERR_ID_RANGE;
        else if (active &&
                 ((m_payload[235:140] != first_q[235:140]) ||
                  (m_payload[129:1] != first_q[129:1])))
            row_error = ERR_IDENTITY;
        else if (m_payload[0] != expected_last)
            row_error = ERR_LAST;
        else if (!pcm_extension_ok(m_payload[431:304]))
            row_error = ERR_PCM;
    end

    // BAD_OP precedes token checks; for valid operations STALE precedes BUSY,
    // and BUSY precedes AUDIT_FULL. An audit ACK cannot free space this edge.
    always_comb begin
        command_status = CMD_OK;
        if (cmd_op == 2'd3)
            command_status = CMD_BAD_OP;
        else if ((!active && !((cmd_op == WARM_RESET) && (cmd_token == 64'd0))) ||
                 (active && (cmd_token != token_q)))
            command_status = CMD_STALE;
        else if ((cmd_op == RELEASE) &&
                 (!reader_owned_q || desc_valid_q || rd_rsp_valid_q))
            command_status = CMD_BUSY;
        else if ((cmd_op == WARM_RESET) &&
                 (desc_valid_q || reader_owned_q || rd_rsp_valid_q))
            command_status = CMD_BUSY;
        else if (active && ((cmd_op == RELEASE) || (cmd_op == WARM_RESET)) &&
                 audit_valid_q)
            command_status = CMD_AUDIT_FULL;
    end

    // Cold reset is synchronous to clk; rst_n also gates handshake outputs.
    // Its external precondition is global invalidation of all old obligations.
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= EMPTY;
            count_q <= 11'd0;
            token_q <= 64'd0;
            next_token_q <= 64'd1;
            exhausted_q <= (TOKEN_LIMIT == 64'd0);
            first_q <= 432'd0;
            bad_q <= 432'd0;
            error_q <= ERR_NONE;
            bad_valid_q <= 1'b0;
            revoked_q <= 1'b0;
            reason_q <= 8'd0;
            reader_owned_q <= 1'b0;
            terminal_valid_q <= 1'b0;
            terminal_payload <= 416'd0;
            desc_valid_q <= 1'b0;
            rd_rsp_valid_q <= 1'b0;
            rd_rsp_token <= 64'd0;
            rd_rsp_index <= 10'd0;
            rd_rsp_status <= READ_STALE;
            rd_rsp_payload <= 432'd0;
            cmd_rsp_valid_q <= 1'b0;
            cmd_rsp_token <= 64'd0;
            cmd_rsp_status <= CMD_OK;
            audit_valid_q <= 1'b0;
            audit_token <= 64'd0;
            audit_count <= 11'd0;
            audit_first <= 432'd0;
            audit_bad_valid <= 1'b0;
            audit_bad <= 432'd0;
            audit_error <= ERR_NONE;
            audit_revoked <= 1'b0;
            audit_reason <= 8'd0;
            audit_retire_op <= RELEASE;
            reset_barrier <= 1'b0;
        end else begin
            reset_barrier <= 1'b0;
            if (terminal_valid_q && terminal_ready)
                terminal_valid_q <= 1'b0;
            if (e_valid && e_ready) begin
                terminal_payload <= e_payload;
                terminal_valid_q <= 1'b1;
            end
            if (desc_valid_q && desc_ready) begin
                desc_valid_q <= 1'b0;
                reader_owned_q <= 1'b1;
            end
            if (rd_rsp_valid_q && rd_rsp_ready)
                rd_rsp_valid_q <= 1'b0;
            if (cmd_rsp_valid_q && cmd_rsp_ready)
                cmd_rsp_valid_q <= 1'b0;
            if (audit_valid_q && audit_ready)
                audit_valid_q <= 1'b0;

            if (rd_valid && rd_ready) begin
                rd_rsp_valid_q <= 1'b1;
                rd_rsp_token <= rd_token;
                rd_rsp_index <= rd_index;
                rd_rsp_payload <= 432'd0;
                if (!reader_owned_q || !active || (rd_token != token_q))
                    rd_rsp_status <= READ_STALE;
                else if (revoked_q)
                    rd_rsp_status <= READ_REVOKED;
                else if (state_q != COMPLETE)
                    rd_rsp_status <= READ_STALE;
                else begin
                    rd_rsp_status <= READ_OK;
                    rd_rsp_payload <= record_ram[rd_index];
                end
            end

            if (cmd_fire) begin
                cmd_rsp_valid_q <= 1'b1;
                cmd_rsp_token <= cmd_token;
                cmd_rsp_status <= command_status;
            end

            if (retire_now) begin
                // Save the entire old audit obligation before clearing validity.
                // EMPTY + token0 warm reset creates no new audit record.
                if (active) begin
                    audit_valid_q <= 1'b1;
                    audit_token <= token_q;
                    audit_count <= count_q;
                    audit_first <= first_q;
                    audit_bad_valid <= bad_valid_q;
                    audit_bad <= bad_q;
                    audit_error <= error_q;
                    audit_revoked <= revoked_q;
                    audit_reason <= reason_q;
                    audit_retire_op <= cmd_op;
                end
                state_q <= EMPTY;
                count_q <= 11'd0;
                token_q <= 64'd0;
                first_q <= 432'd0;
                bad_q <= 432'd0;
                error_q <= ERR_NONE;
                bad_valid_q <= 1'b0;
                revoked_q <= 1'b0;
                reason_q <= 8'd0;
                reader_owned_q <= 1'b0;
                desc_valid_q <= 1'b0;
                // Preserve allocator, e, audit history and pending responses.
            end else begin
                if (revoke_now) begin
                    revoked_q <= 1'b1;
                    if (!revoked_q)
                        reason_q <= cmd_reason;
                    if (state_q == RECEIVING)
                        state_q <= DRAIN;
                end

                if (m_fire) begin
                    // Physical address is accepted count, never advertised index.
                    record_ram[count_q[9:0]] <= m_payload;
                    count_q <= count_q + 11'd1;
                    if (state_q == EMPTY) begin
                        token_q <= next_token_q;
                        if (next_token_q == TOKEN_LIMIT)
                            exhausted_q <= 1'b1;
                        else
                            next_token_q <= next_token_q + 64'd1;
                        first_q <= m_payload;
                        revoked_q <= 1'b0;
                        reason_q <= 8'd0;
                        reader_owned_q <= 1'b0;
                        reset_barrier <= m_payload[1];
                        error_q <= row_error;
                        bad_valid_q <= (row_error != ERR_NONE);
                        bad_q <= (row_error != ERR_NONE) ? m_payload : 432'd0;
                    end else if ((error_q == ERR_NONE) && (row_error != ERR_NONE)) begin
                        error_q <= row_error;
                        bad_valid_q <= 1'b1;
                        bad_q <= m_payload;
                    end

                    // An accepted same-edge revoke suppresses new completion.
                    // Already offered descriptors and responses remain history.
                    if ((state_q == DRAIN) || revoked_q || revoke_now ||
                        (row_error != ERR_NONE)) begin
                        if (m_payload[0] || expected_last)
                            state_q <= QUARANTINED;
                        else
                            state_q <= DRAIN;
                    end else if (expected_last) begin
                        state_q <= COMPLETE;
                        desc_valid_q <= 1'b1;
                    end else begin
                        state_q <= RECEIVING;
                    end
                end
            end
        end
    end
endmodule
