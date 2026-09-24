`timescale 1ns/1ps
module tb_independent;
 wire [64:1] done;
 wire joint_done;
 for(genvar w=1;w<=64;w++) begin:g
  unit_check #(.W(w)) u(done[w]);
 end
 joint_check j(joint_done);
 initial begin wait((&done)&&joint_done); $display("REVIEW ALL PASS widths=1..64 and joint"); $finish; end
 initial begin #200000; $fatal(1,"REVIEW TIMEOUT"); end
endmodule

module unit_check #(parameter W=1)(output bit done=0);
 bit clk=0,rst_n=0,snapshot_req=0;
 bit [W-1:0] live_overflow_count=0,live_drop_count=0;
 bit live_overflow_sticky=0,live_drop_sticky=0;
 wire [W-1:0] snapshot_overflow_count,snapshot_drop_count;
 wire snapshot_overflow_sticky,snapshot_drop_sticky,snapshot_valid;
 stream_error_snapshot #(.COUNT_WIDTH(W)) dut(.*);
 always #5 clk=~clk;
 logic [2*W+2:0] expected='0;
 bit [63:0] rng=64'h7f2ac819008bed35;
 integer checks=0;
 task verify;
  checks++;
  if({snapshot_overflow_count,snapshot_drop_count,snapshot_overflow_sticky,snapshot_drop_sticky,snapshot_valid} !== expected)
    $fatal(1,"REVIEW FAIL W=%0d check=%0d expected=%h actual=%h",W,checks,expected,{snapshot_overflow_count,snapshot_drop_count,snapshot_overflow_sticky,snapshot_drop_sticky,snapshot_valid});
 endtask
 task edge_check;
  @(posedge clk);
  if(!rst_n) expected='0;
  else if(snapshot_req) expected={live_overflow_count,live_drop_count,live_overflow_sticky,live_drop_sticky,1'b1};
  else expected[0]=0;
  #1; verify();
 endtask
 task drive(input bit r,q,input bit[W-1:0] a,b,input bit os,ds);
  @(negedge clk);
  rst_n=r;snapshot_req=q;live_overflow_count=a;live_drop_count=b;live_overflow_sticky=os;live_drop_sticky=ds;
  #1;verify();edge_check();
 endtask
 initial begin
  edge_check();
  // Walking bits with four independent sticky combinations; capture then hold.
  for(int k=0;k<W;k++) for(int s=0;s<4;s++) begin
   drive(1,1,64'd1<<k,~(64'd1<<k),s[1],s[0]);
   drive(1,0,~(64'd1<<k),64'd1<<k,~s[1],~s[0]);
  end
  for(int c=0;c<16;c++) begin
   drive(1,1,'1,'1,1,1);
   drive(c[3],c[2],'0,'1,c[1],c[0]);
  end
  for(int k=0;k<1000;k++) begin
   rng=rng^(rng<<7);rng=rng^(rng>>9);rng=rng^(rng<<8);
   drive(k%29!=0,k%11<7,rng,~(rng>>1),rng[13],rng[31]);
  end
  drive(1,1,'1,'1,1,1);
  drive(1,0,0,0,0,0);
  // Sub-cycle reset and request pulses must not change any outputs.
  @(negedge clk); #1;rst_n=0;snapshot_req=1;#1;verify();
  rst_n=1;snapshot_req=0;#1;verify();edge_check();
  $display("REVIEW UNIT PASS W=%0d checks=%0d",W,checks);done=1;
 end
endmodule

module joint_check(output bit done=0);
 bit clk=0,rst_n=0,clear=0,overflow_event=0,drop_event=0,snapshot_req=0;
 wire [2:0] live_overflow_count,live_drop_count,snapshot_overflow_count,snapshot_drop_count;
 wire live_overflow_sticky,live_drop_sticky,snapshot_overflow_sticky,snapshot_drop_sticky,snapshot_valid;
 stream_error_stats #(.COUNT_WIDTH(3)) stats(.clk(clk),.rst_n(rst_n),.clear(clear),.overflow_event(overflow_event),.drop_event(drop_event),.overflow_count(live_overflow_count),.drop_count(live_drop_count),.overflow_sticky(live_overflow_sticky),.drop_sticky(live_drop_sticky));
 stream_error_snapshot #(.COUNT_WIDTH(3)) dut(.*);
 always #5 clk=~clk;
 integer a=0,b=0,checks=0;
 bit sa=0,sb=0;
 logic[8:0] expected=0;
 task cycle(input bit[4:0] c);
  @(negedge clk);{rst_n,clear,overflow_event,drop_event,snapshot_req}=c;
  @(posedge clk);
  if(!rst_n) begin a=0;b=0;sa=0;sb=0;expected=0;end
  else begin
   // Snapshot uses mathematical reference state BEFORE this edge's events.
   if(snapshot_req) expected={3'(a),3'(b),sa,sb,1'b1};else expected[0]=0;
   if(clear) begin a=0;b=0;sa=0;sb=0;end
   if(overflow_event)begin if(a<7)a++;sa=1;end
   if(drop_event)begin if(b<7)b++;sb=1;end
  end
  #1;checks++;
  if({snapshot_overflow_count,snapshot_drop_count,snapshot_overflow_sticky,snapshot_drop_sticky,snapshot_valid} !== expected || live_overflow_count !== 3'(a) || live_drop_count !== 3'(b) || live_overflow_sticky !== sa || live_drop_sticky !== sb)
    $fatal(1,"REVIEW JOINT FAIL controls=%b check=%0d expected=%h actual=%h",c,checks,expected,{snapshot_overflow_count,snapshot_drop_count,snapshot_overflow_sticky,snapshot_drop_sticky,snapshot_valid});
 endtask
 initial begin
  cycle(0);
  for(int first=0;first<32;first++)for(int second=0;second<32;second++) begin
   cycle(0);repeat(9)cycle(5'b10111); // genuinely reach saturation
   cycle(5'(first));cycle(5'(second));
  end
  $display("REVIEW JOINT PASS checks=%0d",checks);done=1;
 end
endmodule
