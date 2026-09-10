`timescale 1ns/1ps
module tb_review;
 wire [32:2] done;
 for(genvar w=2;w<=32;w++)begin:g
  review_width #(.W(w)) u(done[w]);
 end
 initial begin wait(&done);$display("REVIEW ALL PASS widths=2..32");$finish;end
 initial begin #100000;$fatal(1,"REVIEW TIMEOUT");end
endmodule
module review_width #(parameter W=24)(output bit done=0);
 bit [W-1:0] x[4];
 wire [127:0] y;
 pcm4_signext_pack #(.SAMPLE_WIDTH(W)) dut(x[0],x[1],x[2],x[3],y);
 bit [31:0] rng=32'hdf931a27;
 integer checks=0;
 task check;
  longint signed n;
  logic [127:0] expected;
  #1;
  for(int c=0;c<4;c++)begin
   n=x[c];
   if(n>=(64'd1<<(W-1)))n=n-(64'd1<<W);
   expected[c*32+:32]=n[31:0];
  end
  checks++;
  if(y!==expected)$fatal(1,"REVIEW FAIL W=%0d check=%0d inputs=%h/%h/%h/%h expected=%h actual=%h",W,checks,x[0],x[1],x[2],x[3],expected,y);
 endtask
 initial begin
  for(int c=0;c<4;c++)x[c]=c;
  check();
  for(int c=0;c<4;c++)for(int b=0;b<W;b++)begin
   x[c]=32'd1<<b;check();x[c]=~(32'd1<<b);check();
  end
  for(int mask=0;mask<16;mask++)begin
   for(int c=0;c<4;c++)begin x[c]=c;x[c][W-1]=mask[c];end
   check();
  end
  if(W<=3)for(int k=0;k<(1<<(4*W));k++)begin
   for(int c=0;c<4;c++)x[c]=k>>(c*W);
   check();
  end
  repeat(512)begin
   for(int c=0;c<4;c++)begin
    rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);x[c]=rng;
   end
   check();
  end
  $display("REVIEW PASS W=%0d comparisons=%0d",W,checks);done=1;
 end
endmodule
