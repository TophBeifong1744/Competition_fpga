`timescale 1ns/1ps
module tb_frontend;
    reg clk=0;always #5 clk=~clk;
    reg rst=0,run=0;reg [3:0] pdm=0;
    wire c1,c2,c3,c4,valid,last;wire [31:0] data,status;wire[3:0]keep;
    four_mic_top #(.WARMUP_SAMPLES(4),.SAMPLES_PER_PACKET(4),.FIFO_LOG2(4)) dut(
        clk,rst,run,pdm,c1,c2,c3,c4,status,data,keep,valid,1'b1,last);
    reg[31:0]rng=32'h91234987;integer cycles=0,groups=0,words=0,errors=0;
    reg[255:0]expected[0:1023];integer accepted=0,received=0;
    reg[63:0]last_id;bit have_id=0;
    always @(negedge clk)begin
        rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
        // Distinct per-lane inputs, update away from the capture clock edge.
        pdm={rng[4],rng[2]^rng[3],rng[9],rng[0]};
    end
    always @(posedge clk)begin
        cycles++;
        if(c1!==c2||c1!==c3||c1!==c4)$fatal(1,"physical clocks differ");
        if(!rst)begin
            have_id=0;
        end else begin
            if(c1 !== (dut.phase>=10))$fatal(1,"common divider phase");
            if(dut.pv!=0 && dut.pv!=15)$fatal(1,"CIC valid alignment");
            if(&dut.pv)begin
                if(have_id && dut.id!=last_id+1)$fatal(1,"frontend ID stopped/restarted unexpectedly");
                last_id=dut.id;have_id=1;groups++;
            end
            if(dut.capture.push)begin
                expected[accepted][63:0]=dut.id;
                for(integer c=0;c<4;c++)expected[accepted][64+c*32+:32]={{8{dut.pcm[c*24+23]}},dut.pcm[c*24+:24]};
                expected[accepted][223:192]={28'b0,dut.clip};expected[accepted][255:224]=0;accepted++;
            end
            if(valid)begin
                if(data!==expected[received][words*32+:32])$fatal(1,"top channel mapping/packing");
                if(words==7)begin words=0;received++;end else words++;
            end
        end
    end
    task tick(input integer n);repeat(n)@(negedge clk);endtask
    initial begin
        tick(5);rst=1;wait(status[1]);@(negedge clk);run=1;
        tick(45000);run=0;wait(status[3]);tick(9000);
        run=1;tick(23000);run=0;wait(status[3]);tick(4);
        if(accepted!=received || received==0 || received%4)$fatal(1,"top drain");
        rst=0;tick(4);if({c1,c2,c3,c4}!=0)$fatal(1,"reset clocks");
        $display("FRONTEND_REGRESSION_PASS groups=%0d captured=%0d cycles=%0d",groups,received,cycles);$finish;
    end
    initial begin #2000000;$fatal(1,"frontend timeout");end
endmodule
