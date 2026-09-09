`timescale 1ns/1ps
// 任务一：可暂停的四通道 AXI4-Stream 测试源，格式 one-test-source-v1。
// 正/负/零码型在4组内覆盖每个通道。仅码型/接口验证，不是录音。
// 16位通道用补码解释；本格式不是H1离线CSV格式。
// 默认：每包2组采样，共2包；每组3拍，因此一次启动共12拍、48字节。
// 打包：拍0=sample_id；拍1={ch1,ch0}；拍2={ch3,ch2}。
// 每通道16位，数据按16位回绕；采样编号32位，按32位回绕。
// start：aclk同步的单周期脉冲，仅空闲时接受；忙碌时忽略。
// 每次接受start，所有计数从0开始。不包含跨时钟域/按键消抖。
// aresetn：低有效、异步复位；外部应保证同步释放。
// 复位中断当前包，不产生done；实际系统需同时处理DMA的半包状态。
// TREADY为0时不产生新的采样，不能用此版本证明真实固定采样率无丢样。
module test_source #(
    parameter int unsigned SAMPLES_PER_PACKET = 2, // 必须 >= 1
    parameter int unsigned PACKET_COUNT       = 2  // 必须 >= 1
)(
    input  logic        aclk,
    input  logic        aresetn,
    input  logic        start,

    output logic [31:0] m_axis_tdata,
    output logic [3:0]  m_axis_tkeep,
    output logic        m_axis_tvalid,
    input  logic        m_axis_tready,
    output logic        m_axis_tlast,

    output logic        busy,
    output logic        done
);

    // 1. 记忆当前位置的寄存器：只由下方always_ff驱动。
    localparam int SAMPLE_IDX_W =
        (SAMPLES_PER_PACKET > 1) ? $clog2(SAMPLES_PER_PACKET) : 1;
    localparam int PACKET_IDX_W =
        (PACKET_COUNT > 1) ? $clog2(PACKET_COUNT) : 1;

    logic [1:0] beat_idx;                         // 组内拍位置：0、1、2
    logic [31:0] sample_id;                       // 全局采样编号：跨包连续
    logic [SAMPLE_IDX_W-1:0] sample_in_packet;    // 包内采样位置
    logic [PACKET_IDX_W-1:0] packet_id;           // 当前包位置

    logic [15:0] ch0, ch1, ch2, ch3;
    logic transfer_enable;
    logic last_beat, last_sample, last_packet;

    // 2. 组合判断：观察当前状态，不保存状态。
    assign last_beat   = (beat_idx == 2'd2);
    assign last_sample = (sample_in_packet ==
                          SAMPLE_IDX_W'(SAMPLES_PER_PACKET - 1));
    assign last_packet = (packet_id == PACKET_IDX_W'(PACKET_COUNT - 1));

    // 有数据就声明有效，不等待TREADY，避免与接收端互等。
    assign m_axis_tvalid = busy;
    assign m_axis_tkeep  = 4'b1111; // 本格式每拍4个字节全部有效
    assign m_axis_tlast  = busy && last_beat && last_sample;
    assign transfer_enable = m_axis_tvalid && m_axis_tready;

    // 每4组轮转四种相位；通道号改变相位和幅度，任一组四值均不同。
    // phase=(采样编号+通道号) mod 4；magnitude=1+256*通道号+sid[15:2]。
    // 相位0=零，1=正幅度，2=负幅度，3=接近负满量程。
    // 幅度最大17152，可由signed16无损表达；返回的是补码位模式。
    function automatic logic [15:0] channel_pattern(
        input logic [31:0] sid,
        input logic [1:0] channel
    );
        logic [1:0] phase;
        logic [15:0] magnitude;
        begin
            phase = sid[1:0] + channel;
            magnitude = 16'd1 + {6'd0, channel, 8'd0}
                                  + {2'd0, sid[15:2]};
            case (phase)
                2'd0: channel_pattern = 16'h0000;
                2'd1: channel_pattern = magnitude;
                2'd2: channel_pattern = 16'd0 - magnitude;
                2'd3: channel_pattern = 16'h8000 + {14'd0, channel};
                default: channel_pattern = 16'h0000;
            endcase
        end
    endfunction

    // 3. 数据通路：根据当前采样编号、拍位置选择当前输出。
    // 组合块用阻塞赋值“=”，所有路径都有默认值，避免锁存器。
    // 不在任何always_ff中再次给这些信号赋值，包括复位。
    always_comb begin
        ch0 = channel_pattern(sample_id, 2'd0);
        ch1 = channel_pattern(sample_id, 2'd1);
        ch2 = channel_pattern(sample_id, 2'd2);
        ch3 = channel_pattern(sample_id, 2'd3);

        m_axis_tdata = 32'd0;
        if (busy) begin
            case (beat_idx)
                2'd0: m_axis_tdata = sample_id;
                2'd1: m_axis_tdata = {ch1, ch0};
                2'd2: m_axis_tdata = {ch3, ch2};
                default: m_axis_tdata = 32'd0;
            endcase
        end
    end

    // 4. 控制通路：时钟沿上更新状态，使用非阻塞赋值“<=”。
    // DMA在上升沿接收“旧状态”对应的数据；计数更新后输出下一拍。
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            beat_idx        <= '0;
            sample_id       <= '0;
            sample_in_packet <= '0;
            packet_id       <= '0;
            busy            <= 1'b0;
            done            <= 1'b0;
        end else begin
            // 默认每周期清零，仅完成时覆盖为1，形成单周期脉冲。
            done <= 1'b0;

            if (!busy) begin
                if (start) begin
                    beat_idx         <= '0;
                    sample_id        <= '0;
                    sample_in_packet <= '0;
                    packet_id        <= '0;
                    busy             <= 1'b1;
                end
            end else if (transfer_enable) begin
                // 忙碌期间忽略start，只有成功握手才推进位置。
                if (!last_beat) begin
                    beat_idx <= beat_idx + 2'd1;
                end else begin
                    beat_idx  <= '0;
                    sample_id <= sample_id + 32'd1;

                    if (!last_sample) begin
                        sample_in_packet <= sample_in_packet + 1'b1;
                    end else begin
                        sample_in_packet <= '0;
                        if (!last_packet) begin
                            packet_id <= packet_id + 1'b1;
                        end else begin
                            // 最后一包最后一拍真正被接收，才算完成。
                            busy <= 1'b0;
                            done <= 1'b1;
                        end
                    end
                end
            end
            // busy且未握手：所有位置寄存器保持。
            // 因此TDATA/TLAST/TKEEP/TVALID也保持，不丢失当前拍。
        end
    end

    // 仅用于仿真的参数合法性检查，不生成硬件。
    // synthesis translate_off
    initial begin
        if (SAMPLES_PER_PACKET == 0 || PACKET_COUNT == 0)
            $fatal(1, "SAMPLES_PER_PACKET and PACKET_COUNT must be >= 1");
    end
    // synthesis translate_on
endmodule
