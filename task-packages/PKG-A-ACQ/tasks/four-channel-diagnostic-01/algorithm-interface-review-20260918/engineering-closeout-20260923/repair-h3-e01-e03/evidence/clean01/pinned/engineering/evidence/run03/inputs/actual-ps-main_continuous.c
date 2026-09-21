/* Independent C1 prototype. Never run with the short-capture bitstream.
 * Core 0 standalone, no other core/DMA/XSDB access to RX while running.
 */
#include "xparameters.h"
#include "xaxidma.h"
#include "xaxidma_hw.h"
#include "xgpio.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "xiltimer.h"
#include "sleep.h"
#include "continuous_core.h"
#include "scene_store.h"
#ifndef SDT
#error Vitis SDT Cortex-A9 BSP required
#endif
static XAxiDma dma;
static XGpio gpio;
static struct session sessions[1];
/* Allocated by the existing linker BELOW RX_BASE, never a hard-coded DDR address. */
__attribute__((aligned(64),used)) uint32_t scene_archive[SCENE_TOTAL_WORDS];
static struct scene_store archive;
static int archive_ready;
static uint32_t verify_packet[SLOT_STRIDE/4U];
static int dma_ready,gpio_ready;
static unsigned started,completed;
extern char end[];
// Used constants in the actual compilation unit, verified in .o AND ELF.
__attribute__((used,section(".rodata.continuous_contract")))
const uint32_t continuous_contract[]={0x434f4e31U,RX_BASE,RX_LIMIT,GROUPS_PER_PACKET,
    WORDS_PER_GROUP,PACKET_BYTES,GUARD_BYTES,SLOT_STRIDE,SLOT_COUNT,RX_USED,
    XPAR_PS7_DDR_0_BASEADDRESS,XPAR_PS7_DDR_0_HIGHADDRESS,
    XPAR_AXI_DMA_0_BASEADDR,XPAR_AXI_GPIO_0_BASEADDR,SHORT_RUN_US,SHORT_MIN_GROUPS};
__attribute__((used,section(".rodata.scene_contract")))
const uint32_t scene_contract[]={0x53434e31U,1U,RUN_US,MIN_GROUPS,SCENE_CAP_GROUPS,
    SCENE_CAP_BYTES,GUARD_BYTES,2U,WORDS_PER_GROUP*4U,48000U,TIMEOUT_US};
