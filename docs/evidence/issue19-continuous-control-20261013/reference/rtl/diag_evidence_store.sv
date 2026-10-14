`timescale 1ns/1ps
// TEST_ONLY complete evidence rings and one immutable 32-bit head snapshot.
module diag_evidence_store #(
    parameter integer SOURCE_DEPTH=64,
    parameter integer OTHER_DEPTH=8
)(
    input wire clk, input wire cold_rst_n,
    input wire source_valid, output wire source_ready, input wire [1055:0] source_payload,
    input wire retire_valid, output wire retire_ready, input wire [1183:0] retire_payload,
    input wire isolation_valid, output wire isolation_ready, input wire [1080:0] isolation_payload,
    input wire terminal_valid, output wire terminal_ready, input wire [709:0] terminal_payload,
    input wire summary_valid, output wire summary_ready, input wire [871:0] summary_payload,
    input wire summary_reserved, output wire summary_capacity,
    output wire reserve_warning, output wire full,
    output wire [31:0] counts,
    output wire [63:0] local_cycle, output wire [63:0] next_sequence,
    input wire select_valid, input wire [2:0] select_bank,
    input wire ack_valid, input wire [63:0] ack_sequence, input wire [5:0] ack_word,
    input wire abort_valid,
    output wire export_valid, output wire [31:0] export_data,
    output wire [2:0] export_bank, output wire [63:0] export_sequence,
    output wire [5:0] export_word, export_words,
    output wire export_last,
    output reg error_pulse, output reg [7:0] error_code,
    output wire allocator_exhausted
);
    reg [63:0] cycle_q,seq_q;
    reg seq_exhausted_q,cycle_exhausted_q;
    wire [4:0] bank_ready, head_valid;
    wire [4:0] offers={summary_valid,terminal_valid,isolation_valid,retire_valid,source_valid};
    localparam integer SOURCE_COUNT_BITS=$clog2(SOURCE_DEPTH+1);
    localparam integer OTHER_COUNT_BITS=$clog2(OTHER_DEPTH+1);
    wire [SOURCE_COUNT_BITS-1:0] bank_count0;
    wire [OTHER_COUNT_BITS-1:0] bank_count1,bank_count2,bank_count3,bank_count4;
    // WA-DUT-003: match the actual bank port, then zero-extend to the
    // fixed diagnostic layout. Formal 64/8 and reduced 2/2 lose no count bits.
    wire [6:0] count0={{(7-SOURCE_COUNT_BITS){1'b0}},bank_count0};
    wire [3:0] count1={{(4-OTHER_COUNT_BITS){1'b0}},bank_count1};
    wire [3:0] count2={{(4-OTHER_COUNT_BITS){1'b0}},bank_count2};
    wire [3:0] count3={{(4-OTHER_COUNT_BITS){1'b0}},bank_count3};
    wire [3:0] count4={{(4-OTHER_COUNT_BITS){1'b0}},bank_count4};
    wire [1183:0] head0;
    wire [1311:0] head1;
    wire [1208:0] head2;
    wire [837:0] head3;
    wire [999:0] head4;
    wire [4:0] pop;
    wire [3:0] fire_total={3'd0,(offers[0] && bank_ready[0])}+
        {3'd0,(offers[1] && bank_ready[1])}+{3'd0,(offers[2] && bank_ready[2])}+
        {3'd0,(offers[3] && bank_ready[3])}+{3'd0,(offers[4] && bank_ready[4])};
    wire [64:0] last_sequence={1'b0,seq_q}+{61'd0,fire_total}-(fire_total!=0 ? 65'd1 : 65'd0);
    wire sequence_fits=fire_total==0 || !last_sequence[64];
    wire allow_capture=cold_rst_n && !seq_exhausted_q && sequence_fits;
    wire [4:0] fires=offers & bank_ready & {5{cold_rst_n && !seq_exhausted_q && sequence_fits}};
    wire [63:0] seq1=seq_q+{63'd0,fires[0]};
    wire [63:0] seq2=seq1+{63'd0,fires[1]};
    wire [63:0] seq3=seq2+{63'd0,fires[2]};
    wire [63:0] seq4=seq3+{63'd0,fires[3]};
    assign local_cycle=cycle_q;
    assign next_sequence=seq_q;
    assign allocator_exhausted=seq_exhausted_q || cycle_exhausted_q;
    assign source_ready=allow_capture && bank_ready[0];
    assign retire_ready=allow_capture && bank_ready[1];
    assign isolation_ready=allow_capture && bank_ready[2];
    assign terminal_ready=allow_capture && bank_ready[3];
    assign summary_ready=allow_capture && bank_ready[4];
    // Only this reader can produce a summary. A descriptor acceptance
    // reserves one pre-edge free slot through its eventual summary save.
    assign summary_capacity=allow_capture && count4<OTHER_DEPTH && !summary_reserved;
    assign full=count0==SOURCE_DEPTH || count1==OTHER_DEPTH || count2==OTHER_DEPTH ||
        count3==OTHER_DEPTH || count4==OTHER_DEPTH;
    assign reserve_warning=count0>=((SOURCE_DEPTH>8) ? SOURCE_DEPTH-8 : 1) ||
        count1>=((OTHER_DEPTH>2) ? OTHER_DEPTH-2 : 1) ||
        count2>=((OTHER_DEPTH>2) ? OTHER_DEPTH-2 : 1) ||
        count3>=((OTHER_DEPTH>2) ? OTHER_DEPTH-2 : 1) ||
        ({1'b0,count4}+summary_reserved)>=((OTHER_DEPTH>2) ? OTHER_DEPTH-2 : 1);
    assign counts={9'd0,count4,count3,count2,count1,count0};
    diag_record_bank #(.PAYLOAD_BITS(1056),.DEPTH(SOURCE_DEPTH)) b0(
        .clk(clk),.cold_rst_n(cold_rst_n),.push_valid(source_valid && allow_capture),.push_ready(bank_ready[0]),
        .push_payload(source_payload),.push_cycle(cycle_q),.push_seq(seq_q),.pop(pop[0]),
        .head_valid(head_valid[0]),.head_record(head0),.count(bank_count0));
    diag_record_bank #(.PAYLOAD_BITS(1184),.DEPTH(OTHER_DEPTH)) b1(
        .clk(clk),.cold_rst_n(cold_rst_n),.push_valid(retire_valid && allow_capture),.push_ready(bank_ready[1]),
        .push_payload(retire_payload),.push_cycle(cycle_q),.push_seq(seq1),.pop(pop[1]),
        .head_valid(head_valid[1]),.head_record(head1),.count(bank_count1));
    diag_record_bank #(.PAYLOAD_BITS(1081),.DEPTH(OTHER_DEPTH)) b2(
        .clk(clk),.cold_rst_n(cold_rst_n),.push_valid(isolation_valid && allow_capture),.push_ready(bank_ready[2]),
        .push_payload(isolation_payload),.push_cycle(cycle_q),.push_seq(seq2),.pop(pop[2]),
        .head_valid(head_valid[2]),.head_record(head2),.count(bank_count2));
    diag_record_bank #(.PAYLOAD_BITS(710),.DEPTH(OTHER_DEPTH)) b3(
        .clk(clk),.cold_rst_n(cold_rst_n),.push_valid(terminal_valid && allow_capture),.push_ready(bank_ready[3]),
        .push_payload(terminal_payload),.push_cycle(cycle_q),.push_seq(seq3),.pop(pop[3]),
        .head_valid(head_valid[3]),.head_record(head3),.count(bank_count3));
    diag_record_bank #(.PAYLOAD_BITS(872),.DEPTH(OTHER_DEPTH)) b4(
        .clk(clk),.cold_rst_n(cold_rst_n),.push_valid(summary_valid && allow_capture),.push_ready(bank_ready[4]),
        .push_payload(summary_payload),.push_cycle(cycle_q),.push_seq(seq4),.pop(pop[4]),
        .head_valid(head_valid[4]),.head_record(head4),.count(bank_count4));
    reg select_armed,ack_armed,abort_armed;
    reg snapshot_valid_q;
    reg [1311:0] snapshot_q;
    reg [2:0] bank_q;
    reg [63:0] snapshot_seq_q;
    reg [5:0] word_q,words_q;
    wire select_event=select_valid && select_armed;
    wire ack_event=ack_valid && ack_armed;
    wire abort_event=abort_valid && abort_armed;
    wire correct_ack=snapshot_valid_q && ack_sequence==snapshot_seq_q && ack_word==word_q;
    wire last_ack=cold_rst_n && ack_event && correct_ack && word_q==words_q-1 && !abort_event;
    genvar b;
    generate for(b=0;b<5;b=b+1) begin: pop_decode
        assign pop[b]=last_ack && bank_q==b;
    end endgenerate
    assign export_valid=cold_rst_n && snapshot_valid_q;
    assign export_data=snapshot_q[word_q*32+:32];
    assign export_bank=bank_q;
    assign export_sequence=snapshot_seq_q;
    assign export_word=word_q;
    assign export_words=words_q;
    assign export_last=snapshot_valid_q && word_q==words_q-1;
    always @(posedge clk) begin
        if(!cold_rst_n) begin
            cycle_q<=0; seq_q<=0; seq_exhausted_q<=0; cycle_exhausted_q<=0;
            select_armed<=0; ack_armed<=0; abort_armed<=0;
            snapshot_valid_q<=0; snapshot_q<=0; bank_q<=0;
            snapshot_seq_q<=0; word_q<=0; words_q<=0; error_pulse<=0; error_code<=0;
        end else begin
            error_pulse<=0;
            if(cycle_q!=64'hffffffffffffffff) cycle_q<=cycle_q+64'd1;
            else if(!cycle_exhausted_q) begin
                cycle_exhausted_q<=1; error_pulse<=1; error_code<=8'd4;
            end
            if(!sequence_fits && !seq_exhausted_q) begin
                seq_exhausted_q<=1; error_pulse<=1; error_code<=8'd3;
            end else if(fire_total!=0 && allow_capture) begin
                if(last_sequence[63:0]==64'hffffffffffffffff) begin seq_exhausted_q<=1; seq_q<=64'hffffffffffffffff; end
                else seq_q<=seq_q+{60'd0,fire_total};
            end
            if(!select_valid) select_armed<=1; else if(select_armed) select_armed<=0;
            if(!ack_valid) ack_armed<=1; else if(ack_armed) ack_armed<=0;
            if(!abort_valid) abort_armed<=1; else if(abort_armed) abort_armed<=0;
            if(abort_event) snapshot_valid_q<=0; // head remains unconsumed
            else begin
                if(ack_event) begin
                    if(!correct_ack) begin error_pulse<=1; error_code<=8'd2; end
                    else if(last_ack) snapshot_valid_q<=0;
                    else word_q<=word_q+1'b1;
                end
                if(select_event) begin
                    if(snapshot_valid_q || select_bank>4 || !head_valid[select_bank]) begin
                        error_pulse<=1; error_code<=8'd1;
                    end else begin
                        snapshot_valid_q<=1; bank_q<=select_bank; word_q<=0;
                        case(select_bank)
                            0: begin snapshot_q<={128'd0,head0}; snapshot_seq_q<=head0[1183:1120]; words_q<=37; end
                            1: begin snapshot_q<=head1; snapshot_seq_q<=head1[1311:1248]; words_q<=41; end
                            2: begin snapshot_q<={103'd0,head2}; snapshot_seq_q<=head2[1208:1145]; words_q<=38; end
                            3: begin snapshot_q<={474'd0,head3}; snapshot_seq_q<=head3[837:774]; words_q<=27; end
                            4: begin snapshot_q<={312'd0,head4}; snapshot_seq_q<=head4[999:936]; words_q<=32; end
                            default: snapshot_valid_q<=0;
                        endcase
                    end
                end
            end
        end
    end
endmodule
