`timescale 1ns/1ps

module test_source_bd #(
    parameter integer SAMPLES_PER_PACKET = 2,
    parameter integer PACKET_COUNT       = 2
)(
    input  wire        aclk,
    input  wire        aresetn,
    input  wire        start,

    output wire [31:0] m_axis_tdata,
    output wire [3:0]  m_axis_tkeep,
    output wire        m_axis_tvalid,
    input  wire        m_axis_tready,
    output wire        m_axis_tlast,

    output wire        busy,
    output wire        done
);

    // 包装层只连接端口，实际逻辑仍由原来的 SV 模块实现。
    test_source #(
        .SAMPLES_PER_PACKET(SAMPLES_PER_PACKET),
        .PACKET_COUNT      (PACKET_COUNT)
    ) u_test_source (
        .aclk          (aclk),
        .aresetn       (aresetn),
        .start         (start),

        .m_axis_tdata  (m_axis_tdata),
        .m_axis_tkeep  (m_axis_tkeep),
        .m_axis_tvalid (m_axis_tvalid),
        .m_axis_tready (m_axis_tready),
        .m_axis_tlast  (m_axis_tlast),

        .busy          (busy),
        .done          (done)
    );

endmodule