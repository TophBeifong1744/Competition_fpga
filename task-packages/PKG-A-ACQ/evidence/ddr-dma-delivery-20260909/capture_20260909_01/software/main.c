/*
 * 任务三：一次启动、两包、四组实收数据导出。待实板运行验收。
 * 硬件合同：one-test-source-v1，SAMPLES_PER_PACKET=2，PACKET_COUNT=2。
 * Vitis 2025.2，Cortex-A9 standalone/SDT，AXI DMA simple S2MM。
 * 运行前必须下载匹配的新比特流并初始化PS，确保PL测试源处于复位后的空闲态。
 * lscript.ld: 程序DDR ORIGIN=0x00100000 LENGTH=0x00F00000。
 * 专用接收区[0x01000000,0x01100000)，本程序只使用其前128字节。
 * 不允许其他CPU核、DMA、程序缓冲区使用这一区域。
 */
#include "xparameters.h"
#include "xil_printf.h"
#include "xil_cache.h"
#include "xstatus.h"
#include "xgpio.h"
#include "xaxidma.h"
#include "xaxidma_hw.h"
#include "sleep.h"

#ifndef SDT
#error "This example requires the verified SDT BSP."
#endif

#define RX_BASE       ((UINTPTR)0x01000000U)
#define RX_LIMIT      ((UINTPTR)0x01100000U)
#define SLOT_BYTES    64U
#define PACKET_BYTES  24U
#define PACKETS       2U
#define POLL_LIMIT    1000000U
#define BATCH_COUNT   1U
#define SENTINEL      (0xA5A50000U ^ Batch)
#define ERROR_MASK    (XAXIDMA_ERR_ALL_MASK | XAXIDMA_IRQ_ERROR_MASK)

static unsigned Batch;
static XGpio Gpio;
static XAxiDma Dma;
extern char end[]; /* 当前链接脚本中，所有栈之后的地址符号 */

/* 独立列出的首4组golden值，按32位AXI拍顺序排列。 */
static const u32 golden[PACKETS][PACKET_BYTES / 4U] = {
    {0x00000000U, 0x01010000U, 0x8003FDFFU,
     0x00000001U, 0xFEFF0001U, 0x00008002U},
    {0x00000002U, 0x8001FFFFU, 0x03010000U,
     0x00000003U, 0x00008000U, 0xFCFF0201U}
};

static u32 rx_status(void)
{
    return XAxiDma_ReadReg(Dma.RegBase,
                          XAXIDMA_RX_OFFSET + XAXIDMA_SR_OFFSET);
}

static void dump_dma(const char *stage, unsigned packet)
{
    u32 cr = XAxiDma_ReadReg(Dma.RegBase,
                            XAXIDMA_RX_OFFSET + XAXIDMA_CR_OFFSET);
    u32 sr = rx_status();
    xil_printf("%s batch=%u packet=%u CR=0x%08x SR=0x%08x errors=0x%08x\r\n",
               stage, Batch, packet, (unsigned)cr, (unsigned)sr,
               (unsigned)(sr & ERROR_MASK));
}

static int wait_packet(void)
{
    for (u32 i = 0; i < POLL_LIMIT; ++i) {
        u32 sr = rx_status();
        if (sr & ERROR_MASK)
            return XST_FAILURE;
        /* 必须看到本次的完成标志与空闲，而不只是Busy为假。 */
        if ((sr & XAXIDMA_IRQ_IOC_MASK) && (sr & XAXIDMA_IDLE_MASK))
            return XST_SUCCESS;
    }
    xil_printf("FAIL: receive poll limit reached (%u polls)\r\n",
               (unsigned)POLL_LIMIT);
    return XST_FAILURE;
}

static int signed16(u32 value)
{
    value &= 0xFFFFU;
    return (value & 0x8000U) ? (int)value - 65536 : (int)value;
}

