`timescale 1ns/1ps
// NP-1.0: one same-clock development reader; ends at FFT_INPUT.
module pcm4_numeric_preprocess #(
    parameter HANN_FILE = "hann-u18f17.mem"
) (
    input wire clk, cold_rst_n,
    input wire research_profile_valid,
    input wire desc_valid, output wire desc_ready,
    input wire [63:0] desc_token, desc_generation,
    input wire [431:0] desc_first, input wire [164:0] desc_context,
    output wire rd_valid, input wire rd_ready,
    output wire [63:0] rd_token, rd_generation,
    output wire [164:0] rd_context, output wire [9:0] rd_index,
    input wire rd_rsp_valid, output wire rd_rsp_ready,
    input wire [63:0] rd_rsp_token, rd_rsp_generation,
    input wire [164:0] rd_rsp_context, input wire [9:0] rd_rsp_index,
    input wire [1:0] rd_rsp_status,
    input wire [431:0] rd_rsp_payload, input wire rd_rsp_origin,
    output wire reader_close_valid, input wire reader_close_ready,
    output wire [63:0] reader_close_token, reader_close_generation,
    output wire reader_no_future_access,
    input wire binding_valid,
    input wire [63:0] bound_token, bound_generation,
    input wire [164:0] current_context,
    input wire new_work_allowed, local_cancel_now, pending_cancel,
    input wire first_error_valid, input wire [7:0] first_error_code,
    input wire data_clear_req_valid, output wire data_clear_req_ready,
    output wire fft_valid, input wire fft_ready,
    output wire fft_domain, output wire [1:0] fft_channel,
    output wire [9:0] fft_index,
    output wire signed [28:0] fft_real, fft_imag,
    output wire fft_numeric_valid, fft_overflow, fft_last,
    output wire [63:0] fft_token, fft_generation,
    output wire [164:0] fft_context, output wire [431:0] fft_frame_first,
    output wire report_valid, input wire report_ready,
    output wire [2001:0] report_payload,
    output wire abort_valid, input wire abort_ready,
    output wire [2079:0] abort_payload,
    output wire busy, read_pending
);
    localparam logic [3:0] IDLE=0, READ_REQ=1, READ_WAIT=2, MEAN=3,
        LOAD=4, CALCULATE=5, SEND=6, DRAIN=7, QUIET=8, CLOSE=9,
        BUILD_REPORT=10, WAIT_REPORT=11;
    localparam logic [2:0] UNIT_PENDING=0, UNIT_OK=1,
        UNIT_ABORTED=2, UNIT_ERROR=3;
    localparam logic [7:0] ERR_NONE=0, ERR_PROFILE=1,
        ERR_DESC_TUPLE=2, ERR_DESC_RAW=3, ERR_UNREQUESTED_RSP=4,
        ERR_RSP_TUPLE=5, ERR_RSP_STATUS=6, ERR_ROW_IDENTITY=7,
        ERR_ROW_ID_RANGE=8, ERR_ROW_LAST=9, ERR_PCM_EXTENSION=10,
        ERR_COEFFICIENT=11, ERR_MEAN_RANGE=12, ERR_GATE_RANGE=13,
        ERR_DOA_RANGE=14, ERR_BINDING=15, ERR_FSM=16, ERR_COUNTER=17;

    // Fields concatenate in declaration order, MSB first. Full external layout
    // and the twelve status/count lane orders are in NUMERIC-CONTRACT.md.
    typedef struct packed {
        logic [63:0] token, generation;
        logic [164:0] context_tag;
        logic [431:0] frame_first;
        logic [35:0] unit_status;
        logic [95:0] mean_s24;
        logic [87:0] output_counts;
        logic [31:0] read_requests, read_responses, read_terminals;
        logic [10:0] qualified_rows;
        logic [13:0] generated, qualified, transferred_on_abort;
        logic [13:0] unsent_cancelled, not_generated;
        logic aborted, close_done, protocol_error, numeric_error, profile_valid;
        logic [7:0] cancel_reasons, error_code;
        logic caller_error_valid;
        logic [7:0] caller_error_code;
        logic [11:0] abort_units;
        logic signed [43:0] first_fault_value;
        logic first_fault_domain;
        logic [1:0] first_fault_channel;
        logic [9:0] first_fault_index;
        logic signed [23:0] first_fault_pcm;
        logic [17:0] first_fault_coefficient;
        logic bad_rsp_valid;
        logic [63:0] bad_rsp_token, bad_rsp_generation;
        logic [164:0] bad_rsp_context;
        logic [9:0] bad_rsp_index;
        logic [1:0] bad_rsp_status;
        logic bad_rsp_origin;
        logic [431:0] bad_rsp_payload;
    } report_t;
    typedef struct packed {
        report_t at_edge;
        logic held_valid, held_domain;
        logic [1:0] held_channel;
        logic [9:0] held_index;
        logic signed [28:0] held_real, held_imag;
        logic held_numeric_valid, held_overflow, held_last;
        logic response_on_abort, read_on_abort, pending_after_edge;
    } abort_t;

    // Logical capacity, not an assertion about physical BRAM mapping. Neither
    // PCM nor coefficient memory is cleared by runtime/cold control reset.
    logic [95:0] pcm_ram [0:1023];
    logic [17:0] hann_rom [0:1023];
    integer rom_i;
    initial begin
        // Missing/short files leave an illegal coefficient, never a silent zero.
        for (rom_i=0; rom_i<1024; rom_i=rom_i+1)
            hann_rom[rom_i]=18'h3ffff;
        $readmemh(HANN_FILE, hann_rom);
    end

    logic [3:0] state_q;
    logic [63:0] token_q, generation_q;
    logic [164:0] context_q;
    logic [431:0] first_q;
    logic read_pending_q, cancelled_q, close_done_q, profile_q;
    logic [9:0] read_index_q;
    logic [31:0] requests_q, responses_q, terminals_q;
    logic [10:0] rows_q;
    logic signed [33:0] sums_q [0:3];
    logic signed [23:0] means_q [0:3];
    logic [1:0] mean_channel_q;
    logic [35:0] statuses_q;
    logic [87:0] output_counts_q;
    logic [11:0] abort_units_q;
    logic [13:0] generated_q, qualified_q, transfer_abort_q;
    logic [7:0] cancel_reasons_q, error_code_q;
    logic protocol_error_q, numeric_error_q, caller_error_q;
    logic [7:0] caller_code_q;
    logic signed [43:0] fault_value_q;
    logic fault_domain_q;
    logic [1:0] fault_channel_q;
    logic [9:0] fault_index_q;
    logic signed [23:0] fault_pcm_q;
    logic [17:0] fault_coefficient_q;
    logic bad_rsp_q;
    logic [63:0] bad_token_q, bad_generation_q;
    logic [164:0] bad_context_q;
    logic [9:0] bad_index_q;
    logic [1:0] bad_status_q;
    logic bad_origin_q;
    logic [431:0] bad_payload_q;
    logic out_domain_q;
    logic [1:0] out_channel_q;
    logic [9:0] out_index_q;
    logic signed [23:0] pcm_q;
    logic [17:0] coefficient_q;
    logic fft_valid_q;
    logic signed [28:0] fft_real_q;
    logic report_valid_q, abort_valid_q;
    report_t report_q, report_live, abort_edge_report;
    abort_t abort_q;

    wire active = state_q!=IDLE && state_q!=WAIT_REPORT;
    wire before_close = active && !close_done_q && state_q!=CLOSE;
    wire desc_fire = desc_valid && desc_ready;
    wire request_fire = rd_valid && rd_ready;
    wire response_fire = rd_rsp_valid && rd_rsp_ready;
    wire close_fire = reader_close_valid && reader_close_ready;
    wire fft_fire = fft_valid && fft_ready;
    wire clear_fire = data_clear_req_valid && data_clear_req_ready;
    wire response_echo = read_pending_q && rd_rsp_token==token_q &&
        rd_rsp_generation==generation_q && rd_rsp_context==context_q &&
        rd_rsp_index==read_index_q;
    wire terminal_fire = response_fire && response_echo;
    wire [64:0] response_id = {1'b0,first_q[129:66]} + {55'd0,read_index_q};
    wire [64:0] frame_end = {1'b0,first_q[129:66]} + 65'd1023;
    wire [64:0] descriptor_end = {1'b0,desc_first[129:66]} + 65'd1023;
    wire tuple_current = binding_valid && bound_token==token_q &&
        bound_generation==generation_q && current_context==context_q;
    wire descriptor_tuple = binding_valid && desc_token!=0 && desc_generation!=0 &&
        desc_token==bound_token && desc_generation==bound_generation &&
        desc_context==current_context && desc_context[164:163]==2'd1 &&
        desc_context[162] && desc_context[97] && desc_context[32] &&
        desc_context[31:0]==desc_first[235:204];

    assign desc_ready=cold_rst_n && state_q==IDLE &&
        !report_valid_q && !abort_valid_q && !data_clear_req_valid;
    // The pre-edge offer may really fire on the cancellation edge. It is then
    // a drain obligation, never an excuse to synthesize a response or close.
    assign rd_valid=cold_rst_n && state_q==READ_REQ && !cancelled_q && !read_pending_q;
    assign rd_token=token_q;
    assign rd_generation=generation_q;
    assign rd_context=context_q;
    assign rd_index=read_index_q;
    // Unexpected responses are ACKed/audited while active. Only an exact echo
    // of the actually accepted request terminates its outstanding obligation.
    assign rd_rsp_ready=cold_rst_n && active;
    assign reader_close_valid=cold_rst_n && state_q==CLOSE &&
        !read_pending_q && !fft_valid_q && !close_done_q;
    assign reader_close_token=token_q;
    assign reader_close_generation=generation_q;
    assign reader_no_future_access=reader_close_valid &&
        (cancelled_q || (qualified_q==14'd8192 && rows_q==11'd1024));
    assign data_clear_req_ready=cold_rst_n && active && !cancelled_q;
    assign fft_valid=cold_rst_n && fft_valid_q;
    assign fft_domain=out_domain_q;
    assign fft_channel=out_channel_q;
    assign fft_index=out_index_q;
    assign fft_real=fft_real_q;
    assign fft_imag=29'sd0;
    assign fft_numeric_valid=1'b1; // Valid is withdrawn on internal numeric failure.
    assign fft_overflow=1'b0;
    assign fft_last=(out_index_q==10'd1023);
    assign fft_token=token_q;
    assign fft_generation=generation_q;
    assign fft_context=context_q;
    assign fft_frame_first=first_q;
    assign report_valid=cold_rst_n && report_valid_q;
    assign report_payload=report_q;
    assign abort_valid=cold_rst_n && abort_valid_q;
    assign abort_payload=abort_q;
    assign busy=cold_rst_n && (state_q!=IDLE || report_valid_q || abort_valid_q);
    assign read_pending=cold_rst_n && read_pending_q;

    function automatic logic extension_ok(input logic [127:0] pcm);
        integer c;
        begin
            extension_ok=1'b1;
            for(c=0;c<4;c=c+1)
                if(pcm[c*32+24 +:8]!={8{pcm[c*32+23]}})
                    extension_ok=1'b0;
        end
    endfunction

    // Extra absolute-value bit handles the minimum signed source exactly.
    function automatic logic signed [43:0] rne_shift(
        input logic signed [43:0] value, input integer shift
    );
        logic signed [44:0] wide;
        logic [44:0] magnitude, quotient, remainder, half;
        begin
            wide={value[43],value};
            magnitude=value[43] ? $unsigned(-wide) : $unsigned(wide);
            quotient=magnitude>>shift;
            remainder=magnitude & ((45'd1<<shift)-45'd1);
            half=45'd1<<(shift-1);
            if(remainder>half || (remainder==half && quotient[0]))
                quotient=quotient+45'd1;
            wide=value[43] ? -$signed(quotient) : $signed(quotient);
            rne_shift=wide[43:0];
        end
    endfunction

    logic signed [24:0] centered;
    logic signed [43:0] product_value, rounded_value, mean_value;
    logic signed [23:0] saturated_doa;
    logic signed [28:0] fft_candidate;
    logic coefficient_ok, mean_range_bad, gate_range_bad, doa_range_bad;
    logic next_domain;
    logic [1:0] next_channel;
    logic [9:0] next_index;
    logic [3:0] output_instance, status_instance;
    always_comb begin
        centered=$signed({pcm_q[23],pcm_q}) -
            $signed({means_q[out_channel_q][23],means_q[out_channel_q]});
        if(out_domain_q)
            product_value=$signed(pcm_q)*$signed({1'b0,coefficient_q});
        else
            product_value=$signed(centered)*$signed({1'b0,coefficient_q});
        rounded_value=rne_shift(product_value,17);
        mean_value=rne_shift($signed({{10{sums_q[mean_channel_q][33]}},sums_q[mean_channel_q]}),10);
        // Case equality to a known comparison value fails closed in simulation
        // for a malformed/unknown ROM word; hardware uses the unsigned range.
        coefficient_ok=((coefficient_q<=18'd131072)===1'b1);
        mean_range_bad=mean_value < -44'sd8388608 || mean_value > 44'sd8388607;
        gate_range_bad=rounded_value < -44'sd16777216 || rounded_value > 44'sd16777215;
        doa_range_bad=rounded_value < -44'sd8388608 || rounded_value > 44'sd8388607;
        if(rounded_value < -44'sd8388608) saturated_doa=-24'sd8388608;
        else if(rounded_value > 44'sd8388607) saturated_doa=24'sd8388607;
        else saturated_doa=rounded_value[23:0];
        // Exact concatenation after range checks; no early S25-to-S24 clamp.
        fft_candidate=out_domain_q ? {saturated_doa[23],saturated_doa,4'b0} :
            {rounded_value[24:0],4'b0};
        next_domain=out_domain_q;
        next_channel=out_channel_q;
        next_index=out_index_q+10'd1;
        if(out_index_q==10'd1023) begin
            next_index=0;
            next_channel=out_channel_q+2'd1;
            if(out_channel_q==2'd3) begin next_channel=0; next_domain=1'b1; end
        end
        output_instance={out_domain_q,out_channel_q};
        status_instance=4'd4+{1'b0,out_domain_q,out_channel_q};
    end

    logic [7:0] response_error, fault_now;
    logic fault_numeric;
    logic [11:0] unfinished;
    logic [7:0] reasons_now;
    logic abort_event;
    integer u;
    always_comb begin
        response_error=ERR_NONE;
        if(response_fire) begin
            if(!read_pending_q) response_error=ERR_UNREQUESTED_RSP;
            else if(!response_echo) response_error=ERR_RSP_TUPLE;
            else if(rd_rsp_origin || rd_rsp_status!=2'd0) response_error=ERR_RSP_STATUS;
            else if(rd_rsp_payload[139:130]!=read_index_q ||
                    rd_rsp_payload[235:140]!=first_q[235:140] ||
                    rd_rsp_payload[129:1]!=first_q[129:1]) response_error=ERR_ROW_IDENTITY;
            else if(frame_end[64] || response_id[64] ||
                    frame_end[63:0]!=rd_rsp_payload[65:2] ||
                    response_id[63:0]!=rd_rsp_payload[303:240]) response_error=ERR_ROW_ID_RANGE;
            else if(rd_rsp_payload[0]!=(read_index_q==10'd1023)) response_error=ERR_ROW_LAST;
            else if(!extension_ok(rd_rsp_payload[431:304])) response_error=ERR_PCM_EXTENSION;
        end
        fault_now=ERR_NONE;
        fault_numeric=1'b0;
        if(desc_fire) begin
            if(!descriptor_tuple) fault_now=ERR_DESC_TUPLE;
            else if(desc_first[139:130]!=0 || desc_first[0] || descriptor_end[64] ||
                    descriptor_end[63:0]!=desc_first[65:2] ||
                    desc_first[303:240]!=desc_first[129:66] ||
                    !extension_ok(desc_first[431:304])) fault_now=ERR_DESC_RAW;
            else if(!research_profile_valid) fault_now=ERR_PROFILE;
        end else if(active) begin
            if(!close_done_q && !tuple_current) fault_now=ERR_BINDING;
            else if(response_error!=ERR_NONE) fault_now=response_error;
            else if(!research_profile_valid && !cancelled_q) fault_now=ERR_PROFILE;
            else if(state_q==MEAN && mean_range_bad) begin fault_now=ERR_MEAN_RANGE; fault_numeric=1'b1; end
            else if(state_q==CALCULATE && !coefficient_ok) begin fault_now=ERR_COEFFICIENT; fault_numeric=1'b1; end
            else if(state_q==CALCULATE && !out_domain_q && gate_range_bad) begin fault_now=ERR_GATE_RANGE; fault_numeric=1'b1; end
            else if(state_q==CALCULATE && out_domain_q && doa_range_bad) begin fault_now=ERR_DOA_RANGE; fault_numeric=1'b1; end
            else if((response_fire && responses_q==32'hffff_ffff) ||
                    (terminal_fire && terminals_q==32'hffff_ffff)) fault_now=ERR_COUNTER;
            else if(state_q>WAIT_REPORT) fault_now=ERR_FSM;
        end
        for(u=0;u<12;u=u+1)
            unfinished[u]=(statuses_q[u*3 +:3]!=UNIT_OK);
        reasons_now=8'd0;
        if(local_cancel_now) reasons_now[0]=1'b1;
        if(pending_cancel) reasons_now[1]=1'b1;
        if(first_error_valid) reasons_now[2]=1'b1;
        if((before_close || desc_fire) && !new_work_allowed) reasons_now[3]=1'b1;
        if(clear_fire) reasons_now[4]=1'b1;
        if((active || desc_fire) && !research_profile_valid) reasons_now[5]=1'b1;
        if(fault_now!=ERR_NONE && fault_now!=ERR_PROFILE)
            if(fault_numeric) reasons_now[7]=1'b1; else reasons_now[6]=1'b1;
        abort_event=(active || desc_fire) && (desc_fire || !cancelled_q) &&
            (reasons_now!=0 || fault_now!=ERR_NONE);
    end

    // The live view is latched only after actual close. The abort copy is
    // independently latched at E and remains immutable through its own stall.
    integer c;
    always_comb begin
        report_live='0;
        report_live.token=token_q;
        report_live.generation=generation_q;
        report_live.context_tag=context_q;
        report_live.frame_first=first_q;
        report_live.unit_status=statuses_q;
        for(c=0;c<4;c=c+1) report_live.mean_s24[c*24 +:24]=means_q[c];
        report_live.output_counts=output_counts_q;
        report_live.read_requests=requests_q;
        report_live.read_responses=responses_q;
        report_live.read_terminals=terminals_q;
        report_live.qualified_rows=rows_q;
        report_live.generated=generated_q;
        report_live.qualified=qualified_q;
        report_live.transferred_on_abort=transfer_abort_q;
        report_live.unsent_cancelled=cancelled_q ? generated_q-qualified_q-transfer_abort_q : 14'd0;
        report_live.not_generated=14'd8192-generated_q;
        report_live.aborted=cancelled_q;
        report_live.close_done=close_done_q;
        report_live.protocol_error=protocol_error_q;
        report_live.numeric_error=numeric_error_q;
        report_live.profile_valid=profile_q;
        report_live.cancel_reasons=cancel_reasons_q;
        report_live.error_code=error_code_q;
        report_live.caller_error_valid=caller_error_q;
        report_live.caller_error_code=caller_code_q;
        report_live.abort_units=abort_units_q;
        report_live.first_fault_value=fault_value_q;
        report_live.first_fault_domain=fault_domain_q;
        report_live.first_fault_channel=fault_channel_q;
        report_live.first_fault_index=fault_index_q;
        report_live.first_fault_pcm=fault_pcm_q;
        report_live.first_fault_coefficient=fault_coefficient_q;
        report_live.bad_rsp_valid=bad_rsp_q;
        report_live.bad_rsp_token=bad_token_q;
        report_live.bad_rsp_generation=bad_generation_q;
        report_live.bad_rsp_context=bad_context_q;
        report_live.bad_rsp_index=bad_index_q;
        report_live.bad_rsp_status=bad_status_q;
        report_live.bad_rsp_origin=bad_origin_q;
        report_live.bad_rsp_payload=bad_payload_q;
        abort_edge_report=report_live;
        if(desc_fire) begin
            // IDLE retains old diagnostics; a newly accepted descriptor must
            // never acquire that previous tuple or status in its abort record.
            abort_edge_report='0;
            abort_edge_report.token=desc_token;
            abort_edge_report.generation=desc_generation;
            abort_edge_report.context_tag=desc_context;
            abort_edge_report.frame_first=desc_first;
            abort_edge_report.profile_valid=research_profile_valid;
            abort_edge_report.not_generated=14'd8192;
        end
        abort_edge_report.aborted=1'b1;
        abort_edge_report.cancel_reasons=reasons_now;
        abort_edge_report.abort_units=desc_fire ? 12'hfff : unfinished;
        abort_edge_report.read_requests=desc_fire ? 32'd0 : requests_q+{31'd0,request_fire};
        abort_edge_report.read_responses=desc_fire ? 32'd0 :
            ((responses_q==32'hffff_ffff) ? responses_q : responses_q+{31'd0,response_fire});
        abort_edge_report.read_terminals=desc_fire ? 32'd0 :
            ((terminals_q==32'hffff_ffff) ? terminals_q : terminals_q+{31'd0,terminal_fire});
        abort_edge_report.transferred_on_abort=desc_fire ? 14'd0 : transfer_abort_q+{13'd0,fft_fire};
        abort_edge_report.unsent_cancelled=abort_edge_report.generated-
            abort_edge_report.qualified-abort_edge_report.transferred_on_abort;
        if(fault_now!=ERR_NONE && (desc_fire || error_code_q==ERR_NONE)) begin
            abort_edge_report.error_code=fault_now;
            abort_edge_report.numeric_error=fault_numeric;
            abort_edge_report.protocol_error=!fault_numeric && fault_now!=ERR_PROFILE;
            abort_edge_report.first_fault_domain=out_domain_q;
            abort_edge_report.first_fault_channel=(state_q==MEAN) ? mean_channel_q : out_channel_q;
            abort_edge_report.first_fault_index=out_index_q;
            abort_edge_report.first_fault_pcm=pcm_q;
            abort_edge_report.first_fault_coefficient=coefficient_q;
            abort_edge_report.first_fault_value=(state_q==MEAN) ? mean_value :
                ((fault_now==ERR_COEFFICIENT) ? product_value : rounded_value);
            if(desc_fire) begin
                abort_edge_report.first_fault_value=44'sd0;
                abort_edge_report.first_fault_domain=1'b0;
                abort_edge_report.first_fault_channel=2'd0;
                abort_edge_report.first_fault_index=10'd0;
                abort_edge_report.first_fault_pcm=desc_first[327:304];
                abort_edge_report.first_fault_coefficient=18'd0;
            end
        end
        if(first_error_valid && (desc_fire || !caller_error_q)) begin
            abort_edge_report.caller_error_valid=1'b1;
            abort_edge_report.caller_error_code=first_error_code;
        end
        if(!research_profile_valid) abort_edge_report.profile_valid=1'b0;
        if(response_error!=ERR_NONE && !bad_rsp_q) begin
            abort_edge_report.bad_rsp_valid=1'b1;
            abort_edge_report.bad_rsp_token=rd_rsp_token;
            abort_edge_report.bad_rsp_generation=rd_rsp_generation;
            abort_edge_report.bad_rsp_context=rd_rsp_context;
            abort_edge_report.bad_rsp_index=rd_rsp_index;
            abort_edge_report.bad_rsp_status=rd_rsp_status;
            abort_edge_report.bad_rsp_origin=rd_rsp_origin;
            abort_edge_report.bad_rsp_payload=rd_rsp_payload;
        end
    end

    integer lane, unit_i;
    always_ff @(posedge clk) begin
        if(!cold_rst_n) begin
            state_q<=IDLE; token_q<=0; generation_q<=0; context_q<=0; first_q<=0;
            read_pending_q<=0; read_index_q<=0; cancelled_q<=0; close_done_q<=0; profile_q<=0;
            requests_q<=0; responses_q<=0; terminals_q<=0; rows_q<=0;
            for(lane=0;lane<4;lane=lane+1) begin sums_q[lane]<=0; means_q[lane]<=0; end
            mean_channel_q<=0; statuses_q<=0; output_counts_q<=0; abort_units_q<=0;
            generated_q<=0; qualified_q<=0; transfer_abort_q<=0;
            cancel_reasons_q<=0; error_code_q<=ERR_NONE;
            protocol_error_q<=0; numeric_error_q<=0; caller_error_q<=0; caller_code_q<=0;
            fault_value_q<=0; fault_domain_q<=0; fault_channel_q<=0; fault_index_q<=0;
            fault_pcm_q<=0; fault_coefficient_q<=0; bad_rsp_q<=0;
            bad_token_q<=0; bad_generation_q<=0; bad_context_q<=0; bad_index_q<=0;
            bad_status_q<=0; bad_origin_q<=0; bad_payload_q<=0;
            out_domain_q<=0; out_channel_q<=0; out_index_q<=0; pcm_q<=0; coefficient_q<=0;
            fft_valid_q<=0; fft_real_q<=0; report_valid_q<=0; abort_valid_q<=0;
            report_q<='0; abort_q<='0;
        end else begin
            if(report_valid_q && report_ready) report_valid_q<=0;
            if(abort_valid_q && abort_ready) abort_valid_q<=0;
            if(request_fire) begin
                read_pending_q<=1;
                requests_q<=requests_q+32'd1;
            end
            if(response_fire && responses_q!=32'hffff_ffff) responses_q<=responses_q+32'd1;
            if(terminal_fire) begin
                read_pending_q<=0;
                if(terminals_q!=32'hffff_ffff) terminals_q<=terminals_q+32'd1;
            end
            if(active && first_error_valid && !caller_error_q) begin
                caller_error_q<=1; caller_code_q<=first_error_code;
            end
            if(active && !research_profile_valid) profile_q<=0;
            if(active && cancelled_q) cancel_reasons_q<=cancel_reasons_q | reasons_now;
            if(active && fault_now!=ERR_NONE) begin
                if(fault_numeric) numeric_error_q<=1;
                else if(fault_now!=ERR_PROFILE) protocol_error_q<=1;
            end
            // A malformed late response cannot clear or replace the first fault.
            if(active && fault_now!=ERR_NONE && error_code_q==ERR_NONE) begin
                error_code_q<=fault_now;
                fault_value_q<=(state_q==MEAN) ? mean_value :
                    ((fault_now==ERR_COEFFICIENT) ? product_value : rounded_value);
                fault_domain_q<=out_domain_q;
                fault_channel_q<=(state_q==MEAN) ? mean_channel_q : out_channel_q;
                fault_index_q<=out_index_q; fault_pcm_q<=pcm_q; fault_coefficient_q<=coefficient_q;
            end
            if(response_error!=ERR_NONE && !bad_rsp_q) begin
                bad_rsp_q<=1; bad_token_q<=rd_rsp_token; bad_generation_q<=rd_rsp_generation;
                bad_context_q<=rd_rsp_context; bad_index_q<=rd_rsp_index;
                bad_status_q<=rd_rsp_status; bad_origin_q<=rd_rsp_origin; bad_payload_q<=rd_rsp_payload;
            end

            if(desc_fire) begin
                token_q<=desc_token; generation_q<=desc_generation;
                context_q<=desc_context; first_q<=desc_first;
                read_pending_q<=0; read_index_q<=0; close_done_q<=0; cancelled_q<=0;
                profile_q<=research_profile_valid;
                requests_q<=0; responses_q<=0; terminals_q<=0; rows_q<=0;
                for(lane=0;lane<4;lane=lane+1) begin sums_q[lane]<=0; means_q[lane]<=0; end
                mean_channel_q<=0; statuses_q<=0; output_counts_q<=0; abort_units_q<=0;
                generated_q<=0; qualified_q<=0; transfer_abort_q<=0; cancel_reasons_q<=0;
                error_code_q<=ERR_NONE; protocol_error_q<=0; numeric_error_q<=0;
                caller_error_q<=0; caller_code_q<=0;
                fault_value_q<=0; fault_domain_q<=0; fault_channel_q<=0; fault_index_q<=0;
                fault_pcm_q<=0; fault_coefficient_q<=0; bad_rsp_q<=0;
                bad_token_q<=0; bad_generation_q<=0; bad_context_q<=0; bad_index_q<=0;
                bad_status_q<=0; bad_origin_q<=0; bad_payload_q<=0;
                out_domain_q<=0; out_channel_q<=0; out_index_q<=0;
                pcm_q<=0; coefficient_q<=0; fft_valid_q<=0; fft_real_q<=0;
                state_q<=READ_REQ;
            end

            if(abort_event) begin
                cancelled_q<=1;
                fft_valid_q<=0;
                cancel_reasons_q<=reasons_now;
                abort_units_q<=desc_fire ? 12'hfff : unfinished;
                if(desc_fire) statuses_q<={12{UNIT_ABORTED}};
                else for(unit_i=0;unit_i<12;unit_i=unit_i+1)
                    if(statuses_q[unit_i*3 +:3]!=UNIT_OK)
                        statuses_q[unit_i*3 +:3]<=UNIT_ABORTED;
                if(fault_numeric && !desc_fire) begin
                    if(state_q==MEAN) statuses_q[mean_channel_q*3 +:3]<=UNIT_ERROR;
                    else statuses_q[status_instance*3 +:3]<=UNIT_ERROR;
                end
                if(fault_now!=ERR_NONE && (desc_fire || error_code_q==ERR_NONE)) begin
                    error_code_q<=fault_now;
                    protocol_error_q<=!fault_numeric && fault_now!=ERR_PROFILE;
                    numeric_error_q<=fault_numeric;
                    fault_value_q<=abort_edge_report.first_fault_value;
                    fault_domain_q<=abort_edge_report.first_fault_domain;
                    fault_channel_q<=abort_edge_report.first_fault_channel;
                    fault_index_q<=abort_edge_report.first_fault_index;
                    fault_pcm_q<=abort_edge_report.first_fault_pcm;
                    fault_coefficient_q<=abort_edge_report.first_fault_coefficient;
                end
                if(first_error_valid) begin caller_error_q<=1; caller_code_q<=first_error_code; end
                if(!research_profile_valid) profile_q<=0;
                if(fft_fire) transfer_abort_q<=transfer_abort_q+14'd1;
                abort_q.at_edge<=abort_edge_report;
                abort_q.held_valid<=!desc_fire && fft_valid_q;
                abort_q.held_domain<=(!desc_fire && fft_valid_q) ? out_domain_q : 1'b0;
                abort_q.held_channel<=(!desc_fire && fft_valid_q) ? out_channel_q : 2'd0;
                abort_q.held_index<=(!desc_fire && fft_valid_q) ? out_index_q : 10'd0;
                abort_q.held_real<=(!desc_fire && fft_valid_q) ? fft_real_q : 29'sd0;
                abort_q.held_imag<=29'sd0;
                abort_q.held_numeric_valid<=!desc_fire && fft_valid_q;
                abort_q.held_overflow<=0;
                abort_q.held_last<=!desc_fire && fft_valid_q && out_index_q==10'd1023;
                abort_q.response_on_abort<=response_fire;
                abort_q.read_on_abort<=request_fire;
                abort_q.pending_after_edge<=request_fire || (read_pending_q && !terminal_fire);
                abort_valid_q<=1;
                state_q<=(!desc_fire && close_done_q) ? BUILD_REPORT : DRAIN;
            end else if(!desc_fire) begin
                case(state_q)
                    IDLE: begin end
                    READ_REQ: if(request_fire) state_q<=READ_WAIT;
                    READ_WAIT: if(terminal_fire && !cancelled_q && response_error==ERR_NONE) begin
                        for(lane=0;lane<4;lane=lane+1) begin
                            pcm_ram[read_index_q][lane*24 +:24]<=rd_rsp_payload[304+lane*32 +:24];
                            sums_q[lane]<=sums_q[lane]+$signed({{10{rd_rsp_payload[327+lane*32]}},rd_rsp_payload[304+lane*32 +:24]});
                        end
                        rows_q<=rows_q+11'd1;
                        if(read_index_q==10'd1023) begin mean_channel_q<=0; state_q<=MEAN; end
                        else begin read_index_q<=read_index_q+10'd1; state_q<=READ_REQ; end
                    end
                    MEAN: begin
                        means_q[mean_channel_q]<=mean_value[23:0];
                        statuses_q[mean_channel_q*3 +:3]<=UNIT_OK;
                        if(mean_channel_q==2'd3) state_q<=LOAD;
                        else mean_channel_q<=mean_channel_q+2'd1;
                    end
                    LOAD: begin
                        pcm_q<=$signed(pcm_ram[out_index_q][out_channel_q*24 +:24]);
                        coefficient_q<=hann_rom[out_index_q];
                        state_q<=CALCULATE;
                    end
                    CALCULATE: begin
                        fft_real_q<=fft_candidate;
                        fft_valid_q<=1;
                        generated_q<=generated_q+14'd1;
                        state_q<=SEND;
                    end
                    SEND: if(fft_fire) begin
                        fft_valid_q<=0;
                        qualified_q<=qualified_q+14'd1;
                        output_counts_q[output_instance*11 +:11]<=
                            output_counts_q[output_instance*11 +:11]+11'd1;
                        if(out_index_q==10'd1023)
                            statuses_q[status_instance*3 +:3]<=UNIT_OK;
                        if(out_domain_q && out_channel_q==2'd3 && out_index_q==10'd1023)
                            state_q<=QUIET;
                        else begin
                            // Synchronous prefetch only when the old item ACKs.
                            // CALCULATE on the later edge uses these new words.
                            pcm_q<=$signed(pcm_ram[next_index][next_channel*24 +:24]);
                            coefficient_q<=hann_rom[next_index];
                            out_domain_q<=next_domain;
                            out_channel_q<=next_channel;
                            out_index_q<=next_index;
                            state_q<=CALCULATE;
                        end
                    end
                    DRAIN: if(!read_pending_q) state_q<=QUIET;
                    QUIET: if(!read_pending_q && !fft_valid_q) state_q<=CLOSE;
                    CLOSE: begin end // Actual close_fire below is the only exit.
                    BUILD_REPORT: begin
                        // Preserve newly observed late diagnostics/counters
                        // before freezing the immutable report on a later edge.
                        if(!response_fire && !(first_error_valid && !caller_error_q) &&
                           !(fault_now!=ERR_NONE && error_code_q==ERR_NONE) &&
                           !(profile_q && !research_profile_valid) &&
                           (!cancelled_q || (cancel_reasons_q | reasons_now)==cancel_reasons_q)) begin
                            report_q<=report_live;
                            report_valid_q<=1;
                            state_q<=WAIT_REPORT;
                        end
                    end
                    WAIT_REPORT: if((!report_valid_q || report_ready) &&
                                    (!abort_valid_q || abort_ready)) state_q<=IDLE;
                    default: state_q<=DRAIN; // ERR_FSM also retains the first fault.
                endcase
            end
            // Closing E is also an observation edge. A genuine cancel on E is
            // recorded above, but its matching close handshake remains history.
            if(close_fire) begin close_done_q<=1; state_q<=BUILD_REPORT; end
        end
    end
endmodule
