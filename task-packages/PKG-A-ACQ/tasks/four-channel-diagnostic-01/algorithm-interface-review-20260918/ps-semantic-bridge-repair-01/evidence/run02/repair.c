#include "ps_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct psb_bridge b;
static struct psb_config config;
static uint64_t tick;
static unsigned commits, checks, cases;
#define CHECK(x) do { checks++; if (!(x)) { fprintf(stderr,"FAIL line=%d case=%u: %s\n",__LINE__,cases,#x); exit(1); } } while(0)
static bool clockfn(void *ctx, uint64_t *now) { (void)ctx; *now=tick; return true; }
static void eventfn(void *ctx, const struct psb_event *e) {
 (void)ctx; if(e->kind==PSB_COMMIT_EVENT) commits++;
}
static void init(void) {
 memset(&config,0,sizeof config); memset(config.binding,0x31,sizeof config.binding);
 config.ttl_samples=4096; config.max_rows=UINT64_MAX;
 config.max_frame=100; config.max_interval=100; config.required_status=3;
 struct psb_hooks h={0}; h.clock=clockfn; h.event=eventfn;
 CHECK(psb_init(&b,&config,&h)==PSB_OK); CHECK(psb_start(&b,1)==PSB_OK);
 commits=0; tick=2047;
}
static void feed(unsigned first, unsigned count) {
 while(count) {
  unsigned n=count>250u ? 250u:count; uint8_t raw[8000]={0}; struct psb_token t;
  for(unsigned i=0;i<n;i++) for(unsigned j=0;j<4;j++) raw[32u*i+j]=(uint8_t)((first+i)>>(8u*j));
  CHECK(psb_enqueue(&b,raw,(size_t)n*32u,NULL,0,&t)==PSB_OK); CHECK(psb_pump(&b)==PSB_OK);
  first+=n; count-=n;
 }
}
static struct psb_token begin(void) {
 struct psb_token f,r; const struct psb_frame *v;
 CHECK(psb_frame_acquire(&b,&f,&v)==PSB_OK); CHECK(psb_result_begin(&b,f,&r)==PSB_OK);
 CHECK(psb_frame_release(&b,f)==PSB_OK); return r;
}
static void setup(struct psb_token *r, struct psb_token *s) {
 init(); feed(0,1024); *r=begin(); feed(1024,512); *s=begin();
}
static struct psb_completion comp(struct psb_token t, uint32_t status, uint64_t payload) {
 struct psb_completion c={0}; c.token=t; c.status=status; c.payload=payload;
 memcpy(c.binding,config.binding,PSB_BINDING); return c;
}
static enum psb_rc dispatch(const struct psb_completion *c,size_t n) {
 struct psb_batch batch={PSB_NO_CONTROL,false,c,n}; return psb_dispatch(&b,&batch);
}
static void unavailable(struct psb_token r) {
 uint64_t p=123; CHECK(psb_result_take(&b,r,&p)!=PSB_OK); CHECK(p==123);
}
static void conflict_permutations(void) {
 for(unsigned kind=0;kind<3;kind++) {
  for(unsigned a=0;a<4;a++) for(unsigned d=0;d<4;d++) for(unsigned e=0;e<4;e++) for(unsigned f=0;f<4;f++) {
   if(a==d || a==e || a==f || d==e || d==f || e==f) continue;
   cases++; struct psb_token r,s; setup(&r,&s);
   struct psb_completion c[4]={comp(r,3,7),comp(r,1,7),comp(s,3,9),comp(r,3,7)};
   if(kind==0) c[1].payload=99;
   if(kind==1) c[1].binding[0]^=1u;
   if(kind==2) c[1].status=4;
   struct psb_completion ordered[4]={c[a],c[d],c[e],c[f]};
   CHECK(dispatch(ordered,4)==PSB_REJECT);
   CHECK(commits==0 && !b.result[r.slot].was_committed && !b.result[s.slot].was_committed);
   CHECK(b.result[r.slot].owner==PSB_INVALID && !b.failed);
   unavailable(r); unavailable(s);
   bool audited=false; for(size_t i=0;i<b.audit_count;i++) if(b.audit[i].kind==PSB_COMPLETION_ERROR) audited=true;
   CHECK(audited);
   /* An unaffected transaction needs an explicit later dispatch to commit. */
   struct psb_completion retry=comp(s,0,0);
   CHECK(dispatch(&retry,1)==PSB_OK && commits==1);
   uint64_t payload=0; CHECK(psb_result_take(&b,s,&payload)==PSB_OK && payload==9);
   CHECK(dispatch(&retry,1)==PSB_REJECT && commits==1);
  }
 }
 puts("PASS conflicts_72_permutations_no_commit_no_take");
}
static void valid_permutations(void) {
 for(unsigned a=0;a<4;a++) for(unsigned d=0;d<4;d++) for(unsigned e=0;e<4;e++) for(unsigned f=0;f<4;f++) {
  if(a==d || a==e || a==f || d==e || d==f || e==f) continue;
  cases++; struct psb_token r,s; setup(&r,&s);
  struct psb_completion c[4]={comp(r,1,7),comp(r,2,7),comp(s,3,9),comp(r,3,7)};
  struct psb_completion ordered[4]={c[a],c[d],c[e],c[f]};
  CHECK(dispatch(ordered,4)==PSB_OK && commits==2);
  uint64_t payload=0; CHECK(psb_result_take(&b,r,&payload)==PSB_OK && payload==7);
  CHECK(psb_result_take(&b,s,&payload)==PSB_OK && payload==9);
  unavailable(r); unavailable(s);
 }
 puts("PASS valid_24_permutations_duplicate_complement_two_transactions");
}
static void partial_and_prior_commit(void) {
 for(unsigned order=0;order<2;order++) {
  cases++; struct psb_token r,s; setup(&r,&s); struct psb_completion c=comp(r,1,7);
  CHECK(dispatch(&c,1)==PSB_OK && commits==0);
  struct psb_completion pair[2]; pair[order]=comp(r,2,99);pair[1u-order]=comp(s,3,9);
  CHECK(dispatch(pair,2)==PSB_REJECT && commits==0);unavailable(r);unavailable(s);
 }
 for(unsigned kind=0;kind<3;kind++) {
  cases++; struct psb_token r,s; setup(&r,&s);struct psb_completion c=comp(r,3,7);
  CHECK(dispatch(&c,1)==PSB_OK && commits==1);
  if(kind==0)c.payload=99;
  if(kind==1)c.binding[0]^=1u;
  if(kind==2)c.status=4;
  CHECK(dispatch(&c,1)==PSB_FAULT && b.failed && commits==1);
  unavailable(r);unavailable(s);
 }
 cases++; struct psb_token r,s; setup(&r,&s);
 struct psb_completion pair[2]={comp(r,1,7),comp(r,2,7)};
 CHECK(dispatch(pair,2)==PSB_OK && commits==1);
 puts("PASS partial_across_batches_prior_commit_conflict_and_complement");
}
static void unknown_errors(void) {
 for(unsigned kind=0;kind<4;kind++) for(unsigned order=0;order<2;order++) {
  cases++;struct psb_token r,s;setup(&r,&s);struct psb_token bad=r;
  if(kind==0)bad.slot=PSB_RESULTS;
  if(kind==1)bad.slot=UINT32_MAX;
  if(kind==2)bad.generation+=100;
  if(kind==3) {
   struct psb_completion done=comp(r,3,7);uint64_t p;
   CHECK(dispatch(&done,1)==PSB_OK);CHECK(psb_result_take(&b,r,&p)==PSB_OK);
   CHECK(psb_result_release(&b,r)==PSB_OK);
  }
  unsigned before=commits;
  struct psb_completion pair[2];pair[order]=comp(bad,0,0);pair[order].error=true;
  pair[1u-order]=comp(s,3,9);
  CHECK(dispatch(pair,2)==PSB_FAULT && b.failed && !b.active && commits==before);
  unavailable(r);unavailable(s);CHECK((b.reasons&PSB_LATE)!=0);
 }
 for(unsigned kind=0;kind<3;kind++) for(unsigned order=0;order<2;order++) {
  cases++;struct psb_token r,s;setup(&r,&s);struct psb_token old=r;old.session=0;
  if(kind==0)old.slot=PSB_RESULTS;
  if(kind==1)old.slot=UINT32_MAX;
  if(kind==2)old.generation+=100;
  struct psb_completion pair[2];pair[order]=comp(old,0,0);pair[order].error=true;pair[1u-order]=comp(s,3,9);
  CHECK(dispatch(pair,2)==PSB_REJECT && !b.failed && b.active && commits==1);
  uint64_t payload=0;CHECK(psb_result_take(&b,s,&payload)==PSB_OK && payload==9);
 }
 puts("PASS current_unknown_error_8_cases_old_session_isolation_6_cases");
}
static void generation_boundaries(void) {
 cases++;init();feed(0,1000);b.generation=UINT64_MAX-2u;feed(1000,24);
 struct psb_token t;const struct psb_frame *v;
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && t.generation==UINT64_MAX);
 CHECK(psb_frame_release(&b,t)==PSB_OK);
 uint8_t raw[32]={0};CHECK(psb_enqueue(&b,raw,sizeof raw,NULL,0,&t)==PSB_FAULT);
 CHECK(b.failed && b.generation==UINT64_MAX);
 cases++;init();feed(0,1024);feed(1024,500);b.generation=UINT64_MAX-2u;feed(1524,12);
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && v->desc.frame==0);
 CHECK(psb_frame_release(&b,t)==PSB_OK);
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && t.generation==UINT64_MAX && v->desc.frame==1);
 CHECK(psb_frame_release(&b,t)==PSB_OK);CHECK(psb_frame_acquire(&b,&t,&v)==PSB_WAIT);
 cases++;init();feed(0,1000);b.generation=UINT64_MAX-3u;feed(1000,24);
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && t.generation==UINT64_MAX-1u);
 struct psb_token r;CHECK(psb_result_begin(&b,t,&r)==PSB_OK && r.generation==UINT64_MAX);
 struct psb_completion c=comp(r,3,7);CHECK(dispatch(&c,1)==PSB_OK && commits==1);
 uint64_t payload;CHECK(psb_result_take(&b,r,&payload)==PSB_OK && payload==7);
 cases++;init();feed(0,1000);b.generation=UINT64_MAX-1u;
 CHECK(psb_enqueue(&b,raw,sizeof raw,NULL,0,&t)==PSB_OK && t.generation==UINT64_MAX);
 CHECK(psb_enqueue(&b,raw,sizeof raw,NULL,0,&t)==PSB_FAULT);
 CHECK(b.frame[0].owner==PSB_FREE && b.frame[1].owner==PSB_FREE);
 /* Physical slot order can differ from generation order after slot reuse. */
 cases++;init();feed(0,1536);
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && t.slot==0);
 CHECK(psb_frame_release(&b,t)==PSB_OK);
 feed(1536,500);b.generation=UINT64_MAX-2u;feed(2036,12);
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && t.slot==1 && v->desc.frame==1);
 CHECK(psb_frame_release(&b,t)==PSB_OK);
 CHECK(psb_frame_acquire(&b,&t,&v)==PSB_OK && t.slot==0 && t.generation==UINT64_MAX);
 /* Exhaustion inside publish must never publish an unacquirable READY. */
 cases++;init();feed(0,1000);b.generation=UINT64_MAX-1u;
 uint8_t last[24u*32u]={0};
 for(unsigned i=0;i<24;i++) for(unsigned j=0;j<4;j++) last[32u*i+j]=(uint8_t)((1000u+i)>>(8u*j));
 CHECK(psb_enqueue(&b,last,sizeof last,NULL,0,&t)==PSB_OK && t.generation==UINT64_MAX);
 CHECK(psb_pump(&b)==PSB_FAULT && b.failed && b.frame_count==0);
 CHECK(b.frame[0].owner==PSB_FREE && b.frame[1].owner==PSB_FREE);
 puts("PASS generation_MAX_acquire_two_frame_order_result_allocation_exhaustion");
}
int main(void) {
 conflict_permutations();valid_permutations();partial_and_prior_commit();unknown_errors();generation_boundaries();
 printf("REPAIR_PASS cases=%u assertions=%u\n",cases,checks);return 0;
}