_Static_assert(SCENE_CAP_GROUPS%GROUPS_PER_PACKET==0, "whole packet capacity");
static enum failure save_packet(void *ctx,const uint32_t *p) {
    (void)ctx;return scene_append(&archive,p);
}
/* Post-stop readback, reusing the exact packet checks and comparing all statistics. */
static int archive_matches(struct session *s) {
    struct session checked;session_init(&checked);
    if(!scene_guards_ok(&archive) || archive.saved_groups!=s->groups)return 0;
    for(unsigned g=0;g<archive.saved_groups;g+=GROUPS_PER_PACKET) {
        memcpy(verify_packet,archive.data+g*WORDS_PER_GROUP,PACKET_BYTES);
        for(unsigned w=PACKET_BYTES/4U;w<SLOT_STRIDE/4U;w++)verify_packet[w]=SENTINEL;
        if(check_packet(&checked,verify_packet)!=OK)return 0;
    }
    return checked.groups==s->groups && checked.packets==s->packets &&
        checked.first_id==s->first_id && checked.last_id==s->last_id &&
        memcmp(checked.minimum,s->minimum,sizeof(s->minimum))==0 &&
        memcmp(checked.maximum,s->maximum,sizeof(s->maximum))==0 &&
        memcmp(checked.zeros,s->zeros,sizeof(s->zeros))==0 &&
        memcmp(checked.clips,s->clips,sizeof(s->clips))==0;
}
static uint64_t now_us(void *ctx)
{
    XTime t;
    (void)ctx;
    XTime_GetTime(&t);
    return (uint64_t)t * 1000000U / (COUNTS_PER_SECOND);
}
static uint32_t src(void *ctx){(void)ctx;return XGpio_DiscreteRead(&gpio,2);}
static uint32_t sr(void *ctx){(void)ctx;return XAxiDma_ReadReg(dma.RegBase,XAXIDMA_RX_OFFSET+XAXIDMA_SR_OFFSET);}
static uint32_t length(void *ctx){(void)ctx;return XAxiDma_ReadReg(dma.RegBase,XAXIDMA_RX_OFFSET+XAXIDMA_BUFFLEN_OFFSET);}
static void run_level(void *ctx,int v){(void)ctx;XGpio_DiscreteWrite(&gpio,1,(unsigned)v);}
static UINTPTR address(unsigned slot){return RX_BASE+slot*SLOT_STRIDE;}
static void prepare(void *ctx,unsigned slot){
    (void)ctx;volatile uint32_t *p=(volatile uint32_t*)address(slot);
    for(unsigned i=0;i<SLOT_STRIDE/4;i++)p[i]=SENTINEL;
    Xil_DCacheFlushRange((INTPTR)p,SLOT_STRIDE);
    Xil_DCacheInvalidateRange((INTPTR)p,SLOT_STRIDE);
}
static const uint32_t *acquire(void *ctx,unsigned slot){
    (void)ctx;UINTPTR a=address(slot);Xil_DCacheInvalidateRange((INTPTR)a,SLOT_STRIDE);
    return (const uint32_t*)a;
}
static int arm(void *ctx,unsigned slot,uint32_t bytes){
    (void)ctx;XAxiDma_IntrAckIrq(&dma,XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);
    return XAxiDma_SimpleTransfer(&dma,address(slot),bytes,XAXIDMA_DEVICE_TO_DMA)!=XST_SUCCESS;
}
static void retain(void){for(;;)usleep(100000);}
static void print_session(unsigned n,struct session *s){
    xil_printf("SESSION %u result=%s groups=%u packets=%u bytes_checked=%u stop_sent=%u\r\n",n,failure_name(s->failed),s->groups,s->packets,s->packets*PACKET_BYTES,s->stop_sent);
    xil_printf("first=%08x%08x last=%08x%08x capture_command_us=%u drain_us=%u max_check_us=%u max_arm_gap_us=%u\r\n",(u32)(s->first_id>>32),(u32)s->first_id,(u32)(s->last_id>>32),(u32)s->last_id,s->stop_sent?(u32)(s->stop_us-s->start_us):0,s->stop_sent?(u32)(s->end_us-s->stop_us):0,(u32)s->max_check_us,(u32)s->max_arm_gap_us);
    xil_printf("SOURCE=%08x DMA_SR=%08x length=%u active=%d owners=%u,%u bad_group=%u bad_lane=%u bad_value=%08x\r\n",s->last_source,s->last_sr,s->last_length,s->active,s->owner[0],s->owner[1],s->bad_group,s->bad_lane,s->bad_value);
    xil_printf("CHECK first_failure=%s verified_packets=%u verified_groups=%u guard_checked_per_verified_packet=1\r\n",failure_name(s->failed),s->packets,s->groups);
    unsigned first=s->trace_count>16?s->trace_count-16:0;
    for(unsigned i=first;i<s->trace_count;i++){
        struct trace *t=&s->recent[i%16];
        xil_printf("TRACE packet=%u slot=%u SR=%08x SOURCE=%08x length=%u\r\n",t->packet,t->slot,t->sr,t->source,t->length);
    }
    for(unsigned c=0;c<4;c++)xil_printf("mic%u min=%d max=%d zeros=%u clip_flags=%u\r\n",c,s->minimum[c],s->maximum[c],s->zeros[c],s->clips[c]);
}
int main(void){
    const char *error="init";
    xil_printf("\r\nFOUR SCENE S1 candidate build %s %s\r\n",__DATE__,__TIME__);
    xil_printf("RX=[%08x,%08x) slot_stride=%u packet=%u guard=%u used=%u end=%08x\r\n",RX_BASE,RX_LIMIT,SLOT_STRIDE,PACKET_BYTES,GUARD_BYTES,RX_USED,(u32)(UINTPTR)end);
    xil_printf("PROFILE=S1_6S_RAW target_us=%u min_groups=%u capacity_groups=%u record_bytes=32 timeout_us=%u\r\n",RUN_US,MIN_GROUPS,SCENE_CAP_GROUPS,TIMEOUT_US);
    xil_printf("One continuous segment; original IDs/flags; CPU archive, no realtime UART\r\n");
    if((UINTPTR)end>RX_BASE || RX_BASE<XPAR_PS7_DDR_0_BASEADDRESS || RX_LIMIT-1U>XPAR_PS7_DDR_0_HIGHADDRESS){error="memory-contract";goto fail;}
    if((UINTPTR)scene_archive<XPAR_PS7_DDR_0_BASEADDRESS ||
       (UINTPTR)scene_archive%64U ||
       (UINTPTR)scene_archive+sizeof(scene_archive)>(UINTPTR)end ||
       (UINTPTR)scene_archive+sizeof(scene_archive)>RX_BASE){error="archive-contract";goto fail;}
    scene_store_init(&archive,scene_archive,SCENE_CAP_GROUPS);archive_ready=1;
    xil_printf("ARCHIVE allocation=%08x data=%08x capacity_bytes=%u total_bytes=%u guard_each=%u\r\n",
        (u32)(UINTPTR)scene_archive,(u32)(UINTPTR)archive.data,SCENE_CAP_BYTES,(u32)sizeof(scene_archive),GUARD_BYTES);
    if(XGpio_Initialize(&gpio,XPAR_AXI_GPIO_0_BASEADDR)!=XST_SUCCESS){error="gpio-init";goto fail;}
    gpio_ready=1;run_level(0,0);XGpio_SetDataDirection(&gpio,1,0);XGpio_SetDataDirection(&gpio,2,0xffffffffU);
    // Check ABI BEFORE DMA init, before writing RX or issuing start.
    if(!gpio.IsDual || (src(0)&0xff000000U)!=SOURCE_SIGNATURE){error="wrong-bitstream-C1-required";goto fail;}
    XAxiDma_Config *cfg=XAxiDma_LookupConfig(XPAR_AXI_DMA_0_BASEADDR);
    if(!cfg||cfg->HasSg||!cfg->HasS2Mm||cfg->MicroDmaMode){error="dma-config";goto fail;}
    if(XAxiDma_CfgInitialize(&dma,cfg)!=XST_SUCCESS){error="dma-init";goto fail;}
    dma_ready=1;XAxiDma_IntrDisable(&dma,XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);
    uint64_t t=now_us(0);
    while(!(src(0)&2U))if(src(0)&SOURCE_FATAL || now_us(0)-t>=TIMEOUT_US){error="warmup";goto fail;}
    Xil_DCacheEnable();
    const struct io io={0,now_us,src,sr,length,run_level,arm,prepare,acquire,save_packet};
    session_init(&sessions[0]);started=1;
    xil_printf("START session=0 target_us=%u min_groups=%u no_UART_until_stop\r\n",RUN_US,MIN_GROUPS);
    enum failure f=session_run(&sessions[0],&io);
    if(f){error=failure_name(f);goto fail;}
    if(!archive_matches(&sessions[0])){error="archive-readback-mismatch";goto fail;}
    completed=1;print_session(0,&sessions[0]);
    /* Source drained; both RX slots FREE. Publish dirty CPU archive to physical DDR. */
    Xil_DCacheFlushRange((INTPTR)scene_archive,sizeof(scene_archive));
    u32 bytes=archive.saved_groups*WORDS_PER_GROUP*4U;
    xil_printf("SCENE_INTEGRITY_PASS groups=%u packets=%u bytes=%u fnv1a32=%08x guard_ok=1\r\n",
        archive.saved_groups,sessions[0].packets,bytes,scene_fnv1a(&archive));
    xil_printf("READY_FOR_DDR_DUMP base=%08x bytes=%u words=%u\r\n",(u32)(UINTPTR)archive.data,bytes,bytes/4U);
    xil_printf("SUMMARY started=%u completed=%u failures=0; diagnostic only; NOT acoustic acceptance\r\n",started,completed);
    xil_printf("RUN LOW, drained; DO NOT reset/re-run before BIN dump; no further capture during export\r\n");retain();return 0;
fail:
    // Freeze pre-reset registers FIRST, deassert RUN, then quiesce DMA. No auto retry.
    {u32 pre_src=gpio_ready?src(0):0,pre_sr=dma_ready?sr(0):0;
    if(gpio_ready)run_level(0,0);
    xil_printf("CONTINUOUS_FAIL reason=%s PRE_RESET_SOURCE=%08x PRE_RESET_DMA=%08x\r\n",error,pre_src,pre_sr);}
    xil_printf("SUMMARY started=%u completed=%u failures=1 abort_no_retry=1\r\n",started,completed);
    for(unsigned n=0;n<started;n++)print_session(n,&sessions[n]);
    if(dma_ready){
        XAxiDma_Reset(&dma);uint64_t reset=now_us(0);
        while(!XAxiDma_ResetIsDone(&dma))if(now_us(0)-reset>=TIMEOUT_US){xil_printf("RESET_TIMEOUT DDR_NOT_STABLE\r\n");retain();}
        Xil_DCacheInvalidateRange((INTPTR)RX_BASE,RX_USED);
    }
    if(archive_ready){
        Xil_DCacheFlushRange((INTPTR)scene_archive,sizeof(scene_archive));
        xil_printf("FAILED_ARCHIVE_PREFIX base=%08x groups=%u bytes=%u guard_ok=%u NOT_SUCCESS_CAPTURE\r\n",
            (u32)(UINTPTR)archive.data,archive.saved_groups,archive.saved_groups*32U,scene_guards_ok(&archive));
    }
    xil_printf("FAIL retained; PL sticky NOT cleared. Save full UART and optional diagnostic RX dump 4032 words; reset PS+PL explicitly before retry\r\n");
    retain();return 1;
}
