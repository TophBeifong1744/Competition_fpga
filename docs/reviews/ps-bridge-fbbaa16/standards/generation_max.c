#include "ps_bridge.h"
#include <assert.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
static struct psb_bridge bridge;
static void feed(uint32_t start, size_t count) {
 uint8_t data[8000]={0}; struct psb_token t;
 for(size_t i=0;i<count;i++) { uint32_t id=start+(uint32_t)i; for(unsigned j=0;j<4;j++)data[i*32+j]=(uint8_t)(id>>(8*j)); }
 assert(psb_enqueue(&bridge,data,count*32,NULL,0,&t)==PSB_OK);
 assert(psb_pump(&bridge)==PSB_OK);
}
int main(void) {
 struct psb_config config={0};struct psb_hooks hooks={0};
 memset(config.binding,1,sizeof(config.binding));config.max_rows=UINT64_MAX;
 config.max_frame=UINT32_MAX-1;config.max_interval=UINT32_MAX-1;config.required_status=1;config.ttl_samples=512;
 assert(psb_init(&bridge,&config,&hooks)==PSB_OK);assert(psb_start(&bridge,1)==PSB_OK);
 for(uint32_t i=0;i<4;i++)feed(i*250,250);
 /* Authorized finite-counter boundary injection; frames are produced only by enqueue/pump. */
 bridge.generation=UINT64_MAX-2;
 feed(1000,24);
 assert(bridge.frame[0].owner==PSB_READY);assert(bridge.frame[0].token.generation==UINT64_MAX);
 struct psb_token token={0};const struct psb_frame *frame=NULL;
 enum psb_rc rc=psb_frame_acquire(&bridge,&token,&frame);
 printf("published_generation=%" PRIu64 " owner=%d acquire_rc=%d active=%d failed=%d\n",bridge.frame[0].token.generation,bridge.frame[0].owner,rc,bridge.active,bridge.failed);
 printf("expected=PSB_OK(%d); observed=PSB_WAIT(%d); generated READY frame is unreachable\n",PSB_OK,PSB_WAIT);
 return rc==PSB_WAIT && !bridge.failed ? 0:1;
}
