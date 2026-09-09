`timescale 1ns/1ps
// 接收端参考模型以“成功接收拍数”推导编号/通道，不读DUT内部状态。
// ready为接收端驱动，模拟DMA背压；本TB不实例化真实DMA IP。
module source_case #(
    parameter integer S=2, P=2, ID=0
)(output logic finished=0);
    localparam integer TOTAL=3*S*P;
    logic clk=0, rstn=0, start=0, ready=0;
    always #5 clk=~clk;
    wire [31:0] data;
    wire [3:0] keep;
    wire valid,last,busy,done;
    test_source #(.SAMPLES_PER_PACKET(S),.PACKET_COUNT(P)) dut (
        .aclk(clk),.aresetn(rstn),.start(start),
        .m_axis_tdata(data),.m_axis_tkeep(keep),
        .m_axis_tvalid(valid),.m_axis_tready(ready),.m_axis_tlast(last),
        .busy(busy),.done(done)
    );
    bit active=0;
    integer accepted=0, cycles=0, completions=0, aborted=0, tails=0;
    integer pos_count[0:3], neg_count[0:3], zero_count[0:3];
    integer stalls=0, tail_stalls=0, busy_starts=0;
    integer c, phase_run;
    logic [31:0] rng=32'hA51938B7;
    integer capture;
    string capture_name;

    // 独立算术模型：有符号整数计算后才转成16位，不调用DUT函数。
    function automatic integer expected_channel(input integer sid, channel);
        integer phase, magnitude;
        begin
            phase=(sid+channel)%4;
            magnitude=1+256*channel+((sid%65536)/4);
            case(phase)
                0: expected_channel=0;
                1: expected_channel=magnitude;
                2: expected_channel=-magnitude;
                3: expected_channel=-32768+channel;
            endcase
        end
    endfunction

    function automatic logic [31:0] expected_word(input integer index);
        integer sid;
        logic [15:0] low_word, high_word;
        begin
            sid=index/3;
            if (index%3==0) expected_word=sid;
            else begin
                low_word=expected_channel(sid,(index%3-1)*2);
                high_word=expected_channel(sid,(index%3-1)*2+1);
                expected_word={high_word,low_word};
            end
        end
    endfunction

    task automatic step(input bit r, s, reset_n);
        bit exp_done;
        integer channel, actual_value;
        begin
            @(negedge clk);
            ready=r; start=s; rstn=reset_n;
            // 此处提供半个周期给组合数据稳定；上升沿前的值才是收到的值。
            @(posedge clk);
            exp_done=0;
            if (!reset_n) begin
                if(active) aborted++;
                active=0; accepted=0; tails=0;
            end else begin
                if(valid !== active || busy !== active)
                    $fatal(1,"CASE%0d valid/busy mismatch beat=%0d",ID,accepted);
                if(keep !== 4'hf) $fatal(1,"CASE%0d TKEEP mismatch",ID);
                if(active) begin
                    if(s) busy_starts++;
                    // 无ready时也逐拍检查，证明所有阻塞周期的保持行为。
                    if(data !== expected_word(accepted))
                        $fatal(1,"CASE%0d data beat=%0d actual=%h expected=%h",
                               ID,accepted,data,expected_word(accepted));
                    if(last !== (accepted%(3*S)==3*S-1))
                        $fatal(1,"CASE%0d TLAST beat=%0d",ID,accepted);
                    if(!r) begin stalls++; if(last) tail_stalls++; end
                    if(r) begin
                        if(last) tails++;
                        if(capture && completions==0)
                            $fdisplay(capture,"%0d,%0d,%08x,%01x,%0d",
                                      accepted,accepted/3,data,keep,last);
                        if(accepted%3!=0) begin
                            for(integer lane=0;lane<2;lane++) begin
                                channel=(accepted%3-1)*2+lane;
                                actual_value=$signed(data[lane*16 +:16]);
                                if(actual_value>0) pos_count[channel]++;
                                else if(actual_value<0) neg_count[channel]++;
                                else zero_count[channel]++;
                            end
                        end
                        accepted++;
                        if(accepted==TOTAL) begin
                            if(tails!=P) $fatal(1,"CASE%0d packet count",ID);
                            active=0; exp_done=1; completions++;
                        end
                    end
                end else begin
                    if(last!==0 || data!==0) $fatal(1,"CASE%0d idle outputs",ID);
                    if(s) begin active=1; accepted=0; tails=0; end
                end
            end
            #1;
            if(done!==exp_done || busy!==active || valid!==active)
                $fatal(1,"CASE%0d premature/missing done or bad state",ID);
            cycles++;
            if(cycles>3000000) $fatal(1,"CASE%0d timeout",ID);
        end
    endtask

    initial begin
        for(c=0;c<4;c++) begin pos_count[c]=0;neg_count[c]=0;zero_count[c]=0;end
        capture=0;
        // 仅默认用例输出实际接收拍CSV，便于人工核对打包。
        if(ID==0) begin
            capture=$fopen("accepted_beats.csv","w");
            if(!capture) $fatal(1,"Cannot open capture file");
            $fdisplay(capture,"beat_index,sample_id,tdata_hex,tkeep_hex,tlast");
        end
        step(0,0,0); repeat(2) step(1,0,1);
        // 第一轮：无ready启动，持续ready、最终包尾长阻塞、忙碌start。
        step(0,1,1); repeat(7) step(0,0,1);
        while(accepted<TOTAL-1) step(1,1,1);
        repeat(8) step(0,1,1);
        step(1,1,1); repeat(3) step(1,0,1);
        // 第一轮单独检查符号覆盖，不能用多次启动累计掩盖漏测。
        if(S*P>=4) begin
            for(c=0;c<4;c++) begin
                if(pos_count[c]==0 || neg_count[c]==0 || zero_count[c]==0)
                    $fatal(1,"CASE%0d first-run CH%0d sign coverage missing",ID,c);
            end
            $display("FIRST_RUN_SIGN_COVERAGE_PASS CASE%0d",ID);
        end
        // 第二轮：可复现随机背压。长例越过sample_id低16位回绕。
        step(1,1,1);
        while(active) begin
            rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            step(rng[0]|rng[3],0,1);
        end
        repeat(2) step(1,0,1);
        // 三种拍位置被阻塞时分别复位；复位打断不冒充正常完成。
        for(phase_run=0;phase_run<3;phase_run++) begin
            step(0,1,1);
            repeat(phase_run) step(1,0,1);
            step(0,0,1); step(0,0,0); step(0,0,1);
        end
        // 第三轮：每一拍（包括每个包尾）强制背压，再接收。
        step(0,1,1);
        while(active) begin step(0,0,1); step(1,0,1); end
        repeat(3) step(1,0,1);

        if(completions!=3 || aborted!=3 || stalls==0 || tail_stalls==0 || busy_starts==0)
            $fatal(1,"CASE%0d control coverage missing",ID);
        for(c=0;c<4;c++) begin
            $display("COVER CASE%0d CH%0d positive=%0d negative=%0d zero=%0d",
                     ID,c,pos_count[c],neg_count[c],zero_count[c]);
            // 1组边界例不要求覆盖全部符号；>=4组的用例逐通道强制覆盖。
            if(S*P>=4 && (pos_count[c]==0 || neg_count[c]==0 || zero_count[c]==0))
                $fatal(1,"CASE%0d channel%0d sign coverage missing",ID,c);
        end
        $display("PASS CASE%0d S=%0d P=%0d full_runs=%0d aborts=%0d stalls=%0d tail_stalls=%0d",
                 ID,S,P,completions,aborted,stalls,tail_stalls);
        if(capture) $fclose(capture);
        finished=1;
    end
endmodule

module tb_test_source;
    wire f0,f1,f2,f3;
    source_case #(.S(2),.P(2),.ID(0)) c0(f0);
    source_case #(.S(1),.P(1),.ID(1)) c1(f1);
    source_case #(.S(3),.P(3),.ID(2)) c2(f2);
    source_case #(.S(257),.P(257),.ID(3)) c3(f3);
    initial begin
        wait(f0&&f1&&f2&&f3);
        $display("ALL TASK1 TESTS PASS");
        $finish;
    end
    initial begin #100000000; $fatal(1,"Global watchdog timeout"); end
endmodule
