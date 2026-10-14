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
    // 四通道分库，每库单同步读/单写；COLLECT和CROSS互斥。
    (* ram_style="block" *) logic [49:0] spectrum0 [0:512];
    (* ram_style="block" *) logic [49:0] spectrum1 [0:512];
    (* ram_style="block" *) logic [49:0] spectrum2 [0:512];
    (* ram_style="block" *) logic [49:0] spectrum3 [0:512];
    logic [49:0] spectrum_read [0:3];
    logic [49:0] spectrum_a,spectrum_b;
    logic cross_phase;
    logic [1:0] normal_phase;
    logic [2:0] math_phase;
    logic signed [49:0] product_arbr,product_aibi,product_aibr,product_arbi;
    logic signed [50:0] cross_re_exact,cross_im_exact;
    logic signed [101:0] cross_re_square,cross_im_square;
    // 跨谱分四级寄存：乘积、加减、平方、求和；bin/配对/复数载荷同步延迟。
    logic signed [49:0] product_arbr_q,product_aibi_q,product_aibr_q,product_arbi_q;
    logic signed [50:0] cross_re_q,cross_im_q;
    logic signed [101:0] cross_re_square_q,cross_im_square_q;
    logic signed [50:0] square_re_q,square_im_q,sum_re_q,sum_im_q;
    logic [102:0] cross_sum_q;
    logic [6:0] product_bin_q,value_bin_q,square_bin_q,sum_bin_q;
    logic [2:0] product_pair_q,value_pair_q,square_pair_q,sum_pair_q;
    logic product_valid,value_valid,square_valid,sum_valid,cross_commit;
    logic signed [39:0] ls_syy_bx,ls_sxy_by,ls_sxx_by,ls_sxy_bx;
    logic signed [40:0] ls_num_x,ls_num_y;
    logic signed [45:0] ux_square,uy_square;
    logic signed [63:0] residue_square;
    logic alu_start,alu_ready,alu_done,alu_busy;
    logic [1:0] alu_op;
    wide_t alu_a,alu_b,alu_result;
    // 接合算术先按原生操作数的完整值域定宽，再符号扩展至不变的192位核。
    logic signed [36:0] delta_saved;
    logic signed [40:0] margin_saved;
    logic signed [57:0] solve_x_saved,solve_y_saved;
    logic signed [26:0] angle_saved;
    logic signed [25:0] lag_difference,margin_difference,peak_magnitude;
    logic signed [26:0] lag_den_signed,lag_den_positive,cordic_sum;
    logic signed [36:0] lag_numerator_signed,lag_numerator;
    logic signed [40:0] margin_numerator;
    logic signed [15:0] det_product_xy,det_product_cross;
    logic signed [16:0] det_exact;
    logic signed [28:0] ls_denominator;
    logic signed [57:0] ls_scaled_x,ls_scaled_y;
    logic signed [23:0] residual_direction;
    logic signed [47:0] residual_numerator;
    logic [114:0] mask_scaled_square;
    logic [22:0] abs_ux,abs_uy;
    logic signed [31:0] alu_shift;
    logic phat_start,phat_ready,phat_done,phat_busy;
    logic [51:0] phat_result;
    // 私有ALU接线不复制transaction身份或PHAT状态机。
    logic phat_alu_start,phat_alu_ready,phat_alu_done;
    logic [1:0] phat_alu_op;
    wide_t phat_alu_a,phat_alu_b,phat_alu_result;
    logic signed [31:0] phat_alu_shift;
    // 工作集精确缩减：跨谱仅7..85，lag及邻点仅-9..+9。
    (* ram_style="block" *) logic [204:0] cross_work [0:78];
    logic [204:0] cross_read;
    (* ram_style="block" *) logic [49:0] phat_half [0:78];
    logic [49:0] ip_half_data;
    logic signed [24:0] correlation [0:18];
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
    integer i,j,a_ch,b_ch,addr_a,addr_b,next_half_index,scan_index,left_index,right_index;
    integer dx,dy,bits,norm_shift,det;
    wide_t ar,ai,br,bi,delta,den,numerator,tau;
    logic signed [31:0] residue;
    wide_t solve_x,solve_y,predicted,norm,normal_square,angle_rounded,margin;
    logic [51:0] normalized;
    logic front_ok;
    // 只在当前配对计算窗口提交；取消同拍阻断写缓存与最大值更新。
    assign cross_commit=cold_rst_n && !killed && (state==CROSS || state==NORMALIZE) &&
      sum_valid && sum_pair_q==pair_id;
    // NORMALIZE的PHAT与四种后处理状态互斥，共用同一原192位服务。
    doa_math_shared backend_math(.clk(clk),.cold_rst_n(cold_rst_n),.cancel(killed),
      .phat_start(phat_alu_start),.phat_ready(phat_alu_ready),.phat_operation(phat_alu_op),
      .phat_operand_a(phat_alu_a),.phat_operand_b(phat_alu_b),.phat_shift(phat_alu_shift),
      .phat_done(phat_alu_done),.phat_result(phat_alu_result),
      .backend_start(alu_start),.backend_ready(alu_ready),.backend_operation(alu_op),
      .backend_operand_a(alu_a),.backend_operand_b(alu_b),.backend_shift(alu_shift),
      .backend_done(alu_done),.backend_result(alu_result),.backend_busy(alu_busy));
    doa_phat_client phat_math(.clk(clk),.cold_rst_n(cold_rst_n),.cancel(killed),
      .start(phat_start),.ready(phat_ready),.done(phat_done),.in_real($signed(cross_read[101:51])),
      .in_imag($signed(cross_read[50:0])),.in_square($unsigned(normal_square)),.result(phat_result),.busy(phat_busy),
      .alu_start(phat_alu_start),.alu_ready(phat_alu_ready),.alu_done(phat_alu_done),
      .alu_op(phat_alu_op),.alu_a(phat_alu_a),.alu_b(phat_alu_b),
      .alu_shift(phat_alu_shift),.alu_result(phat_alu_result));
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
      // CONFIG预置第0点；每次真实接受才同步读取下一点，stall不改数据。
      next_half_index=input_count<512 ? input_count+1 : 1023-input_count;
      ip_input_data=0;
      if(input_count<1024) begin
        ip_input_data[24:0]=ip_half_data[49:25];
        ip_input_data[56:32]=input_count<=512 ? ip_half_data[24:0] : -$signed(ip_half_data[24:0]);
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
      spectrum_a=spectrum_read[a_ch];spectrum_b=spectrum_read[b_ch];
      // 25位输入的单乘积精确占50位，加/减精确占51位。
      product_arbr=$signed(spectrum_a[49:25])*$signed(spectrum_b[49:25]);
      product_aibi=$signed(spectrum_a[24:0])*$signed(spectrum_b[24:0]);
      product_aibr=$signed(spectrum_a[24:0])*$signed(spectrum_b[49:25]);
      product_arbi=$signed(spectrum_a[49:25])*$signed(spectrum_b[24:0]);
      cross_re_exact={product_arbr_q[49],product_arbr_q}+{product_aibi_q[49],product_aibi_q};
      cross_im_exact={product_aibr_q[49],product_aibr_q}-{product_arbi_q[49],product_arbi_q};
      cross_re_square=cross_re_q*cross_re_q;
      cross_im_square=cross_im_q*cross_im_q;
      normal_square={89'd0,cross_read[204:102]};
      normalized=phat_result;
      // correlation槽0..18对应原自然序位置1015..1023,0..9。
      scan_index=lag+9;
      left_index=peak_lag+8;
      right_index=peak_lag+10;
      // S25三项和差需S27；相邻差S26左移11需S37，不截合法端点。
      lag_den_signed=27'($signed(correlation[left_index]))-
        (27'($signed(peak))<<<1)+27'($signed(correlation[right_index]));
      lag_difference=26'($signed(correlation[left_index]))-26'($signed(correlation[right_index]));
      lag_numerator_signed=37'(lag_difference)<<<11;
      lag_den_positive=lag_den_signed<0 ? -lag_den_signed : lag_den_signed;
      lag_numerator=lag_den_signed<0 ? -lag_numerator_signed : lag_numerator_signed;
      den=wide_t'(lag_den_positive);numerator=wide_t'(lag_numerator);
      delta=wide_t'(delta_saved);
      if(delta>2048) delta=2048; if(delta< -2048) delta=-2048;
      tau=wide_t'(peak_lag)*4096+delta;
      margin=wide_t'(margin_saved);
      det_product_xy=$signed(sxx)*$signed(syy);
      det_product_cross=$signed(sxy)*$signed(sxy);
      det_exact=17'(det_product_xy)-17'(det_product_cross);
      det=det_exact;
      solve_x=wide_t'(solve_x_saved);solve_y=wide_t'(solve_y_saved);
      ls_syy_bx=$signed(syy)*$signed(bx);ls_sxy_by=$signed(sxy)*$signed(by);
      ls_sxx_by=$signed(sxx)*$signed(by);ls_sxy_bx=$signed(sxy)*$signed(bx);
      ls_num_x={ls_syy_bx[39],ls_syy_bx}-{ls_sxy_by[39],ls_sxy_by};
      ls_num_y={ls_sxx_by[39],ls_sxx_by}-{ls_sxy_bx[39],ls_sxy_bx};
      ls_scaled_x=58'(ls_num_x)*58'sd87808;
      ls_scaled_y=58'(ls_num_y)*58'sd87808;
      ls_denominator=29'(det_exact)*29'sd1920;
      margin_difference=26'($signed(peak))-(second_valid ? 26'($signed(second_peak)) : 26'sd0);
      margin_numerator=41'(margin_difference)<<<15;
      peak_magnitude=peak==0 ? 26'sd1 : (peak<0 ? -26'($signed(peak)) : 26'($signed(peak)));
      // 必须先扩一位再求负，覆盖ux/uy最小负码；S24和×7864320需S48。
      residual_direction=(dx==0 ? 24'sd0 : (dx<0 ? -24'($signed(ux_q20)) : 24'($signed(ux_q20))))+
        (dy==0 ? 24'sd0 : 24'($signed(uy_q20)));
      residual_numerator=48'(residual_direction)*48'sd7864320;
      cordic_sum=27'($signed(ca))+27'($signed(coffset));
      mask_scaled_square={12'd0,cross_read[204:102]}*115'd2500;
      ux_square=$signed(ux_q20)*$signed(ux_q20);uy_square=$signed(uy_q20)*$signed(uy_q20);
      residue_square=$signed(residue[31:0])*$signed(residue[31:0]);
      // 共享除法核由各状态发起；无组合除法/余数或sqrt调用。
      alu_start=0;alu_op=0;alu_a=0;alu_b=1;alu_shift=0;
      if(!killed && alu_ready) case(state)
        LAG_FINAL: begin
          if(math_phase==0) begin alu_start=1;alu_a=numerator;alu_b=den;end
          if(math_phase==2) begin
            alu_start=1;alu_a=wide_t'(margin_numerator);alu_b=wide_t'(peak_magnitude);
          end
        end
        LS_SOLVE: if(first_error_code==0 && valid_pairs>=3 && det>0) begin
          if(math_phase==0) begin
            alu_start=1;alu_a=wide_t'(ls_scaled_x);alu_b=wide_t'(ls_denominator);
          end
          if(math_phase==2) begin
            alu_start=1;alu_a=wide_t'(ls_scaled_y);alu_b=wide_t'(ls_denominator);
          end
        end
        LS_RESIDUAL: if(math_phase==0 && pair_valid[pair_id]) begin
          alu_start=1;alu_a=wide_t'(residual_numerator);
          alu_b=192'sd343*1048576;
        end
        CORDIC_FINAL: if(math_phase==0) begin
          alu_start=1;alu_op=2;alu_a=wide_t'(cordic_sum);alu_shift=8;
        end
        default: begin end
      endcase
      phat_start=state==NORMALIZE && normal_phase==1 && phat_ready && !killed;
      norm=wide_t'(ux_square)+wide_t'(uy_square);
      angle_rounded=wide_t'(angle_saved);
      if(angle_rounded>=46080) angle_rounded=angle_rounded-92160;
      if(angle_rounded< -46080) angle_rounded=angle_rounded+92160;
      bits=0;
      abs_ux=$unsigned(ux_q20<0 ? -ux_q20 : ux_q20);
      abs_uy=$unsigned(uy_q20<0 ? -uy_q20 : uy_q20);
      for(i=0;i<23;i=i+1) if(abs_ux[i] || abs_uy[i]) bits=i+1;
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
    // 无复位数组清零：新事务必须收满原4104个实例后才读取。
    always_ff @(posedge clk) begin
      if(cold_rst_n && s_valid && s_ready && s_id_ok && s_domain && s_bin<=512) case(s_channel)
        0:spectrum0[s_bin]<={s_real,s_imag};
        1:spectrum1[s_bin]<={s_real,s_imag};
        2:spectrum2[s_bin]<={s_real,s_imag};
        3:spectrum3[s_bin]<={s_real,s_imag};
      endcase
      if(cold_rst_n && state==CROSS && !cross_phase && !killed) begin
        spectrum_read[0]<=spectrum0[k];spectrum_read[1]<=spectrum1[k];
        spectrum_read[2]<=spectrum2[k];spectrum_read[3]<=spectrum3[k];
      end
      if(cross_commit)
        cross_work[sum_bin_q]<={cross_sum_q,sum_re_q,sum_im_q};
      if(cold_rst_n && !killed && state==NORMALIZE && normal_phase==0 && k>=7 && k<=85)
        cross_read<=cross_work[k-7];
      // 全部1024点仍交付官方IP，工作集以外显式补零；取消后的真实drain继续。
      if(cold_rst_n && state==CONFIG) ip_half_data<=0;
      else if(cold_rst_n && state==RUN_IP && ip_input_valid && ip_input_ready) begin
        if(input_count<1023 && next_half_index>=7 && next_half_index<=85)
          ip_half_data<=phat_half[next_half_index-7];
        else ip_half_data<=0;
      end
    end
    // 保留原每两拍读bin；尾部提交落在NORMALIZE跳过0..6的空拍内。
    // 数据寄存器不清零，valid在冷复位/取消/事务或配对离开窗口时全部失效。
    always_ff @(posedge clk) begin
      if(!cold_rst_n || killed || (state!=CROSS && state!=NORMALIZE)) begin
        product_valid<=0;value_valid<=0;square_valid<=0;sum_valid<=0;
      end else begin
        product_valid<=state==CROSS && cross_phase;
        value_valid<=product_valid;
        square_valid<=value_valid;
        sum_valid<=square_valid;
        if(state==CROSS && cross_phase) begin
          product_arbr_q<=product_arbr;product_aibi_q<=product_aibi;
          product_aibr_q<=product_aibr;product_arbi_q<=product_arbi;
          product_bin_q<=7'(k-7);product_pair_q<=pair_id;
        end
        if(product_valid) begin
          cross_re_q<=cross_re_exact;cross_im_q<=cross_im_exact;
          value_bin_q<=product_bin_q;value_pair_q<=product_pair_q;
        end
        if(value_valid) begin
          cross_re_square_q<=cross_re_square;cross_im_square_q<=cross_im_square;
          square_re_q<=cross_re_q;square_im_q<=cross_im_q;
          square_bin_q<=value_bin_q;square_pair_q<=value_pair_q;
        end
        if(square_valid) begin
          // S102平方非负；先扩成U103再相加，不截进位、不改原精度。
          cross_sum_q<={1'b0,cross_re_square_q}+{1'b0,cross_im_square_q};
          sum_re_q<=square_re_q;sum_im_q<=square_im_q;
          sum_bin_q<=square_bin_q;sum_pair_q<=square_pair_q;
        end
      end
    end
    always_ff @(posedge clk) begin
      if(!cold_rst_n) begin
        cross_phase<=0;normal_phase<=0;math_phase<=0;
        delta_saved<=0;margin_saved<=0;solve_x_saved<=0;solve_y_saved<=0;angle_saved<=0;residue<=0;
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
        if(cross_commit && cross_sum_q>maximum_square) maximum_square<=cross_sum_q;
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
            k<=7;cross_phase<=0;normal_phase<=0;math_phase<=0;maximum_square<=0;mask_count<=0;pair_bad<=0;
            if(killed || first_error_code!=0) begin
              pair_state[pair_id*4+:4]<=killed ? CANCELLED : NUMERIC;
              backend_stage_state[pair_id*4+:4]<=killed ? CANCELLED : SKIPPED;
              backend_stage_state[(pair_id+6)*4+:4]<=killed ? CANCELLED : SKIPPED;
              backend_stage_state[(pair_id+12)*4+:4]<=killed ? CANCELLED : SKIPPED;
              pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;
            end else state<=CROSS;
          end
          CROSS: begin
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;cross_phase<=0;end
            else if(!cross_phase) cross_phase<=1;
            else begin
              cross_phase<=0;
              if(k==85) begin k<=0;normal_phase<=0;state<=NORMALIZE;end
              else k<=k+1;
            end
          end
          NORMALIZE: begin
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;pair_physically_retired[pair_id]<=1;state<=NEXT_PAIR;normal_phase<=0;end
            else case(normal_phase)
              0: begin
                if(k>=7 && k<=85) begin phat_half[k-7]<=0;normal_phase<=3;end
                else if(k==512) state<=PHAT_FINAL;
                else k<=k+1;
              end
              3: begin
                // 当前bin同步读出后才判mask/发PHAT，禁止读取未写空间。
                if(normal_square>0 && mask_scaled_square>={12'd0,maximum_square}) begin
                  mask_count<=mask_count+1;normal_phase<=1;
                end else begin normal_phase<=0;k<=k+1;end
              end
              1: if(phat_start) normal_phase<=2;
              2: if(phat_done) begin
                if(normalized[51] || normalized[24:0]==25'h1000000) begin
                  pair_bad<=1;if(first_error_code==0) first_error_code<=ERR_PHAT;
                end else phat_half[k-7]<=normalized[49:0];
                normal_phase<=0;
                if(k==512) state<=PHAT_FINAL;else k<=k+1;
              end
              default: normal_phase<=0;
            endcase
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
              if(output_count<=9) correlation[output_count+9]<=$signed(ip_output_data[24:0]);
              else if(output_count>=1015) correlation[output_count-1015]<=$signed(ip_output_data[24:0]);
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
            else if(lag==((pair_id==1 || pair_id==4) ? 8 : 6)) begin math_phase<=0;state<=LAG_FINAL;end
            else lag<=lag+1;
          end
          LAG_FINAL: begin
            if(killed) begin
              pair_state[pair_id*4+:4]<=CANCELLED;backend_stage_state[(pair_id+12)*4+:4]<=CANCELLED;
              math_phase<=0;state<=NEXT_PAIR;
            end else case(math_phase)
              0: if(alu_start) math_phase<=1;
              1: if(alu_done) begin delta_saved<=alu_result;math_phase<=2;end
              2: if(alu_start) math_phase<=3;
              3: if(alu_done) begin margin_saved<=alu_result;math_phase<=4;end
              4: begin
            taus[pair_id]<=tau;pair_tau_q12[pair_id*32+:32]<=tau[31:0];
            pair_peak_codes[pair_id*25+:25]<=peak;pair_margin_q15[pair_id*64+:64]<=margin[63:0];
            if(killed) begin pair_state[pair_id*4+:4]<=CANCELLED;backend_stage_state[(pair_id+12)*4+:4]<=CANCELLED;end
            else if(tau>((pair_id==1 || pair_id==4) ? 32425 : 22928) || tau< -((pair_id==1 || pair_id==4) ? 32425 : 22928)) begin
              pair_state[pair_id*4+:4]<=REJECTED;backend_stage_state[(pair_id+12)*4+:4]<=REJECTED;
            end else begin pair_state[pair_id*4+:4]<=OK;backend_stage_state[(pair_id+12)*4+:4]<=OK;pair_valid[pair_id]<=1;end
            state<=NEXT_PAIR;
                math_phase<=0;
              end
              default: math_phase<=0;
            endcase
          end
          NEXT_PAIR: begin
            if(pair_id==5) begin pair_id<=0;bx<=0;by<=0;sxx<=0;syy<=0;sxy<=0;valid_pairs<=0;math_phase<=0;state<=LS_ACC;end
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
              direction_reason<=killed ? 6 : (first_error_code!=0 ? 7 : (valid_pairs<3 ? 1 : 2));state<=FINISH;math_phase<=0;
            end else case(math_phase)
              0: if(alu_start) math_phase<=1;
              1: if(alu_done) begin solve_x_saved<=alu_result;math_phase<=2;end
              2: if(alu_start) math_phase<=3;
              3: if(alu_done) begin solve_y_saved<=alu_result;math_phase<=4;end
              4: begin
                math_phase<=0;
                if(solve_x< -4194304 || solve_x>4194303 || solve_y< -4194304 || solve_y>4194303) begin
                  backend_stage_state[18*4+:4]<=NUMERIC;
                  if(first_error_code==0) first_error_code<=ERR_CORDIC;state<=FINISH;
                end else begin ux_q20<=solve_x;uy_q20<=solve_y;residual_acc<=0;pair_id<=0;state<=LS_RESIDUAL;end
              end
              default: math_phase<=0;
            endcase
          end
          LS_RESIDUAL: begin
            if(killed) begin math_phase<=0;state<=FINISH;end
            else if(!pair_valid[pair_id]) begin
              if(pair_id==5) state<=GEOMETRY;else pair_id<=pair_id+1;
            end else case(math_phase)
              0: if(alu_start) math_phase<=1;
              1: if(alu_done) begin residue<=alu_result-wide_t'(taus[pair_id]);math_phase<=2;end
              2: begin
                // solve限制23位、tau限制32425：残差绝对值<2^18，32位完全精确。
                residual_acc<=residual_acc+residue_square;
                math_phase<=0;
                if(pair_id==5) state<=GEOMETRY;else pair_id<=pair_id+1;
              end
              default: math_phase<=0;
            endcase
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
              cx<=($signed(ux_q20)<0 ? -28'sd1*$signed(ux_q20) : 28'sd1*$signed(ux_q20))<<<norm_shift;
              cy<=($signed(ux_q20)<0 ? -28'sd1*$signed(uy_q20) : 28'sd1*$signed(uy_q20))<<<norm_shift;
              coffset<=ux_q20<0 ? (uy_q20>=0 ? 26'sd11796480 : -26'sd11796480) : 0;
              ca<=0;iteration<=0;state<=CORDIC_RUN;
            end
          end
          CORDIC_RUN: begin
            if(killed) state<=FINISH;
            else begin
              if(cy>0) begin cx<=cx+(cy>>>iteration);cy<=cy-(cx>>>iteration);ca<=ca+atan_rom(iteration);end
              else if(cy<0) begin cx<=cx-(cy>>>iteration);cy<=cy+(cx>>>iteration);ca<=ca-atan_rom(iteration);end
              if(iteration==23) begin math_phase<=0;state<=CORDIC_FINAL;end else iteration<=iteration+1;
            end
          end
          CORDIC_FINAL: begin
            if(killed) begin state<=FINISH;math_phase<=0;end
            else case(math_phase)
              0: if(alu_start) math_phase<=1;
              1: if(alu_done) begin angle_saved<=alu_result;math_phase<=2;end
              2: begin
                if(first_error_code==0) begin
                  angle_q8<=angle_rounded;angle_numerical_valid<=1;direction_reason<=0;backend_stage_state[19*4+:4]<=OK;
                end
                state<=FINISH;math_phase<=0;
              end
              default: math_phase<=0;
            endcase
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
