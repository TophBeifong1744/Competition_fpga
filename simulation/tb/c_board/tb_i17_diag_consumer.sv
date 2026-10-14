`timescale 1ns/1ps
module tb_i17_diag_consumer;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,m_ready=0,push=0;
    wire [31:0] bank_counts;
    wire select_valid,ack_valid,export_valid,export_last,m_valid,m_last,idle;
    wire [2:0] select_bank,export_bank,m_bank;
    wire [63:0] ack_sequence,export_sequence,m_sequence,records_consumed;
    wire [5:0] ack_word,export_word,export_words,m_word,m_words;
    wire [31:0] export_data,m_data;wire error_pulse;wire [7:0] error_code;
    wire [4:0] ready;
    i17_diag_consumer dut(.*);
    diag_evidence_store #(.SOURCE_DEPTH(16),.OTHER_DEPTH(8)) store(
        .clk(clk),.cold_rst_n(rst_n),
        .source_valid(push),.source_ready(ready[0]),.source_payload({1056{1'b1}}),
        .retire_valid(push),.retire_ready(ready[1]),.retire_payload({1184{1'b1}}),
        .isolation_valid(push),.isolation_ready(ready[2]),.isolation_payload({1081{1'b1}}),
        .terminal_valid(push),.terminal_ready(ready[3]),.terminal_payload({710{1'b1}}),
        .summary_valid(push),.summary_ready(ready[4]),.summary_payload({872{1'b1}}),
        .summary_reserved(1'b0),.counts(bank_counts),.select_valid(select_valid),.select_bank(select_bank),
        .ack_valid(ack_valid),.ack_sequence(ack_sequence),.ack_word(ack_word),.abort_valid(1'b0),
        .export_valid(export_valid),.export_data(export_data),.export_bank(export_bank),
        .export_sequence(export_sequence),.export_word(export_word),.export_words(export_words),.export_last(export_last),
        .error_pulse(error_pulse),.error_code(error_code));
    integer words[0:4],records[0:4],next_word[0:4],cycles=0,total=0;
    bit previous_ack=0,previous_stall=0;
    reg [31:0] stalled_data;reg [63:0] stalled_seq;reg [5:0] stalled_word;reg [2:0] stalled_bank;
    integer lengths[0:4]='{37,41,38,27,32};
    always @(posedge clk) if(rst_n) begin
        cycles++;
        if(error_pulse) $fatal(1,"EXPORT_CHECK store_error=%0d",error_code);
        if(ack_valid && previous_ack) $fatal(1,"EXPORT_CHECK adjacent ACK");
        if(previous_stall && (!m_valid || {m_data,m_sequence,m_word,m_bank}!={stalled_data,stalled_seq,stalled_word,stalled_bank}))
            $fatal(1,"EXPORT_CHECK stall instability");
        if(m_valid && m_ready) begin
            if(m_bank>4 || m_words!=lengths[m_bank] || m_word!=next_word[m_bank] || m_last!=(m_word==lengths[m_bank]-1))
                $fatal(1,"EXPORT_CHECK framing bank=%0d word=%0d",m_bank,m_word);
            // 每条记录LSB payload的前32位全部1，是独立设置的输入，不读DUT期待值。
            if(m_word==0 && m_data!==($test$plusargs("CANARY") ? 32'hfffffffe : 32'hffffffff))
                $fatal(1,"EXPORT_CHECK payload canary");
            words[m_bank]++;total++;
            if(m_last) begin records[m_bank]++;next_word[m_bank]=0;end
            else next_word[m_bank]++;
        end
        previous_ack=ack_valid;
        previous_stall=m_valid&&!m_ready;
        if(previous_stall) begin stalled_data=m_data;stalled_seq=m_sequence;stalled_word=m_word;stalled_bank=m_bank;end
    end
    initial begin
        for(integer b=0;b<5;b++)begin words[b]=0;records[b]=0;next_word[b]=0;end
        repeat(4)@(negedge clk);rst_n=1;repeat(3)@(negedge clk);
        // 同沿五bank，连续三条；捕获/导出并行，随后长反压。
        push=1;repeat(3)@(negedge clk);push=0;
        repeat(100)@(negedge clk);
        if(records_consumed!=0 || !export_valid || bank_counts==0) $fatal(1,"EXPORT_CHECK false consumption under stall");
        for(integer n=0;n<1700;n++) begin @(negedge clk);m_ready=(n%7!=0 && n%7!=1);end
        m_ready=1;repeat(300)@(negedge clk);
        for(integer b=0;b<5;b++)if(records[b]!=3 || words[b]!=3*lengths[b])$fatal(1,"EXPORT_CHECK missing bank=%0d",b);
        if(!idle || bank_counts!=0 || records_consumed!=15 || total!=525)$fatal(1,"EXPORT_CHECK totals");
        $display("EXPORT_COMPLETE records=%0d words=%0d cycles=%0d",records_consumed,total,cycles);$finish;
    end
    initial begin #100000;$fatal(1,"EXPORT_HANG");end
endmodule
