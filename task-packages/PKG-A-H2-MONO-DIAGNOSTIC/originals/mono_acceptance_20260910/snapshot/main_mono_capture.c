/* Requires NEW XSA: shared 61.44MHz AXI domain; GPIO ch1 output1,
 * GPIO ch2 input32 connected to single_mic_top.status. NOT old test-source bit.
 * Region reserved by lscript.ld: program ends below 0x01000000.
 * Keep other cores/DMA away from RX. Captures once; holds buffer for JTAG dump.
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
#error Requires SDT BSP
#endif
#define BASE ((UINTPTR)0x01000000U)
#define LIMIT ((UINTPTR)0x01100000U)
#define SAMPLES 48000U
#define PACKET 4000U
#define BYTES (SAMPLES*16U)
#define ERR (XAXIDMA_ERR_ALL_MASK|XAXIDMA_IRQ_ERROR_MASK)
static XAxiDma dma;
static XGpio gpio;
extern char end[];
static u32 sr(void){return XAxiDma_ReadReg(dma.RegBase,XAXIDMA_RX_OFFSET+XAXIDMA_SR_OFFSET);}
static int expired(XTime begin,unsigned secs){
 XTime now;XTime_GetTime(&now);return now-begin>(XTime)COUNTS_PER_SECOND*secs;
}
int main(void){
 XAxiDma_Config *cfg;
 XTime begin;
 unsigned p=0,zeros=0,clips=0;
 int32_t minimum=8388607,maximum=-8388608;
 uint64_t previous=0,first=0;
 u32 fnv=2166136261U;
 volatile u32 *rx=(volatile u32*)BASE;
 xil_printf("\r\nMONO PDM capture v1 build %s %s\r\n",__DATE__,__TIME__);
 if((UINTPTR)end>BASE || BASE<(UINTPTR)XPAR_PS7_DDR_0_BASEADDRESS ||
    LIMIT-1U>(UINTPTR)XPAR_PS7_DDR_0_HIGHADDRESS || BASE+BYTES+64U>LIMIT){
  xil_printf("FAIL buffer region\r\n");return 1;
 }
 if(XGpio_Initialize(&gpio,XPAR_AXI_GPIO_0_BASEADDR)!=XST_SUCCESS)return 1;
 if(!gpio.IsDual){xil_printf("FAIL requires NEW dual-channel GPIO XSA\r\n");return 1;}
 XGpio_DiscreteWrite(&gpio,1,0);XGpio_SetDataDirection(&gpio,1,0);
 XGpio_SetDataDirection(&gpio,2,0xffffffffU);
 cfg=XAxiDma_LookupConfig(XPAR_AXI_DMA_0_BASEADDR);
 if(!cfg||cfg->HasSg||!cfg->HasS2Mm||cfg->MicroDmaMode)return 1;
 if(XAxiDma_CfgInitialize(&dma,cfg)!=XST_SUCCESS)return 1;
 XAxiDma_IntrDisable(&dma,XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);
 XTime_GetTime(&begin);
 while(!(XGpio_DiscreteRead(&gpio,2)&2U)){
  if(expired(begin,2)){xil_printf("FAIL audio clock/warmup timeout\r\n");return 1;}
 }
 if(XGpio_DiscreteRead(&gpio,2)&5U){xil_printf("FAIL source busy or overflow; reset PL\r\n");return 1;}
 Xil_DCacheEnable();
 for(unsigned i=0;i<(BYTES+64U)/4U;i++)rx[i]=0xa5a55a5aU;
 Xil_DCacheFlushRange((INTPTR)BASE,BYTES+64U);
 Xil_DCacheInvalidateRange((INTPTR)BASE,BYTES+64U);
 for(p=0;p<BYTES/PACKET;p++){
  XAxiDma_IntrAckIrq(&dma,XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);
  if(XAxiDma_SimpleTransfer(&dma,BASE+p*PACKET,PACKET,XAXIDMA_DEVICE_TO_DMA)!=XST_SUCCESS)goto fail;
  if(p==0){XGpio_DiscreteWrite(&gpio,1,1);usleep(10);XGpio_DiscreteWrite(&gpio,1,0);}
  XTime_GetTime(&begin);
  while(1){
   u32 s=sr();
   if((s&ERR)||(XGpio_DiscreteRead(&gpio,2)&4U)||expired(begin,2))goto fail;
   if((s&XAXIDMA_IRQ_IOC_MASK)&&(s&XAXIDMA_IDLE_MASK))break;
  }
  if(XAxiDma_ReadReg(dma.RegBase,XAXIDMA_RX_OFFSET+XAXIDMA_BUFFLEN_OFFSET)!=PACKET)goto fail;
 }
 Xil_DCacheInvalidateRange((INTPTR)BASE,BYTES+64U);
 if(!(XGpio_DiscreteRead(&gpio,2)&8U))goto fail;
 for(unsigned i=BYTES/4U;i<(BYTES+64U)/4U;i++)if(rx[i]!=0xa5a55a5aU)goto fail;
 for(unsigned i=0;i<SAMPLES;i++){
  uint64_t id=((uint64_t)rx[4*i+1]<<32)|rx[4*i];
  int32_t v=(int32_t)rx[4*i+2];u32 flags=rx[4*i+3];
  if(i==0)first=id;
  else if(id!=previous+1U)goto fail;
  previous=id;
  if(v < -8388608 || v>8388607 || (flags&~2U))goto fail;
  if(v<minimum)minimum=v;
  if(v>maximum)maximum=v;
  if(v==0)zeros++;
  if(flags&2U)clips++;
 }
 for(unsigned i=0;i<BYTES;i++){fnv^=((volatile unsigned char*)BASE)[i];fnv*=16777619U;}
 xil_printf("CAPTURE_INTEGRITY_PASS samples=%u bytes=%u packets=%u\r\n",SAMPLES,BYTES,BYTES/PACKET);
 xil_printf("first_id_hex=%08x%08x last_id_hex=%08x%08x\r\n",(u32)(first>>32),(u32)first,(u32)(previous>>32),(u32)previous);
 xil_printf("min=%d max=%d zeros=%u clipped=%u\r\n",(int)minimum,(int)maximum,zeros,clips);
 xil_printf("DMA_SR=%08x SOURCE_STATUS=%08x fnv1a32=%08x\r\n",sr(),XGpio_DiscreteRead(&gpio,2),fnv);
 xil_printf("READY_FOR_DDR_DUMP base=01000000 bytes=768000 words=192000\r\n");
 xil_printf("Integrity is not acoustic acceptance. Do not reset/re-run before dump.\r\n");
 while(1){usleep(100000);}
fail:
 xil_printf("FAIL packet=%u DMA_SR=%08x SOURCE_STATUS=%08x\r\n",p,sr(),XGpio_DiscreteRead(&gpio,2));
 XGpio_DiscreteWrite(&gpio,1,0);XAxiDma_Reset(&dma);
 xil_printf("Reject this acquisition; reset PS/PL before retry.\r\n");
 return 1;
}
