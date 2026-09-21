#define main primary_probe_main
#include "probe.c"
#undef main
int main(void){
 memset(&original,0,sizeof original);memset(original.binding,0x31,sizeof original.binding);
 original.ttl_samples=4096;original.max_rows=UINT64_MAX;original.max_frame=100;original.max_interval=100;original.required_status=3;
 struct psb_hooks h={0};h.clock=clockfn;REQUIRE(psb_init(&b,&original,&h)==PSB_OK);REQUIRE(psb_start(&b,1)==PSB_OK);
 feed(0,1023,0);
 b.generation=UINT64_MAX-2u; /* Contract explicitly permits finite-counter white-box injection. */
 feed(1023,1,0); /* enqueue uses MAX-1; publish uses MAX. */
 REQUIRE(b.frame[0].owner==PSB_READY && b.frame[0].token.generation==UINT64_MAX);
 struct psb_token token;const struct psb_frame *view=NULL;
 enum psb_rc rc=psb_frame_acquire(&b,&token,&view);
 printf("generation_max_ready acquire=%u failed=%u active=%u ready=%u\n",(unsigned)rc,(unsigned)b.failed,(unsigned)b.active,(unsigned)(b.frame[0].owner==PSB_READY));
 return 0;
}
