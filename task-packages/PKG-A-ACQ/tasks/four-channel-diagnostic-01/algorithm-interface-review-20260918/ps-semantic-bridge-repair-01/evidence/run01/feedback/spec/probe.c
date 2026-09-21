#include "ps_bridge.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <inttypes.h>
static struct psb_bridge b;
static struct psb_config original;
static uint64_t tick=1023;
#define REQUIRE(x) do { if(!(x)){fprintf(stderr,"setup failure line %d\n",__LINE__);exit(2);} }while(0)
static bool clockfn(void *ctx,uint64_t *now){(void)ctx;*now=tick;return true;}
static void put32(uint8_t *p,uint32_t n){for(unsigned j=0;j<4;j++)p[j]=(uint8_t)(n>>(j*8u));}
static void feed(unsigned first,unsigned count,unsigned flags){
 for(unsigned j=0;j<count;j++){
  uint8_t raw[32]={0};struct psb_token t;put32(raw,first+j);put32(raw+24,flags);
  REQUIRE(psb_enqueue(&b,raw,sizeof raw,NULL,0,&t)==PSB_OK);REQUIRE(psb_pump(&b)==PSB_OK);
 }
}
static struct psb_token setup(void){
 memset(&original,0,sizeof original);memset(original.binding,0x31,sizeof original.binding);
 original.ttl_samples=4096;original.max_rows=UINT64_MAX;original.max_frame=100;original.max_interval=100;original.required_status=3;
 struct psb_hooks h={0};h.clock=clockfn;REQUIRE(psb_init(&b,&original,&h)==PSB_OK);REQUIRE(psb_start(&b,1)==PSB_OK);tick=1023;
 feed(0,1024,0);struct psb_token f,r;const struct psb_frame *view;
 REQUIRE(psb_frame_acquire(&b,&f,&view)==PSB_OK);REQUIRE(psb_result_begin(&b,f,&r)==PSB_OK);REQUIRE(psb_frame_release(&b,f)==PSB_OK);return r;
}
static struct psb_completion comp(struct psb_token t,unsigned status,uint64_t payload){
 struct psb_completion c={0};c.token=t;c.status=status;c.payload=payload;memcpy(c.binding,original.binding,PSB_BINDING);return c;
}
static enum psb_rc dispatch(struct psb_completion *c,size_t n,enum psb_control ctrl){struct psb_batch batch={ctrl,false,c,n};return psb_dispatch(&b,&batch);}
static void show(const char *name,enum psb_rc rc,struct psb_token r){
 uint64_t payload=0;enum psb_rc take=psb_result_take(&b,r,&payload);
 REQUIRE(payload<=99u);
 printf("%s rc=%u failed=%u active=%u take=%u payload=%u reasons=%u\n",name,(unsigned)rc,(unsigned)b.failed,(unsigned)b.active,(unsigned)take,(unsigned)payload,b.reasons);
}
int main(void){
 for(unsigned which=0;which<3;which++){
  struct psb_token r=setup();struct psb_completion c=comp(r,3,7);REQUIRE(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK);
  if(which==0)feed(1024,1,1);else REQUIRE(dispatch(NULL,0,which==1?PSB_CONTROL_STOP:PSB_CONTROL_RESET)==PSB_OK);
  c.error=true;enum psb_rc rc=dispatch(&c,1,PSB_NO_CONTROL);REQUIRE(b.failed && b.result[r.slot].was_committed);show(which==0?"late_after_clip":which==1?"late_after_stop":"late_after_reset",rc,r);
 }
 {struct psb_token r=setup();struct psb_completion c=comp(r,3,7);REQUIRE(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK);
  REQUIRE(dispatch(NULL,0,PSB_CONTROL_STOP)==PSB_OK);REQUIRE(psb_result_release(&b,r)==PSB_OK);REQUIRE(psb_start(&b,2)==PSB_OK);
  c.error=true;enum psb_rc rc=dispatch(&c,1,PSB_NO_CONTROL);REQUIRE(!b.failed && b.active);show("old_session_error",rc,r);}
 {struct psb_token r=setup();struct psb_completion c=comp(r,3,7);REQUIRE(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK);
  uint64_t p;REQUIRE(psb_result_take(&b,r,&p)==PSB_OK);REQUIRE(psb_result_release(&b,r)==PSB_OK);c.error=true;
  enum psb_rc rc=dispatch(&c,1,PSB_NO_CONTROL);REQUIRE(b.failed);show("released_current_error",rc,r);}
 {struct psb_token r=setup();struct psb_completion c=comp(r,3,7);memset(original.binding,0x71,sizeof original.binding);
  enum psb_rc rc=dispatch(&c,1,PSB_NO_CONTROL);REQUIRE(rc==PSB_OK);show("external_config_mutation_snapshot",rc,r);}
 {struct psb_token r=setup();struct psb_completion c=comp(r,0,0);c.token.slot=PSB_RESULTS;c.error=true;
  enum psb_rc rc=dispatch(&c,1,PSB_NO_CONTROL);show("unknown_current_out_of_range_error",rc,r);}
 for(unsigned order=0;order<2;order++){
  struct psb_token r=setup();struct psb_completion cs[2];cs[order]=comp(r,3,7);cs[1u-order]=comp(r,1,99);
  enum psb_rc rc=dispatch(cs,2,PSB_NO_CONTROL);show(order==0?"full_then_conflicting_partial":"conflicting_partial_then_full",rc,r);
 }
 for(unsigned order=0;order<2;order++){
  struct psb_token r=setup();struct psb_completion cs[2];cs[order]=comp(r,3,7);cs[1u-order]=comp(r,1,7);cs[1u-order].binding[0]^=1u;
  enum psb_rc rc=dispatch(cs,2,PSB_NO_CONTROL);show(order==0?"full_then_wrong_binding":"wrong_binding_then_full",rc,r);
 }
 return 0;
}