static int check_packet(unsigned packet, UINTPTR address)
{
    const volatile u32 *rx = (const volatile u32 *)address;
    unsigned errors = 0;
    for (unsigned i = 0; i < PACKET_BYTES / 4U; ++i) {
        u32 actual = rx[i];
        if (Batch == 0U || actual != golden[packet][i])
            xil_printf("packet=%u word=%u got=%08x expected=%08x\r\n",
                   packet, i, (unsigned)actual, (unsigned)golden[packet][i]);
        if (actual != golden[packet][i])
            ++errors;
    }
    /* 每个槽后40字节不应被DMA写入，检测紧邻包尾的越界。 */
    for (unsigned i = PACKET_BYTES / 4U; i < SLOT_BYTES / 4U; ++i) {
        if (rx[i] != SENTINEL) {
            xil_printf("FAIL: guard changed packet=%u word=%u\r\n", packet, i);
            ++errors;
        }
    }
    for (unsigned s = 0; Batch == 0U && s < 2U; ++s) {
        u32 w1 = rx[s * 3U + 1U];
        u32 w2 = rx[s * 3U + 2U];
        xil_printf("sample=%u ch0=%d ch1=%d ch2=%d ch3=%d\r\n",
                   (unsigned)rx[s * 3U], signed16(w1), signed16(w1 >> 16),
                   signed16(w2), signed16(w2 >> 16));
    }
    if (Batch == 0U || errors)
        xil_printf("packet=%u compare_errors=%u\r\n", packet, errors);
    return errors ? XST_FAILURE : XST_SUCCESS;
}

