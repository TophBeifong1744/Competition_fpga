`timescale 1ns/1ps
module tb_continuous #(parameter P=4, LG=4);
    reg clk=0;always #5 clk=~clk;
    reg rst=0,run=0,ready=1;
    reg [3:0] pv=0,clip=0;
    reg [95:0] pcm=0;
    reg [63:0] id=0;
    wire [31:0] data,status;wire [3:0] keep;wire valid,last;
    reg take=0;
    pcm4_continuous_axis #(.SAMPLES_PER_PACKET(P),.FIFO_LOG2(LG)) dut
        (clk,rst,run,ready,pv,pcm,clip,id,data,keep,valid,last,take,status);
    integer errors=0,checks=0,accepted=0,received=0,words=0,cycles=0,packets=0;
    integer exp_in=0,exp_out=0,random_mode=0,period=24;
    bit checking=1,producer=0;
    reg [255:0] expected[0:99999];
    reg [31:0] old_data;reg old_last,stalled=0;
    reg prev_run=0;reg[63:0] prev_id;bit seen_id=0;
    reg [31:0] rng=32'h537acdef;
    task ck(input bit ok,input string msg);
        checks++;if(!ok)begin $display("FAIL cycle=%0d %s",cycles,msg);errors++;if(errors>10)$fatal;end
    endtask
    always @(negedge clk) begin
        if(producer) begin
            pv=(cycles%period==0)?15:0;
            if(pv)begin
                id=id+1;
                pcm[23:0]=id[23:0];pcm[47:24]=-id[23:0];
                pcm[71:48]=24'h800000+id[23:0];pcm[95:72]=0;
                clip=id[3:0]==0 ? 4'b0100 : 0;
            end
        end
        if(random_mode)begin rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};take=(rng[3:0]>3);end
    end
    always @(posedge clk) begin
        cycles++;
        if(!rst)begin stalled=0;seen_id=0;prev_run=0;end else begin
            if(run&&!prev_run)seen_id=0;
            prev_run=run;
            ck(status[31:24]==8'hc1,"ABI signature");
            if(stalled)ck(valid && data===old_data && last===old_last,"AXIS stable under backpressure");
            stalled=valid&&!take;old_data=data;old_last=last;
            if(checking && dut.push)begin
                if(seen_id)ck(id==prev_id+1,"no omitted input group within a segment");
                prev_id=id;seen_id=1;
                expected[accepted][63:0]=id;
                for(integer c=0;c<4;c++)expected[accepted][64+c*32+:32]={{8{pcm[c*24+23]}},pcm[c*24+:24]};
                expected[accepted][223:192]={28'b0,clip};expected[accepted][255:224]=0;
                accepted++;exp_in=(exp_in+1)%P;
            end
            if(valid&&take&&checking)begin
                ck(received<accepted,"no phantom group");
                ck(data===expected[received][words*32+:32],"exact word/channel/raw ID");
                ck(keep==15,"all four byte lanes valid");
                ck(last==((words==7)&&(exp_out==P-1)),"TLAST exactly at packet boundary");
                if(words==7)begin words=0;received++;exp_out=(exp_out+1)%P;if(last)packets++;end
                else words++;
            end
        end
    end
    task tick(input integer n);repeat(n)@(negedge clk);endtask
    task reset;
        run=0;producer=0;pv=0;take=0;random_mode=0;rst=0;tick(4);
        accepted=0;received=0;words=0;exp_in=0;exp_out=0;checking=1;rst=1;tick(2);
    endtask
    task drain;
        integer t=0;
        while((!status[3] || status[7])&&t<P*100)begin tick(1);t++;end
        ck(t<P*100,"bounded full packet drain");ck(accepted==received,"no silent drop");
        ck(accepted%P==0 && words==0,"stop only full packet and group");
        ck(!status[2]&&!status[5],"clean stop has no fatal error");
    endtask
    initial begin
        reset();producer=1;random_mode=1;
        // Repeated same-PL restarts at every ingress packet position.
        for(integer phase=0;phase<4;phase++)begin
            run=1;tick(1);
            while(accepted<P*4*(phase+1) || exp_in!=phase)tick(1);
            run=0;drain();tick(55);
        end
        ck(status[4],"clip-ever persists across restarts");
        $display("CASE clean stop/restart random-backpressure PASS groups=%0d packets=%0d",received,packets);
        // Stop before first group: zero-packet stop, no forced fake TLAST.
        producer=0;pv=0;run=1;tick(2);run=0;drain();
        $display("CASE zero-group stop PASS");
        // Long stall: stop remains pending until a complete packet can drain.
        reset();producer=1;run=1;period=24;take=0;
        while(accepted<2*P-1)tick(1);
        run=0;tick(60);ck(!status[0] && !status[3],"capture stopped while FIFO waits for drain");
        run=1;tick(2); // a premature new edge while draining must NOT auto-restart
        take=1;drain();tick(period*2);
        ck(!status[0] && status[3],"held high after drain does not auto-restart");
        $display("CASE boundary stop with held final packet and premature restart PASS");
        // Saturating error, refused restart, explicit reset only recovery.
        reset();producer=1;run=1;period=2;take=0;
        tick((1<<LG)*2+30);ck(status[2] && status[23:8]==1 && !status[3],"overflow is sticky, rejected event counted");
        producer=0;pv=0;checking=0;take=1;run=0;tick((1<<LG)*9);run=1;tick(10);
        ck(status[2]&&!status[0],"overflow cannot restart without reset");
        force dut.rejected=16'hffff;tick(1);release dut.rejected;
        ck(status[23:8]==16'hffff,"saturated diagnostic state retained");
        $display("CASE overflow + refused restart PASS (expected injected fault)");
        reset();pv=4'b0011;tick(1);pv=0;run=1;tick(4);
        ck(status[5]&&!status[0]&&!status[3],"mismatch even in idle is fatal");
        $display("CASE channel valid mismatch PASS (expected injected fault)");
        reset();period=24;producer=1;run=1;take=1;tick(200);
        rst=0;tick(2);ck(!valid,"explicit reset abort flushes FIFO");
        if(errors==0)$display("RTL_CONTINUOUS_PASS packet=%0d fifo=%0d checks=%0d; protocol-only, not board/timing",P,1<<LG,checks);
        else $fatal(1,"errors=%0d",errors);
        $finish;
    end
    initial begin #5000000;$fatal(1,"watchdog");end
endmodule
module tb_production;
    tb_continuous #(.P(250),.LG(10)) bench();
endmodule
