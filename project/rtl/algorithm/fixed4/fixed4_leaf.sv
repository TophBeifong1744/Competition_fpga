// One clock, one context, one complex S29 input per accepted beat.
// The manager owns context allocation, abort persistence, and physical retirement.
module fixed4_leaf (
    input  logic               clk,
    input  logic               cold_reset,

    output logic               ctx_active,
    output logic [63:0]        active_ctx,
    output logic               terminal_saved,
    input  logic               begin_valid,
    output logic               begin_ready,
    input  logic [63:0]        begin_ctx,

    input  logic               s_valid,
    output logic               s_ready,
    input  logic [63:0]        s_ctx,
    input  logic [9:0]         s_bin,
    input  logic signed [28:0] s_re,
    input  logic signed [28:0] s_im,

    output logic               m_valid,
    input  logic               m_ready,
    output logic [63:0]        m_ctx,
    output logic [9:0]         m_bin,
    output logic signed [24:0] m_re,
    output logic signed [24:0] m_im,
    output logic               m_numeric_valid,
    output logic               m_ov_re,
    output logic               m_ov_im,

    input  logic               cancel,
    input  logic [31:0]        cancel_causes,
    output logic               protocol_fault_now,
    output logic [1:0]         protocol_fault_bits_now,
    output logic               data_done,
    output logic               sticky_numeric_overflow,

    output logic               terminal_cancelled,
    output logic [63:0]        terminal_ctx,
    output logic [34:0]        terminal_causes,
    output logic [9:0]         terminal_n,
    output logic [9:0]         terminal_p,
    output logic               terminal_t,
    output logic [9:0]         terminal_cancelled_untransferred,
    output logic               terminal_s_transfer,
    output logic [9:0]         terminal_t_bin,
    input  logic               terminal_saved_ack,
    input  logic [63:0]        ack_ctx,
    output logic               local_quiescent,
    input  logic               retire_valid,
    input  logic [63:0]        retire_ctx,
    input  logic               retire_safe
);
    localparam logic [9:0] BEATS = 10'd513;
    localparam logic signed [29:0] S25_MIN = -30'sd16777216;
    localparam logic signed [29:0] S25_MAX =  30'sd16777215;

    logic [9:0] n_count, p_count;
    logic q_valid;
    logic input_transfer, output_transfer;
    logic kill, ack_ok, retire_ok;
    logic [34:0] cause_now;
    logic signed [29:0] rounded_re, rounded_im;
    logic overflow_re, overflow_im;

    // floor(x/16) plus one for residues above half, or a half with odd floor.
    // Keeping the result wide permits overflow detection before S25 narrowing.
    function automatic logic signed [29:0] round_even_div16(
        input logic signed [28:0] value
    );
        logic signed [29:0] floor_value;
        logic increment;
        begin
            floor_value = $signed({value[28], value}) >>> 4;
            increment = (value[3:0] > 4'd8) ||
                        ((value[3:0] == 4'd8) && floor_value[0]);
            round_even_div16 = floor_value + $signed({29'b0, increment});
        end
    endfunction

    assign rounded_re = round_even_div16(s_re);
    assign rounded_im = round_even_div16(s_im);
    assign overflow_re = (rounded_re < S25_MIN) || (rounded_re > S25_MAX);
    assign overflow_im = (rounded_im < S25_MIN) || (rounded_im > S25_MAX);

    // No combinational cancel mask: an old output and a new physical input
    // can both transfer on the abort edge and must be accounted for.
    assign begin_ready = !cold_reset && !ctx_active && (begin_ctx != 64'b0);
    assign s_ready = !cold_reset && ctx_active && !terminal_cancelled &&
                     !data_done && (n_count < BEATS) && (!q_valid || m_ready);
    assign m_valid = !cold_reset && q_valid;
    assign input_transfer = s_valid && s_ready;
    assign output_transfer = m_valid && m_ready;

    assign protocol_fault_bits_now[0] = input_transfer &&
                                         (s_ctx != active_ctx);
    assign protocol_fault_bits_now[1] = input_transfer &&
                                         (s_bin != n_count);
    assign protocol_fault_now = |protocol_fault_bits_now;
    assign kill = cancel || protocol_fault_now;
    assign cause_now = {cancel ? cancel_causes : 32'b0,
                        protocol_fault_bits_now, cancel};

    assign local_quiescent = !ctx_active || terminal_cancelled || data_done;
    assign ack_ok = terminal_saved_ack && ctx_active && terminal_cancelled &&
                    (ack_ctx == active_ctx) && !terminal_saved;
    assign retire_ok = retire_valid && ctx_active &&
                       (retire_ctx == active_ctx) && local_quiescent &&
                       retire_safe && !kill &&
                       (terminal_cancelled ? terminal_saved : data_done);

    // cold_reset is a legal, synchronous cold-start/retired-state operation.
    // Its legality and rejected ack/retire requests are audited by the manager.
    always_ff @(posedge clk) begin
        if (cold_reset) begin
            ctx_active <= 1'b0;
            active_ctx <= '0;
            terminal_saved <= 1'b0;
            n_count <= '0;
            p_count <= '0;
            q_valid <= 1'b0;
            m_ctx <= '0;
            m_bin <= '0;
            m_re <= '0;
            m_im <= '0;
            m_numeric_valid <= 1'b0;
            m_ov_re <= 1'b0;
            m_ov_im <= 1'b0;
            data_done <= 1'b0;
            sticky_numeric_overflow <= 1'b0;
            terminal_cancelled <= 1'b0;
            terminal_ctx <= '0;
            terminal_causes <= '0;
            terminal_n <= '0;
            terminal_p <= '0;
            terminal_t <= 1'b0;
            terminal_cancelled_untransferred <= '0;
            terminal_s_transfer <= 1'b0;
            terminal_t_bin <= '0;
        end else if (!ctx_active) begin
            // cancel while idle is an environment violation, not a terminal.
            if (begin_valid && begin_ready) begin
                ctx_active <= 1'b1;
                active_ctx <= begin_ctx;
                terminal_saved <= 1'b0;
                n_count <= '0;
                p_count <= '0;
                q_valid <= 1'b0;
                m_ctx <= '0;
                m_bin <= '0;
                m_re <= '0;
                m_im <= '0;
                m_numeric_valid <= 1'b0;
                m_ov_re <= 1'b0;
                m_ov_im <= 1'b0;
                data_done <= 1'b0;
                sticky_numeric_overflow <= 1'b0;
                terminal_cancelled <= 1'b0;
                terminal_ctx <= '0;
                terminal_causes <= '0;
                terminal_n <= '0;
                terminal_p <= '0;
                terminal_t <= 1'b0;
                terminal_cancelled_untransferred <= '0;
                terminal_s_transfer <= 1'b0;
                terminal_t_bin <= '0;
            end
        end else begin
            if (ack_ok)
                terminal_saved <= 1'b1;

            if (terminal_cancelled) begin
                // Only the cause union may change after the first snapshot.
                terminal_causes <= terminal_causes | cause_now;
            end else if (kill) begin
                // N and P are pre-edge semantic/physical counts. The old
                // output transfer T is retained; the new input is discarded.
                terminal_cancelled <= 1'b1;
                terminal_ctx <= active_ctx;
                terminal_causes <= cause_now;
                terminal_n <= n_count;
                terminal_p <= p_count;
                terminal_t <= output_transfer;
                terminal_cancelled_untransferred <=
                    n_count - p_count - {9'b0, output_transfer};
                terminal_s_transfer <= input_transfer;
                terminal_t_bin <= output_transfer ? m_bin : 10'b0;
                q_valid <= 1'b0;
                data_done <= 1'b0;
            end else begin
                if (output_transfer) begin
                    p_count <= p_count + 10'd1;
                    if ((p_count == 10'd512) && (n_count == BEATS))
                        data_done <= 1'b1;
                end

                if (input_transfer) begin
                    n_count <= n_count + 10'd1;
                    q_valid <= 1'b1;
                    m_ctx <= active_ctx;
                    m_bin <= s_bin;
                    m_ov_re <= overflow_re;
                    m_ov_im <= overflow_im;
                    m_numeric_valid <= !(overflow_re || overflow_im);
                    m_re <= (overflow_re || overflow_im) ? 25'sd0 : rounded_re[24:0];
                    m_im <= (overflow_re || overflow_im) ? 25'sd0 : rounded_im[24:0];
                    if (overflow_re || overflow_im)
                        sticky_numeric_overflow <= 1'b1;
                end else if (output_transfer) begin
                    q_valid <= 1'b0;
                end
            end

            // The pre-edge predicates deliberately reject same-edge ack or
            // cancel as evidence for retirement.
            if (retire_ok) begin
                ctx_active <= 1'b0;
                active_ctx <= '0;
                terminal_saved <= 1'b0;
                n_count <= '0;
                p_count <= '0;
                q_valid <= 1'b0;
                m_ctx <= '0;
                m_bin <= '0;
                m_re <= '0;
                m_im <= '0;
                m_numeric_valid <= 1'b0;
                m_ov_re <= 1'b0;
                m_ov_im <= 1'b0;
                data_done <= 1'b0;
                sticky_numeric_overflow <= 1'b0;
                terminal_cancelled <= 1'b0;
                terminal_ctx <= '0;
                terminal_causes <= '0;
                terminal_n <= '0;
                terminal_p <= '0;
                terminal_t <= 1'b0;
                terminal_cancelled_untransferred <= '0;
                terminal_s_transfer <= 1'b0;
                terminal_t_bin <= '0;
            end
        end
    end
endmodule
