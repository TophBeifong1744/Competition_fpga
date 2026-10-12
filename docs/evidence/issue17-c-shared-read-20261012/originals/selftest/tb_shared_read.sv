`timescale 1ns/1ps
module tb_shared_read;
 reg clk=0,rst_n=0;always #5 clk=~clk;
 reg [4:0] action=0;reg [31:0] read_select=0;
 reg [159:0] context_config=0;reg [95:0] map_config=0;
 reg [7:0] controller_state=10,controller_error=8'h12,manager_state=5;
 reg [31:0] local_error=32'h13579abc,bank_counts=0;
 reg [63:0] cycle=0;
 reg report_valid=0,abort_valid=0;wire report_ready,abort_ready;
 reg [724:0] identity=0,frontend_abort_identity=0;
 reg [6625:0] terminal=0;reg frontend_abort_seen=1;
 reg [179:0] frontend_abort_payload=0;reg [63:0] policy=64'haf12569876543210;
 reg [17:0] raw_angle=18'h3d300;reg [8:0] command_angle=135,servo_angle=180;
 reg map_valid=1,numerical_valid=1,delivery_eligible=1,qualified_delivery=1;
 reg current_qualified=1,servo_command_valid=1,servo_accept=0,servo_reject=0;
 reg [3:0] servo_reject_reason=0;reg [7:0] first_error=8'h34;
 reg export_valid=0;reg [31:0] export_data=0;reg [2:0] export_bank=0;
 reg [63:0] export_seq=0;reg [5:0] export_word=0,export_words=0;reg export_last=0;
 wire export_select;wire [2:0] export_select_bank;wire export_ack;
 wire [63:0] export_ack_seq;wire [5:0] export_ack_word;wire export_abort;
 wire report_full,abort_full,diag_full,diag_partial,empty,busy;
 wire [7:0] error_code;wire [63:0] result;wire [31:0] read_data;
 wire [127:0] read_meta;wire [255:0] ila_sample;
 i17_vio_evidence dut(.*);
 wire  old_report_ready;
 wire  old_abort_ready;
 wire  old_export_select;
 wire [2:0] old_export_select_bank;
 wire  old_export_ack;
 wire [63:0] old_export_ack_seq;
 wire [5:0] old_export_ack_word;
 wire  old_export_abort;
 wire  old_report_full;
 wire  old_abort_full;
 wire  old_diag_full;
 wire  old_diag_partial;
 wire  old_empty;
 wire  old_busy;
 wire [7:0] old_error_code;
 wire [63:0] old_result;
 wire [31:0] old_read_data;
 wire [127:0] old_read_meta;
 wire [255:0] old_ila_sample;
 i17_vio_evidence_baseline old(.report_ready(old_report_ready),.abort_ready(old_abort_ready),.export_select(old_export_select),.export_select_bank(old_export_select_bank),.export_ack(old_export_ack),.export_ack_seq(old_export_ack_seq),.export_ack_word(old_export_ack_word),.export_abort(old_export_abort),.report_full(old_report_full),.abort_full(old_abort_full),.diag_full(old_diag_full),.diag_partial(old_diag_partial),.empty(old_empty),.busy(old_busy),.error_code(old_error_code),.result(old_result),.read_data(old_read_data),.read_meta(old_read_meta),.ila_sample(old_ila_sample),.*);
 // 中文用途：19个公开输出逐拍比较准确135271基线，独立预期只取输入夹具和合同。
 integer miter_checks=0,checks=0,j,k,xz_cases=0,whitebox_cases=0;
 integer canary,canary_miter;
 reg [63:0] sampled_cycle;
 reg [31:0] held_data,observed_data;
 reg [127:0] held_meta,wanted_meta,live_frozen;
 reg [255:0] config_fixture;
 reg [724:0] identity_fixture;
 reg [7:0] prior_error,next_error;
 reg [31:0] selectors[0:7];
 always @(posedge clk) cycle<=cycle+1;
 // 四态case比较包括reset边沿；miter与独立checker各自有隔离负例。
 always @(negedge clk) begin
  miter_checks++;
  if({report_ready,abort_ready,export_select,export_select_bank,export_ack,export_ack_seq,export_ack_word,export_abort,report_full,abort_full,diag_full,diag_partial,empty,busy,error_code,result,read_data,read_meta,ila_sample} !== {old_report_ready,old_abort_ready,old_export_select,old_export_select_bank,old_export_ack,old_export_ack_seq,old_export_ack_word,old_export_abort,old_report_full,old_abort_full,old_diag_full,old_diag_partial,old_empty,old_busy,old_error_code,old_result,old_read_data,old_read_meta,old_ila_sample})
   $fatal(1,"SHARED_MITER cycle=%0d all19 mismatch",cycle);
 end
 task step;begin sampled_cycle=cycle;@(posedge clk);#2;end endtask
 task ck(input bit ok,input string why);begin checks++;
  if(!ok)$fatal(1,"SHARED_CHECK cycle=%0d %s",cycle,why);
 end endtask
 // 字段格式源于公开meta约定，全部内容由刺激计划显式传入。
 function automatic [127:0] exp_meta(input [63:0] seq_id,input [3:0] typ,input [7:0] idx,
  input [7:0] count,input bit valid_record,input bit partial,input [2:0] bank,input [7:0] err);
  reg [127:0] m;
  begin m=0;m[63:0]=seq_id;m[67:64]=typ;m[75:68]=idx;m[83:76]=count;
   m[84]=valid_record&&(idx<count);m[85]=(idx==count-1);m[86]=partial;
   m[89:87]=bank;m[97:90]=err;exp_meta=m;
  end
 endfunction
 task read_expect(input [31:0] wanted,input [127:0] metadata,input [7:0] err,input string tag);
  begin
   ck(read_data===wanted,$sformatf("%s data exp=%h got=%h",tag,wanted,read_data));
   ck(read_meta===metadata,{tag," meta"});ck(error_code===err,{tag," error"});
  end
 endtask
 task dump_expect(input [31:0] wanted,input [127:0] metadata,input bit tail,input string tag);
  reg [255:0] expected_sample;
  begin
   expected_sample={32'h49313744,sampled_cycle,metadata,wanted};
   ck(ila_sample===expected_sample,$sformatf("%s aligned ILA exp=%h got=%h",tag,expected_sample,ila_sample));
   ck(busy===!tail,{tag," busy edge"});
   $display("SHARED_DUMP cycle=%0d sample_cycle=%0d type=%0d word=%0d data=%h meta=%h",cycle,sampled_cycle,metadata[67:64],metadata[75:68],ila_sample[31:0],ila_sample[159:32]);
  end
 endtask
 task reset_check;
  begin
   ck({export_select,export_select_bank,export_ack,export_ack_seq,export_ack_word,export_abort,
       report_full,abort_full,diag_full,diag_partial,busy,error_code,result,read_data,read_meta,ila_sample}==='0,"reset clears all registered public outputs/busy");
   ck(empty===1'b1&&report_ready===1'b0&&abort_ready===1'b0,"reset gates readiness");
  end
 endtask
 initial begin
  canary=$test$plusargs("CANARY_SHARED");canary_miter=$test$plusargs("CANARY_MITER");
  config_fixture=256'hfedcba98765432100123456789abcdef102030405060708090a0b0c0d0e0f001;
  identity_fixture=725'h123456789abcdef;
  selectors[0]=32'h00000707;selectors[1]=32'h0000000f;selectors[2]=32'h12340009;
  selectors[3]=32'hxxxxzzzz;selectors[4]=32'h00000083;selectors[5]=32'h0000ff03;
  selectors[6]=32'hzzzzxxxx;selectors[7]=32'h00000200;
  bank_counts=0;step;reset_check;step;rst_n=1;step;
  ck(report_ready&&abort_ready&&empty&&!busy,"initial readiness");
  // READ与新report同拍；地址保持0，先读旧0，再读新捕获值。
  read_select=0;context_config=config_fixture[159:0];map_config=config_fixture[255:160];
  report_valid=1;action=1;step;report_valid=0;action=0;
  read_expect(0,exp_meta(0,0,0,8,0,0,0,0),8'h34,"same-edge report old");
  ck(busy&&!report_full,"report pending edge");step;
  ck(report_full&&!busy,"report publish edge");action=1;step;action=0;
  read_expect(config_fixture[31:0],exp_meta(0,0,0,8,1,0,0,8'h34),8'h34,"stable-address report new");
  // abort记录和READ同拍同样采旧值；次拍相同地址读新identity。
  read_select=7;identity=identity_fixture;abort_valid=1;action=1;step;abort_valid=0;action=0;
  read_expect(0,exp_meta(0,7,0,23,0,0,0,8'h34),8'h34,"same-edge abort old");
  action=1;step;action=0;
  read_expect(identity_fixture[31:0],exp_meta(1,7,0,23,1,0,0,8'h34),8'h34,"stable-address abort new");
  // 首/中/末字READ拒绝，multi-action报32，ABORT脉冲均不截断DUMP。
  held_data=read_data;held_meta=read_meta;read_select=0;action=4;step;action=0;
  ck(busy&&ila_sample==0,"dump starts next edge");prior_error=8'h34;
  for(j=0;j<8;j++)begin
   read_select=selectors[j];action=0;next_error=prior_error;
   if(j==0||j==4||j==7)begin action=1;next_error=8'h33;end
   if(j==2)begin action=5;next_error=8'h32;end
   if(j==3)action=16;
   step;action=0;
   wanted_meta=exp_meta(0,0,j,8,1,0,0,prior_error);
   observed_data=ila_sample[31:0];if(canary&&j==0)observed_data=observed_data^32'h100;
   ck(observed_data===config_fixture[j*32+:32],$sformatf("DUMP_BUSY_CONTENT word=%0d exp=%h got=%h",j,config_fixture[j*32+:32],observed_data));
   dump_expect(config_fixture[j*32+:32],wanted_meta,j==7,"busy DUMP");
   ck(read_data===held_data&&read_meta===held_meta,"busy READ registers hold");
   ck(error_code===next_error,"busy error priority");ck(export_abort===(j==3),"ABORT one-edge pulse during DUMP");
   prior_error=next_error;
  end
  read_select=32'h00000200;action=1;step;action=0;
  read_expect(config_fixture[95:64],exp_meta(0,0,2,8,1,0,0,8'h33),8'h33,"first idle READ");
  ck(!busy&&ila_sample==0&&!export_abort,"dump drain");held_data=read_data;held_meta=read_meta;
  action=5;step;action=0;ck(error_code==8'h32&&!busy&&ila_sample==0,"idle multi-action rejects without DUMP");
  ck(read_data===held_data&&read_meta===held_meta,"idle multi-action holds READ");
  // live DUMP来自启动时的冻结向量；输入在每个输出字前变化，READ取最新输入。
  live_frozen={8'h32,controller_error,manager_state,controller_state,local_error,bank_counts,28'd0,4'b0011};
  read_select=9;action=4;step;action=0;ck(busy&&ila_sample==0,"live dump start");
  for(j=0;j<4;j++)begin
   controller_state=8'h80+j;controller_error=8'h90+j;manager_state=8'ha0+j;
   local_error=32'hdead0000+j;bank_counts=32'h12340000+j;read_select=selectors[j+2];
   step;dump_expect(live_frozen[j*32+:32],exp_meta(0,9,j,4,1,0,0,8'h32),j==3,"frozen live DUMP");
  end
  read_select=32'h00000309;action=1;step;action=0;
  read_expect({8'h32,8'h93,8'ha3,8'h83},exp_meta(0,9,3,4,1,0,0,8'h32),8'h32,"live READ real time");
  // 同步reset在活跃DUMP中清除公开寄存器，取消残余输出。
  bank_counts=0;read_select=0;action=4;step;action=0;step;
  dump_expect(config_fixture[31:0],exp_meta(0,0,0,8,1,0,0,8'h32),0,"before reset");
  rst_n=0;step;reset_check;step;reset_check;rst_n=1;step;
  ck(ila_sample==0&&read_data==0&&read_meta==0&&!busy&&!report_full&&!abort_full,"reset has no residual dump");
  // 稳定kind5/index0：合法FETCH改变diag_mem/count/valid，随后同地址READ必须更新。
  read_select=5;bank_counts=1;action=2;step;action=0;
  ck(export_select&&export_select_bank==0&&busy,"diag select");step;
  export_valid=1;export_data=32'hcafebabe;export_bank=0;export_seq=64'h1234;export_word=0;export_words=1;export_last=1;
  step;ck(diag_partial&&!diag_full&&!export_ack&&busy,"diag captured edge");
  step;ck(export_ack&&export_ack_seq==64'h1234&&export_ack_word==0,"diag ACK edge");
  export_valid=0;step;ck(diag_full&&!diag_partial&&!busy&&!export_ack,"diag completed edge");
  action=1;step;action=0;
  read_expect(32'hcafebabe,exp_meta(64'h1234,5,0,1,1,0,0,0),0,"stable-address diag new");
  // 只改变error，地址和记录保持；metadata下一次READ必须体现新error。
  action=5;step;action=0;ck(error_code==8'h32,"stable-address error change");
  action=1;step;action=0;
  read_expect(32'hcafebabe,exp_meta(64'h1234,5,0,1,1,0,0,8'h32),8'h32,"stable-address error meta");
  held_data=read_data;held_meta=read_meta;
  for(k=10;k<16;k++)begin read_select=k;action=1;step;action=0;
   ck(error_code==8'h33&&read_data===held_data&&read_meta===held_meta,"illegal kind rejects");end
  for(k=0;k<17;k++)begin
   read_select=(k==0)?32'h00000085:((32'h1<<(k+15))|32'h5);action=1;step;action=0;
   ck(error_code==8'h33&&read_data===held_data&&read_meta===held_meta,"reserved selector rejects");
  end
  // 公开XZ控制仅与准确旧RTL比较，不假设未知一律拒绝。
  for(k=0;k<32;k++)begin
   read_select=32'h00000009;read_select[k]=1'bx;action=1;step;action=0;xz_cases++;
   step;read_select=32'h00000009;read_select[k]=1'bz;action=1;step;action=0;xz_cases++;step;
  end
  // 白盒限定注入：dumping=X/Z不是自然运行场景，只审原if的四态等价性。
  read_select=5;action=1;force dut.dumping=1'bx;force old.dumping=1'bx;step;whitebox_cases++;step;
  action=0;release dut.dumping;release old.dumping;
  force dut.dumping=1'bz;force old.dumping=1'bz;action=1;step;whitebox_cases++;step;
  action=0;release dut.dumping;release old.dumping;bank_counts=0;rst_n=0;step;reset_check;
  rst_n=1;step;
  if(canary_miter)begin force dut.read_data=32'h1;step;end
  step;
  $display("SHARED_COMPLETE checks=%0d miter_cycles=%0d outputs=19 xz_cases=%0d whitebox_cases=%0d pending=0",checks,miter_checks,xz_cases,whitebox_cases);$finish;
 end
 initial begin #100000;$fatal(1,"TIMEOUT_HANG shared");end
endmodule
