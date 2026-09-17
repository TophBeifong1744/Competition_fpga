/* Host syntax check ONLY; not a BSP model, not linked, never used in firmware. */
#ifndef SCENE_TEST_STUBS_H
#define SCENE_TEST_STUBS_H
#include <stdint.h>
typedef uint32_t u32;
typedef uintptr_t UINTPTR;
typedef intptr_t INTPTR;
typedef uint64_t XTime;
#define SDT 1
#define COUNTS_PER_SECOND 333333343U
#define XPAR_PS7_DDR_0_BASEADDRESS 0x00100000U
#define XPAR_PS7_DDR_0_HIGHADDRESS 0x3fffffffU
#define XPAR_AXI_DMA_0_BASEADDR 0x40400000U
#define XPAR_AXI_GPIO_0_BASEADDR 0x41200000U
#define XAXIDMA_RX_OFFSET 0x30U
#define XAXIDMA_SR_OFFSET 0x04U
#define XAXIDMA_BUFFLEN_OFFSET 0x28U
#define XAXIDMA_IRQ_ALL_MASK 0x7000U
#define XAXIDMA_DEVICE_TO_DMA 1
#define XST_SUCCESS 0
typedef struct { UINTPTR RegBase; } XAxiDma;
typedef struct { int IsDual; } XGpio;
typedef struct { int HasSg,HasS2Mm,MicroDmaMode; } XAxiDma_Config;
void XTime_GetTime(XTime*);
u32 XGpio_DiscreteRead(XGpio*,unsigned);
void XGpio_DiscreteWrite(XGpio*,unsigned,u32);
void XGpio_SetDataDirection(XGpio*,unsigned,u32);
int XGpio_Initialize(XGpio*,UINTPTR);
u32 XAxiDma_ReadReg(UINTPTR,u32);
void XAxiDma_IntrAckIrq(XAxiDma*,u32,int);
void XAxiDma_IntrDisable(XAxiDma*,u32,int);
int XAxiDma_SimpleTransfer(XAxiDma*,UINTPTR,u32,int);
XAxiDma_Config *XAxiDma_LookupConfig(UINTPTR);
int XAxiDma_CfgInitialize(XAxiDma*,XAxiDma_Config*);
void XAxiDma_Reset(XAxiDma*);
int XAxiDma_ResetIsDone(XAxiDma*);
void Xil_DCacheFlushRange(INTPTR,u32);
void Xil_DCacheInvalidateRange(INTPTR,u32);
void Xil_DCacheEnable(void);
void xil_printf(const char*,...);
int usleep(unsigned long);
#endif
