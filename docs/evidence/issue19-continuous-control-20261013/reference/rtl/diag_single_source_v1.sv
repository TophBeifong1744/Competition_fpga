`timescale 1ns/1ps
`default_nettype none
// 实际FF offer先登记单帧租约，完成且物理义务归还后自动开放下一帧。
// 仍是声明上下文内的诊断控制，不生成生产Tracker或声学真值。
module diag_single_source_v1 (
    input wire clk, rst_n,
    input wire run_enable, config_valid, stop_now, fault_now, cancel_now,
    input wire [88:0] config_tuple,
    input wire [164:0] declared_context,
    input wire source_offer_valid,
    input wire [724:0] source_tuple,
    input wire completion_valid, pipeline_quiet,
    output wire lease_owned, armed, current_qualified, configuration_changed,
    output wire [724:0] leased_tuple,
    output wire [63:0] policy_id
);
    localparam [63:0] DIAGV001 = 64'h4449414756303031;
    reg owned_q, qualified_q, completed_q;
    reg [724:0] tuple_q;
    reg [88:0] config_q;
    // Parent context_t MSB layout: status[164:163], boot_valid[162],
    // epoch_valid[97], sid_valid[32]. Status 1 is DECLARED; zero is UNBOUND.
    wire context_declared = declared_context[164:163] == 2'd1 &&
                            declared_context[162] &&
                            declared_context[97] &&
                            declared_context[32];
    wire offer_declared = context_declared && source_tuple[596:432] == declared_context;
    wire valid_now = run_enable && config_valid && config_tuple == config_q &&
        context_declared && tuple_q[596:432] == declared_context &&
        !stop_now && !fault_now && !cancel_now;
    assign lease_owned = owned_q;
    assign configuration_changed = owned_q &&
        (!config_valid || config_tuple != config_q || !context_declared ||
         tuple_q[596:432] != declared_context);
    assign armed = owned_q && qualified_q;
    assign leased_tuple = tuple_q;
    assign policy_id = DIAGV001;
    assign current_qualified = rst_n && owned_q && qualified_q && valid_now;

    always @(posedge clk) begin
        if (!rst_n) begin
            owned_q <= 1'b0;
            qualified_q <= 1'b0;
            completed_q <= 1'b0;
            tuple_q <= 725'd0;
            config_q <= 89'd0;
        end else begin
            if (owned_q) begin
                if (!valid_now) qualified_q <= 1'b0;
                if (completion_valid) completed_q <= 1'b1;
                // 不以撤销资格冒充归还；报告/ABORT与真实空闲条件同时成立才释放。
                if ((completed_q || completion_valid) && pipeline_quiet) begin
                    owned_q <= 1'b0;
                    qualified_q <= 1'b0;
                    completed_q <= 1'b0;
                end
            end else if (source_offer_valid) begin
                tuple_q <= source_tuple;
                config_q <= config_tuple;
                owned_q <= 1'b1;
                completed_q <= 1'b0;
                // 取消后的终结也取得所有权用于排空，资格不能在后续沿补回。
                qualified_q <= run_enable && config_valid && offer_declared &&
                    !stop_now && !fault_now && !cancel_now;
            end
        end
    end
endmodule
`default_nettype wire
