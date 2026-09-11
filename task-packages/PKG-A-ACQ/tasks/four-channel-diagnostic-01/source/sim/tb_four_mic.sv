`timescale 1ns/1ps
module tb_four_mic;
    reg clk=0; always #8.138020833 clk=~clk;
    reg rst=0,start=0,ready=0;
    reg [3:0] pv=0,clip=0;
    reg [95:0] pcm=0;
    reg [63:0] id=0;
    wire [31:0] data,status; wire [3:0] keep; wire valid,last;
    pcm4_capture_axis #(.TOTAL_SAMPLES(19),.SAMPLES_PER_PACKET(4),.FIFO_LOG2(3)) cap(
        clk,rst,start,1'b1,pv,pcm,clip,id,data,keep,valid,last,ready,status);
    integer got=0,mode=0,run_no=0,cycles=0,fd;
    reg stalled=0; reg [31:0] held; reg heldlast;
    reg [63:0] base_id=64'hffffffF8;
    function automatic signed [23:0] value(input integer row,ch);
        case((row+ch)%4)
            0:value=-8388608; 1:value=8388607; 2:value=0; 3:value=-513-row*4-ch;
        endcase
    endfunction
    function automatic [31:0] expected(input integer idx);
        integer row,word; reg [63:0] eid; reg signed [23:0] v;
        begin
            row=idx/8;word=idx%8;eid=base_id+row;
            if(word==0) expected=eid[31:0];
            else if(word==1) expected=eid[63:32];
            else if(word<6) begin v=value(row,word-2);expected={{8{v[23]}},v};end
            else if(word==6) expected=1<<(row%4);
            else expected=0;
        end
    endfunction
    always @(posedge clk) begin
        if(!rst) begin got=0;stalled=0;end
        else begin
            if(stalled && (!valid || data!==held || last!==heldlast)) $fatal(1,"STALL");
            if(valid && ready && mode==0) begin
                if(data!==expected(got)) $fatal(1,"WORD %0d got %h expected %h",got,data,expected(got));
                if(last!==((got%32==31)||(got==151))) $fatal(1,"TLAST %0d",got);
                if(keep!==15) $fatal(1,"KEEP");
                $fdisplay(fd,"%0d,%0d,%08x,%0d",run_no,got,data,last);
                got=got+1;
            end
            stalled=valid&&!ready;held=data;heldlast=last;
        end
    end
    task automatic reset_cap;
        begin
            @(negedge clk);rst=0;pv=0;start=0;ready=0;
            repeat(3) @(negedge clk);rst=1;
        end
    endtask
    task automatic begin_cap;
        begin @(negedge clk);start=1;@(negedge clk);start=0;end
    endtask
    task automatic send(input integer row,mask=15);
        begin
            @(negedge clk);id=base_id+row;pv=mask;clip=1<<(row%4);
            for(integer ch=0;ch<4;ch=ch+1) pcm[ch*24+:24]=value(row,ch);
            @(negedge clk);pv=0;
        end
    endtask
    task automatic normal_run;
        begin
            begin_cap();
            fork
                begin
                    for(integer r=0;r<19;r=r+1) begin
                        send(r);repeat(18) @(negedge clk);
                        // busy-start must not reset counters or packet phase
                        if(r==3) begin @(negedge clk);start=1;@(negedge clk);start=0;end
                    end
                end
                begin
                    for(integer c=0;c<600;c=c+1) begin @(negedge clk);ready=(c%5!=0);end
                    ready=1;
                end
            join
            repeat(3) @(negedge clk);
            if(got!=152 || !status[3] || status[2] || status[5] || status[0]) $fatal(1,"NORMAL %0d %h",got,status);
            $display("PACKET_PASS run=%0d groups=19 words=152 channels/sign/IDcarry/stall/partialTLAST",run_no);
        end
    endtask
    reg trst=0,tstart=0;reg [3:0] tdata=0;
    wire tclk,tv,tl;wire [3:0] tclks;wire [31:0] td,ts;wire [3:0] tk;
    assign tclk=tclks[0];
    integer bits=0,tw=0;reg [63:0] tid,first_tid;
    reg top_done=0;
    four_mic_top #(.WARMUP_SAMPLES(8),.TOTAL_SAMPLES(12),.SAMPLES_PER_PACKET(5)) topdut(
        .aclk(clk),.aresetn(trst),.start(tstart),.pdm_data(tdata),
        .pdm_clk1(tclks[0]),.pdm_clk2(tclks[1]),.pdm_clk3(tclks[2]),.pdm_clk4(tclks[3]),
        .status(ts),.m_axis_tdata(td),.m_axis_tkeep(tk),.m_axis_tvalid(tv),
        .m_axis_tready(1'b1),.m_axis_tlast(tl));
    integer phase_check=0,clock_checks=0;
    // Check exact divide-by-20 phase, all four pads and synchronous reset.
    // Sample after the DUT NBA updates (the master period is ~16.276 ns).
    always @(posedge clk) begin
        if(!trst) phase_check=0;
        else phase_check=(phase_check+1)%20;
        #1;
        if(tclks !== {4{(phase_check>=10)}}) $fatal(1,"C_ADAPTER_CLOCK phase=%0d clocks=%b",phase_check,tclks);
        clock_checks=clock_checks+1;
    end
    always @(negedge tclk) if(trst) begin
        #100;tdata[0]=1;tdata[1]=0;tdata[2]=bits%2;tdata[3]=(bits%4!=0);bits=bits+1;
    end
    always @(posedge tclk) if(trst) tdata=4'bxxxx;
    always @(posedge clk) if(trst && tv) begin
        case(tw%8)
            0:tid[31:0]=td;
            1:begin
                tid[63:32]=td;
                if(tw==1) begin first_tid=tid;if(tid<8)$fatal(1,"WARMUP");end
                else if(tid!=first_tid+tw/8) $fatal(1,"TOPID");
            end
            2:if(td!==32'h007fffff)$fatal(1,"MIC0");
            3:if(td!==32'hff800000)$fatal(1,"MIC1");
            4:if(td!==0)$fatal(1,"MIC2 %h",td);
            5:if(td!==32'h00400000)$fatal(1,"MIC3 %h",td);
            6:if(td!==1)$fatal(1,"TOPFLAGS");
            7:if(td!==0)$fatal(1,"RESERVED");
        endcase
        if(tl!==((tw==39)||(tw==79)||(tw==95)))$fatal(1,"TOPTAIL");
        tw=tw+1;
    end
    initial begin
        repeat(5) @(negedge clk);trst=1;
        wait(ts[1]);@(negedge clk);tstart=1;@(negedge clk);tstart=0;
        wait(ts[3]);@(negedge clk);
        if(tw!=96||ts[5])$fatal(1,"TOPCOUNT");
        $display("TOP_PASS DATA1..4 to mic0..3, four distinct densities delay100ns highphaseX shared IDs/warmup");
        // Reset again while the common output is HIGH, then require a clean epoch.
        wait(tclk);@(negedge clk);trst=0;
        repeat(3) @(negedge clk);
        if(tclks!==0 || topdut.phase!==0 || topdut.id!==0 || topdut.warmup!==0) $fatal(1,"C_ADAPTER_RESET");
        trst=1;repeat(41) @(negedge clk);
        $display("C_ADAPTER_CLOCK_RESET_PASS checks=%0d one divider/four outputs",clock_checks);top_done=1;
    end
    initial begin
        fd=$fopen("accepted_words.csv","w");if(!fd)$fatal(1,"file");
        $fdisplay(fd,"run,word,data_hex,last");
        reset_cap();normal_run();
        // Same frontend epoch, second capture without reset must restart packet counters.
        run_no=1;base_id=64'h200000000;got=0;normal_run();
        mode=1;reset_cap();begin_cap();
        for(integer r=0;r<9;r=r+1)send(r);
        if(!status[2]||status[0]||status[31:16]!=1||status[3])$fatal(1,"OVERFLOW");
        ready=1;repeat(80)@(negedge clk);begin_cap();
        if(status[0]||status[3])$fatal(1,"OVERFLOW RESTART");
        $display("OVERFLOW_PASS abort sticky and reset-required");
        reset_cap();begin_cap();send(0);send(1,7);
        if(!status[5]||status[0]||status[3])$fatal(1,"SYNC");
        ready=1;repeat(20)@(negedge clk);begin_cap();
        if(status[0])$fatal(1,"SYNC RESTART");
        $display("SYNC_PASS partial valid abort/reset-required");
        reset_cap();begin_cap();send(0);ready=1;repeat(3)@(negedge clk);
        reset_cap(); // reset in middle of record
        if(valid||status[3]||status[5]||status[2])$fatal(1,"RESET residue");
        mode=0;run_no=2;base_id=0;normal_run();
        $display("RESET_PASS mid-record discard and clean restart");
        wait(top_done);$fclose(fd);$display("ALL_FOUR_TESTS_PASS");$finish;
    end
    initial begin #2000000;$fatal(1,"TIMEOUT");end
endmodule