int main(void)
{
    int status;
    XAxiDma_Config *cfg;
    unsigned packet = 0;
    unsigned completed_packets = 0;

    xil_printf("\r\nDMA capture export v1\r\n");
    xil_printf("Build: %s %s\r\n", __DATE__, __TIME__);
    xil_printf("Program end=0x%08x RX=[0x%08x,0x%08x)\r\n",
               (unsigned)(UINTPTR)end, (unsigned)RX_BASE, (unsigned)RX_LIMIT);

    if ((UINTPTR)end > RX_BASE ||
        RX_BASE < (UINTPTR)XPAR_PS7_DDR_0_BASEADDRESS ||
        RX_LIMIT - 1U > (UINTPTR)XPAR_PS7_DDR_0_HIGHADDRESS ||
        RX_BASE + PACKETS * SLOT_BYTES > RX_LIMIT) {
        xil_printf("FAIL: unsafe receive region\r\n");
        return 1;
    }

    status = XGpio_Initialize(&Gpio, XPAR_AXI_GPIO_0_BASEADDR);
    if (status != XST_SUCCESS) {
        xil_printf("FAIL: GPIO init=%d\r\n", status);
        return 1;
    }
    XGpio_DiscreteWrite(&Gpio, 1, 0);
    XGpio_SetDataDirection(&Gpio, 1, 0);
    usleep(10); /* 保证上升沿检测模块先采到低电平 */

    cfg = XAxiDma_LookupConfig(XPAR_AXI_DMA_0_BASEADDR);
    if (cfg == NULL || cfg->HasSg || !cfg->HasS2Mm || cfg->MicroDmaMode) {
        xil_printf("FAIL: DMA config must be normal simple S2MM\r\n");
        return 1;
    }
    status = XAxiDma_CfgInitialize(&Dma, cfg);
    if (status != XST_SUCCESS) {
        xil_printf("FAIL: DMA init=%d\r\n", status);
        return 1;
    }
    XAxiDma_IntrDisable(&Dma, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DEVICE_TO_DMA);
    dump_dma("INIT", 0);
    if (rx_status() & ERROR_MASK)
        goto fail;

    /*
     * 本机A9 BSP以32字节为缓存行。64字节槽起止均对齐，
     * 两包不共享缓存行。DMA传输长度仍是24，不是64。
     */
    Xil_DCacheEnable();
    xil_printf("Batches=%u packets_per_batch=2 bytes_per_packet=24\r\n", BATCH_COUNT);
    xil_printf("Cache ON; slots=64 bytes; DMA init once; no reset between batches\r\n");
    for (Batch = 0; Batch < BATCH_COUNT; ++Batch) {
        /* 每批低电平重新武装边沿检测；仅上一批完整检查通过才进入。 */
        XGpio_DiscreteWrite(&Gpio, 1, 0);
        usleep(10);
        for (unsigned p = 0; p < PACKETS; ++p) {
            UINTPTR address = RX_BASE + p * SLOT_BYTES;
            volatile u32 *rx = (volatile u32 *)address;
            for (unsigned i = 0; i < SLOT_BYTES / 4U; ++i)
                rx[i] = SENTINEL;
            /* 在DMA接管之前清理脏缓存，避免之后旧数据回写覆盖新数据。 */
            Xil_DCacheFlushRange((INTPTR)address, SLOT_BYTES);
            Xil_DCacheInvalidateRange((INTPTR)address, SLOT_BYTES);
        }
        /* 每批重填不同哨兵，不能把上批相同码型的残留当作新接收结果。 */

        for (packet = 0; packet < PACKETS; ++packet) {
            UINTPTR address = RX_BASE + packet * SLOT_BYTES;
            u32 actual_bytes;

            /* 完成标志是写1清除；防止上一次IOC造成误判。 */
            XAxiDma_IntrAckIrq(&Dma, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DEVICE_TO_DMA);
            status = (int)XAxiDma_SimpleTransfer(&Dma, address, PACKET_BYTES,
                                               XAXIDMA_DEVICE_TO_DMA);
            if (status != XST_SUCCESS) {
                xil_printf("FAIL: submit packet=%u code=%d\r\n", packet, status);
                goto fail;
            }
            if (Batch == 0U)
                dump_dma("ARMED", packet);

            /* 只在第一包接收已经准备好之后启动源，一次启动产生两包。 */
            if (packet == 0U) {
                XGpio_DiscreteWrite(&Gpio, 1, 1);
                usleep(10);
                XGpio_DiscreteWrite(&Gpio, 1, 0);
            }

            /* 传输过程中CPU不能访问对应接收槽，包括Memory Inspector。 */
            if (wait_packet() != XST_SUCCESS)
                goto fail;
            dump_dma("DONE", packet);
            actual_bytes = XAxiDma_ReadReg(Dma.RegBase,
                                XAXIDMA_RX_OFFSET + XAXIDMA_BUFFLEN_OFFSET);
            xil_printf("RX batch=%u packet=%u actual_bytes=%u\r\n",
                       Batch, packet, (unsigned)actual_bytes);
            if (actual_bytes != PACKET_BYTES) {
                xil_printf("FAIL: unexpected received length\r\n");
                goto fail;
            }

            /* DMA完成后只失效缓存；不要把CPU旧副本flush回DDR。 */
            Xil_DCacheInvalidateRange((INTPTR)address, SLOT_BYTES);
            if (check_packet(packet, address) != XST_SUCCESS)
                goto fail;
            ++completed_packets;
        }
        if ((Batch + 1U) % 100U == 0U)
            xil_printf("PROGRESS batches=%u/%u packets=%u errors=0\r\n",
                       Batch + 1U, BATCH_COUNT, completed_packets);
    }
    xil_printf("MULTIBATCH PASS: batches=%u packets=%u bytes=%u samples=%u errors=0\r\n",
               BATCH_COUNT, completed_packets,
               completed_packets * PACKET_BYTES, completed_packets * 2U);
    /*
     * Export ONLY after both packets pass length, payload and guard checks.
     * Values below come from DDR receive slots, never from golden[].
     * No new transfer starts; CPU now owns both invalidated receive slots.
     * stream_error=0 means no error observed by this diagnostic harness.
     */
    xil_printf("BEGIN_SAMPLES_CSV\r\n");
    xil_printf("sample_id,mic0,mic1,mic2,mic3,stream_error,error_flags\r\n");
    for (unsigned p = 0; p < PACKETS; ++p) {
        const volatile u32 *rx =
            (const volatile u32 *)(RX_BASE + p * SLOT_BYTES);
        for (unsigned i = 0; i < 2U; ++i) {
            u32 id = rx[i * 3U];
            u32 w1 = rx[i * 3U + 1U];
            u32 w2 = rx[i * 3U + 2U];
            xil_printf("%u,%d,%d,%d,%d,0,\r\n",
                       (unsigned)id, signed16(w1), signed16(w1 >> 16),
                       signed16(w2), signed16(w2 >> 16));
        }
    }
    xil_printf("END_SAMPLES_CSV\r\n");
    xil_printf("EXPORT PASS: packets=2 bytes=48 samples=4 errors=0\r\n");
    return 0;

fail:
    dump_dma("FAIL", packet);
    xil_printf("Completed packets before failure=%u\r\n", completed_packets);
    XGpio_DiscreteWrite(&Gpio, 1, 0);
    XAxiDma_Reset(&Dma);
    for (u32 i = 0; i < POLL_LIMIT; ++i) {
        if (XAxiDma_ResetIsDone(&Dma)) {
            xil_printf("DMA reset done.\r\n");
            break;
        }
        if (i == POLL_LIMIT - 1U)
            xil_printf("DMA reset timeout.\r\n");
    }
    /* DMA复位不等于测试源复位。错误后不能直接重新发start。 */
    xil_printf("STOP: reinitialize PS and reprogram PL before retry.\r\n");
    return 1;
}
