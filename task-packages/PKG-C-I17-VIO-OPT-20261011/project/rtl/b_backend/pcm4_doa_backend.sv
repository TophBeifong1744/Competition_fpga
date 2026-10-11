`timescale 1ns/1ps
// Native fixed4 consumer. Official IFFT25 is external; no behavioral FFT substitute.
module pcm4_doa_backend (
    input logic clk, cold_rst_n,
    input logic begin_valid, output logic begin_ready,
    input logic [63:0] begin_token, begin_generation,
    input logic [164:0] begin_context, input logic [431:0] begin_frame_first,
    input logic gate_evidence_valid, gate_qualified,
    input logic [63:0] gate_policy_id,
    input logic s_valid, output logic s_ready,
    input logic [63:0] s_token, s_generation,
    input logic [164:0] s_context, input logic [431:0] s_frame_first,
    input logic s_domain, input logic [1:0] s_channel, input logic [9:0] s_bin,
    input logic signed [24:0] s_real, s_imag,
    input logic s_numeric_valid, s_ov_real, s_ov_imag, s_qualified,
    input logic s_terminal_valid, output logic s_terminal_ready,
    input logic [6625:0] s_terminal_data,
    input logic s_abort_valid, output logic s_abort_ready,
    input logic [724:0] s_abort_identity, input logic [179:0] s_abort_data,
    input logic cancel_now, stop_now, input logic [7:0] cancel_causes,
    input logic [724:0] cancel_identity,
    output logic frontend_cancel_request,
    output logic [724:0] active_identity,
    // Exact official AXIS contract: IFFT25, config inverse, natural1024, /2 each stage.
    output logic [23:0] ip_config_data, output logic ip_config_valid,
    input logic ip_config_ready,
    output logic [63:0] ip_input_data, output logic ip_input_valid, ip_input_last,
    input logic ip_input_ready,
    input logic [63:0] ip_output_data, input logic [9:0] ip_output_index,
    input logic ip_output_valid, ip_output_last, output logic ip_output_ready,
    input logic [7:0] ip_status_data, input logic ip_status_valid,
    output logic ip_status_ready,
    input logic ip_event_unexpected_last, ip_event_missing_last, ip_event_overflow,
    output logic report_valid, input logic report_ready,
    output logic signed [17:0] angle_q8,
    output logic angle_numerical_valid, output logic angle_delivery_eligible,
    output logic report_gate_evidence_valid, report_gate_qualified,
    output logic [63:0] report_gate_policy_id,
    output logic [6625:0] frontend_terminal_record,
    output logic frontend_abort_seen,
    output logic [724:0] frontend_abort_identity_record,
    output logic [179:0] frontend_abort_record,
    output logic [23:0] pair_state,
    output logic [83:0] backend_stage_state,
    output logic [5:0] pair_hardware_started, pair_physically_retired, pair_valid,
    output logic [191:0] pair_tau_q12,
    output logic [149:0] pair_peak_codes,
    output logic [383:0] pair_margin_q15,
    output logic [41:0] pair_mask_counts,
    output logic [65:0] ifft_input_counts, ifft_output_counts,
    output logic [47:0] ifft_status_records,
    output logic [5:0] ifft_status_seen,
    output logic signed [22:0] ux_q20, uy_q20,
    output logic [63:0] residual_square_q24, norm_square_q40,
    output logic [7:0] direction_reason,
    output logic [7:0] first_error_code,
    output logic transaction_cancelled,
    output logic abort_valid, input logic abort_ready,
    output logic [7:0] first_cancel_causes, accumulated_cancel_causes,
    output logic [23:0] abort_pair_state,
    output logic [83:0] abort_stage_state,
    output logic [5:0] abort_hardware_started, abort_physically_retired,
    output logic [65:0] abort_ifft_input_counts, abort_ifft_output_counts,
    output logic [5:0] abort_ifft_status_seen,
    output logic [3:0] abort_ip_transfers,
    output logic busy, ip_obligation,
    output logic [4:0] debug_state
);
    import doa_math_pkg::*;
    // Exact full FF report: port declaration order, first field MSB. 725-bit tuple
    // plus5901 raw audit bits. Never substitute quiet/source_seen for this ACK.
    typedef struct packed {
      logic [63:0] token,generation; logic [164:0] context_bits;
      logic [431:0] frame_first; logic [63:0] unit_state;
      logic [15:0] hardware_started,physically_retired;
      logic [87:0] fft_input_counts,fft_output_counts;
      logic [79:0] fixed4_input_counts,fixed4_output_counts,fixed4_qualified_counts;
      logic [63:0] fft_status_raw; logic [7:0] fft_status_seen;
      logic [55:0] fft_event_seen; logic [511:0] fixed4_contexts;
      logic [279:0] fixed4_cancel_causes_record;
      logic [79:0] fixed4_terminal_n_record,fixed4_terminal_p_record;
      logic [79:0] fixed4_cancelled_unsent_record,fixed4_terminal_t_bin_record;
      logic [7:0] fixed4_terminal_t_record,fixed4_terminal_s_record;
      logic [7:0] fixed4_cancel_saved,fixed4_retire_accepted;
      logic [13:0] source_received;
      logic transaction_cancelled,protocol_error,numeric_error;
      logic [7:0] first_error_code,accumulated_cancel_causes;
      logic [2001:0] source_report_record; logic [2079:0] source_abort_record;
      logic source_report_seen,source_abort_seen;
    } frontend_t;
    frontend_t front_now,front_saved;
    assign front_now=s_terminal_data;
    assign front_saved=frontend_terminal_record;
    localparam logic [4:0] IDLE=0,COLLECT=1,BARRIER=2,PAIR_BEGIN=3,CROSS=4,
      NORMALIZE=5,PHAT_FINAL=6,CONFIG=7,RUN_IP=8,IP_FINAL=9,
      LAG_SCAN=10,LAG_FINAL=11,NEXT_PAIR=12,LS_ACC=13,LS_SOLVE=14,
      LS_RESIDUAL=15,GEOMETRY=16,CORDIC_INIT=17,CORDIC_RUN=18,
      CORDIC_FINAL=19,FINISH=20,REPORT=21,LAG_MARGIN=22;
    localparam logic [3:0] PENDING=0,OK=1,REJECTED=2,NUMERIC=3,PROTOCOL=4,CANCELLED=5,SKIPPED=6;
    localparam logic [7:0] ERR_ID=1,ERR_ORDER=2,ERR_SOURCE_NUMERIC=3,
      ERR_FRONTEND=4,ERR_PHAT=5,ERR_IFFT_INDEX=6,ERR_IFFT_LAST=7,
      ERR_IFFT_STATUS=8,ERR_IFFT_EVENT=9,ERR_CORDIC=10;
    logic [4:0] state;
    logic [12:0] received;
    logic [9:0] expected_bin; logic [2:0] expected_lane;
    logic terminal_seen,source_bad;
    logic [49:0] spectrum [0:2051];
    logic signed [50:0] cross_real [0:512],cross_imag [0:512];
    logic [49:0] phat_half [0:512];
    logic signed [24:0] correlation [0:1023];
    logic [2:0] pair_id;
    logic [9:0] k;
    logic [6:0] mask_count;
    logic [102:0] maximum_square;
    logic pair_bad,ip_pair_bad,ip_pair_numeric;
    logic [10:0] input_count,output_count;
    logic status_received;
    logic signed [5:0] lag,peak_lag;
    logic signed [24:0] peak;
    logic signed [24:0] second_peak;
    logic second_valid;
    logic signed [31:0] taus [0:5];
    logic signed [31:0] bx,by;
    logic signed [7:0] sxx,syy,sxy;
    logic [3:0] valid_pairs;
    logic signed [27:0] cx,cy;
    logic signed [25:0] ca,coffset;
    logic [4:0] iteration;
    logic [63:0] residual_acc;
    logic abort_consumed,report_consumed;
    wire external_kill=(cancel_now || stop_now) && busy && cancel_identity==active_identity;
    wire source_kill=s_abort_valid && busy && s_abort_identity==active_identity;
    // A foreign physical ACK revokes current-edge eligibility, not reliable cancellation.
    wire foreign_abort_ack_now=s_abort_valid && s_abort_ready && s_abort_identity!=active_identity;
    wire kill_now=external_kill || source_kill;
    wire [7:0] reliable_causes=(external_kill ? cancel_causes | (stop_now ? 8'h02 : 8'h01) : 8'h00) |
      (source_kill ? 8'h04 : 8'h00);
    wire begin_external_kill=(cancel_now || stop_now) && cancel_identity=={begin_token,begin_generation,begin_context,begin_frame_first};
    wire begin_source_kill=s_abort_valid && s_abort_identity=={begin_token,begin_generation,begin_context,begin_frame_first};
    wire begin_kill=begin_external_kill || begin_source_kill;
    wire [7:0] begin_causes=(begin_external_kill ? cancel_causes | (stop_now ? 8'h02 : 8'h01) : 8'h00) |
      (begin_source_kill ? 8'h04 : 8'h00);
    wire killed=transaction_cancelled || kill_now;
    wire s_id_ok={s_token,s_generation,s_context,s_frame_first}==active_identity;
    integer i,j,a_ch,b_ch,addr_a,addr_b,half_index,scan_index,left_index,right_index;
    integer dx,dy,bits,norm_shift,det;
    wide_t ar,ai,br,bi,cr,ci,square,delta,den,numerator,tau;
    wide_t solve_x,solve_y,predicted,residue,norm,normal_square,angle_rounded,margin;
    logic [51:0] normalized;
    logic front_ok;
    always_comb begin
      begin_ready=(state==IDLE);
      busy=(state!=IDLE); debug_state=state;
      s_ready=(state==COLLECT && !terminal_seen);
      s_terminal_ready=(state==COLLECT && !terminal_seen);
      s_abort_ready=busy && !frontend_abort_seen;
      frontend_cancel_request=external_kill || (begin_valid && begin_ready && begin_external_kill);
      report_valid=(state==REPORT && !report_consumed && !kill_now);
      angle_delivery_eligible=report_valid && angle_numerical_valid &&
        report_gate_evidence_valid && report_gate_qualified && !killed &&
        !foreign_abort_ack_now && first_error_code==0;
      ip_config_data=24'h0AAAAA; ip_config_valid=(state==CONFIG);
      ip_obligation=pair_hardware_started[pair_id] && !pair_physically_retired[pair_id];
      ip_input_valid=(state==RUN_IP && input_count<1024);
      ip_input_last=input_count==1023;
      ip_output_ready=(state==RUN_IP && output_count<1024);
      ip_status_ready=(state==RUN_IP && !status_received);
      half_index=input_count<=512 ? input_count : 1024-input_count;
      ip_input_data=0;
      if(input_count<1024) begin
        ip_input_data[24:0]=phat_half[half_index][49:25];
        ip_input_data[56:32]=input_count<=512 ? phat_half[half_index][24:0] : -$signed(phat_half[half_index][24:0]);
      end
      case(pair_id)
        0:begin a_ch=0;b_ch=1;dx=1;dy=0;end
        1:begin a_ch=0;b_ch=2;dx=1;dy=1;end
        2:begin a_ch=0;b_ch=3;dx=0;dy=1;end
        3:begin a_ch=1;b_ch=2;dx=0;dy=1;end
        4:begin a_ch=1;b_ch=3;dx=-1;dy=1;end
        default:begin a_ch=2;b_ch=3;dx=-1;dy=0;end
      endcase
      addr_a=a_ch*513+k; addr_b=b_ch*513+k;
      ar=0;ai=0;br=0;bi=0;
      if(k<=512) begin
        ar=wide_t'($signed(spectrum[addr_a][49:25])); ai=wide_t'($signed(spectrum[addr_a][24:0]));
        br=wide_t'($signed(spectrum[addr_b][49:25])); bi=wide_t'($signed(spectrum[addr_b][24:0]));
      end
      cr=ar*br+ai*bi; ci=ai*br-ar*bi;
      square=cr*cr+ci*ci;
      normalized=0;
      normal_square=0;
      if(state==NORMALIZE && k>=7 && k<=85)
        normalized=phat_normalize(cross_real[k],cross_imag[k]);
      if(k>=7 && k<=85)
        normal_square=wide_t'(cross_real[k])*wide_t'(cross_real[k])+wide_t'(cross_imag[k])*wide_t'(cross_imag[k]);
      scan_index=lag<0 ? 1024+lag : lag;
      left_index=peak_lag<=0 ? 1023+peak_lag : peak_lag-1;
      right_index=peak_lag< -1 ? 1025+peak_lag : peak_lag+1;
      den=wide_t'(correlation[left_index])-2*wide_t'(peak)+wide_t'(correlation[right_index]);
      numerator=(wide_t'(correlation[left_index])-wide_t'(correlation[right_index]))<<<11;
      if(den<0) begin den=-den;numerator=-numerator;end
      delta=den==0 ? 0 : rne_div(numerator,den);
      if(delta>2048) delta=2048; if(delta< -2048) delta=-2048;
      tau=wide_t'(peak_lag)*4096+delta;
      margin=rne_div((wide_t'(peak)-(second_valid ? wide_t'(second_peak) : 192'sd0))<<<15,
        peak==0 ? 192'sd1 : (peak<0 ? -wide_t'(peak) : wide_t'(peak)));
      det=sxx*syy-sxy*sxy;
      solve_x=rne_div((wide_t'(syy)*wide_t'(bx)-wide_t'(sxy)*wide_t'(by))*343*256,wide_t'(det)*1920);
      solve_y=rne_div((wide_t'(sxx)*wide_t'(by)-wide_t'(sxy)*wide_t'(bx))*343*256,wide_t'(det)*1920);
      predicted=rne_div((wide_t'(dx)*wide_t'(ux_q20)+wide_t'(dy)*wide_t'(uy_q20))*1920*4096,192'sd343*1048576);
      residue=predicted-wide_t'(taus[pair_id]);
      norm=wide_t'(ux_q20)*wide_t'(ux_q20)+wide_t'(uy_q20)*wide_t'(uy_q20);
      angle_rounded=rne_shift(wide_t'(ca)+wide_t'(coffset),8);
      if(angle_rounded>=46080) angle_rounded=angle_rounded-92160;
      if(angle_rounded< -46080) angle_rounded=angle_rounded+92160;
      bits=0;
      for(i=0;i<23;i=i+1) begin
        if(($unsigned(ux_q20<0 ? -ux_q20 : ux_q20)>>i)!=0 ||
           ($unsigned(uy_q20<0 ? -uy_q20 : uy_q20)>>i)!=0) bits=i+1;
      end
      norm_shift=24-bits;
      front_ok={front_now.token,front_now.generation,front_now.context_bits,front_now.frame_first}==active_identity &&
        front_now.unit_state==64'h1111111111111111 &&
        front_now.hardware_started==16'hFFFF && front_now.physically_retired==16'hFFFF &&
        front_now.fft_status_seen==8'hFF && front_now.fft_status_raw==0 &&
        front_now.source_received==8192 && front_now.source_report_seen &&
        !front_now.source_abort_seen && !front_now.transaction_cancelled &&
        !front_now.protocol_error && !front_now.numeric_error && front_now.first_error_code==0;
      for(i=0;i<8;i=i+1) begin
        if(front_now.fft_input_counts[i*11+:11]!=1024 || front_now.fft_output_counts[i*11+:11]!=1024 ||
           front_now.fixed4_input_counts[i*10+:10]!=513 || front_now.fixed4_output_counts[i*10+:10]!=513 ||
           front_now.fixed4_qualified_counts[i*10+:10]!=513) front_ok=0;
      end
    end
    always_ff @(posedge clk) begin
      if(!cold_rst_n) begin
        state<=IDLE; active_identity<=0; received<=0; expected_bin<=0; expected_lane<=0;
        terminal_seen<=0; source_bad<=0; frontend_terminal_record<=0;
        frontend_abort_seen<=0; frontend_abort_identity_record<=0; frontend_abort_record<=0;
        pair_id<=0; k<=0; maximum_square<=0; mask_count<=0; pair_bad<=0; ip_pair_bad<=0;
        pair_state<=0;backend_stage_state<=0;pair_hardware_started<=0;pair_physically_retired<=0;pair_valid<=0;ip_pair_numeric<=0;
        pair_tau_q12<=0;pair_peak_codes<=0;pair_margin_q15<=0;pair_mask_counts<=0;ifft_input_counts<=0;ifft_output_counts<=0;
        ifft_status_records<=0;ifft_status_seen<=0;
        angle_q8<=0;angle_numerical_valid<=0;report_gate_evidence_valid<=0;
        report_gate_qualified<=0;report_gate_policy_id<=0;first_error_code<=0;
        transaction_cancelled<=0;abort_valid<=0;abort_consumed<=0;report_consumed<=0;
        first_cancel_causes<=0;accumulated_cancel_causes<=0;abort_pair_state<=0;abort_stage_state<=0;
        abort_hardware_started<=0;abort_physically_retired<=0;
        abort_ifft_input_counts<=0;abort_ifft_output_counts<=0;abort_ifft_status_seen<=0;abort_ip_transfers<=0;
        input_count<=0;output_count<=0;status_received<=0;
        lag<=0;peak_lag<=0;peak<=0;second_peak<=0;second_valid<=0;bx<=0;by<=0;sxx<=0;syy<=0;sxy<=0;
        valid_pairs<=0;ux_q20<=0;uy_q20<=0;residual_acc<=0;residual_square_q24<=0;norm_square_q40<=0;
        direction_reason<=5;
        cx<=0;cy<=0;ca<=0;coffset<=0;iteration<=0;
        for(j=0;j<6;j=j+1) taus[j]<=0;
      end else begin
        if(s_abort_valid && s_abort_ready) begin
          frontend_abort_seen<=1; frontend_abort_record<=s_abort_data;
          frontend_abort_identity_record<=s_abort_identity;
          if(s_abort_identity!=active_identity && first_error_code==0) first_error_code<=ERR_ID;
        end
        if(abort_valid && abort_ready) begin abort_valid<=0;abort_consumed<=1;end
        if(report_valid && report_ready) report_consumed<=1;
        if(kill_now) begin
          transaction_cancelled<=1;
          accumulated_cancel_causes<=accumulated_cancel_causes | reliable_causes;
          if(!transaction_cancelled) begin
            abort_valid<=1;abort_consumed<=0;
            first_cancel_causes<=reliable_causes;
            abort_pair_state<=pair_state;abort_stage_state<=backend_stage_state;abort_hardware_started<=pair_hardware_started;
            abort_physically_retired<=pair_physically_retired;
            abort_ifft_input_counts<=ifft_input_counts;abort_ifft_output_counts<=ifft_output_counts;
            abort_ifft_status_seen<=ifft_status_seen;
            abort_ip_transfers<={ip_status_valid && ip_status_ready,ip_output_valid && ip_output_ready,
              ip_input_valid && ip_input_ready,ip_config_valid && ip_config_ready};
          end
        end
        case(state)
          IDLE: if(begin_valid && begin_ready) begin
            active_identity<={begin_token,begin_generation,begin_context,begin_frame_first};
            received<=0;expected_bin<=0;expected_lane<=0;terminal_seen<=0;source_bad<=0;
            frontend_terminal_record<=0;frontend_abort_seen<=0;frontend_abort_record<=0;
            frontend_abort_identity_record<=0;pair_state<=0;backend_stage_state<=0;pair_hardware_started<=0;
            pair_physically_retired<=0;pair_valid<=0;pair_tau_q12<=0;pair_peak_codes<=0;pair_margin_q15<=0;pair_mask_counts<=0;
            ifft_input_counts<=0;ifft_output_counts<=0;ifft_status_records<=0;ifft_status_seen<=0;
            report_gate_evidence_valid<=gate_evidence_valid;report_gate_qualified<=gate_qualified;
            report_gate_policy_id<=gate_policy_id;angle_numerical_valid<=0;angle_q8<=0;
            first_error_code<=0;transaction_cancelled<=begin_kill;abort_valid<=begin_kill;abort_consumed<=0;report_consumed<=0;
            first_cancel_causes<=begin_kill ? begin_causes : 0;
            accumulated_cancel_causes<=begin_kill ? begin_causes : 0;
            abort_pair_state<=0;abort_stage_state<=0;abort_hardware_started<=0;abort_physically_retired<=0;pair_id<=0;
            abort_ifft_input_counts<=0;abort_ifft_output_counts<=0;abort_ifft_status_seen<=0;abort_ip_transfers<=0;
            ux_q20<=0;uy_q20<=0;residual_square_q24<=0;norm_square_q40<=0;
            direction_reason<=5;
            for(j=0;j<6;j=j+1) taus[j]<=0;
            state<=COLLECT;
          end
          COLLECT: begin
            if(s_valid && s_ready) begin
              received<=received+1;
              if(!s_id_ok || {s_domain,s_channel}!=expected_lane || s_bin!=expected_bin || received>=4104) begin
                source_bad<=1; if(first_error_code==0) first_error_code<=!s_id_ok ? ERR_ID : ERR_ORDER;
              end else if(!s_numeric_valid || s_ov_real || s_ov_imag || !s_qualified) begin
                source_bad<=1;
                if(first_error_code==0 && (!s_numeric_valid || s_ov_real || s_ov_imag || (!s_qualified && !killed))) first_error_code<=ERR_SOURCE_NUMERIC;
              end
              if(s_id_ok && s_domain && s_bin<=512) spectrum[s_channel*513+s_bin]<={s_real,s_imag};
              if(expected_bin==512) begin expected_bin<=0;expected_lane<=expected_lane+1;end
              else expected_bin<=expected_bin+1;
            end
            if(s_terminal_valid && s_terminal_ready) begin
              frontend_terminal_record<=s_terminal_data; terminal_seen<=1;
              // Same-edge final source data is allowed; BARRIER sees resulting count/error.
              if(!front_ok) begin
                source_bad<=1;
                if(first_error_code==0 && (!front_now.transaction_cancelled || front_now.protocol_error || front_now.numeric_error || front_now.first_error_code!=0)) first_error_code<=ERR_FRONTEND;
              end
              state<=BARRIER;
            end
          end
          BARRIER: begin
            if(front_saved.transaction_cancelled && !frontend_abort_seen) begin
              // A cancelled frontend owes its actual independent held ABORT record.
            end else if(received!=4104 || source_bad || frontend_abort_seen || first_error_code!=0 || killed) begin
              if(received!=4104 && first_error_code==0 && !killed && !front_saved.transaction_cancelled) first_error_code<=ERR_ORDER;
              for(j=0;j<6;j=j+1) pair_state[j*4+:4]<=(killed || front_saved.transaction_cancelled) ? CANCELLED : PROTOCOL;
              pair_physically_retired<=6'h3F;state<=FINISH;
            end else state<=PAIR_BEGIN;
          end
          PAIR_BEGIN: begin
            k<=7;maximum_square<=0;mask_count<=0;pair_bad<=0;
            if(killed || first_error_code!=0) begin
              pair_state[pair_id*4+:4]<=killed ? CANCELLED : NUMERIC;
              backend_stage_state[pair_id*4+:4]<=killed ? CANCELLED : SKIPPED;
              backend_stage_state[(pair_id+6)*4+:4]<=killed ? CANCELLED : SKIPPED;
              backend_stage_state[(pair_id+12)*4+:4]<=killed ? CANCELLED : SKIPPED;
              pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;
            end else state<=CROSS;
          end
          CROSS: begin
            cross_real[k]<=cr[50:0];cross_imag[k]<=ci[50:0];
            if(square>$unsigned(maximum_square)) maximum_square<=square[102:0];
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;end
            else if(k==85) begin k<=0;state<=NORMALIZE;end
            else k<=k+1;
          end
          NORMALIZE: begin
            phat_half[k]<=0;
            if(k>=7 && k<=85) begin
              if(normal_square>0 && normal_square*2500>=$unsigned(maximum_square)) begin
                mask_count<=mask_count+1;
                if(normalized[51] || normalized[24:0]==25'h1000000) begin
                  pair_bad<=1;if(first_error_code==0) first_error_code<=ERR_PHAT;
                end else phat_half[k]<=normalized[49:0];
              end
            end
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;end
            else if(k==512) state<=PHAT_FINAL;
            else k<=k+1;
          end
          PHAT_FINAL: begin
            pair_mask_counts[pair_id*7+:7]<=mask_count;
            if(pair_bad || killed || mask_count<12) begin
              pair_state[pair_id*4+:4]<=killed ? CANCELLED : (pair_bad ? NUMERIC : REJECTED);
              backend_stage_state[pair_id*4+:4]<=killed ? CANCELLED : (pair_bad ? NUMERIC : REJECTED);
              backend_stage_state[(pair_id+6)*4+:4]<=killed ? CANCELLED : SKIPPED;
              backend_stage_state[(pair_id+12)*4+:4]<=killed ? CANCELLED : SKIPPED;
              pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;
            end else begin backend_stage_state[pair_id*4+:4]<=OK;state<=CONFIG;end
          end
          CONFIG: if(ip_config_valid && ip_config_ready) begin
            pair_hardware_started[pair_id]<=1;input_count<=0;output_count<=0;
            status_received<=0;ip_pair_bad<=0;ip_pair_numeric<=0;state<=RUN_IP;
          end
          RUN_IP: begin
            if(ip_input_valid && ip_input_ready) begin
              input_count<=input_count+1;ifft_input_counts[pair_id*11+:11]<=input_count+1;
            end
            if(ip_output_valid && ip_output_ready) begin
              output_count<=output_count+1;ifft_output_counts[pair_id*11+:11]<=output_count+1;
              correlation[output_count[9:0]]<=$signed(ip_output_data[24:0]);
              if(ip_output_index!=output_count[9:0]) begin
                ip_pair_bad<=1;if(first_error_code==0) first_error_code<=ERR_IFFT_INDEX;
              end else if(ip_output_last!=(output_count==1023)) begin
                ip_pair_bad<=1;if(first_error_code==0) first_error_code<=ERR_IFFT_LAST;
              end
            end
            if(ip_status_valid && ip_status_ready) begin
              status_received<=1;ifft_status_seen[pair_id]<=1;ifft_status_records[pair_id*8+:8]<=ip_status_data;
              if(ip_status_data!=0) begin
                ip_pair_bad<=1;if(ip_status_data[0]) ip_pair_numeric<=1;
                if(first_error_code==0) first_error_code<=ERR_IFFT_STATUS;
              end
            end
            if(ip_event_unexpected_last || ip_event_missing_last || ip_event_overflow) begin
              if(ip_event_overflow) ip_pair_numeric<=1;
              ip_pair_bad<=1;if(first_error_code==0) first_error_code<=ERR_IFFT_EVENT;
            end
            if(input_count==1024 && output_count==1024 && status_received) state<=IP_FINAL;
          end
          IP_FINAL: begin
            pair_physically_retired[pair_id]<=1;
            if(killed || ip_pair_bad) begin
              pair_state[pair_id*4+:4]<=killed ? CANCELLED : (ip_pair_numeric ? NUMERIC : PROTOCOL);
              backend_stage_state[(pair_id+6)*4+:4]<=killed ? CANCELLED : (ip_pair_numeric ? NUMERIC : PROTOCOL);
              backend_stage_state[(pair_id+12)*4+:4]<=killed ? CANCELLED : SKIPPED;state<=NEXT_PAIR;
            end else begin
              backend_stage_state[(pair_id+6)*4+:4]<=OK;
              lag<=(pair_id==1 || pair_id==4) ? -8 : -6;peak<=-25'sd16777216;peak_lag<=0;
              second_peak<=0;second_valid<=0;state<=LAG_SCAN;
            end
          end
          LAG_SCAN: begin
            if(lag==((pair_id==1 || pair_id==4) ? -8 : -6) || correlation[scan_index]>peak) begin peak<=correlation[scan_index];peak_lag<=lag;end
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;state<=NEXT_PAIR;end
            else if(lag==((pair_id==1 || pair_id==4) ? 8 : 6)) begin
              lag<=(pair_id==1 || pair_id==4) ? -8 : -6;state<=LAG_MARGIN;
            end
            else lag<=lag+1;
          end
          LAG_MARGIN: begin
            if((lag<peak_lag-1 || lag>peak_lag+1) && (!second_valid || correlation[scan_index]>second_peak)) begin
              second_peak<=correlation[scan_index];second_valid<=1;
            end
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;state<=NEXT_PAIR;end
            else if(lag==((pair_id==1 || pair_id==4) ? 8 : 6)) state<=LAG_FINAL;
            else lag<=lag+1;
          end
          LAG_FINAL: begin
            taus[pair_id]<=tau;pair_tau_q12[pair_id*32+:32]<=tau[31:0];
            pair_peak_codes[pair_id*25+:25]<=peak;pair_margin_q15[pair_id*64+:64]<=margin[63:0];
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;backend_stage_state[(pair_id+12)*4+:4]<=CANCELLED;end
            else if(tau>((pair_id==1 || pair_id==4) ? 32425 : 22928) || tau< -((pair_id==1 || pair_id==4) ? 32425 : 22928)) begin
              pair_state[pair_id*4+:4]<=REJECTED;backend_stage_state[(pair_id+12)*4+:4]<=REJECTED;
            end else begin pair_state[pair_id*4+:4]<=OK;backend_stage_state[(pair_id+12)*4+:4]<=OK;pair_valid[pair_id]<=1;end
            state<=NEXT_PAIR;
          end
          NEXT_PAIR: begin
            if(pair_id==5) begin pair_id<=0;bx<=0;by<=0;sxx<=0;syy<=0;sxy<=0;valid_pairs<=0;state<=LS_ACC;end
            else begin pair_id<=pair_id+1;state<=PAIR_BEGIN;end
          end
          LS_ACC: begin
            if(pair_valid[pair_id]) begin
              bx<=bx+dx*taus[pair_id];by<=by+dy*taus[pair_id];
              sxx<=sxx+dx*dx;syy<=syy+dy*dy;sxy<=sxy+dx*dy;valid_pairs<=valid_pairs+1;
            end
            if(pair_id==5) state<=LS_SOLVE; else pair_id<=pair_id+1;
          end
          LS_SOLVE: begin
            if(killed || first_error_code!=0 || valid_pairs<3 || det<=0) begin
              backend_stage_state[18*4+:4]<=killed ? CANCELLED : (first_error_code!=0 ? SKIPPED : REJECTED);
              direction_reason<=killed ? 6 : (first_error_code!=0 ? 7 : (valid_pairs<3 ? 1 : 2));state<=FINISH;
            end
            else if(solve_x< -4194304 || solve_x>4194303 || solve_y< -4194304 || solve_y>4194303) begin
              backend_stage_state[18*4+:4]<=NUMERIC;
              if(first_error_code==0) first_error_code<=ERR_CORDIC;state<=FINISH;
            end else begin ux_q20<=solve_x;uy_q20<=solve_y;residual_acc<=0;pair_id<=0;state<=LS_RESIDUAL;end
          end
          LS_RESIDUAL: begin
            if(pair_valid[pair_id]) residual_acc<=residual_acc+residue*residue;
            if(pair_id==5) state<=GEOMETRY; else pair_id<=pair_id+1;
          end
          GEOMETRY: begin
            residual_square_q24<=residual_acc;norm_square_q40<=norm;
            if(killed || first_error_code!=0 || residual_acc>valid_pairs*64'd4194304 ||
              norm<192'sd10995200164 || norm>192'sd1858175196201) begin
                direction_reason<=killed ? 6 : (first_error_code!=0 ? 7 : (residual_acc>valid_pairs*64'd4194304 ? 3 : 4));state<=FINISH;
                backend_stage_state[18*4+:4]<=killed ? CANCELLED : (first_error_code!=0 ? SKIPPED : REJECTED);
              end
            else begin backend_stage_state[18*4+:4]<=OK;state<=CORDIC_INIT;end
          end
          CORDIC_INIT: begin
            if(ux_q20==0 && uy_q20==0) begin
              backend_stage_state[19*4+:4]<=NUMERIC;if(first_error_code==0) first_error_code<=ERR_CORDIC;state<=FINISH;
            end
            else begin
              cx<=($signed(ux_q20)<0 ? -wide_t'(ux_q20) : wide_t'(ux_q20))<<<norm_shift;
              cy<=($signed(ux_q20)<0 ? -wide_t'(uy_q20) : wide_t'(uy_q20))<<<norm_shift;
              coffset<=ux_q20<0 ? (uy_q20>=0 ? 26'sd11796480 : -26'sd11796480) : 0;
              ca<=0;iteration<=0;state<=CORDIC_RUN;
            end
          end
          CORDIC_RUN: begin
            if(killed) state<=FINISH;
            else begin
              if(cy>0) begin cx<=cx+(cy>>>iteration);cy<=cy-(cx>>>iteration);ca<=ca+atan_rom(iteration);end
              else if(cy<0) begin cx<=cx-(cy>>>iteration);cy<=cy+(cx>>>iteration);ca<=ca-atan_rom(iteration);end
              if(iteration==23) state<=CORDIC_FINAL;else iteration<=iteration+1;
            end
          end
          CORDIC_FINAL: begin
            if(!killed && first_error_code==0) begin
              angle_q8<=angle_rounded;angle_numerical_valid<=1;direction_reason<=0;backend_stage_state[19*4+:4]<=OK;
            end
            state<=FINISH;
          end
          FINISH: begin
            // All six final instances, but hardware_started distinguishes unexecuted ones.
            for(j=0;j<6;j=j+1) if(pair_state[j*4+:4]==PENDING) pair_state[j*4+:4]<=killed ? CANCELLED : REJECTED;
            for(j=0;j<20;j=j+1) if(backend_stage_state[j*4+:4]==PENDING)
              backend_stage_state[j*4+:4]<=(killed || front_saved.transaction_cancelled) ? CANCELLED : SKIPPED;
            backend_stage_state[20*4+:4]<=killed ? CANCELLED :
              (!angle_numerical_valid || !report_gate_evidence_valid ? SKIPPED : (report_gate_qualified ? OK : REJECTED));
            if(!angle_numerical_valid && (killed || front_saved.transaction_cancelled)) direction_reason<=6;
            state<=REPORT;
          end
          REPORT: if(!kill_now && (report_consumed || (report_valid && report_ready)) &&
            (!abort_valid || abort_ready) && (!transaction_cancelled || abort_consumed || (abort_valid && abort_ready))) state<=IDLE;
          default: begin if(first_error_code==0) first_error_code<=ERR_FRONTEND;state<=FINISH;end
        endcase
      end
    end
endmodule
