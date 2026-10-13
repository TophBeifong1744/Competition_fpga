`timescale 1ns/1ps
module tb_i17_continuous_noise;
    reg clk=0;always #8.138 clk=~clk;
    reg rst_n=0,cmd_valid=0,stop_request=0,diag_ready=1;
    reg [2:0] cmd_op=0;reg [159:0] context_pending={64'd1,64'd2,32'd3};
    reg [95:0] map_pending=0;reg [23:0] timeout_pending=24'd8388608;
    reg [3:0] mic_data=0;wire [3:0] mic_clock;
    wire cmd_ready,cmd_done;wire [7:0] cmd_error,control_state,first_fault;
    wire diag_valid,diag_last,result_valid,result_abort,result_eligible,pwm_horizontal,pwm_vertical;
    wire [31:0] diag_data,core_status;wire [2:0] diag_bank;wire [63:0] diag_sequence;
    wire [5:0] diag_word,diag_words;wire [63:0] reports_consumed,aborts_consumed,records_consumed;
    wire signed [17:0] result_angle_q8;wire [8:0] result_angle_deg;wire [724:0] result_identity;
    wire [255:0] ila_sample;
    i17_continuous_top #(.WARMUP_SAMPLES(0),
        .HANN_FILE("../../../../docs/evidence/issue19-continuous-control-20261013/reference/hann-u18f17.mem")) dut(.*);
    integer cycle=0,pdm_edges=0,accepts=0,reports=0,aborts=0,fd,phase=0;
    integer accum[0:3],targets[0:3],shifted,p1,p2;
    reg [63:0] last_generation=0;bit generation_known=0;
    function automatic integer triangle(input integer x,input integer period);
        integer v;begin v=x%period;if(v<0)v+=period;triangle=v<period/2?v:period-v;end
    endfunction
    // 独立宽带测试声源：相同确定序列，0/3路延迟5个PCM周期，不force任何内部结果。
    function automatic integer broadband(input integer sample);
        reg [31:0] h;
        begin
            h=sample+32'h6d2b79f5;
            h=(h^(h>>16))*32'h7feb352d;
            h=(h^(h>>15))*32'h846ca68b;
            h=h^(h>>16);
            broadband=4096+(h[14:0]*3)/4;
        end
    endfunction
    // 实际PDM，不force PCM/FFT/B输出；二维合成移位声源仅作自然链路诊断。
    always @(negedge mic_clock[0])if(rst_n)begin
        for(integer k=0;k<4;k++)begin
            shifted=pdm_edges/64-((k==0||k==3)?5:0);
            p1=triangle(shifted,41);p2=triangle(shifted,67);
            targets[k]=broadband(shifted);accum[k]+=targets[k];
            if(accum[k]>=32768)begin mic_data[k]=1;accum[k]-=32768;end else mic_data[k]=0;
        end
        pdm_edges++;
    end
    task command(input [2:0] op);
        begin @(negedge clk);cmd_op=op;cmd_valid=1;@(posedge clk);#1;
            if(!cmd_done || cmd_error!=0)$fatal(1,"TOP_CHECK command op=%0d error=%0d",op,cmd_error);
            @(negedge clk);cmd_valid=0;
        end
    endtask
    always @(posedge clk)if(rst_n)begin
        cycle++;
        if($test$plusargs("FULL_PROBE") && cycle>=1000000 && cycle%1000==0)
            $display("PROBE cycle=%0d ff=%0d npbusy=%0d ffvalid=%0d doa=%0d halt=%0d fault=%0d",cycle,dut.ff_debug_state,dut.ff_np_busy,dut.ff_m_valid,dut.doa_busy,dut.u_core.source.forward_window.halt_reader,first_fault);
        if($test$plusargs("FULL_PROBE") && cycle==2000000)begin $display("PROBE_COMPLETE reports=%0d",reports);$finish;end
        if(cycle<20)$display("TOP_INITIAL cycle=%0d state=%0d manager=%0d fault=%0d",cycle,control_state,dut.diag_manager_state,first_fault);
        if(result_valid)begin
            reports++;
            $display("NOISE_REPORT cycle=%0d angle=%0d eligible=%0d b_error=%0d numeric=%0d",cycle,$signed(result_angle_q8),result_eligible,dut.doa_first_error_code,dut.doa_angle_numerical_valid);
            if(phase==1 && generation_known && result_identity[660:597]<=last_generation)$fatal(1,"TOP_CHECK repeated generation");
            last_generation=result_identity[660:597];generation_known=1;
            $fwrite(fd,"REPORT,%0d,%0d,%0d,%0d,%h\n",cycle,$signed(result_angle_q8),result_angle_deg,result_eligible,result_identity);
        end
        if(result_abort)begin aborts++;$fwrite(fd,"ABORT,%0d,%h\n",cycle,result_identity);end
        if(dut.servo_angle_valid)begin
            accepts++;
            if(stop_request || dut.fault_now || !result_eligible)$fatal(1,"TOP_CHECK unauthorized motion");
        end
        if(cycle%500000==0)$display("TOP_PROGRESS cycle=%0d state=%0d manager=%0d reports=%0d accepts=%0d fault=%0d",cycle,control_state,dut.diag_manager_state,reports,accepts,first_fault);
        if(cycle>24000000)$fatal(1,"TOP_HANG");
    end
    // 观察真实连接的组合振荡；同一时刻变化过多即报错，不把占用CPU当时钟推进。
    time change_time=0;integer changes=0;
    always @(dut.fault_now or dut.stop_now or dut.run_level or dut.source_fault or
        dut.ff_m_valid or dut.u_core.ff_m_ready or dut.doa_report_valid or
        dut.u_core.common_cancel or dut.diag_current_qualified)begin
        if($time!=change_time)begin change_time=$time;changes=0;end
        changes++;
        if(changes>10000)$fatal(1,"TOP_DELTA time=%0t cycle=%0d ff=%0d doa=%0d fault=%0d cancel=%0d",$time,cycle,dut.ff_debug_state,dut.doa_busy,dut.fault_now,dut.u_core.common_cancel);
    end
    initial begin
        fd=$fopen("events.csv","w");for(integer k=0;k<4;k++)accum[k]=0;
        map_pending[23:0]=24'd46080;map_pending[25:24]=1;
        map_pending[43:26]=-18'sd46080;map_pending[61:44]=18'sd46079;
        map_pending[70:62]=0;map_pending[79:71]=360;map_pending[80]=1;map_pending[81]=1;
        repeat(5)@(negedge clk);rst_n=1;repeat(4)@(negedge clk);
        command(1);wait(control_state==2);command(2);phase=1;
        if($test$plusargs("FULL_STALL"))begin
            diag_ready=0;wait(first_fault!=0);
            if(dut.u_consumer.records_consumed!=0 || !dut.diag_export_valid || dut.servo_enable)$fatal(1,"TOP_CHECK export stall failure");
            diag_ready=1;repeat(500)@(negedge clk);
            $display("CONTINUOUS_STALL_COMPLETE cycle=%0d fault=%0d retained_record=1",cycle,first_fault);$finish;
        end
        // 三个自然完整报告后真实STOP/重启；长期session期限另复用32拍/1000拍独立检查。
        wait(reports>=3);
        if(first_fault!=0 || control_state!=5 || reports<3 || accepts<2 || records_consumed<3)
            $fatal(1,"TOP_CHECK continuous fault=%0d state=%0d reports=%0d accepts=%0d records=%0d",first_fault,control_state,reports,accepts,records_consumed);
        // 在真实在途FFT/后端义务时STOP；保持STOP，排空后显式warm和新SID重启。
        wait(dut.ff_busy || dut.doa_ip_obligation);@(negedge clk);stop_request=1;phase=2;
        wait(control_state==7);repeat(40)@(negedge clk);
        if(dut.u_core.doa_busy || dut.u_core.ff_busy || dut.run_level || dut.servo_enable)$fatal(1,"TOP_CHECK stop drain");
        command(4);wait(control_state==0);context_pending[31:0]=4;stop_request=0;
        generation_known=0;command(1);wait(control_state==2);command(2);phase=3;
        wait(result_valid);@(posedge clk);#1;
        if(result_identity[463:432]!=4 || first_fault!=0)$fatal(1,"TOP_CHECK restart context");
        $display("CONTINUOUS_NOISE_STOP_COMPLETE cycles=%0d reports=%0d accepts=%0d aborts=%0d restart_sid=4",cycle,reports,accepts,aborts);$finish;
    end
endmodule
