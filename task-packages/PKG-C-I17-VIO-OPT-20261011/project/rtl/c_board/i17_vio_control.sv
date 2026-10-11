`timescale 1ns/1ps
`default_nettype none
// 中文用途：同域 VIO 命令转为一次真实窗口的配置、启动、身份绑定及授权握手。
module i17_vio_control (
    input wire clk, rst_n,
    input wire [31:0] control,
    input wire [159:0] context_pending,
    input wire [95:0] map_pending,
    input wire [31:0] read_pending,
    input wire config_ready, frontend_ready,
    input wire [7:0] manager_state,
    input wire ff_busy, ff_quiet, ff_obligation, doa_busy, doa_obligation, axis_valid,
    input wire ff_terminal_valid, ff_abort_valid, ff_m_valid,
    input wire [724:0] source_identity,
    input wire current_qualified, report_saved, abort_saved,
    input wire evidence_empty, io_busy,
    output reg [159:0] context_config,
    output reg [95:0] map_config,
    output wire config_valid, research_valid, map_valid, servo_enable,
    output reg start, diag_start, warm_reset,
    output wire stop_now, fault_now, fft_permit,
    output wire arm_request,
    output reg [724:0] declared_tuple,
    output wire [164:0] declared_context,
    output wire [63:0] declared_generation,
    output reg [4:0] action,
    output reg [31:0] read_command,
    output reg [7:0] state, error_code,
    output reg configured,
    output wire observe_only, motion_open_request
);
    localparam [7:0] IDLE=0, CONFIG=1, READY=2, WAIT_FRONTEND=3,
        START_SOURCE=4, START_DIAG=5, BIND=6, ARM_LOW=7, ARM_HIGH=8,
        WAIT_QUALIFIED=9, RUN=10, DRAIN=11, HELD=12, RECOVER=13;
    reg [31:0] previous;
    reg baseline, authorization, fault_q;
    reg recovery_seen_active;
    wire [31:0] changed = (control ^ previous) & 32'h000001fb;
    wire multiple = (changed & (changed - 32'd1)) != 0;
    wire quiet = ff_quiet && !ff_busy && !ff_obligation && !doa_busy &&
                 !doa_obligation && !axis_valid;
    wire [164:0] expected_context = {2'd1,1'b1,context_config[159:96],
         1'b1,context_config[95:32],1'b1,context_config[31:0]};
    wire pending_map_legal;
    signed_angle_map check_pending (
        .config_valid(map_pending[80]),.angle_q8(18'sd0),
        .offset_q8(map_pending[23:0]),.direction(map_pending[25:24]),
        .domain_min_q8(map_pending[43:26]),.domain_max_q8(map_pending[61:44]),
        .mechanical_min(map_pending[70:62]),.mechanical_max(map_pending[79:71]),
        .servo_max(9'd360),.config_legal(pending_map_legal),.valid(),.angle_deg());
    wire pending_legal = map_pending[95:83] == 0 &&
        (map_pending[82] ? !map_pending[81] : (map_pending[81] && pending_map_legal &&
         map_pending[70:62]<=9'd180 && map_pending[79:71]>=9'd180));
    assign observe_only = map_config[82];
    assign stop_now = control[2] || fault_q;
    assign fault_now = fault_q;
    assign config_valid = state == CONFIG && !stop_now;
    assign research_valid = configured;
    assign map_valid = configured && !observe_only && map_config[80];
    assign servo_enable = authorization && !stop_now && !fault_q && map_valid && map_config[81];
    assign motion_open_request = servo_enable && current_qualified;
    assign arm_request = (state == ARM_HIGH || state == WAIT_QUALIFIED || state == RUN) && servo_enable;
    // STOP 后仍排空 FFT/status，撤授权不能变成对已有义务的反压。
    assign fft_permit = state == RUN || state == DRAIN || state == HELD || state == RECOVER;
    assign declared_context = declared_tuple[596:432];
    assign declared_generation = declared_tuple[660:597];
    always @(posedge clk) begin
        if (!rst_n) begin
            previous<=0; baseline<=0; context_config<=0; map_config<=96'h400000000000000000000;
            configured<=0; authorization<=0; fault_q<=0; start<=0;
            diag_start<=0; warm_reset<=0; declared_tuple<=0;
            state<=IDLE; error_code<=0; action<=0; read_command<=0;
            recovery_seen_active<=0;
        end else begin
            previous<=control; baseline<=1; diag_start<=0; warm_reset<=0; action<=0;
            // 上电采样当前 toggle 基线，不把 JTAG 保留值当作一次新操作。
            if (baseline) begin
                case (state)
                    CONFIG: if(config_valid && config_ready) begin configured<=1; state<=READY; end
                    WAIT_FRONTEND: if(frontend_ready) begin start<=1; state<=START_SOURCE; end
                    START_SOURCE: begin diag_start<=1; state<=START_DIAG; end
                    START_DIAG: state<=BIND;
                    BIND: if(ff_abort_valid || ff_terminal_valid || ff_m_valid) begin
                        fault_q<=1; error_code<=8'h21; state<=DRAIN; start<=0; authorization<=0;
                    end else if(ff_busy) begin
                        if(source_identity[596:432] != expected_context) begin
                            fault_q<=1; error_code<=8'h22; state<=DRAIN; start<=0; authorization<=0;
                        end else begin
                            declared_tuple<=source_identity;
                            state<=observe_only ? RUN : ARM_LOW;
                        end
                    end
                    ARM_LOW: state<=ARM_HIGH;
                    ARM_HIGH: state<=WAIT_QUALIFIED;
                    WAIT_QUALIFIED: if(current_qualified) state<=RUN;
                    // C-VIO-STATIC-001：前端 NORMAL_HOLD 不代表 DOA/IFFT 已完成。
                    // 单窗口许可保持到真实结果/ABORT 被存下，或明确错误/STOP。
                    RUN: if(report_saved || abort_saved || manager_state==8'd10) begin
                        state<=DRAIN; start<=0; authorization<=0;
                    end
                    DRAIN: if(quiet) state<=HELD;
                    RECOVER: begin
                        // C-VIO-STATIC-002：请求被原 manager 采样前的旧 IDLE 不能作恢复完成。
                        if(!warm_reset && manager_state>=8'd6 && manager_state<=8'd9)
                            recovery_seen_active<=1;
                        if(recovery_seen_active && manager_state==0 && config_ready && quiet) begin
                            configured<=0; fault_q<=0; state<=IDLE;
                        end
                    end
                    default: begin end
                endcase
                // 无论当前读数事务如何，STOP 都优先撤销本窗口的运动资格。
                if(stop_now) begin
                    authorization<=0; start<=0; diag_start<=0;
                    if(state>=WAIT_FRONTEND && state<=RUN) state<=DRAIN;
                    if(state==CONFIG) begin state<=IDLE; configured<=0; end
                end
                if(state>=ARM_LOW && state<=WAIT_QUALIFIED &&
                   (ff_abort_valid || ff_terminal_valid || ff_m_valid || manager_state==8'd10)) begin
                    fault_q<=1; error_code<=8'h23; state<=DRAIN; start<=0; authorization<=0;
                end
                if(changed!=0) begin
                    if(control[31:9]!=0 || multiple) error_code<=8'h01;
                    else if(changed[3]) begin
                        if(!io_busy && state!=CONFIG) begin
                            warm_reset<=1; start<=0; authorization<=0; configured<=0; state<=RECOVER;
                            recovery_seen_active<=0;
                        end else error_code<=8'h02;
                    end else if(changed[4] || changed[5] || changed[6] || changed[7] || changed[8]) begin
                        // 读出不触发运动；STOP 下仍允许保存/释放证据。
                        action<={changed[8],changed[7],changed[6],changed[5],changed[4]};
                        read_command<=read_pending;
                    end else if(stop_now) error_code<=8'h03;
                    else if(changed[0]) begin
                        if((state==IDLE || state==READY) && quiet && evidence_empty && !io_busy && config_ready && pending_legal) begin
                            context_config<=context_pending; map_config<=map_pending;
                            configured<=0; state<=CONFIG;
                        end else error_code<=8'h04;
                    end else if(changed[1]) begin
                        if(state==READY && configured && quiet && evidence_empty && !io_busy && manager_state==0) begin
                            authorization<=!observe_only && map_config[81]; state<=WAIT_FRONTEND;
                        end else error_code<=8'h05;
                    end
                end
            end
        end
    end
endmodule
`default_nettype wire
