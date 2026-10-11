`timescale 1ns/1ps
module tb_control;
 reg clk=0,rst_n=0; always #5 clk=~clk;
 reg [31:0] control=4,read_pending=0;
 reg [159:0] context_pending=0; reg [95:0] map_pending=0;
 reg config_ready=1,frontend_ready=0; reg [7:0] manager_state=0;
 reg ff_busy=0,ff_quiet=1,ff_obligation=0,doa_busy=0,doa_obligation=0,axis_valid=0;
 reg ff_terminal_valid=0,ff_abort_valid=0,ff_m_valid=0;
 reg [724:0] source_identity=0;
 reg current_qualified=0,report_saved=0,abort_saved=0,evidence_empty=1,io_busy=0;
 wire [159:0] context_config; wire [95:0] map_config;
 wire config_valid,research_valid,map_valid,servo_enable,start,diag_start,warm_reset;
 wire stop_now,fault_now,fft_permit,arm_request;
 wire [724:0] declared_tuple; wire [164:0] declared_context;wire [63:0] declared_generation;
 wire [4:0] action;wire [31:0] read_command;wire [7:0] state,error_code;
 wire configured,observe_only,motion_open_request;
 i17_vio_control dut(.*);
 integer cycle=0, checks=0,canary,limit;
 reg [159:0] observed_context;
 always @(posedge clk) begin cycle=cycle+1; #1;
  $display("CTRL_EDGE cycle=%0d state=%0d cfg=%b start=%b diag=%b arm=%b permit=%b stop=%b error=%h",cycle,state,configured,start,diag_start,arm_request,fft_permit,stop_now,error_code);
 end
 task step; begin @(posedge clk); #2; end endtask
 task check(input bit ok,input string why);begin checks=checks+1;
  if(!ok) $fatal(1,"CONTROL_CHECK cycle=%0d %s",cycle,why);
 end endtask
 task toggle(input integer b);begin control[b]=~control[b];step;end endtask
 task reset_case;begin
  rst_n=0;control=4;config_ready=1;frontend_ready=0;manager_state=0;
  ff_busy=0;ff_quiet=1;ff_obligation=0;doa_busy=0;doa_obligation=0;axis_valid=0;
  ff_terminal_valid=0;ff_abort_valid=0;ff_m_valid=0;current_qualified=0;
  report_saved=0;abort_saved=0;evidence_empty=1;io_busy=0;
  step;step;rst_n=1;step;step;control[2]=0;step;
 end endtask
 task config_case(input bit obs);begin
  context_pending={64'h11223344,64'h55667788,32'h12345678};
  map_pending=0;map_pending[23:0]=180*256;map_pending[25:24]=1;
  map_pending[43:26]=-90*256;map_pending[61:44]=90*256;
  map_pending[70:62]=90;map_pending[79:71]=270;
  map_pending[80]=!obs;map_pending[81]=!obs;map_pending[82]=obs;
  toggle(0); check(config_valid,"COMMIT must enter actual config handshake");
  config_ready=0;context_pending=0;map_pending=0;
  repeat(3)begin step;check(config_valid&&!configured,"config waits real ready");end
  observed_context=context_config;
  if(canary) observed_context=observed_context^160'd1;
  check(observed_context=={64'h11223344,64'h55667788,32'h12345678},"atomic context snapshot");
  config_ready=1;step;check(configured&&research_valid,"configuration accepted");
 end endtask
 task start_and_bind(input bit obs);begin
  frontend_ready=0;
  toggle(1);
  repeat(7)begin step;check(!start&&!diag_start&&!fft_permit&&!arm_request,"wait real warmup ready");end
  frontend_ready=1;step;check(start&&!diag_start,"source start precedes diag start");
  step;check(diag_start,"diag start follows source edge");step;
  source_identity={64'h12345,64'h6789,{2'd1,1'b1,64'h11223344,1'b1,64'h55667788,1'b1,32'h12345678},432'h123456789abcdef};
  ff_busy=1;ff_quiet=0;step;
  check(declared_tuple==source_identity,"identity is actual source identity");
  check(declared_generation==64'h6789,"generation exact");
  if(obs)begin check(fft_permit&&!arm_request&&!servo_enable&&!map_valid,"observe numeric no motion");end
  else begin
   check(!arm_request&&!fft_permit,"bound identity before arm high");step;
   check(arm_request&&!fft_permit,"arm high before numeric permit");
   repeat(4)begin step;check(!fft_permit,"wait true qualification");end
   current_qualified=1;step;
   check(fft_permit&&arm_request&&motion_open_request,"qualified run");
  end
 end endtask
 initial begin
  canary=$test$plusargs("CANARY_CONTROL");
  // Retained action toggles at reset must not be interpreted as new requests.
  control=32'h1ff;step;rst_n=1;step;step;
  check(!configured&&!start&&action==0&&!warm_reset,"reset toggle baseline");
  reset_case;config_case(0);
  if($test$plusargs("CASE_WARM_RACE"))begin
   // Core samples the registered warm_reset on the following clock edge.
   toggle(3);check(warm_reset,"warm request issued");
   step;manager_state=6;config_ready=0;#1;
   check(state==13,"C-VIO-STATIC-002 must not complete recovery using pre-request idle");
   // Frozen native manager: PREPARE6 -> WAIT_RESET7 -> RESET_WAIT8 -> CLEAR9.
   repeat(2)begin step;check(state==13,"native PREPARE pending");end
   manager_state=7;step;check(state==13,"native WAIT_RESET pending");
   manager_state=8;step;check(state==13,"native RESET_WAIT pending");
   manager_state=9;step;check(state==13,"native CLEAR pending");
   manager_state=0;config_ready=1;axis_valid=1;step;
   check(state==13,"returned idle still waits AXIS drain");axis_valid=0;step;
   check(state==0&&!configured,"recovery completes after native return idle");
   $display("CONTROL_COMPLETE WARM_RACE pending=0");$finish;
  end
  start_and_bind(0);
  if($test$plusargs("CASE_EARLY_FINISH"))begin
   // Frontend normal_finished is NOT completion of DOA/IFFT or delivery.
   manager_state=5;doa_busy=1;ff_busy=0;ff_quiet=1;step;
   check(servo_enable&&arm_request,"C-VIO-STATIC-001 frontend finished must retain pending DOA authorization");
   repeat(3)begin step;check(servo_enable,"wait true backend report");end
   report_saved=1;step;check(!servo_enable,"revoke only after report or STOP");
   $display("CONTROL_COMPLETE EARLY_FINISH pending=0");$finish;
  end
  // STOP dominates same-edge START and terminal notification, no replay later.
  control[2]=1;report_saved=1;toggle(1);
  check(!start&&!arm_request&&!servo_enable&&fft_permit,"STOP START report priority/drain");
  report_saved=0;control[2]=0;repeat(3)step;
  check(!start&&!arm_request,"no stale authorization replay");
  evidence_empty=0;ff_busy=0;ff_quiet=1;step;toggle(0);
  check(!config_valid,"full evidence blocks COMMIT");
  // Recovery must not assume idle before the external contract is satisfied.
  manager_state=10;ff_obligation=1;toggle(3);check(warm_reset,"warm reset request");
  repeat(4)begin step;check(!configured&&!start,"recovery pending real drain");end
  manager_state=6;config_ready=0;step;
  manager_state=7;step;manager_state=8;step;manager_state=9;step;
  manager_state=0;config_ready=1;ff_obligation=0;step;
  check(!configured&&!start&&!servo_enable,"recover remains disarmed");
  evidence_empty=1;config_case(1);start_and_bind(1);
  repeat(6)begin step;check(!arm_request&&!servo_enable,"observe stays disarmed");end
  abort_saved=1;step;abort_saved=0;check(!start,"one window ends without rearm");
  // Context mismatch and premature terminal each reject qualification.
  reset_case;config_case(0);toggle(1);frontend_ready=1;step;step;step;
  source_identity=0;ff_busy=1;step;
  check(fault_now&&!arm_request&&!servo_enable,"mismatched context rejected");
  reset_case;config_case(0);toggle(1);frontend_ready=1;step;step;step;
  ff_terminal_valid=1;ff_busy=1;step;
  check(fault_now&&!arm_request&&!servo_enable,"early terminal rejected");
  // Conflicting actions are rejected, read selection is atomic under STOP.
  reset_case;control=control^32'h3;step;check(!config_valid&&!start&&error_code==1,"conflicting actions");
  control[2]=1;read_pending=32'h00000323;toggle(4);
  check(action==1&&read_command==32'h323,"read allowed under STOP, selector captured");
  read_pending=0;step;check(action==0&&read_command==32'h323,"read one-shot stable selection");
  $display("CONTROL_COMPLETE checks=%0d pending=0",checks);$finish;
 end
 initial begin #100000;$fatal(1,"TIMEOUT_HANG control");end
endmodule
