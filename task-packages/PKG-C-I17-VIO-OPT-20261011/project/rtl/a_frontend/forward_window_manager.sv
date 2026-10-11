`timescale 1ns/1ps
// TEST_ONLY control namespace. Cold reset only uses external aresetn.
// diag_reset is an explicit warm request, never a cold reset shortcut.
module forward_window_manager #(
    parameter integer WATCHDOG_BITS=23
)(
    input wire clk, input wire cold_rst_n,
    input wire config_valid, output wire config_ready,
    input wire config_boot_valid, input wire [63:0] config_boot,
    input wire config_epoch_valid, input wire [63:0] config_epoch,
    input wire config_sid_valid, input wire [31:0] config_sid,
    input wire start_control, stop_control, warm_control,
    output wire decl_boot_valid, output wire [63:0] decl_boot,
    output wire decl_epoch_valid, output wire [63:0] decl_epoch,
    output wire decl_sid_valid, output wire [31:0] decl_sid,
    output wire start_valid, input wire start_ready,
    output wire stop_valid, input wire stop_ready,
    output wire prepare_valid, input wire prepare_ready,
    output wire reset_valid, input wire reset_ready,
    output wire clear_valid, input wire clear_ready,
    input wire actual_start_fire, actual_stop_fire,
    input wire m_fire, m_last,
    input wire terminal_copy, terminal_drained,
    input wire [31:0] source_status,
    input wire session_active, fault_latched, local_cancel,
    input wire [2:0] caller_lifecycle,
    input wire reset_abort, reset_executed,
    input wire bank_warning, bank_full, allocator_exhausted,
    input wire ff_quiet, normal_source_quiet, ff_abort,
    output wire ff_session_aborted,
    input wire store_error, input wire [7:0] store_error_code,
    input wire caller_error, input wire [7:0] caller_error_code,
    output wire halt_reader,
    output wire config_present, output wire terminal_seen,
    output wire [7:0] state,
    output wire [31:0] frame_count,
    output wire [63:0] actual_start_count, actual_stop_count,
    output wire [63:0] m_count, terminal_count,
    output wire error_valid, output wire [7:0] error_code
);
    localparam [7:0] IDLE=0, START_OFFER=1, RUN=2, STOP_OFFER=3,
        DRAIN=4, NORMAL_HOLD=5, PREPARE_OFFER=6, WAIT_RESET=7,
        RESET_WAIT=8, CLEAR_OFFER=9, ERROR_HOLD=10;
    localparam [7:0] ERR_NONE=0, ERR_CONFIG=1, ERR_START=2, ERR_BANK_FULL=3,
        ERR_ALLOCATOR=4, ERR_EXPORT=6, ERR_WATCHDOG=7,
        ERR_CALLER=8, ERR_RESET_ABORT=9, ERR_COUNTER=10, ERR_CONTROL=11;
    reg [7:0] state_q;
    reg start_armed,stop_armed,warm_armed,config_armed;
    reg config_q,boot_valid_q,epoch_valid_q,sid_valid_q;
    reg [63:0] boot_q,epoch_q;
    reg [31:0] sid_q;
    reg halt_q,warm_pending_q,terminal_q;
    reg ff_abort_q;
    reg error_q;
    reg [7:0] error_code_q;
    reg [31:0] frames_q;
    reg [63:0] starts_q,stops_q,rows_q,terminals_q;
    reg [WATCHDOG_BITS-1:0] watchdog_q;
    reg watchdog_active_q;
    wire start_event=start_control && start_armed;
    wire stop_event=stop_control && stop_armed;
    wire warm_event=warm_control && warm_armed;
    wire config_event=config_valid && config_ready;
    wire all_declared=boot_valid_q && epoch_valid_q && sid_valid_q;
    wire source_drained=source_status[31:24]==8'hc1 && !source_status[5] &&
        !source_status[2] && source_status[3] && !source_status[0] &&
        !source_status[6] && !source_status[7];
    wire normal_finished=terminal_q && source_drained && !session_active &&
        ff_quiet && normal_source_quiet;
    wire watchdog_timeout=watchdog_active_q && (&watchdog_q) && !normal_finished;
    wire local_fault=bank_full || allocator_exhausted || store_error || watchdog_timeout;
    // Current forward abort is session control; full original reasons stay in forward records.
    wire session_abort=ff_abort || ff_abort_q;
    assign ff_session_aborted=ff_abort_q;
    wire source_fault=fault_latched || local_cancel || caller_error;
    // Hard failures can retain obligations indefinitely. No forced reset.
    // Warm cancellation must not wait for FFT/report ready or normal_finished.
    assign halt_reader=halt_q || local_fault || source_fault || session_abort ||
        warm_event || warm_pending_q ||
        state_q==PREPARE_OFFER || state_q==WAIT_RESET || state_q==RESET_WAIT ||
        state_q==CLEAR_OFFER || state_q==ERROR_HOLD;
    assign config_ready=cold_rst_n && state_q==IDLE && config_armed;
    assign config_present=config_q;
    assign decl_boot_valid=boot_valid_q;
    assign decl_boot=boot_q;
    assign decl_epoch_valid=epoch_valid_q;
    assign decl_epoch=epoch_q;
    assign decl_sid_valid=sid_valid_q;
    assign decl_sid=sid_q;
    assign start_valid=cold_rst_n && state_q==START_OFFER && !local_fault && !source_fault && !session_abort && !warm_event && !warm_pending_q && !stop_event;
    assign stop_valid=cold_rst_n && state_q==STOP_OFFER && !local_fault && !source_fault && !session_abort;
    // Prepare starts caller cancellation; ff_quiet here would deadlock a live lease.
    assign prepare_valid=cold_rst_n && state_q==PREPARE_OFFER && caller_lifecycle!=7;
    assign reset_valid=cold_rst_n && state_q==WAIT_RESET && warm_pending_q && !allocator_exhausted && ff_quiet;
    assign clear_valid=cold_rst_n && state_q==CLEAR_OFFER && ff_quiet;
    assign state=state_q;
    assign frame_count=frames_q;
    assign terminal_seen=terminal_q;
    assign actual_start_count=starts_q;
    assign actual_stop_count=stops_q;
    assign m_count=rows_q;
    assign terminal_count=terminals_q;
    assign error_valid=error_q;
    assign error_code=error_code_q;
    always @(posedge clk) begin
        if(!cold_rst_n) begin
            state_q<=IDLE; start_armed<=0; stop_armed<=0; warm_armed<=0; config_armed<=0;
            config_q<=0; boot_valid_q<=0; epoch_valid_q<=0; sid_valid_q<=0;
            boot_q<=0; epoch_q<=0; sid_q<=0; halt_q<=0; warm_pending_q<=0; terminal_q<=0; ff_abort_q<=0;
            frames_q<=0; starts_q<=0; stops_q<=0; rows_q<=0; terminals_q<=0;
            watchdog_q<=0; watchdog_active_q<=0; error_q<=0; error_code_q<=ERR_NONE;
        end else begin
            if(!start_control) start_armed<=1; else if(start_armed) start_armed<=0;
            if(!stop_control) stop_armed<=1; else if(stop_armed) stop_armed<=0;
            if(!warm_control) warm_armed<=1; else if(warm_armed) warm_armed<=0;
            if(!config_valid) config_armed<=1; else if(config_event) config_armed<=0;
            if(config_event) begin
                config_q<=1; boot_valid_q<=config_boot_valid; boot_q<=config_boot;
                epoch_valid_q<=config_epoch_valid; epoch_q<=config_epoch;
                sid_valid_q<=config_sid_valid; sid_q<=config_sid;
                if(!(config_boot_valid && config_epoch_valid && config_sid_valid) && !error_q) begin
                    error_q<=1; error_code_q<=ERR_CONFIG;
                end
            end
            if(m_fire) begin
                if(rows_q!=64'hffffffffffffffff) rows_q<=rows_q+64'd1;
                if(m_last && frames_q!=32'hffffffff) frames_q<=frames_q+32'd1;
            end
            if(terminal_copy) begin
                if(terminals_q!=64'hffffffffffffffff) terminals_q<=terminals_q+64'd1;
                if(terminal_drained) terminal_q<=1;
            end
            if(actual_start_fire) begin
                if(starts_q!=64'hffffffffffffffff) starts_q<=starts_q+64'd1;
                frames_q<=0; terminal_q<=0; watchdog_q<=0; watchdog_active_q<=1;
            end else if(watchdog_active_q && !(&watchdog_q)) watchdog_q<=watchdog_q+1'b1;
            if(actual_stop_fire && stops_q!=64'hffffffffffffffff) stops_q<=stops_q+64'd1;
            if(normal_finished || reset_executed) watchdog_active_q<=0;
            if(ff_abort) ff_abort_q<=1;
            if(local_fault || source_fault || session_abort) halt_q<=1;
            // First local diagnostic error is retained across warm clear.
            // Detailed native caller code and export code remain separate ports.
            if(!error_q) begin
                if(allocator_exhausted) begin error_q<=1; error_code_q<=ERR_ALLOCATOR; end
                else if(bank_full) begin error_q<=1; error_code_q<=ERR_BANK_FULL; end
                else if(store_error) begin error_q<=1; error_code_q<=ERR_EXPORT; end
                else if(watchdog_timeout) begin error_q<=1; error_code_q<=ERR_WATCHDOG; end
                else if(caller_error) begin error_q<=1; error_code_q<=ERR_CALLER; end
                else if(rows_q==64'hffffffffffffffff || terminals_q==64'hffffffffffffffff ||
                    starts_q==64'hffffffffffffffff || stops_q==64'hffffffffffffffff || frames_q==32'hffffffff)
                    begin error_q<=1; error_code_q<=ERR_COUNTER; halt_q<=1; end
            end
            if(warm_event) warm_pending_q<=1;
            case(state_q)
                IDLE: begin
                    // An accepted warm request owns recovery before any new start.
                    if(warm_event) state_q<=PREPARE_OFFER;
                    else if(start_event) begin
                        if(config_q && all_declared && !bank_warning && !bank_full && !allocator_exhausted &&
                            !source_fault && !local_fault && !session_abort && !halt_q) state_q<=START_OFFER;
                        else if(!error_q) begin error_q<=1; error_code_q<=ERR_START; end
                    end
                end
                START_OFFER: begin
                    if(local_fault || source_fault || session_abort) state_q<=PREPARE_OFFER;
                    else if(start_valid && start_ready) state_q<=RUN;
                    // Warm owns prepare/reset/clear; stop only withdraws the offer.
                    else if(warm_event) state_q<=PREPARE_OFFER;
                    else if(stop_event) state_q<=IDLE;
                end
                RUN: begin
                    if(local_fault || source_fault || session_abort) state_q<=PREPARE_OFFER;
                    else if(stop_event || warm_event || bank_warning || (m_fire && m_last && frames_q==2))
                        state_q<=STOP_OFFER;
                end
                STOP_OFFER: begin
                    if(local_fault || source_fault || session_abort) state_q<=PREPARE_OFFER;
                    else if(stop_valid && stop_ready) state_q<=DRAIN;
                end
                DRAIN: begin
                    if(local_fault || source_fault || session_abort) state_q<=PREPARE_OFFER;
                    else if(normal_finished) begin
                        state_q<=warm_pending_q || warm_event ? PREPARE_OFFER : NORMAL_HOLD;
                    end
                end
                NORMAL_HOLD: begin
                    if(warm_event) state_q<=PREPARE_OFFER;
                    else if(local_fault || source_fault || session_abort) state_q<=PREPARE_OFFER;
                end
                PREPARE_OFFER: if(prepare_valid && prepare_ready) state_q<=WAIT_RESET;
                WAIT_RESET: if(reset_valid && reset_ready) state_q<=RESET_WAIT;
                RESET_WAIT: begin
                    if(reset_executed) state_q<=CLEAR_OFFER;
                    else if(reset_abort) begin
                        state_q<=ERROR_HOLD; warm_pending_q<=0;
                        if(!error_q) begin error_q<=1; error_code_q<=ERR_RESET_ABORT; end
                    end
                end
                CLEAR_OFFER: if(clear_valid && clear_ready) begin
                    state_q<=IDLE; warm_pending_q<=0; halt_q<=0; config_q<=0; ff_abort_q<=0;
                    // Banks, export snapshot, identity allocators and first
                    // diagnostic error survive. A new explicit config is needed.
                end
                ERROR_HOLD: begin
                    if(warm_event && caller_lifecycle==4 && !allocator_exhausted) state_q<=WAIT_RESET;
                end
                default: begin state_q<=ERROR_HOLD; halt_q<=1; end
            endcase
            if(caller_lifecycle==7) begin state_q<=ERROR_HOLD; halt_q<=1; warm_pending_q<=0; end
        end
    end
endmodule
