/* Derived from the preserved single_mic_capture application.
 * ss-four-record-0.1; NOT compatible with the old mono bitstream.
 * Core 0 only; no other core or DMA may access the reserved RX region.
 */
#include "xparameters.h"
#include "xaxidma.h"
#include "xaxidma_hw.h"
#include "xgpio.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "xiltimer.h"
#include "sleep.h"
#include <stdint.h>
#ifndef SDT
#error This application requires the Vitis SDT BSP
#endif
#define CONFIG_VERSION "four-channel-c-adapter-v1"
#define BASE ((UINTPTR)0x00100000U)
#define LIMIT ((UINTPTR)0x01100000U)
#define GROUPS 32000U
#define WORDS_PER_GROUP 8U
#define PACKET 8000U
#define BYTES (GROUPS * WORDS_PER_GROUP * 4U)
#define GUARD 64U
#define SENTINEL 0xa5a55a5aU
#define DMA_ERRORS (XAXIDMA_ERR_ALL_MASK | XAXIDMA_IRQ_ERROR_MASK)
#define SOURCE_FATAL ((1U << 2) | (1U << 5))
_Static_assert(BYTES + GUARD <= 0x100000U, "RX region exceeded");
_Static_assert(BYTES % PACKET == 0 && PACKET % 32 == 0, "Packet/cache alignment");
static XAxiDma dma;
static XGpio gpio;
static int dma_ready, gpio_ready;
static u32 packet_sr[BYTES/PACKET], packet_len[BYTES/PACKET];
extern char end[];
static u32 sr(void) { return XAxiDma_ReadReg(dma.RegBase,XAXIDMA_RX_OFFSET+XAXIDMA_SR_OFFSET); }
static u32 status(void) { return XGpio_DiscreteRead(&gpio,2); }
static int expired(XTime begin, unsigned seconds) {
    XTime now; XTime_GetTime(&now);
    return now-begin > (XTime)COUNTS_PER_SECOND*seconds;
}
static void retain(void) { while (1) usleep(100000); }
int main(void) {
    XAxiDma_Config *cfg;
    XTime begin;
    const char *reason="not-started";
    unsigned p=0, completed=0, bad_group=0, bad_lane=0;
    unsigned zeros[4]={0}, clips[4]={0}, clip_groups=0;
    int32_t minimum[4]={8388607,8388607,8388607,8388607};
    int32_t maximum[4]={-8388608,-8388608,-8388608,-8388608};
    uint64_t previous=0, first=0;
    u32 fnv=2166136261U, final_source;
    volatile u32 *rx=(volatile u32*)BASE;
    xil_printf("\r\nFOUR PDM capture %s build %s %s\r\n",CONFIG_VERSION,__DATE__,__TIME__);
    xil_printf("C adapter DATA1..4=mic0..3; CLK1..4 common PDM phase; J4 numbered 1:1\r\n");
    xil_printf("layout=ss-four-record-0.1 groups=%u packet_bytes=%u bytes=%u guard=%u\r\n",GROUPS,PACKET,BYTES,GUARD);
    xil_printf("Program end=%08x RX=[01000000,01100000) configured_fs=48000 duration=32000/48000 seconds\r\n",(u32)(UINTPTR)end);
    if ((UINTPTR)end>BASE || BASE<XPAR_PS7_DDR_0_BASEADDRESS ||
        LIMIT-1U>XPAR_PS7_DDR_0_HIGHADDRESS || BASE+BYTES+GUARD>LIMIT) {
        reason="buffer-region"; goto fail;
    }
    if (XGpio_Initialize(&gpio,XPAR_AXI_GPIO_0_BASEADDR)!=XST_SUCCESS) {
        reason="gpio-init"; goto fail;
    }
    gpio_ready=1;
    if (!gpio.IsDual) { reason="gpio-not-dual"; goto fail; }
    XGpio_DiscreteWrite(&gpio,1,0); XGpio_SetDataDirection(&gpio,1,0);
    XGpio_SetDataDirection(&gpio,2,0xffffffffU);
    cfg=XAxiDma_LookupConfig(XPAR_AXI_DMA_0_BASEADDR);
    if (!cfg || cfg->HasSg || !cfg->HasS2Mm || cfg->MicroDmaMode) {
        reason="dma-config"; goto fail;
    }
    if (XAxiDma_CfgInitialize(&dma,cfg)!=XST_SUCCESS) { reason="dma-init"; goto fail; }
    dma_ready=1;
    XAxiDma_IntrDisable(&dma,XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);
    xil_printf("INIT DMA_SR=%08x SOURCE_STATUS=%08x\r\n",sr(),status());
    XTime_GetTime(&begin);
    while (!(status()&2U)) {
        if (status()&SOURCE_FATAL) { reason="warmup-fatal"; goto fail; }
        if (expired(begin,2)) { reason="warmup-timeout"; goto fail; }
    }
    if (status()&(SOURCE_FATAL|1U|0xffff0000U)) { reason="source-not-clean-idle"; goto fail; }
    Xil_DCacheEnable();
    for (unsigned i=0;i<(BYTES+GUARD)/4;i++) rx[i]=SENTINEL;
    Xil_DCacheFlushRange((INTPTR)BASE,BYTES+GUARD);
    Xil_DCacheInvalidateRange((INTPTR)BASE,BYTES+GUARD);
    xil_printf("Cache ON: full RX+guard flush/invalidate before DMA; invalidate after; no CPU RX access during DMA\r\n");
    for (p=0;p<BYTES/PACKET;p++) {
        XAxiDma_IntrAckIrq(&dma,XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);
        if (XAxiDma_SimpleTransfer(&dma,BASE+p*PACKET,PACKET,XAXIDMA_DEVICE_TO_DMA)!=XST_SUCCESS) {
            reason="dma-arm"; goto fail;
        }
        if (p==0) { XGpio_DiscreteWrite(&gpio,1,1); usleep(10); XGpio_DiscreteWrite(&gpio,1,0); }
        XTime_GetTime(&begin);
        while (1) {
            u32 s=sr(), st=status();
            if (st&SOURCE_FATAL) { reason="source-overflow-or-sync-error"; goto fail; }
            if (s&DMA_ERRORS) { reason="dma-error"; goto fail; }
            if (expired(begin,2)) { reason="dma-timeout"; goto fail; }
            if ((s&XAXIDMA_IRQ_IOC_MASK) && (s&XAXIDMA_IDLE_MASK)) break;
        }
        packet_sr[p]=sr();
        packet_len[p]=XAxiDma_ReadReg(dma.RegBase,XAXIDMA_RX_OFFSET+XAXIDMA_BUFFLEN_OFFSET);
        if (packet_len[p]!=PACKET) { reason="packet-length"; goto fail; }
        completed++;
    }
    Xil_DCacheInvalidateRange((INTPTR)BASE,BYTES+GUARD);
    final_source=status();
    if ((final_source&(SOURCE_FATAL|1U|0xffff0000U)) || !(final_source&8U)) {
        reason="source-final-status"; goto fail;
    }
    for (unsigned i=BYTES/4;i<(BYTES+GUARD)/4;i++)
        if (rx[i]!=SENTINEL) { reason="guard-overwrite"; goto fail; }
    for (unsigned i=0;i<GROUPS;i++) {
        uint64_t id=((uint64_t)rx[8*i+1]<<32)|rx[8*i];
        u32 flags=rx[8*i+6]; bad_group=i;
        if (i==0) first=id;
        else if (previous==UINT64_MAX || id!=previous+1U) { reason="id-discontinuity"; goto fail; }
        previous=id;
        if ((flags&~15U) || rx[8*i+7]) { reason="flags-or-reserved"; goto fail; }
        if (flags) clip_groups++;
        for (unsigned ch=0;ch<4;ch++) {
            int32_t v=(int32_t)rx[8*i+2+ch]; bad_lane=ch;
            if (v < -8388608 || v > 8388607) { reason="signed24-range"; goto fail; }
            if (v<minimum[ch]) minimum[ch]=v;
            if (v>maximum[ch]) maximum[ch]=v;
            if (!v) zeros[ch]++;
            if (flags&(1U<<ch)) clips[ch]++;
        }
    }
    if (!!(final_source&16U) != !!clip_groups) { reason="clip-status-mismatch"; goto fail; }
    for (unsigned i=0;i<BYTES;i++) { fnv^=((volatile unsigned char*)BASE)[i]; fnv*=16777619U; }
    /* Logging deferred until capture ends, to avoid FIFO overflow from UART. */
    for (unsigned i=0;i<completed;i++) xil_printf("DONE packet=%u actual_bytes=%u DMA_SR=%08x\r\n",i,packet_len[i],packet_sr[i]);
    xil_printf("FOUR_CAPTURE_INTEGRITY_PASS groups=%u bytes=%u packets=%u clip_groups=%u\r\n",GROUPS,BYTES,completed,clip_groups);
    xil_printf("first_id_hex=%08x%08x last_id_hex=%08x%08x\r\n",(u32)(first>>32),(u32)first,(u32)(previous>>32),(u32)previous);
    for (unsigned ch=0;ch<4;ch++) xil_printf("mic%u min=%d max=%d zeros=%u clipped=%u\r\n",ch,(int)minimum[ch],(int)maximum[ch],zeros[ch],clips[ch]);
    xil_printf("DMA_SR=%08x SOURCE_STATUS=%08x sync_error=%u overflow=%u fnv1a32=%08x\r\n",sr(),final_source,(final_source>>5)&1U,(final_source>>2)&1U,fnv);
    xil_printf("READY_FOR_DDR_DUMP base=01000000 bytes=1024000 words=256000\r\n");
    xil_printf("diagnostic only; flags preserved; not acoustic acceptance. Do not reset/re-run before dump.\r\n");
    retain(); return 0;
fail:
    /* Record registers BEFORE reset; never call this partial capture clean. */
    xil_printf("FOUR_CAPTURE_FAIL reason=%s packet=%u completed_packets=%u completed_bytes=%u group=%u lane=%u\r\n",reason,p,completed,completed*PACKET,bad_group,bad_lane);
    if (gpio_ready) {
        u32 st=status();
        xil_printf("SOURCE_STATUS=%08x overflow=%u sync_error=%u rejected_events=%u\r\n",st,(st>>2)&1U,(st>>5)&1U,st>>16);
        XGpio_DiscreteWrite(&gpio,1,0);
    }
    if (dma_ready) {
        xil_printf("DMA_SR_BEFORE_RESET=%08x\r\n",sr()); XAxiDma_Reset(&dma);
        XTime_GetTime(&begin);
        while (!XAxiDma_ResetIsDone(&dma)) if (expired(begin,2)) {
            xil_printf("DMA_RESET_TIMEOUT: DDR may not be stable; do not call dump valid\r\n"); retain();
        }
        Xil_DCacheInvalidateRange((INTPTR)BASE,BYTES+GUARD);
    }
    for (unsigned i=0;i<completed;i++) xil_printf("PARTIAL packet=%u actual_bytes=%u DMA_SR=%08x\r\n",i,packet_len[i],packet_sr[i]);
    xil_printf("REJECT_ACQUISITION: preserve serial and diagnostic buffer separately; no H1 clean export. Reset PS/PL before retry.\r\n");
    retain(); return 1;
}
