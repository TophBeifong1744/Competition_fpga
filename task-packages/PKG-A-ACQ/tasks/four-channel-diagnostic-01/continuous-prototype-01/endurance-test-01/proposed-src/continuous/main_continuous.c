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
#ifndef SDT
#error Vitis SDT Cortex-A9 BSP required
#endif
static XAxiDma dma;
static XGpio gpio;
static struct session sessions[SESSION_COUNT];
static int dma_ready,gpio_ready;
static unsigned started,completed;
extern char end[];
// Used constants in the actual compilation unit, verified in .o AND ELF.
__attribute__((used,section(".rodata.continuous_contract")))
const uint32_t continuous_contract[]={0x434f4e31U,RX_BASE,RX_LIMIT,GROUPS_PER_PACKET,
    WORDS_PER_GROUP,PACKET_BYTES,GUARD_BYTES,SLOT_STRIDE,SLOT_COUNT,RX_USED,
    XPAR_PS7_DDR_0_BASEADDRESS,XPAR_PS7_DDR_0_HIGHADDRESS,
    XPAR_AXI_DMA_0_BASEADDR,XPAR_AXI_GPIO_0_BASEADDR,SHORT_RUN_US,SHORT_MIN_GROUPS};
__attribute__((used,section(".rodata.endurance_contract")))
const uint32_t endurance_contract[]={0x454e4431U,1U,LONG_RUN_US,LONG_MIN_GROUPS,
    SHORT_RUN_US,SHORT_MIN_GROUPS,SHORT_SESSIONS,SESSION_COUNT,RESTART_GAP_US,TIMEOUT_US};
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
    xil_printf("\r\nFOUR ENDURANCE E1 candidate build %s %s\r\n",__DATE__,__TIME__);
    xil_printf("RX=[%08x,%08x) slot_stride=%u packet=%u guard=%u used=%u end=%08x\r\n",RX_BASE,RX_LIMIT,SLOT_STRIDE,PACKET_BYTES,GUARD_BYTES,RX_USED,(u32)(UINTPTR)end);
    xil_printf("PROFILE=E1_300S_10X10S long_us=%u long_groups=%u short_us=%u short_groups=%u short_count=%u gap_us=%u timeout_us=%u\r\n",
        LONG_RUN_US,LONG_MIN_GROUPS,SHORT_RUN_US,SHORT_MIN_GROUPS,SHORT_SESSIONS,RESTART_GAP_US,TIMEOUT_US);
    xil_printf("One >=300s segment + ten >=10s segments; no PS/PL/DMA reset between; no full audio archive\r\n");
    if((UINTPTR)end>RX_BASE || RX_BASE<XPAR_PS7_DDR_0_BASEADDRESS || RX_LIMIT-1U>XPAR_PS7_DDR_0_HIGHADDRESS){error="memory-contract";goto fail;}
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
    const struct io io={0,now_us,src,sr,length,run_level,arm,prepare,acquire};
    for(unsigned n=0;n<SESSION_COUNT;n++){
        session_init(&sessions[n]);
        started=n+1U;
        xil_printf("START session=%u target_us=%u min_groups=%u no_UART_until_stop\r\n",n,endurance_schedule[n].run_us,endurance_schedule[n].min_groups);
        enum failure f=session_run_config(&sessions[n],&io,&endurance_schedule[n]);
        if(f){error=failure_name(f);goto fail;}
        if(n && sessions[n].first_id<=sessions[n-1U].last_id){
            sessions[n].failed=ID_ERROR;error="restart-id-did-not-advance";goto fail;
        }
        completed=n+1U;
        // Both DMA and source are idle. No active producer while printing.
        print_session(n,&sessions[n]);
        if(n+1U<SESSION_COUNT){xil_printf("DRAINED; restart acquisition only in 1s; IDs may gap across this intentional stop\r\n");usleep(RESTART_GAP_US);}
    }
    xil_printf("ENDURANCE_11_SESSIONS_PASS_NOT_ACCEPTANCE; online checked/recycled, NOT a saved continuous BIN\r\n");
    xil_printf("SUMMARY started=%u completed=%u failures=0 normal_between_session_resets=0\r\n",started,completed);
    xil_printf("RUN level LOW; retain logs; no board acceptance or hour-long claim\r\n");retain();return 0;
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
    xil_printf("FAIL retained; PL sticky NOT cleared. Save full UART and optional diagnostic RX dump 4032 words; reset PS+PL explicitly before retry\r\n");
    retain();return 1;
}
