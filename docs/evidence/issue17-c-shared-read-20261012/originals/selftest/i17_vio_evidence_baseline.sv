`timescale 1ns/1ps
`default_nettype none
// 中文用途：真实 report/ABORT 独立保存，诊断逐字存后 ACK；VIO/ILA 导出不隐式删除。
module i17_vio_evidence_baseline (
    input wire clk, rst_n,
    input wire [4:0] action,
    input wire [31:0] read_select,
    input wire [159:0] context_config,
    input wire [95:0] map_config,
    input wire [7:0] controller_state, controller_error, manager_state,
    input wire [31:0] local_error, bank_counts,
    input wire [63:0] cycle,
    input wire report_valid, abort_valid,
    output wire report_ready, abort_ready,
    input wire [724:0] identity,
    input wire [6625:0] terminal,
    input wire frontend_abort_seen,
    input wire [724:0] frontend_abort_identity,
    input wire [179:0] frontend_abort_payload,
    input wire [63:0] policy,
    input wire [17:0] raw_angle,
    input wire [8:0] command_angle, servo_angle,
    input wire map_valid, numerical_valid, delivery_eligible, qualified_delivery,
    input wire current_qualified, servo_command_valid, servo_accept, servo_reject,
    input wire [3:0] servo_reject_reason,
    input wire [7:0] first_error,
    input wire export_valid,
    input wire [31:0] export_data,
    input wire [2:0] export_bank,
    input wire [63:0] export_seq,
    input wire [5:0] export_word, export_words,
    input wire export_last,
    output reg export_select,
    output reg [2:0] export_select_bank,
    output reg export_ack,
    output reg [63:0] export_ack_seq,
    output reg [5:0] export_ack_word,
    output reg export_abort,
    output reg report_full, abort_full, diag_full, diag_partial,
    output wire empty, busy,
    output reg [7:0] error_code,
    output wire [63:0] result,
    output reg [31:0] read_data,
    output reg [127:0] read_meta,
    output reg [255:0] ila_sample
);
    reg report_pending;
    reg [724:0] report_identity, report_abort_identity, backend_identity;
    reg [6625:0] report_terminal;
    reg [179:0] report_abort_payload;
    reg [511:0] report_header;
    reg [191:0] backend_header;
    reg [159:0] report_context;
    reg [95:0] report_map;
    reg [31:0] diag_mem [0:63];
    reg [63:0] report_seq, backend_seq, next_seq, diag_seq;
    reg sequence_exhausted;
    reg [5:0] diag_words, expected_word;
    reg [6:0] captured_words;
    reg [2:0] diag_bank, fetch_state;
    reg [3:0] dump_type;
    reg [7:0] dump_word, dump_words;
    reg [63:0] dump_seq;
    reg dumping;
    reg [8:0] dumped;
    reg [127:0] live_snapshot;
    wire [127:0] live_status={error_code,controller_error,manager_state,controller_state,local_error,bank_counts,
        28'd0,diag_partial,diag_full,abort_full,report_full};
    wire report_fire = report_valid && report_ready;
    wire abort_fire = abort_valid && abort_ready;
    assign report_ready = rst_n && !report_full && !report_pending && !sequence_exhausted;
    assign abort_ready = rst_n && !abort_full && !sequence_exhausted &&
                         !(report_fire && next_seq==64'hffffffffffffffff);
    wire [64:0] sequence_next={1'b0,next_seq}+{64'd0,report_fire}+{64'd0,abort_fire};
    assign empty = !report_full && !report_pending && !abort_full && !diag_full && !diag_partial && bank_counts==0;
    assign busy = dumping || fetch_state!=0 || report_pending;
    assign result = report_full ? report_header[191:128] : 64'd0;
    wire [3:0] selected_type = read_select[3:0];
    wire [2:0] selected_bank = read_select[6:4];
    wire [7:0] selected_word = read_select[15:8];
    wire select_legal = read_select[31:16]==0 && !read_select[7] && selected_type<=9;
    // 每类记录均按最低有效 32 位先出；尾字补零，无内容截断。
    function automatic [7:0] words_for(input [3:0] kind);
        case(kind)
            0: words_for=8; 1: words_for=16; 2: words_for=23;
            3: words_for=208; 4: words_for=6; 5: words_for={1'b0,captured_words};
            6: words_for=23; 7: words_for=23; 8: words_for=6; 9: words_for=4;
            default: words_for=0;
        endcase
    endfunction
    function automatic valid_for(input [3:0] kind);
        case(kind)
            0,1,2,3,4,6: valid_for=report_full;
            5: valid_for=diag_full || diag_partial;
            7,8: valid_for=abort_full;
            9: valid_for=1'b1;
            default: valid_for=0;
        endcase
    endfunction
    function automatic [63:0] seq_for(input [3:0] kind);
        if(kind==9) seq_for=0;
        else if(kind==5) seq_for=diag_seq;
        else if(kind==7 || kind==8) seq_for=backend_seq;
        else seq_for=report_seq;
    endfunction
    // 先在各记录内选32位，再按类型选择，避免先构造6656位宽的类型多路器。
    function automatic [31:0] word_for(input [3:0] kind,input [7:0] index);
        reg [255:0] config_words;
        reg [735:0] identity_words, abort_identity_words, backend_identity_words;
        reg [6655:0] terminal_words;
        reg [191:0] abort_payload_words;
        begin
            config_words={report_map,report_context};
            identity_words={11'd0,report_identity};
            abort_identity_words={11'd0,report_abort_identity};
            backend_identity_words={11'd0,backend_identity};
            terminal_words={30'd0,report_terminal};
            abort_payload_words={12'd0,report_abort_payload};
            word_for=32'd0;
            // 每个if保留未知/越界index返回0；diag读取不以captured_words截短。
            case(kind)
                0: if(index<8) word_for=config_words[index[2:0]*32+:32];
                1: if(index<16) word_for=report_header[index[3:0]*32+:32];
                2: if(index<23) word_for=identity_words[index[4:0]*32+:32];
                3: if(index<208) word_for=terminal_words[index*32+:32];
                4: if(index<6) word_for=abort_payload_words[index[2:0]*32+:32];
                5: if(index<64) word_for=diag_mem[index[5:0]];
                6: if(index<23) word_for=abort_identity_words[index[4:0]*32+:32];
                7: if(index<23) word_for=backend_identity_words[index[4:0]*32+:32];
                8: if(index<6) word_for=backend_header[index[2:0]*32+:32];
                9: if(index<4) word_for=live_snapshot[index[1:0]*32+:32];
                default: begin end
            endcase
        end
    endfunction
    // meta: seq[63:0], type[67:64], word[75:68], words[83:76], valid84,
    // last85, partial86, bank[89:87], error[97:90], reserved[127:98].
    function automatic [127:0] meta_for(input [3:0] kind,input [7:0] index);
        reg [127:0] m;
        begin
            m=0; m[63:0]=seq_for(kind); m[67:64]=kind; m[75:68]=index;
            m[83:76]=words_for(kind); m[84]=valid_for(kind) && index<words_for(kind);
            m[85]=index==words_for(kind)-1; m[86]=(kind==5 && diag_partial);
            m[89:87]=(kind==5 ? diag_bank : 3'd0); m[97:90]=error_code; meta_for=m;
        end
    endfunction
    always @(posedge clk) begin
        if(!rst_n) begin
            report_full<=0; abort_full<=0; diag_full<=0; diag_partial<=0; report_pending<=0;
            next_seq<=0; report_seq<=0; backend_seq<=0; diag_seq<=0;
            sequence_exhausted<=0;
            diag_words<=0; captured_words<=0; expected_word<=0; diag_bank<=0; fetch_state<=0;
            dumping<=0; dump_type<=0; dump_word<=0; dump_words<=0; dump_seq<=0; dumped<=0;
            export_select<=0; export_select_bank<=0; export_ack<=0; export_ack_seq<=0;
            export_ack_word<=0; export_abort<=0; error_code<=0; read_data<=0; read_meta<=0; ila_sample<=0;
            report_identity<=0; report_abort_identity<=0; backend_identity<=0;
            report_terminal<=0; report_abort_payload<=0; report_header<=0; backend_header<=0;
            report_context<=0; report_map<=0;
            live_snapshot<=0;
        end else begin
            export_select<=0; export_ack<=0; export_abort<=0; ila_sample<=0;
            // report ACK 当拍保存事实；后一拍取运行时 gate 的注册 accept/reject。
            if(report_fire) begin
                report_pending<=1; report_seq<=next_seq; report_identity<=identity;
                report_terminal<=terminal; report_abort_identity<=frontend_abort_identity;
                report_abort_payload<=frontend_abort_payload; report_context<=context_config; report_map<=map_config;
                report_header<=0;
                report_header[63:0]<=cycle; report_header[127:64]<=policy;
                report_header[145:128]<=raw_angle; report_header[154:146]<=command_angle;
                report_header[173:164]<={first_error,frontend_abort_seen,servo_command_valid};
                report_header[179:174]<={current_qualified,qualified_delivery,delivery_eligible,numerical_valid,map_valid,1'b1};
                report_header[223:192]<=local_error; report_header[255:224]<=bank_counts;
                report_header[263:256]<=controller_state; report_header[271:264]<=manager_state;
                report_header[279:272]<=controller_error;
                dumped[0]<=0; dumped[1]<=0; dumped[2]<=0; dumped[3]<=0; dumped[4]<=0; dumped[6]<=0;
            end
            if(report_pending) begin
                report_pending<=0; report_full<=1;
                report_header[163:155]<=servo_angle;
                report_header[185:180]<={servo_reject_reason,servo_reject,servo_accept};
            end
            if(abort_fire) begin
                abort_full<=1; backend_identity<=identity;
                backend_seq<=next_seq+{63'd0,report_fire};
                backend_header<=0; backend_header[63:0]<=cycle;
                backend_header[71:64]<=first_error; backend_header[103:72]<=local_error;
                backend_header[111:104]<=manager_state; backend_header[119:112]<=controller_state;
                backend_header[127:120]<=controller_error; dumped[7]<=0; dumped[8]<=0;
            end
            if(report_fire || abort_fire) begin
                if(sequence_next[64]) begin next_seq<=64'hffffffffffffffff; sequence_exhausted<=1; end
                else next_seq<=sequence_next[63:0];
            end
            if(sequence_exhausted && (report_valid || abort_valid)) error_code<=8'h39;
            // FETCH: SELECT -> 数据检查/保存 -> ACK -> 一个低电平间隔 -> 下一字。
            case(fetch_state)
                1: fetch_state<=2;
                2: if(export_valid) begin
                    if(export_bank!=diag_bank || export_word!=expected_word || export_words==0 ||
                        (expected_word!=0 && (export_seq!=diag_seq || export_words!=diag_words)) ||
                        export_last!=(export_word==export_words-1)) begin
                        error_code<=8'h31; diag_partial<=1; fetch_state<=0;
                    end else begin
                        diag_mem[expected_word]<=export_data;
                        captured_words<={1'b0,expected_word}+7'd1;
                        if(expected_word==0) begin diag_seq<=export_seq; diag_words<=export_words; end
                        export_ack_seq<=export_seq; export_ack_word<=export_word;
                        diag_partial<=1; fetch_state<=3;
                    end
                end
                3: begin export_ack<=1; fetch_state<=4; end
                4: begin
                    if(expected_word==diag_words-1) begin diag_full<=1; diag_partial<=0; fetch_state<=0; end
                    else begin expected_word<=expected_word+1'b1; fetch_state<=5; end
                end
                5: fetch_state<=2;
                default: begin end
            endcase
            if(dumping) begin
                ila_sample[31:0]<=word_for(dump_type,dump_word);
                ila_sample[159:32]<=meta_for(dump_type,dump_word);
                ila_sample[223:160]<=cycle; ila_sample[255:224]<=32'h49313744;
                if(dump_word==dump_words-1) begin
                    dumping<=0;
                    if(dump_type<9) dumped[dump_type]<=1;
                end
                else dump_word<=dump_word+1'b1;
            end
            if(action!=0) begin
                if((action & (action-5'd1))!=0) error_code<=8'h32;
                else if(action[4]) begin
                    // 终止读取不丢 core 原始 head；本地部分副本仍保留，必须显式释放。
                    export_abort<=1; fetch_state<=0;
                end else if(busy || !select_legal) error_code<=8'h33;
                else if(action[0]) begin
                    if(selected_type==9 && selected_word<4) read_data<=live_status[selected_word*32+:32];
                    else read_data<=word_for(selected_type,selected_word);
                    read_meta<=meta_for(selected_type,selected_word);
                    if(!valid_for(selected_type) || selected_word>=words_for(selected_type)) error_code<=8'h34;
                end else if(action[1]) begin
                    if(selected_type!=5 || diag_full || diag_partial || selected_bank>4 || export_valid) error_code<=8'h35;
                    else if((selected_bank==0 && bank_counts[6:0]==0) ||
                            (selected_bank==1 && bank_counts[10:7]==0) ||
                            (selected_bank==2 && bank_counts[14:11]==0) ||
                            (selected_bank==3 && bank_counts[18:15]==0) ||
                            (selected_bank==4 && bank_counts[22:19]==0)) error_code<=8'h36;
                    else begin
                        export_select<=1; export_select_bank<=selected_bank; diag_bank<=selected_bank;
                        expected_word<=0; diag_words<=0; captured_words<=0; fetch_state<=1; dumped[5]<=0;
                    end
                end else if(action[2]) begin
                    if(valid_for(selected_type) && words_for(selected_type)!=0) begin
                        dumping<=1; dump_type<=selected_type; dump_word<=0;
                        dump_words<=words_for(selected_type); dump_seq<=seq_for(selected_type);
                        if(selected_type==9) live_snapshot<=live_status;
                    end else error_code<=8'h37;
                end else if(action[3]) begin
                    case(selected_type)
                        0,1,2,3,4,6: if(report_full && (&{dumped[6],dumped[4:0]})) report_full<=0;
                                     else error_code<=8'h38;
                        5: if((diag_full || diag_partial) && (dumped[5] || captured_words==0) && !export_valid) begin diag_full<=0; diag_partial<=0; end
                           else error_code<=8'h38;
                        7,8: if(abort_full && dumped[7] && dumped[8]) abort_full<=0;
                             else error_code<=8'h38;
                        default: error_code<=8'h38;
                    endcase
                end
            end
        end
    end
endmodule
`default_nettype wire
