#include "ps_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static struct psb_bridge b;
static struct psb_config cfg;
static unsigned n, cases, commits;
static uint64_t now;
#define C(x) do { n++; if (!(x)) { printf("FAIL line %d case %u\n",__LINE__,cases); exit(1); } } while(0)
static bool clockfn(void *ctx,uint64_t *p) {(void)ctx; *p=now; return true;}
static void eventfn(void *ctx,const struct psb_event *e) {(void)ctx; if(e->kind==PSB_COMMIT_EVENT) commits++;}
static void init(void) {
 memset(&cfg,0,sizeof cfg); memset(cfg.binding,42,sizeof cfg.binding);
 cfg.ttl_samples=2048; cfg.max_rows=UINT64_MAX; cfg.max_frame=100; cfg.max_interval=100; cfg.required_status=3;
 struct psb_hooks h={0}; h.clock=clockfn; h.event=eventfn;
 C(psb_init(&b,&cfg,&h)==PSB_OK); C(psb_start(&b,1)==PSB_OK); commits=0; now=1023;
}
static void feed(unsigned id,unsigned count,unsigned flags) {
 while(count) { unsigned k=count>250?250:count; uint8_t raw[8000]={0}; struct psb_token p;
 for(unsigned i=0;i<k;i++) { for(unsigned j=0;j<4;j++) raw[32*i+j]=(uint8_t)((id+i)>>(8*j)); raw[32*i+24]=(uint8_t)flags; }
 C(psb_enqueue(&b,raw,32u*k,NULL,0,&p)==PSB_OK); C(psb_pump(&b)==PSB_OK); id+=k; count-=k;
 }
}
static struct psb_token setup(void) {
 init(); feed(0,1024,0); struct psb_token f,r; const struct psb_frame *v;
 C(psb_frame_acquire(&b,&f,&v)==PSB_OK); C(psb_result_begin(&b,f,&r)==PSB_OK); C(psb_frame_release(&b,f)==PSB_OK); return r;
}
static struct psb_completion completion(struct psb_token t) {
 struct psb_completion c={0}; c.token=t;c.status=3;c.payload=17;memcpy(c.binding,b.config.binding,PSB_BINDING);return c;
}
static enum psb_rc dispatch(struct psb_completion *c,size_t count,enum psb_control ctl) {
 struct psb_batch v={ctl,false,c,count}; return psb_dispatch(&b,&v);
}
int main(void) {
 /* Commit fact survives CLIP/STOP/RESET and release; same-session late error is fatal. */
 for(unsigned control=0;control<3;control++) for(unsigned released=0;released<2;released++) {
  cases++;struct psb_token r=setup();struct psb_completion c=completion(r);uint64_t p=99;
  C(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK && commits==1);
  if(control==0) feed(1024,1,1); else C(dispatch(NULL,0,control==1?PSB_CONTROL_STOP:PSB_CONTROL_RESET)==PSB_OK);
  C(b.result[r.slot].was_committed); C(psb_result_take(&b,r,&p)!=PSB_OK && p==99);
  if(released) C(psb_result_release(&b,r)==PSB_OK);
  c.error=true;C(dispatch(&c,1,PSB_NO_CONTROL)==PSB_FAULT && b.failed && commits==1);
 }
 /* Same numeric slot/generation in old session must never poison a new session. */
 for(unsigned control=0;control<2;control++) {
  cases++;struct psb_token old=setup();struct psb_completion c=completion(old);
  C(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK);C(dispatch(NULL,0,control?PSB_CONTROL_RESET:PSB_CONTROL_STOP)==PSB_OK);
  C(psb_result_release(&b,old)==PSB_OK);C(psb_start(&b,2)==PSB_OK);
  feed(0,1024,0);struct psb_token f,r;const struct psb_frame *v;
  C(psb_frame_acquire(&b,&f,&v)==PSB_OK);C(psb_result_begin(&b,f,&r)==PSB_OK);C(psb_frame_release(&b,f)==PSB_OK);
  struct psb_completion batch[2]={completion(r),completion(r)};batch[0].token.session=1;batch[0].error=true;
  C(dispatch(batch,2,PSB_NO_CONTROL)==PSB_REJECT && !b.failed && commits==2);uint64_t p=0;
  C(psb_result_take(&b,r,&p)==PSB_OK && p==17);
 }
 /* status-zero is not payload replacement, but wrong binding still invalidates all new commits. */
 for(unsigned order=0;order<2;order++) for(unsigned badbinding=0;badbinding<2;badbinding++) {
  cases++;struct psb_token r=setup();struct psb_completion pair[2]={completion(r),completion(r)};
  pair[order].status=0;pair[order].payload=999;if(badbinding)pair[order].binding[95]^=1;
  enum psb_rc rc=dispatch(pair,2,PSB_NO_CONTROL);uint64_t p=0;
  if(badbinding) { C(rc==PSB_REJECT && commits==0);C(psb_result_take(&b,r,&p)!=PSB_OK); }
  else { C(rc==PSB_OK && commits==1);C(psb_result_take(&b,r,&p)==PSB_OK && p==17); }
 }
 /* Caller-owned configuration mutation cannot alter captured binding or required status. */
 cases++;struct psb_token r=setup();memset(cfg.binding,1,sizeof cfg.binding);cfg.required_status=1;
 struct psb_completion c=completion(r);c.status=1;C(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK && commits==0);
 c.status=2;C(dispatch(&c,1,PSB_NO_CONTROL)==PSB_OK && commits==1);C(b.result[r.slot].desc.binding[95]==42);
 printf("SPEC_PASS cases=%u assertions=%u\n",cases,n);return 0;
}
