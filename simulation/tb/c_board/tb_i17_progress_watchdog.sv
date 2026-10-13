`timescale 1ns/1ps
module tb_i17_progress_watchdog;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,config_valid=0,start_control=0,m_fire=0,m_last=0;
    wire config_ready, start_valid,halt_reader,error_valid;
    wire [7:0] state,error_code;
    // 限期按32拍缩放；只能刷新真实完整帧，不以任意半帧数据掩盖停顿。
    forward_window_manager #(.WATCHDOG_BITS(5),.CONTINUOUS_WATCHDOG(1)) dut(
        .clk(clk),.cold_rst_n(rst_n),.config_valid(config_valid),.config_ready(config_ready),
        .config_boot_valid(1'b1),.config_boot(64'd1),.config_epoch_valid(1'b1),.config_epoch(64'd2),
        .config_sid_valid(1'b1),.config_sid(32'd3),.start_control(start_control),.stop_control(1'b0),.warm_control(1'b0),
        .start_valid(start_valid),.start_ready(1'b1),.stop_ready(1'b1),.prepare_ready(1'b0),.reset_ready(1'b0),.clear_ready(1'b0),
        .actual_start_fire(start_valid),.actual_stop_fire(1'b0),.m_fire(m_fire),.m_last(m_last),
        .terminal_copy(1'b0),.terminal_drained(1'b0),.source_status(32'hc1000001),
        .session_active(1'b1),.fault_latched(1'b0),.local_cancel(1'b0),.caller_lifecycle(3'd0),
        .reset_abort(1'b0),.reset_executed(1'b0),.bank_warning(1'b0),.bank_full(1'b0),.allocator_exhausted(1'b0),
        .ff_quiet(1'b0),.normal_source_quiet(1'b0),.ff_abort(1'b0),.ff_stop_cancel_normal(1'b0),.ff_late_error(1'b0),
        .store_error(1'b0),.store_error_code(8'd0),.caller_error(1'b0),.caller_error_code(8'd0),
        .halt_reader(halt_reader),.state(state),.error_valid(error_valid),.error_code(error_code));
    initial begin
        repeat(4)@(negedge clk);rst_n=1;repeat(3)@(negedge clk);
        config_valid=1;@(negedge clk);config_valid=0;start_control=1;
        repeat(4)@(negedge clk);start_control=0;
        for(integer n=0;n<1000;n++)begin
            m_fire=1;m_last=n%8==0;@(negedge clk);
            if(halt_reader || error_valid || state!=2)$fatal(1,"WATCHDOG_CHECK healthy continuous session");
        end
        m_last=0; // 仍有零碎流量，不构成真实完整帧进展。
        repeat(35)@(negedge clk);
        if(!halt_reader || !error_valid || error_code!=7 || state!=6)$fatal(1,"WATCHDOG_CHECK no-progress deadline");
        $display("WATCHDOG_COMPLETE continuous_cycles=1000 limit=32 incomplete_traffic_rejected=1");$finish;
    end
    initial begin #100000;$fatal(1,"WATCHDOG_HANG");end
endmodule
