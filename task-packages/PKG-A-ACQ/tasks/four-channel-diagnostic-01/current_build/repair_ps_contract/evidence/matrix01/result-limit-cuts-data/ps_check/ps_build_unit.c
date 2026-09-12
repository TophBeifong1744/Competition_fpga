#include "../inputs/ps/main_four_capture.c"
_Static_assert(sizeof(u32) == 4 && sizeof(UINTPTR) == 4, "ARM32 ABI");
__attribute__((used, section(".rodata.ss_build_ps_contract")))
const unsigned int ss_build_ps_contract[] = {
0x53535043U, 1U, BASE, LIMIT, GROUPS, WORDS_PER_GROUP, BYTES, PACKET, GUARD,
XPAR_PS7_DDR_0_BASEADDRESS, XPAR_PS7_DDR_0_HIGHADDRESS, sizeof(u32), sizeof(UINTPTR)
};
