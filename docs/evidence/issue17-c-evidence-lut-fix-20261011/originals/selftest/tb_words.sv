`timescale 1ns/1ps
module tb_words;
 reg clk=0,rst_n=0;
 i17_vio_evidence dut(.clk(clk),.rst_n(rst_n));
 i17_vio_evidence_before old(.clk(clk),.rst_n(rst_n));
 reg oracle[0:9][0:6655]; integer widths[0:9];
 integer pattern,k,i,b,xbit,checks=0;reg [3:0] kind;reg[7:0] index;
 reg [31:0] want,got,prior;
 task compare(input[3:0] kt,input[7:0] ix,input[31:0] expected_word);
  begin
   got=dut.word_for(kt,ix);prior=old.word_for(kt,ix);checks++;
   if(got !== expected_word)$fatal(1,"WORD_ORACLE_CHECK pattern=%0d kind=%b index=%b want=%h got=%h",pattern,kt,ix,expected_word,got);
   if(got !== prior)$fatal(1,"WORD_DIFFERENTIAL_CHECK kind=%b index=%b old=%h got=%h",kt,ix,prior,got);
  end
 endtask
 initial begin
  widths[0]=256;widths[1]=512;widths[2]=725;widths[3]=6626;widths[4]=180;
  widths[5]=2048;widths[6]=725;widths[7]=725;widths[8]=192;widths[9]=128;
  for(pattern=0;pattern<4;pattern=pattern+1)begin
   for(k=0;k<10;k=k+1)for(b=0;b<6656;b=b+1)begin
    oracle[k][b]=0;
    if(b<widths[k])begin
     case(pattern)
      0:oracle[k][b]=0;
      1:oracle[k][b]=1;
      2:oracle[k][b]=((b*17+k*13)%31)<15;
      3:begin
       oracle[k][b]=((b*17+k*13)%31)<15;
       if(b%67==3)oracle[k][b]=1'bx;
       if(b%71==5)oracle[k][b]=1'bz;
      end
     endcase
    end
   end
   for(b=0;b<160;b=b+1)begin dut.report_context[b]=oracle[0][b+0];old.report_context[b]=oracle[0][b+0];end
   for(b=0;b<96;b=b+1)begin dut.report_map[b]=oracle[0][b+160];old.report_map[b]=oracle[0][b+160];end
   for(b=0;b<512;b=b+1)begin dut.report_header[b]=oracle[1][b+0];old.report_header[b]=oracle[1][b+0];end
   for(b=0;b<725;b=b+1)begin dut.report_identity[b]=oracle[2][b+0];old.report_identity[b]=oracle[2][b+0];end
   for(b=0;b<6626;b=b+1)begin dut.report_terminal[b]=oracle[3][b+0];old.report_terminal[b]=oracle[3][b+0];end
   for(b=0;b<180;b=b+1)begin dut.report_abort_payload[b]=oracle[4][b+0];old.report_abort_payload[b]=oracle[4][b+0];end
   for(b=0;b<725;b=b+1)begin dut.report_abort_identity[b]=oracle[6][b+0];old.report_abort_identity[b]=oracle[6][b+0];end
   for(b=0;b<725;b=b+1)begin dut.backend_identity[b]=oracle[7][b+0];old.backend_identity[b]=oracle[7][b+0];end
   for(b=0;b<192;b=b+1)begin dut.backend_header[b]=oracle[8][b+0];old.backend_header[b]=oracle[8][b+0];end
   for(b=0;b<128;b=b+1)begin dut.live_snapshot[b]=oracle[9][b+0];old.live_snapshot[b]=oracle[9][b+0];end

   for(i=0;i<64;i=i+1)for(b=0;b<32;b=b+1)begin dut.diag_mem[i][b]=oracle[5][i*32+b];old.diag_mem[i][b]=oracle[5][i*32+b];end
   // Captured length deliberately differs from accessible raw memory extent.
   dut.captured_words=1;old.captured_words=1;
   for(k=0;k<16;k=k+1)for(i=0;i<256;i=i+1)begin
    want=0;
    if(k<10 && i<208)for(b=0;b<32;b=b+1)want[b]=oracle[k][i*32+b];
    compare(k,i,want);
   end
   for(k=0;k<16;k=k+1)for(i=0;i<256;i=i+1)for(xbit=0;xbit<8;xbit=xbit+1)begin
    index=i;index[xbit]=1'bx;compare(k,index,0);
    index=i;index[xbit]=1'bz;compare(k,index,0);
   end
   for(k=0;k<16;k=k+1)for(i=0;i<256;i=i+1)for(xbit=0;xbit<4;xbit=xbit+1)begin
    kind=k;kind[xbit]=1'bx;compare(kind,i,0);
    kind=k;kind[xbit]=1'bz;compare(kind,i,0);
   end
  end
  $display("WORD_ORACLE_COMPLETE checks=%0d patterns=4 kind_domain=16 index_domain=256 pending=0",checks);$finish;
 end
endmodule
