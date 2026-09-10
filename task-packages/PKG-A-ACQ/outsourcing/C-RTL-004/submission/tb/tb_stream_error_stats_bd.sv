`timescale 1ns/1ps
module width_check #(parameter integer W=32)(input wire start, output reg done=0);
    reg clk=0, rst_n=0, clear=0, overflow_event=0, drop_event=0;
    wire [W-1:0] wo, wd, co, cd;
    wire ws_o, ws_d, cs_o, cs_d;
    longint unsigned mo=0, md=0;
    localparam logic [63:0] LIMIT = 64'hffffffffffffffff >> (64-W);
    bit so=0, sd=0;
    integer checks=0;
    always #5 clk=~clk; // Test-only clock, not a board frequency contract.
    generate if (W==32) begin : defaults
        stream_error_stats_bd dut(.clk(clk),.rst_n(rst_n),.clear(clear),
            .overflow_event(overflow_event),.drop_event(drop_event),
            .overflow_count(wo),.drop_count(wd),.overflow_sticky(ws_o),.drop_sticky(ws_d));
    end else begin : configured
        stream_error_stats_bd #(.COUNT_WIDTH(W)) dut(.clk(clk),.rst_n(rst_n),.clear(clear),
            .overflow_event(overflow_event),.drop_event(drop_event),
            .overflow_count(wo),.drop_count(wd),.overflow_sticky(ws_o),.drop_sticky(ws_d));
    end endgenerate
    stream_error_stats #(.COUNT_WIDTH(W)) baseline(.clk(clk),.rst_n(rst_n),.clear(clear),
        .overflow_event(overflow_event),.drop_event(drop_event),
        .overflow_count(co),.drop_count(cd),.overflow_sticky(cs_o),.drop_sticky(cs_d));
    task automatic verify(input string label);
        if ({wo,wd,ws_o,ws_d} !== {co,cd,cs_o,cs_d} ||
            {wo,wd,ws_o,ws_d} !== {mo[W-1:0],md[W-1:0],so,sd} ||
            {co,cd,cs_o,cs_d} !== {mo[W-1:0],md[W-1:0],so,sd}) begin
            $display("FAIL W=%0d case=%s input rst/clear/o/d=%b%b%b%b expected=%h/%h/%b%b wrapper=%h/%h/%b%b core=%h/%h/%b%b",
              W,label,rst_n,clear,overflow_event,drop_event,mo,md,so,sd,wo,wd,ws_o,ws_d,co,cd,cs_o,cs_d);
            $fatal(1,"Mismatch");
        end
        checks++;
    endtask
    task automatic step(input bit reset_value, input bit cl, input bit ov, input bit dr, input string label);
        @(negedge clk);
        rst_n=reset_value; clear=cl; overflow_event=ov; drop_event=dr;
        #1; verify({label," before-edge hold"});
        @(posedge clk);
        // Integer arithmetic oracle: define this cycle's starting history,
        // then add events with saturation. Reset overrides both operations.
        if (!reset_value) begin mo=0;md=0;so=0;sd=0; end
        else begin
            if (cl) begin mo=0;md=0;so=0;sd=0; end
            if (ov) begin if (mo<LIMIT) mo=mo+1; so=1; end
            if (dr) begin if (md<LIMIT) md=md+1; sd=1; end
        end
        #1; verify({label," after-edge"});
        $display("CASE PASS W=%0d %s counts=%h/%h sticky=%b%b",W,label,wo,wd,ws_o,ws_d);
    endtask
    initial begin
        wait(start);
        @(posedge clk); #1; verify("initial reset baseline");
        step(1,0,0,0,"idle");
        step(1,0,1,0,"overflow only");
        step(1,0,0,0,"overflow sticky hold");
        step(1,0,0,1,"drop only");
        step(1,0,1,1,"both events");
        repeat(3) step(1,0,1,1,"continuous events");
        step(1,0,0,0,"hold both");
        step(0,1,1,1,"synchronous reset overrides clear and both events");
        step(1,0,1,0,"resume after reset");
        step(1,1,0,0,"clear no event");
        step(1,1,1,0,"clear overflow");
        step(1,1,0,1,"clear drop");
        repeat(3) step(1,1,1,1,"continuous clear both keeps one");
        step(1,0,0,0,"sticky holds after clear event");
        if (W<=3) begin
            step(1,1,0,0,"saturation setup");
            repeat((1<<W)+2) step(1,0,1,0,"overflow saturation independent");
            repeat((1<<W)+2) step(1,0,0,1,"drop saturation independent");
            step(1,0,1,1,"both saturated no wrap");
            step(1,1,0,0,"clear saturated counters");
            step(1,0,1,1,"count after saturation clear");
        end
        step(0,0,0,0,"final reset");
        $display("WIDTH PASS W=%0d checks=%0d time=%0t",W,checks,$time);
        done=1;
    end
endmodule
module tb_stream_error_stats_bd;
    wire d3,d1,d32,d64;
    width_check #(.W(3)) w3(1'b1,d3);
    width_check #(.W(1)) w1(d3,d1);
    width_check w32(d1,d32);
    width_check #(.W(64)) w64(d32,d64);
    initial begin
        wait(d64);
        $display("ALL TESTS PASS: W=3,1,default32,64 core oracle + wrapper oracle + equivalence");
        $finish;
    end
    initial begin #100000; $fatal(1,"TIMEOUT"); end
endmodule
