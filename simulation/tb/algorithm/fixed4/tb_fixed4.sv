`timescale 1ns/1ps
// Independent, cycle-indexed contract model. Run with +CANARY or
// +ILLEGAL_RESET to verify that the acceptance and reset guards fail.
module tb_fixed4;
  logic clk=0;
  always #5 clk=~clk;
  logic cold_reset=0, begin_valid=0, s_valid=0, m_ready=0, cancel=0;
  logic terminal_saved_ack=0, retire_valid=0, retire_safe=0;
  logic [63:0] begin_ctx=0,s_ctx=0,ack_ctx=0,retire_ctx=0;
  logic [9:0] s_bin=0;
  logic signed [28:0] s_re=0,s_im=0;
  logic [31:0] cancel_causes=0;
  wire ctx_active,terminal_saved,begin_ready,s_ready,m_valid;
  wire [63:0] active_ctx,m_ctx,terminal_ctx;
  wire [9:0] m_bin,terminal_n,terminal_p,terminal_cancelled_untransferred,terminal_t_bin;
  wire signed [24:0] m_re,m_im;
  wire m_numeric_valid,m_ov_re,m_ov_im,protocol_fault_now,data_done;
  wire [1:0] protocol_fault_bits_now;
  wire sticky_numeric_overflow,terminal_cancelled,terminal_t,terminal_s_transfer,local_quiescent;
  wire [34:0] terminal_causes;
  wire manager_commit_now = m_valid && m_ready && !cancel && !protocol_fault_now;
  fixed4_leaf dut (.*);

  integer cycle=0, checks=0, inputs=0, outputs=0, audits_ack=0, audits_retire=0;
  integer fixture_inputs=0, manager_commits=0, blocked_fault_outputs=0;
  integer cover_kill_ack=0, cover_duplicate_ack=0, cover_retire_kill=0, cover_busy_begin=0, cover_fault_commit=0;
  integer seen[0:512];
  bit initialized=0, ma=0, msaved=0, mq=0, mdone=0, msticky=0, mterm=0;
  bit mqnum=0,mqovre=0,mqovim=0,mt=0,mstrans=0;
  logic [63:0] mctx=0,mqctx=0,mtctx=0;
  logic [9:0] mn=0,mp=0,mqbin=0,mtn=0,mtp=0,muntrans=0,mtbin=0;
  logic signed [24:0] mqre=0,mqim=0;
  logic [34:0] mtcauses=0;
  integer accepted_at=-1;
  integer seed=32'h5a17_c0de;
  bit canary=0, illegal_reset=0;
  localparam longint signed S25_MIN = -64'sd16777216;
  localparam longint signed S25_MAX =  64'sd16777215;
`include "fixed4_145_inputs.svh"

  task automatic fail(input string reason);
    $display("FIXED4_FAIL cycle=%0d reason=%s seed=%08x ctx=%h n=%0d p=%0d q=%b term=%b",cycle,reason,seed,mctx,mn,mp,mq,mterm);
    $fatal(1,"FIXED4_FAIL");
  endtask
  task automatic eqb(input string name,input logic got,input logic exp);
    checks++;
    if(got !== exp) fail($sformatf("%s got=%b expected=%b",name,got,exp));
  endtask
  task automatic eqv(input string name,input logic [63:0] got,input logic [63:0] exp);
    checks++;
    if(got !== exp) fail($sformatf("%s got=%h expected=%h",name,got,exp));
  endtask
  // Magnitude-only integer quotient/remainder, then restore sign.  This keeps
  // all division and remainder operands nonnegative in the reference model.
  function automatic longint signed rne16(input longint signed x);
    longint signed mag,q,rem;
    mag=(x<0) ? -x : x;
    q=mag/64'sd16;
    rem=mag%64'sd16;
    if(rem>64'sd8 || (rem==64'sd8 && ((q & 64'sd1)!=0))) q++;
    return (x<0) ? -q : q;
  endfunction
  function automatic integer rand32();
    seed=seed^(seed<<13); seed=seed^(seed>>17); seed=seed^(seed<<5);
    return seed;
  endfunction
  function automatic bit outside_s25(input longint signed y);
    return (y < S25_MIN) || (y > S25_MAX);
  endfunction
  task automatic check_outputs;
    bit bready,sr,mv;
    bready=!cold_reset && !ma && begin_ctx!=0;
    sr=!cold_reset && ma && !mterm && !mdone && mn<513 && (!mq || m_ready);
    mv=!cold_reset && mq;
    eqb("begin_ready",begin_ready,bready);
    eqb("s_ready",s_ready,sr);
    eqb("m_valid",m_valid,mv);
    eqb("ctx_active",ctx_active,ma);
    eqv("active_ctx",active_ctx,mctx);
    eqb("terminal_saved",terminal_saved,msaved);
    eqb("data_done",data_done,mdone);
    eqb("sticky",sticky_numeric_overflow,msticky);
    eqb("terminal_cancelled",terminal_cancelled,mterm);
    eqv("terminal_ctx",terminal_ctx,mtctx);
    eqv("terminal_causes",{29'b0,terminal_causes},{29'b0,mtcauses});
    eqv("terminal_n",terminal_n,mtn);
    eqv("terminal_p",terminal_p,mtp);
    eqb("terminal_t",terminal_t,mt);
    eqv("terminal_untransferred",terminal_cancelled_untransferred,muntrans);
    eqb("terminal_s_transfer",terminal_s_transfer,mstrans);
    eqv("terminal_t_bin",terminal_t_bin,mtbin);
    eqb("local_quiescent",local_quiescent,!ma || mterm || mdone);
    if(!ma) begin
      eqv("idle_m_ctx",m_ctx,0);
      eqv("idle_m_bin",m_bin,0);
      eqv("idle_m_re",{39'b0,m_re},0);
      eqv("idle_m_im",{39'b0,m_im},0);
      eqb("idle_numeric_valid",m_numeric_valid,0);
      eqb("idle_ov_re",m_ov_re,0);
      eqb("idle_ov_im",m_ov_im,0);
    end
    if(mv) begin
      eqv("m_ctx",m_ctx,mqctx);
      eqv("m_bin",m_bin,mqbin);
      eqv("m_re",{39'b0,m_re},{39'b0,mqre});
      eqv("m_im",{39'b0,m_im},{39'b0,mqim});
      eqb("m_numeric_valid",m_numeric_valid,mqnum);
      eqb("m_ov_re",m_ov_re,mqovre);
      eqb("m_ov_im",m_ov_im,mqovim);
    end
  endtask
  task automatic tick;
    integer z;
    bit it,ot,fctx,fbin,kill,ackok,retok;
    logic [34:0] cause;
    longint signed rr,ri;
    bit ovre,ovim;
    #1;
    if(initialized) check_outputs();
    if(cold_reset && initialized) begin
      if(ma || mterm || msaved || !local_quiescent || begin_valid || s_valid || cancel || terminal_saved_ack || retire_valid)
        $fatal(1,"ILLEGAL_RESET_ASSERT cycle=%0d",cycle);
    end
    it=initialized && s_valid && s_ready;
    ot=initialized && m_valid && m_ready;
    if(ot && cycle+1<accepted_at+1) fail("output transferred before due cycle");
    fctx=it && s_ctx!=mctx;
    fbin=it && s_bin!=mn;
    kill=cancel||fctx||fbin;
    if(initialized) begin
      eqb("fault_ctx",protocol_fault_bits_now[0],fctx);
      eqb("fault_bin",protocol_fault_bits_now[1],fbin);
      eqb("fault_now",protocol_fault_now,fctx||fbin);
      eqb("manager_commit_gate",manager_commit_now,ot && !kill);
    end
    cause={cancel ? cancel_causes : 32'b0,fbin,fctx,cancel};
    ackok=terminal_saved_ack && ma && mterm && ack_ctx==mctx && !msaved;
    retok=retire_valid && ma && retire_ctx==mctx && (!ma||mterm||mdone) && retire_safe && !kill && (mterm ? msaved : mdone);
    if(terminal_saved_ack && !ackok) audits_ack++;
    if(retire_valid && !retok) audits_retire++;
    if(manager_commit_now) manager_commits++;
    if(ot && (fctx||fbin)) begin
      if(manager_commit_now) fail("manager committed old output on fault edge");
      blocked_fault_outputs++;
    end
    rr=rne16($signed(s_re)); ri=rne16($signed(s_im));
    ovre=outside_s25(rr);
    ovim=outside_s25(ri);
    if(it && mctx==64'h1001 && s_bin==1 &&
       (rr!=2 || ri!=-2 || ovre || ovim))
      $fatal(1,"REFERENCE_MODEL_FAIL bin1 re=%0d im=%0d rounded_re=%0d rounded_im=%0d ov_re=%b ov_im=%b",
             $signed(s_re),$signed(s_im),rr,ri,ovre,ovim);
    @(posedge clk);
    cycle++;
    if(cold_reset) begin
      ma=0; mctx=0; msaved=0; mn=0; mp=0; mq=0; mqctx=0; mqbin=0;
      mqre=0; mqim=0; mqnum=0; mqovre=0; mqovim=0; mdone=0; msticky=0;
      mterm=0; mtctx=0; mtcauses=0; mtn=0; mtp=0; mt=0; muntrans=0;
      mstrans=0; mtbin=0; initialized=1;
    end else if(!ma) begin
      if(begin_valid && begin_ready) begin
        for(z=0;z<513;z++) seen[z]=0;
        ma=1; mctx=begin_ctx; msaved=0; mn=0; mp=0; mq=0; mqctx=0; mqbin=0;
        mqre=0; mqim=0; mqnum=0; mqovre=0; mqovim=0; mdone=0; msticky=0;
        mterm=0; mtctx=0; mtcauses=0; mtn=0; mtp=0; mt=0; muntrans=0;
        mstrans=0; mtbin=0;
      end
    end else begin
      if(ackok) msaved=1;
      if(mterm) mtcauses=mtcauses|cause;
      else if(kill) begin
        mterm=1; mtctx=mctx; mtcauses=cause; mtn=mn; mtp=mp; mt=ot;
        muntrans=mn-mp-(ot ? 1 : 0); mstrans=it; mtbin=ot ? mqbin : 0;
        mq=0; mdone=0;
      end else begin
        if(ot) begin
          if(mqbin !== mp) fail("output order/duplicate");
          seen[mp]++;
          if(seen[mp]!=1) fail("duplicate bin");
          outputs++;
          if(mp==512 && mn==513) mdone=1;
          mp++;
        end
        if(it) begin
          if(s_bin!==mn) fail("accepted bin sequence");
          if(mctx==64'h1001 && s_bin>=5 && s_bin<150) begin
            if(s_re !== prepared_input(s_bin-5)) fail("prepared input identity mismatch");
            fixture_inputs++;
          end
          mn++; inputs++;
          mq=1; mqctx=mctx; mqbin=s_bin;
          mqovre=ovre; mqovim=ovim; mqnum=!(ovre||ovim);
          mqre=(ovre||ovim) ? 0 : rr;
          mqim=(ovre||ovim) ? 0 : ri;
          accepted_at=cycle;
          if(ovre||ovim) msticky=1;
        end else if(ot) mq=0;
      end
      if(retok) begin
        ma=0; mctx=0; msaved=0; mn=0; mp=0; mq=0; mqctx=0; mqbin=0;
        mqre=0; mqim=0; mqnum=0; mqovre=0; mqovim=0; mdone=0; msticky=0;
        mterm=0; mtctx=0; mtcauses=0; mtn=0; mtp=0; mt=0; muntrans=0;
        mstrans=0; mtbin=0;
      end
    end
    #1;
    if(canary && inputs==1 && ma && mq) mqre=mqre+1;
    check_outputs();
  endtask
  task automatic idle_inputs;
    begin_valid=0; s_valid=0; cancel=0; cancel_causes=0;
    terminal_saved_ack=0; retire_valid=0; retire_safe=0;
  endtask
  task automatic start_ctx(input logic [63:0] id);
    idle_inputs(); begin_ctx=id; begin_valid=1; tick(); begin_valid=0;
    if(!ma || mctx!=id) fail("begin not accepted");
  endtask
  task automatic abort_retire(input logic [63:0] id);
    idle_inputs(); terminal_saved_ack=1; ack_ctx=id+1; tick();
    ack_ctx=id; retire_valid=1; retire_ctx=id; retire_safe=1; tick();
    if(!msaved || !ma) fail("ack/retire same edge incorrectly retired");
    terminal_saved_ack=0; tick();
    if(ma) fail("cancelled context not retired");
    idle_inputs();
  endtask
  initial begin : main
    integer i,r,old_ack,old_retire,old_commits,old_blocked;
    longint signed c_pos8,c_pos24,c_neg8,c_neg24,c_hi_ok,c_hi_ov,c_lo_ok;
    canary=$test$plusargs("CANARY"); illegal_reset=$test$plusargs("ILLEGAL_RESET");
    c_pos8=rne16(64'sd8); c_pos24=rne16(64'sd24);
    c_neg8=rne16(-64'sd8); c_neg24=rne16(-64'sd24);
    c_hi_ok=rne16(64'sd268435447);
    c_hi_ov=rne16(64'sd268435448);
    c_lo_ok=rne16(-64'sd268435456);
    if(c_pos8!=0 || c_pos24!=2 || c_neg8!=0 || c_neg24!=-2 ||
       c_hi_ok!=16777215 || c_hi_ov!=16777216 || c_lo_ok!=-16777216 ||
       outside_s25(c_pos24) || outside_s25(c_neg24) ||
       outside_s25(c_hi_ok) || !outside_s25(c_hi_ov) || outside_s25(c_lo_ok))
      $fatal(1,"REFERENCE_MODEL_FAIL RNE/BND p8=%0d p24=%0d n8=%0d n24=%0d hi_ok=%0d hi_ov=%0d lo_ok=%0d bounds=%b%b%b%b%b",
             c_pos8,c_pos24,c_neg8,c_neg24,c_hi_ok,c_hi_ov,c_lo_ok,
             outside_s25(c_pos24),outside_s25(c_neg24),outside_s25(c_hi_ok),
             outside_s25(c_hi_ov),outside_s25(c_lo_ok));
    for(i=0;i<513;i++) seen[i]=0;
    cold_reset=1; tick();
    if(illegal_reset) begin
      cold_reset=0; start_ctx(64'h77);
      cold_reset=1; s_valid=1; tick();
      fail("illegal reset canary escaped");
    end
    cold_reset=0; begin_ctx=0; begin_valid=1; tick();
    if(ma) fail("zero context accepted");
    begin_valid=0;
    start_ctx(64'h1001);
    // 513 exact tags, II=1 when ready, deterministic random stalls and all
    // rounding boundaries including positive, negative and dual overflow.
    m_ready=1;
    for(i=0;i<513;i++) begin
      s_valid=1; s_ctx=mctx; s_bin=i;
      case(i)
        0: begin s_re=8; s_im=-8; end
        1: begin s_re=24; s_im=-24; end
        2: begin s_re=29'sd268435447; s_im=-29'sd268435456; end
        3: begin s_re=29'sd268435448; s_im=-29'sd268435455; end
        4: begin s_re=29'sd268435455; s_im=29'sd268435448; end
        default: begin
          s_re=(i<150) ? prepared_input(i-5) : $signed(rand32());
          s_im=$signed(rand32());
        end
      endcase
      do begin
        r=rand32(); m_ready=(i<6) ? 1 : ((r & 3)!=0);
        tick();
      end while(!(!mterm && mn==i+1));
    end
    s_valid=0; m_ready=1;
    while(!mdone) tick();
    if(inputs!=513 || outputs!=513 || fixture_inputs!=145 || !msticky) fail("normal 513/fixture accounting");
    for(i=0;i<513;i++) if(seen[i]!=1) fail($sformatf("missing tag %0d",i));
    retire_valid=1; retire_ctx=mctx; retire_safe=0; tick();
    if(!ma) fail("unsafe retire accepted");
    retire_safe=1; tick(); if(ma) fail("normal retire rejected");
    idle_inputs();
    // Permanent backpressure: cancellation must discard queued output locally.
    start_ctx(64'h1002); m_ready=0; s_valid=1; s_ctx=mctx; s_bin=0; s_re=16; s_im=32; tick();
    s_valid=0; repeat(4) tick();
    // First kill and ack share E: ack is rejected against pre-edge state.
    old_ack=audits_ack; cancel=1; cancel_causes=32'h1;
    terminal_saved_ack=1; ack_ctx=mctx; tick();
    if(mtn!=1 || mtp!=0 || mt || muntrans!=1 || mstrans ||
       !mterm || msaved || audits_ack!=old_ack+1) fail("first kill/ack rejection");
    cover_kill_ack++;
    // Reserved terminal slot remains occupied even with an empty output queue.
    terminal_saved_ack=0; cancel=0; begin_valid=1; begin_ctx=64'h2002; tick();
    if(!ma || mctx!=64'h1002 || !mterm || begin_ready) fail("cancel slot overwritten by begin");
    cover_busy_begin++; begin_valid=0;
    cancel=1; cancel_causes=32'h2; tick(); if(mtcauses!=35'h19) fail("late cause union");
    cancel=0; terminal_saved_ack=1; ack_ctx=64'h1002;
    retire_valid=1; retire_ctx=64'h1002; retire_safe=1; old_retire=audits_retire; tick();
    if(!msaved || !ma || audits_retire!=old_retire+1) fail("same-edge ack/retire rejection");
    // A repeated correct-ctx ack is still rejected; original snapshot stays.
    retire_valid=0; old_ack=audits_ack; tick();
    if(!ma || !msaved || !mterm || mtn!=1 || mtp!=0 ||
       mtcauses!=35'h19 || audits_ack!=old_ack+1) fail("duplicate ack changed terminal");
    cover_duplicate_ack++;
    // Here retirement would otherwise be legal; kill must block it on E.
    terminal_saved_ack=0; retire_valid=1; cancel=1; cancel_causes=32'h4;
    old_retire=audits_retire; tick();
    if(!ma || !msaved || !mterm || mtn!=1 || mtp!=0 ||
       mtcauses!=35'h39 || audits_retire!=old_retire+1) fail("retire/kill priority");
    cover_retire_kill++;
    cancel=0; tick(); if(ma) fail("cancelled context not retired after kill cleared");
    idle_inputs();
    // Same-edge old output T and newly accepted S are both physical transfers.
    start_ctx(64'h1003); m_ready=0; s_valid=1; s_ctx=mctx; s_bin=0; tick();
    m_ready=1; s_bin=1; cancel=1; cancel_causes=32'h8; tick();
    if(mtn!=1 || mtp!=0 || !mt || mtbin!=0 || muntrans!=0 || !mstrans || mtcauses!=35'h41)
      fail("same-edge S/T cancel snapshot");
    s_valid=0; cancel=0; abort_retire(64'h1003);
    // Local bin error, then local ctx+bin with external cancel; no success commit.
    start_ctx(64'h1004); m_ready=1; s_valid=1; s_ctx=mctx; s_bin=1; tick();
    if(!mterm || mtcauses!=35'h4 || !mstrans || mtn!=0 || mtp!=0) fail("local bin fault");
    s_valid=0; abort_retire(64'h1004);
    start_ctx(64'h1005); s_valid=1; s_ctx=mctx+1; s_bin=1;
    cancel=1; cancel_causes=32'h8; tick();
    if(mtcauses!=35'h47 || !mstrans || mtn!=0) fail("fault/cancel union");
    s_valid=0; cancel=0; abort_retire(64'h1005);
    // Last output and external status/cancel on one edge: physical T, no done.
    start_ctx(64'h1006); m_ready=1;
    for(i=0;i<513;i++) begin s_valid=1; s_ctx=mctx; s_bin=i; s_re=i; s_im=-i; tick(); end
    s_valid=0; cancel=1; cancel_causes=32'h80; tick();
    if(mtn!=513 || mtp!=512 || !mt || mtbin!=512 || muntrans!=0 || mdone)
      fail("last-beat cancellation");
    cancel=0; abort_retire(64'h1006);
    // A local fault arrives while the old output physically transfers. The
    // manager's same-edge public fault gate must suppress a success commit.
    start_ctx(64'h1008); m_ready=0; s_valid=1; s_ctx=mctx; s_bin=0; tick();
    m_ready=1; s_bin=2; old_commits=manager_commits;
    old_blocked=blocked_fault_outputs; tick();
    if(!mterm || !mt || mtbin!=0 || mtcauses!=35'h4 ||
       manager_commits!=old_commits || blocked_fault_outputs!=old_blocked+1)
      fail("same-edge fault allowed manager commit");
    cover_fault_commit++; s_valid=0; abort_retire(64'h1008);
    // Legal retired-state cold reset and request suppression during reset.
    cold_reset=1; tick(); tick(); cold_reset=0; tick();
    if(audits_ack<3 || audits_retire<3 || cover_kill_ack!=1 ||
       cover_duplicate_ack!=1 || cover_retire_kill!=1 || cover_busy_begin!=1 ||
       cover_fault_commit!=1 || fixture_inputs!=145)
      fail("directed cover point missing");
    $display("FIXED4_PASS checks=%0d cycles=%0d inputs=%0d outputs=%0d fixture=%0d ack_reject=%0d retire_reject=%0d seed_initial=5a17c0de",checks,cycle,inputs,outputs,fixture_inputs,audits_ack,audits_retire);
    $finish;
  end
  initial begin #2000000; $fatal(1,"FIXED4_TIMEOUT_HANG"); end
endmodule
