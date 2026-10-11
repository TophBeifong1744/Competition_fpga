`timescale 1ns/1ps
module tb_evidence;
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
 integer checks=0,n,k,j,watch,canary;reg previous_ack=0;
 reg [6655:0] expected [0:9];reg [63:0] seqs [0:9];
 integer lengths [0:9];reg [31:0] seen;reg [127:0] meta;
 always @(posedge clk) begin cycle<=cycle+1;#1;
  if(rst_n)begin
   if(previous_ack&&export_ack)$fatal(1,"DATA_CHECK ACK must have a low cycle");
   previous_ack=export_ack;
   if(export_ack)$display("ACK cycle=%0d seq=%0d word=%0d",cycle,export_ack_seq,export_ack_word);
  end else previous_ack=0;
 end
 task step;begin @(posedge clk);#2;end endtask
 task check(input bit ok,input string why);begin checks++;
  if(!ok)$fatal(1,"DATA_CHECK cycle=%0d %s",cycle,why);
 end endtask
 task act(input integer bitno,input integer kind);begin
  read_select=kind;action=1<<bitno;step;action=0;
 end endtask
 task dump(input integer kind,input bit partial);begin
  act(2,kind);
  for(j=0;j<lengths[kind];j++)begin
   step;seen=ila_sample[31:0];meta=ila_sample[159:32];
   if(canary&&kind==3&&j==17)seen=seen^32'h100;
   check(ila_sample[255:224]==32'h49313744,"DUMP magic");
   check(meta[84]&&meta[67:64]==kind&&meta[75:68]==j&&meta[83:76]==lengths[kind],"DUMP type/index/count/valid");
   check(meta[63:0]==seqs[kind]&&meta[85]==(j==lengths[kind]-1)&&meta[86]==partial,"DUMP identity/last/partial");
   check(seen==expected[kind][j*32+:32],$sformatf("DUMP content kind=%0d word=%0d exp=%h got=%h",kind,j,expected[kind][j*32+:32],seen));
   $display("DUMP_WORD cycle=%0d type=%0d seq=%0d word=%0d data=%h",cycle,kind,meta[63:0],j,seen);
  end
  step;check(ila_sample==0,"DUMP stops at exact final word");
 end endtask
 task fetch_start;begin
  bank_counts=1;act(1,5);check(export_select&&export_select_bank==0,"FETCH selects real bank");step;
 end endtask
 task send_word(input integer index,input integer count,input integer sequence_id,input bit malformed);begin
  export_valid=0;repeat((index*7+17010)%4)step;
  export_bank=0;export_seq=sequence_id;export_word=index;export_words=count;
  export_last=(index==count-1);export_data=32'hc1230000+index;export_valid=1;
  if(malformed)begin
   repeat(5)begin step;check(!export_ack,"malformed word never ACKed");end
   check(diag_partial&&!diag_full&&error_code==8'h31,"malformed record preserved partial");
  end else begin
   watch=0;
   while(!export_ack&&watch<15)begin step;watch++;end
   check(export_ack&&export_ack_seq==sequence_id&&export_ack_word==index,"ACK exact seq and word");
   // Hold the producer word through the consuming clock edge.
   step;export_valid=0;step;
  end
 end endtask
 initial begin
  canary=$test$plusargs("CANARY_DATA");
  for(k=0;k<10;k++)begin expected[k]=0;seqs[k]=0;lengths[k]=0;end
  lengths[0]=8;lengths[1]=16;lengths[2]=23;lengths[3]=208;lengths[4]=6;
  lengths[6]=23;lengths[7]=23;lengths[8]=6;lengths[9]=4;seqs[7]=1;seqs[8]=1;
  for(k=0;k<725;k++)begin identity[k]=(k%7==0);frontend_abort_identity[k]=(k%5==0);end
  for(k=0;k<6626;k++)terminal[k]=(k%11==0||k%13==3);
  for(k=0;k<180;k++)frontend_abort_payload[k]=(k%3==0);
  context_config=160'h112233445566778899aabbccddeeff0012345678;
  map_config=96'hc123456789abcdef76543210;
  expected[0][255:0]={map_config,context_config};expected[2][724:0]=identity;
  expected[3][6625:0]=terminal;expected[4][179:0]=frontend_abort_payload;
  expected[6][724:0]=frontend_abort_identity;expected[7][724:0]=identity;
  step;step;rst_n=1;step;check(report_ready&&abort_ready&&empty,"empty slot readiness");
  expected[1][63:0]=cycle;expected[1][127:64]=policy;
  expected[1][145:128]=raw_angle;expected[1][154:146]=command_angle;
  expected[1][164]=1;expected[1][165]=1;expected[1][173:166]=first_error;
  expected[1][179:174]=6'b111111;
  expected[1][223:192]=local_error;expected[1][255:224]=bank_counts;
  expected[1][263:256]=controller_state;expected[1][271:264]=manager_state;expected[1][279:272]=controller_error;
  expected[8][63:0]=cycle;expected[8][71:64]=first_error;expected[8][103:72]=local_error;
  expected[8][111:104]=manager_state;expected[8][119:112]=controller_state;expected[8][127:120]=controller_error;
  report_valid=1;abort_valid=1;step;
  check(!report_ready&&!abort_ready&&abort_full&&!report_full,"simultaneous slots, report pending");
  report_valid=0;abort_valid=0;servo_accept=1;servo_angle=135;
  expected[1][163:155]=135;expected[1][180]=1;
  identity=0;terminal=0;context_config=0;map_config=0;
  step;check(report_full&&!report_ready&&!abort_ready,"slots full no overwrite");
  check(result[52]&&result[35:27]==135,"next-edge servo belongs to saved report");
  servo_accept=0;servo_angle=511;report_valid=1;abort_valid=1;step;report_valid=0;abort_valid=0;
  act(3,0);check(report_full&&error_code==8'h38,"release before complete export rejected");
  dump(0,0);dump(1,0);dump(2,0);dump(3,0);dump(4,0);dump(6,0);dump(7,0);dump(8,0);
  dump(3,0); // repeat must neither mutate nor consume
  read_select=(207<<8)|3;action=1;step;action=0;
  check(read_data==expected[3][207*32+:32]&&read_meta[85],"tail READ zero padding/last");
  act(3,0);check(!report_full&&abort_full,"report release preserves other slot");
  act(3,7);check(!abort_full&&empty,"abort release after both dumps");
  // Legal small and maximum diagnostic lengths, with deterministic stalls.
  for(n=1;n<=63;n=(n==1?2:n==2?7:n==7?63:64))begin
   fetch_start;seqs[5]=100+n;lengths[5]=n;expected[5]=0;
   for(k=0;k<n;k++)begin expected[5][k*32+:32]=32'hc1230000+k;send_word(k,n,100+n,0);end
   bank_counts=0;check(diag_full&&!diag_partial,"complete FETCH");dump(5,0);
   act(3,5);check(!diag_full&&!diag_partial&&empty,"explicit diag release");
  end
  // Wrong sequence after a good first word never ACKs or consumes the head.
  fetch_start;send_word(0,3,555,0);send_word(1,3,556,1);
  act(4,5);check(export_abort,"read abort request");export_valid=0;step;
  seqs[5]=555;lengths[5]=1;expected[5]=32'hc1230000;dump(5,1);
  bank_counts=0;act(3,5);check(!diag_partial,"partial released only explicitly");
  // Word/count/last malformed first words: no ACK, retain partial marker.
  for(n=0;n<3;n++)begin
   fetch_start;export_valid=1;export_seq=777;export_bank=0;export_word=(n==0?1:0);
   export_words=(n==1?0:2);export_last=(n==2);
   repeat(5)begin step;check(!export_ack,"invalid word/count/last no ACK");end
   check(diag_partial&&!diag_full,"invalid partial marker");act(4,5);export_valid=0;step;
   bank_counts=0;act(3,5);check(!diag_partial,"zero-word error released after abort");
  end
  // Explicit abort while waiting for remaining words must preserve captured prefix.
  fetch_start;send_word(0,3,888,0);act(4,5);check(export_abort&&!export_ack,"partial snapshot abort no false ACK");
  seqs[5]=888;lengths[5]=1;expected[5]=32'hc1230000;dump(5,1);bank_counts=0;act(3,5);
  $display("EVIDENCE_COMPLETE checks=%0d pending=0",checks);$finish;
 end
 initial begin #2000000;$fatal(1,"TIMEOUT_HANG evidence");end
endmodule
