`timescale 1ns/1ps
`default_nettype none
// 中文用途：非VIO同域命令，先声明上下文，再持续启动；STOP只撤运动和新采集，不伪造排空。
module i17_continuous_control (
    input wire clk, rst_n,
    input wire cmd_valid, input wire [2:0] cmd_op,
    output wire cmd_ready, output reg cmd_done, output reg [7:0] cmd_error,
    input wire [159:0] context_pending, input wire [95:0] map_pending,
    input wire [23:0] timeout_pending,
    input wire stop_request,
    input wire config_ready, frontend_ready,
    input wire [7:0] manager_state,
    input wire pipeline_quiet, capture_drained,
    input wire report_fire, abort_fire, source_fault,
    output reg [159:0] context_config, output reg [95:0] map_config,
    output wire [164:0] declared_context,
    output wire config_valid, configured, research_valid, map_valid,
    output wire servo_enable, motion_open_request,
    input wire current_qualified,
    output wire run_level, stop_now, fault_now, fft_permit,
    output reg diag_start, warm_reset,
    output reg [7:0] state, first_fault,
    output reg [63:0] report_count, abort_count
);
    localparam [7:0] IDLE=0, CONFIG=1, READY=2, WAIT_FRONTEND=3,
        START_SOURCE=4, RUN=5, DRAIN=6, HELD=7, RECOVER=8;
    localparam [2:0] CMD_CONFIG=1, CMD_RUN=2, CMD_STOP=3, CMD_RECOVER=4;
    reg configured_q, fault_q, recovery_seen;
    reg [23:0] deadline_q, elapsed_q;
    wire map_legal;
    signed_angle_map check_map (
        .config_valid(map_pending[80]),.angle_q8(18'sd0),
        .offset_q8(map_pending[23:0]),.direction(map_pending[25:24]),
        .domain_min_q8(map_pending[43:26]),.domain_max_q8(map_pending[61:44]),
        .mechanical_min(map_pending[70:62]),.mechanical_max(map_pending[79:71]),
        .servo_max(9'd360),.config_legal(map_legal),.valid(),.angle_deg());
    // 连续前端也需要合法映射；观察模式仅禁止物理运动，不绕过来源资格。
    wire pending_legal = map_pending[95:83]==0 && map_legal &&
        (map_pending[82] ? !map_pending[81] : map_pending[81]) &&
        map_pending[70:62]<=9'd180 && map_pending[79:71]>=9'd180 &&
        timeout_pending!=0 && timeout_pending<=24'd8388608;
    wire command_fire = cmd_valid && cmd_ready;
    wire stop_command = command_fire && cmd_op==CMD_STOP;
    wire recover_command = command_fire && cmd_op==CMD_RECOVER && state!=CONFIG && state!=RECOVER;
    wire timed_state = state==CONFIG || state==WAIT_FRONTEND ||
        state==START_SOURCE || state==RUN || state==DRAIN || state==RECOVER;
    wire progress = (state==RUN && report_fire) ||
        (state==CONFIG && config_ready) || (state==WAIT_FRONTEND && frontend_ready);
    wire timeout_now = timed_state && !progress && elapsed_q>=deadline_q-1'b1;
    wire source_fault_now = (state==START_SOURCE || state==RUN || state==DRAIN) && source_fault;
    wire fault_event = !fault_q && (source_fault_now || (state==RUN && abort_fire));
    wire stop_level = stop_request || stop_command;
    assign cmd_ready = rst_n;
    assign configured = configured_q;
    assign config_valid = state==CONFIG && !stop_level && !fault_q;
    assign declared_context = configured_q || state==CONFIG ?
        {2'd1,1'b1,context_config[159:96],1'b1,context_config[95:32],1'b1,context_config[31:0]} : 165'd0;
    assign research_valid = configured_q;
    assign map_valid = configured_q && map_config[80];
    assign run_level = (state==START_SOURCE || state==RUN) && !stop_level && !recover_command && !fault_q && !timeout_now;
    assign fault_now = fault_q || timeout_now || source_fault_now;
    assign stop_now = stop_level || recover_command || state==DRAIN || state==HELD || state==RECOVER || fault_now;
    assign servo_enable = run_level && !stop_now && !map_config[82] && map_config[81] && map_valid;
    assign motion_open_request = servo_enable && current_qualified;
    // FFT/status始终可排空；资格只用于运动交付，不能反压其自身建立过程。
    assign fft_permit = rst_n;
    always @(posedge clk) begin
        if(!rst_n) begin
            state<=IDLE; configured_q<=0; fault_q<=0; first_fault<=0;
            context_config<=0; map_config<=0; deadline_q<=24'd8388608;
            elapsed_q<=0; diag_start<=0; warm_reset<=0; recovery_seen<=0;
            cmd_done<=0; cmd_error<=0; report_count<=0; abort_count<=0;
        end else begin
            diag_start<=0; warm_reset<=0; cmd_done<=command_fire; cmd_error<=0;
            if(report_fire && report_count!=64'hffffffffffffffff) report_count<=report_count+1'b1;
            if(abort_fire && abort_count!=64'hffffffffffffffff) abort_count<=abort_count+1'b1;
            if(!timed_state || progress) elapsed_q<=0;
            else if(!(&elapsed_q)) elapsed_q<=elapsed_q+1'b1;
            case(state)
                CONFIG: if(config_valid && config_ready) begin configured_q<=1; state<=READY; end
                WAIT_FRONTEND: if(frontend_ready && !stop_level) begin state<=START_SOURCE; elapsed_q<=0; end
                START_SOURCE: begin diag_start<=1; state<=RUN; elapsed_q<=0; end
                RUN: if(manager_state>=3 && manager_state<=5) begin state<=DRAIN; elapsed_q<=0; end
                DRAIN: if(pipeline_quiet && capture_drained && (manager_state==5 || manager_state==0)) begin
                    state<=HELD; elapsed_q<=0;
                end
                RECOVER: begin
                    if(!warm_reset && manager_state>=6 && manager_state<=9) recovery_seen<=1;
                    if(recovery_seen && manager_state==0 && config_ready && pipeline_quiet && capture_drained) begin
                        configured_q<=0; fault_q<=0; state<=IDLE; elapsed_q<=0;
                    end
                end
                default: begin end
            endcase
            if(command_fire) begin
                case(cmd_op)
                    CMD_CONFIG: if((state==IDLE || state==READY) && !stop_request &&
                        pipeline_quiet && capture_drained && config_ready && pending_legal) begin
                        context_config<=context_pending; map_config<=map_pending;
                        deadline_q<=timeout_pending; elapsed_q<=0; configured_q<=0; state<=CONFIG;
                    end else cmd_error<=8'h04;
                    CMD_RUN: if(state==READY && configured_q && !stop_request &&
                        !fault_q && pipeline_quiet && capture_drained && manager_state==0) begin
                        state<=WAIT_FRONTEND; elapsed_q<=0;
                    end else cmd_error<=8'h05;
                    CMD_STOP: begin end // 幂等；低于故障和恢复优先级。
                    CMD_RECOVER: if(recover_command) begin
                        warm_reset<=1; state<=RECOVER; recovery_seen<=0; elapsed_q<=0;
                    end else cmd_error<=8'h02;
                    default: cmd_error<=8'h01;
                endcase
            end
            if(stop_level && !recover_command) begin
                diag_start<=0;
                if(state==CONFIG) begin state<=IDLE; configured_q<=0; end
                else if(state==WAIT_FRONTEND || state==START_SOURCE || state==RUN || state==READY) begin
                    state<=DRAIN; elapsed_q<=0;
                end
            end
            // 取消/晚错和结果无进展均保留首因；绝不超时强清物理busy。
            if(timeout_now || fault_event) begin
                fault_q<=1; diag_start<=0; elapsed_q<=0;
                if(first_fault==0) first_fault<=timeout_now ? 8'h31 : 8'h32;
                if(!recover_command) begin
                    if(timeout_now && (state==DRAIN || state==RECOVER)) state<=HELD;
                    else state<=DRAIN;
                end
            end
        end
    end
endmodule
`default_nettype wire
