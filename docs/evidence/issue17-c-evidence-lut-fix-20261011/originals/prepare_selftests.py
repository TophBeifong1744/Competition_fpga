"""Sequential author self-test assets after product freeze; never writes product files.
Run: python prepare_selftests.py
Outputs: selftest/*.sv. Next: python run_selftests.py
"""
from pathlib import Path
import hashlib, json, re
ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT/'product-freeze.json').read_text())
product = Path(freeze['product_path'])
assert hashlib.sha256(product.read_bytes()).hexdigest() == freeze['product_sha256']
out = ROOT/'selftest'; out.mkdir(exist_ok=True)
old = (ROOT/'inputs/i17_vio_evidence_before.sv').read_text(encoding='utf8')
(out/'i17_vio_evidence_before.sv').write_text(old.replace('module i17_vio_evidence (', 'module i17_vio_evidence_before (', 1),encoding='utf8')
header = old[:old.index(');')]
outputs=[]
for line in header.splitlines():
    m=re.match(r'\s*output (?:wire|reg)\s+(\[[^]]+\])?\s*(.*?)[,]?$',line)
    if m:
        for name in m[2].rstrip(',').split(','):
            outputs.append((m[1] or '',name.strip()))
assert len(outputs)==19, outputs
tb=(ROOT/'inputs/tb_evidence.sv').read_text(encoding='utf8')
miter='\n'.join(' wire %s old_%s;'%(width,name) for width,name in outputs)
miter+='\n i17_vio_evidence_before old('+','.join('.%s(old_%s)'%(name,name) for _,name in outputs)+',.*);\n'
miter+=' integer miter_checks=0;\n always @(negedge clk) if(rst_n) begin\n miter_checks++;\n'
miter+=' if({'+','.join(name for _,name in outputs)+'} !== {'+','.join('old_'+name for _,name in outputs)+'}) $fatal(1,"MITER_CHECK output mismatch at cycle=%0d",cycle);\n end\n'
tb=tb.replace(' i17_vio_evidence dut(.*);',' i17_vio_evidence dut(.*);\n'+miter)
extra=r'''
 // 中文用途：公开READ按输入保存值逐位检查，覆盖全8位索引及未初始化/旧诊断字。
 reg [31:0] diag_oracle [0:63];
 integer read_checks=0;
 task all_reads(input integer first_kind,input integer last_kind);
  integer rk,wi,bi,count; reg legal_record; reg [31:0] want;
  reg [127:0] want_meta,live_before; reg [7:0] prior_error;
  reg [31:0] hold_data; reg [127:0] hold_meta;
  begin
   for(rk=first_kind;rk<=last_kind;rk=rk+1) begin
    for(wi=0;wi<256;wi=wi+1) begin
     prior_error=error_code;count=lengths[rk];
     legal_record=(rk==9)?1:((rk==7||rk==8)?abort_full:((rk==5)?(diag_full||diag_partial):report_full));
     live_before={prior_error,controller_error,manager_state,controller_state,local_error,bank_counts,
                 28'd0,diag_partial,diag_full,abort_full,report_full};
     want=0;
     if(rk==5)begin if(wi<64)want=diag_oracle[wi];end
     else if(rk==9)begin if(wi<4) for(bi=0;bi<32;bi=bi+1)want[bi]=live_before[wi*32+bi];end
     else if(wi<208)for(bi=0;bi<32;bi=bi+1)want[bi]=expected[rk][wi*32+bi];
     want_meta=0;want_meta[63:0]=(rk==9)?0:seqs[rk];
     want_meta[67:64]=rk;want_meta[75:68]=wi;want_meta[83:76]=count;
     want_meta[84]=legal_record&&(wi<count);want_meta[85]=(wi==count-1);
     want_meta[86]=(rk==5)&&diag_partial;want_meta[89:87]=0;want_meta[97:90]=prior_error;
     hold_data=read_data;hold_meta=read_meta;
     read_select=(wi<<8)|rk;action=1;
     #1;check(read_data===hold_data && read_meta===hold_meta,"READ unchanged before sampling edge");
     step;action=0;read_checks++;
     check(read_data===want,$sformatf("READ exact kind=%0d word=%0d want=%h got=%h",rk,wi,want,read_data));
     check(read_meta===want_meta,$sformatf("READ meta kind=%0d word=%0d",rk,wi));
     check(error_code===((!legal_record||wi>=count)?8'h34:prior_error),"READ error semantics");
    end
   end
   hold_data=read_data;hold_meta=read_meta;step;
   check(read_data===hold_data&&read_meta===hold_meta,"READ registers hold on idle edge");
  end
 endtask
'''
tb=tb.replace(' task fetch_start;',extra+'\n task fetch_start;')
tb=tb.replace('watch=0;','diag_oracle[index]=export_data;watch=0;')
tb=tb.replace('  act(3,0);check(!report_full', '  all_reads(0,9);\n  act(3,0);check(!report_full')
tb=tb.replace('  // Legal small and maximum diagnostic lengths', '  all_reads(0,9); // Released records retain their prior raw content.\n  // Legal small and maximum diagnostic lengths')
tb=tb.replace('bank_counts=0;check(diag_full&&!diag_partial,"complete FETCH");dump(5,0);','bank_counts=0;check(diag_full&&!diag_partial,"complete FETCH");dump(5,0);all_reads(5,5);')
tb=tb.replace('seqs[5]=555;lengths[5]=1;expected[5]=32\'hc1230000;dump(5,1);','seqs[5]=555;lengths[5]=1;expected[5]=32\'hc1230000;dump(5,1);all_reads(5,5);')
tb=tb.replace('  $display("EVIDENCE_COMPLETE', '''  // Live READ differs from frozen live DUMP by contract; exercise both.
  expected[9][127:0]={error_code,controller_error,manager_state,controller_state,local_error,bank_counts,28'd0,diag_partial,diag_full,abort_full,report_full};
  dump(9,0);all_reads(9,9);
  $display("PUBLIC_READ_COMPLETE reads=%0d miter_cycles=%0d",read_checks,miter_checks);
  $display("EVIDENCE_COMPLETE''')
(out/'tb_evidence.sv').write_text(tb,encoding='utf8')

# The independent oracle is a bit-addressed architectural record, not a copy of either mux.
records={0:[('report_context',160,0),('report_map',96,160)],1:[('report_header',512,0)],2:[('report_identity',725,0)],3:[('report_terminal',6626,0)],4:[('report_abort_payload',180,0)],6:[('report_abort_identity',725,0)],7:[('backend_identity',725,0)],8:[('backend_header',192,0)],9:[('live_snapshot',128,0)]}
tb=r'''`timescale 1ns/1ps
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
'''
for kind,fields in records.items():
    for name,width,offset in fields:
        tb+=f'   for(b=0;b<{width};b=b+1)begin dut.{name}[b]=oracle[{kind}][b+{offset}];old.{name}[b]=oracle[{kind}][b+{offset}];end\n'
tb+=r'''
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
'''
(out/'tb_words.sv').write_text(tb,encoding='utf8')
print('SELFTEST_ASSETS_READY',out)
