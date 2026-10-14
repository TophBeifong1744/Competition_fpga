`timescale 1ns/1ps
module tb_i17_continuous_control;
    reg clk=0; always #5 clk=~clk;
    reg rst_n=0,cmd_valid=0,stop_request=0,frontend_ready=0;
    reg [2:0] cmd_op=0;
    reg [159:0] context_pending={64'habc,64'hdef,32'd7};
    reg [95:0] map_pending=0;
    reg [23:0] timeout_pending=32;
    reg config_ready=1,pipeline_quiet=1,capture_drained=1,report_manual=0,abort_fire=0,source_fault=0;
    reg [7:0] manager_state=0;
    reg report_offer=0, report_feedback=0;
    wire cmd_ready,cmd_done; wire [7:0] cmd_error,state,first_fault;
    wire [159:0] context_config; wire [95:0] map_config; wire [164:0] declared_context;
    wire config_valid,configured,research_valid,map_valid,servo_enable,motion_open_request;
    wire run_level,stop_now,fault_now,fft_permit,diag_start,warm_reset;
    wire report_fire=report_feedback ? report_offer && !fault_now : report_manual;
    wire [63:0] report_count,abort_count;
    i17_continuous_control dut(.*,.current_qualified(1'b1));
    integer checks=0;
    task ck(input bit good,input string label);
        begin checks++; if(!good) $fatal(1,"CONTROL_CHECK %s state=%0d",label,state); end
    endtask
    task tick; begin @(posedge clk); #1; end endtask
    task command(input [2:0] op,input [7:0] expected_error);
        begin @(negedge clk);cmd_op=op;cmd_valid=1;tick();
            ck(cmd_done && cmd_error==expected_error,"command response");
            @(negedge clk);cmd_valid=0;
        end
    endtask
    task configure;
        begin command(1,0);ck(config_valid && declared_context=={2'd1,1'b1,64'habc,1'b1,64'hdef,1'b1,32'd7},"context before busy");
            tick();ck(state==2 && configured,"configured");
        end
    endtask
    task recover;
        begin command(4,0);ck(warm_reset && state==8,"warm request");
            tick();ck(state==8,"old idle not completion");
            @(negedge clk);manager_state=6;tick();tick();
            @(negedge clk);manager_state=0;tick();
            ck(state==0 && !configured && !fault_now,"observed true recovery");
        end
    endtask
    initial begin
        map_pending[23:0]=24'd46080;map_pending[25:24]=1;
        map_pending[43:26]=-18'sd46080;map_pending[61:44]=18'sd46079;
        map_pending[70:62]=0;map_pending[79:71]=360;map_pending[80]=1;map_pending[81]=1;
        repeat(3)tick();@(negedge clk);rst_n=1;tick();
        command(2,5);timeout_pending=0;command(1,4);timeout_pending=24'd8388609;command(1,4);timeout_pending=32;
        configure();command(2,0);ck(!run_level,"wait warmed frontend");
        tick();ck(state==3 && fft_permit,"FFT permit before qualified");
        @(negedge clk);frontend_ready=1;tick();ck(run_level && declared_context[162],"first run admitted");
        tick();ck(diag_start && state==5,"diagnostic starts after capture");
        @(negedge clk);manager_state=2;
        for(integer n=0;n<100;n++) begin
            repeat(7)tick();@(negedge clk);report_manual=1;tick();
            ck(run_level && !fault_now,"report must not stop session");
            @(negedge clk);report_manual=0;
        end
        ck(report_count==100,"automatic completion count");
        command(1,4); // 配置不可在RUN改变。
        @(negedge clk);report_manual=1;cmd_valid=1;cmd_op=4;#1;
        ck(!servo_enable && !run_level && stop_now,"RECOVER coincident report veto");tick();
        @(negedge clk);report_manual=0;cmd_valid=0;pipeline_quiet=0;capture_drained=0;manager_state=6;
        tick();tick();@(negedge clk);manager_state=0;tick();
        ck(state==8,"recovery waits physical quiet and capture drain");
        @(negedge clk);pipeline_quiet=1;capture_drained=1;tick();ck(state==0,"recovery complete");
        configure();command(2,0);tick();tick();@(negedge clk);manager_state=2;
        @(negedge clk);pipeline_quiet=0;capture_drained=0;report_manual=1;stop_request=1;#1;
        ck(!servo_enable && stop_now && !run_level,"STOP coincident report veto");tick();
        @(negedge clk);report_manual=0;manager_state=4;
        repeat(4)tick();ck(state==6 && fft_permit,"STOP holds drain permits");
        @(negedge clk);pipeline_quiet=1;capture_drained=1;manager_state=5;tick();ck(state==7,"drained held");
        command(2,5);recover();ck(stop_now,"external STOP stays high after recovery");
        @(negedge clk);stop_request=0;configure();command(2,0);tick();tick();
        @(negedge clk);manager_state=2;pipeline_quiet=0;source_fault=1;report_manual=1;#1;
        ck(fault_now && !servo_enable,"late error same-edge report veto");tick();
        ck(first_fault==8'h32,"first fault retained");
        @(negedge clk);source_fault=0;report_manual=0;manager_state=5;pipeline_quiet=1;tick();recover();
        configure();command(2,0);tick();tick();@(negedge clk);manager_state=2;pipeline_quiet=0;
        repeat(33)tick();ck(fault_now && !run_level && first_fault==8'h32,"no completion deadline retains first cause");
        // 排空超时不伪造quiet；等待状态只作安全挂起。
        repeat(35)tick();ck(state==7 && !pipeline_quiet && fault_now,"unretired timeout stays held");
        // 重复RECOVER不得刷新在途恢复期限；真实DRAIN晚错不能被超时替代首因。
        @(negedge clk);rst_n=0;tick();@(negedge clk);rst_n=1;manager_state=0;pipeline_quiet=1;
        tick();configure();command(2,0);tick();tick();@(negedge clk);manager_state=2;
        pipeline_quiet=0;command(3,0);ck(state==6,"stop for late fault test");
        @(negedge clk);source_fault=1;#1;ck(fault_now,"drain fault same-edge propagation");tick();
        ck(first_fault==8'h32 && state==6,"drain first cause is source fault");
        repeat(33)tick();ck(state==7 && first_fault==8'h32,"persistent source fault does not refresh drain timer");
        @(negedge clk);source_fault=0;pipeline_quiet=1;manager_state=5;command(4,0);
        for(integer n=0;n<7;n++)command(4,2);
        repeat(22)tick();ck(state==7 && fault_now,"duplicate recovery commands cannot extend deadline");
        // 按真实B的!kill屏蔽report形成反馈刺激：到期前可完成，到期沿必须撤权。
        @(negedge clk);rst_n=0;tick();@(negedge clk);rst_n=1;manager_state=0;
        pipeline_quiet=1;capture_drained=1;tick();configure();command(2,0);tick();tick();
        @(negedge clk);manager_state=2;pipeline_quiet=0;report_feedback=1;
        wait(dut.elapsed_q==30);@(negedge clk);report_offer=1;#1;
        ck(report_fire && !fault_now && servo_enable,"report before deadline accepted");tick();
        ck(dut.elapsed_q==0 && first_fault==0,"accepted progress clears deadline");
        @(negedge clk);report_offer=0;wait(dut.elapsed_q==31);@(negedge clk);report_offer=1;#1;
        ck(fault_now && !report_fire && !servo_enable,"deadline independent of killed report feedback");tick();
        ck(first_fault==8'h31 && state==6,"deadline first cause and bounded drain");
        $display("CONTROL_COMPLETE checks=%0d reports=%0d",checks,report_count);$finish;
    end
    initial begin #100000;$fatal(1,"CONTROL_HANG");end
endmodule
