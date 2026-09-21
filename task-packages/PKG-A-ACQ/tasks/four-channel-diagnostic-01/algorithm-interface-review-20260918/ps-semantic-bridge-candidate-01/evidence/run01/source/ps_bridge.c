#include "ps_bridge.h"
#include <limits.h>
#include <string.h>

_Static_assert(CHAR_BIT == 8, "8-bit bytes required");
_Static_assert(sizeof(int32_t)==4 && sizeof(uint64_t)==8, "exact-width integers required");

static uint32_t le32(const uint8_t *p) {
 return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static int32_t signed32(uint32_t x) {
 /* Both casts are representable; no implementation-defined unsigned->signed overflow. */
 return x<=INT32_MAX ? (int32_t)x : -1-(int32_t)(UINT32_MAX-x);
}
static struct psb_group decode(const uint8_t *p) {
 struct psb_group g; g.id=(uint64_t)le32(p) | (uint64_t)le32(p+4)<<32;
 for (unsigned i=0;i<4;i++) g.pcm[i]=signed32(le32(p+8+4*i));
 g.flags=le32(p+24); g.reserved=le32(p+28); return g;
}
static bool same(struct psb_token a, struct psb_token b) { return a.session==b.session && a.generation==b.generation && a.slot==b.slot; }
static void revoke(struct psb_bridge *b) {
 for (unsigned i=0;i<PSB_FRAMES;i++) if (b->frame[i].owner!=PSB_FREE) b->frame[i].revoked=true;
 for (unsigned i=0;i<PSB_RESULTS;i++) if (b->result[i].owner!=PSB_FREE) b->result[i].owner=PSB_INVALID;
}
static void fault(struct psb_bridge *b, uint32_t reason) {
 b->reasons|=reason; b->failed=true; b->active=false; revoke(b);
}
static uint32_t tail(const struct psb_bridge *b) { return b->have_frame ? b->new_count : (uint32_t)b->fill; }
static void record(struct psb_bridge *b, struct psb_event e) {
 if (b->audit_count==PSB_AUDIT) { e.reasons|=PSB_AUDIT_FULL; e.fatal=true; fault(b,e.reasons); }
 else b->audit[b->audit_count++]=e;
 b->last_event=e; b->reasons|=e.reasons;
 if (b->hooks.event) b->hooks.event(b->hooks.context,&e);
}
static void global_fault(struct psb_bridge *b, uint32_t why) {
 struct psb_event e={0}; e.kind=PSB_FATAL; e.reasons=why; e.session=b->session;
 e.row=b->rows; e.id=b->previous; e.previous=b->previous; e.have_previous=b->have_previous; e.fatal=true; e.unused_tail=tail(b);
 fault(b,why); record(b,e);
}
static bool token_new(struct psb_bridge *b, uint32_t slot, struct psb_token *t) {
 if (b->generation==UINT64_MAX) { global_fault(b,PSB_COUNTER); return false; }
 *t=(struct psb_token){b->session,++b->generation,slot}; return true;
}
enum psb_rc psb_init(struct psb_bridge *b, const struct psb_config *c, const struct psb_hooks *h) {
 if (!b || !c || !h || !c->max_rows || !c->required_status || c->max_frame==UINT32_MAX || c->max_interval==UINT32_MAX) return PSB_REJECT;
 for (unsigned j=0;j<3;j++) { uint8_t bits=0; for (unsigned i=0;i<32;i++) bits|=c->binding[j*32+i]; if (!bits) return PSB_REJECT; }
 memset(b,0,sizeof(*b)); b->config=*c; b->hooks=*h; return PSB_OK;
}
enum psb_rc psb_start(struct psb_bridge *b, uint64_t session) {
 if (!b || b->active || b->failed || !session || session<=b->last_session || b->input_count) return PSB_REJECT;
 for (unsigned i=0;i<PSB_FRAMES;i++) if (b->frame[i].owner!=PSB_FREE) return PSB_REJECT;
 for (unsigned i=0;i<PSB_RESULTS;i++) if (b->result[i].owner!=PSB_FREE) return PSB_REJECT;
 b->session=b->last_session=session; b->rows=0; b->previous=0; b->fill=0;
 b->frame_count=0; b->interval=0; b->new_count=0;
 b->have_previous=b->segment_open=b->have_interval=b->have_frame=false;
 b->next_reset=true; b->active=true; return PSB_OK;
}
enum psb_rc psb_enqueue(struct psb_bridge *b, const void *bytes, size_t length, const uint32_t *u, size_t uc, struct psb_token *t) {
 if (!b || !b->active || b->failed || !bytes || !t || !length || length>PSB_PACKET*32u || length%32u || (u ? uc!=length/32u : uc!=0)) return PSB_REJECT;
 if (b->input_count==PSB_INPUTS) { global_fault(b,PSB_QUEUE); return PSB_FULL; }
 size_t index=(b->input_head+b->input_count)%PSB_INPUTS;
 struct psb_input *p=&b->input[index];
 if (p->owner!=PSB_FREE) return PSB_REJECT;
 if (!token_new(b,(uint32_t)index,&p->token)) return PSB_FAULT;
 memcpy(p->bytes,bytes,length); p->count=length/32u;
 for (size_t i=0;i<p->count;i++) p->upstream[i]=u ? u[i] : 0;
 p->owner=PSB_READY; *t=p->token; b->input_count++; return PSB_OK;
}
static enum psb_rc publish(struct psb_bridge *b) {
 if (b->frame_count>b->config.max_frame) { global_fault(b,PSB_COUNTER); return PSB_FAULT; }
 unsigned slot;
 for (slot=0;slot<PSB_FRAMES;slot++) if (b->frame[slot].owner==PSB_FREE) break;
 if (slot==PSB_FRAMES) { global_fault(b,PSB_QUEUE); return PSB_FULL; }
 struct psb_frame *f=&b->frame[slot];
 if (!token_new(b,slot,&f->token)) return PSB_FAULT;
 memset(&f->desc,0,sizeof(f->desc));
 f->desc.session=b->session; f->desc.frame=b->frame_count++;
 f->desc.interval=b->interval; f->desc.row_stop=b->rows; f->desc.row_start=b->rows-PSB_N;
 f->desc.first_id=b->window[0].id; f->desc.last_id=b->window[PSB_N-1].id;
 f->desc.reset_before=b->next_reset; memcpy(f->desc.binding,b->config.binding,PSB_BINDING);
 memcpy(f->data,b->window,sizeof(b->window)); f->owner=PSB_READY; f->revoked=false; f->result_issued=false;
 if (b->hooks.frame) b->hooks.frame(b->hooks.context,&f->desc,f->data);
 memmove(b->window,b->window+PSB_H,PSB_H*sizeof(b->window[0]));
 b->fill=PSB_H; b->new_count=0; b->have_frame=true; b->next_reset=false; return PSB_OK;
}
static enum psb_rc accept(struct psb_bridge *b, struct psb_group g, uint32_t upstream) {
 if (b->rows==b->config.max_rows) { global_fault(b,PSB_COUNTER); return PSB_FAULT; }
 uint32_t why=0; uint64_t previous=b->previous, row=b->rows; bool have=b->have_previous;
 if (upstream) why|=PSB_UPSTREAM;
 if (have) {
  if (previous==UINT64_MAX && g.id==0) why|=PSB_WRAP;
  else if (g.id==previous) why|=PSB_DUP;
  else if (g.id<previous) why|=PSB_REVERSE;
  else if (g.id-previous!=1) why|=PSB_DROP;
 }
 if (g.flags&~UINT32_C(15)) why|=PSB_FLAGS;
 if (g.reserved) why|=PSB_RESERVED;
 if (g.flags&15u) why|=PSB_CLIP;
 for (unsigned i=0;i<4;i++) if (g.pcm[i]<-8388608 || g.pcm[i]>8388607) why|=PSB_RANGE;
 b->previous=g.id; b->have_previous=true; b->rows++; /* includes erroneous accepted rows */
 if (why) {
  struct psb_event e={0}; e.kind=PSB_ROW_ERROR; e.reasons=why; e.session=b->session;
  e.row=row; e.id=g.id; e.previous=previous; e.have_previous=have; e.flags=g.flags; e.upstream=upstream;
  e.fatal=(why&PSB_FATAL_MASK)!=0; e.unused_tail=tail(b);
  revoke(b); b->fill=0; b->new_count=0; b->have_frame=false; b->segment_open=false; b->next_reset=true;
  if (e.fatal) fault(b,why);
  record(b,e); return b->failed ? PSB_FAULT : PSB_OK;
 }
 if (!b->segment_open) {
  if (b->have_interval) {
   if (b->interval==b->config.max_interval) { global_fault(b,PSB_COUNTER); return PSB_FAULT; }
   b->interval++;
  }
  b->have_interval=true; b->segment_open=true;
 }
 b->window[b->fill++]=g; b->new_count++;
 return b->fill==PSB_N ? publish(b) : PSB_OK;
}
enum psb_rc psb_pump(struct psb_bridge *b) {
 if (!b || !b->active || b->failed) return PSB_REJECT;
 if (!b->input_count) return PSB_WAIT;
 struct psb_input *p=&b->input[b->input_head];
 if (p->owner!=PSB_READY) return PSB_REJECT;
 p->owner=PSB_HELD;
 for (size_t i=0;i<p->count;i++) {
  enum psb_rc rc=accept(b,decode(p->bytes+32u*i),p->upstream[i]);
  if (rc!=PSB_OK) return rc; /* failure retains packet ownership and bytes */
 }
 p->owner=PSB_FREE; b->input_head=(b->input_head+1u)%PSB_INPUTS; b->input_count--; return PSB_OK;
}
enum psb_rc psb_frame_acquire(struct psb_bridge *b, struct psb_token *t, const struct psb_frame **out) {
 if (!b || !t || !out || b->failed || !b->active) return PSB_REJECT;
 unsigned slot=PSB_FRAMES; uint64_t oldest=UINT64_MAX;
 for (unsigned i=0;i<PSB_FRAMES;i++) if (b->frame[i].owner==PSB_READY && !b->frame[i].revoked && b->frame[i].token.generation<oldest) { oldest=b->frame[i].token.generation; slot=i; }
 if (slot==PSB_FRAMES) return PSB_WAIT;
 b->frame[slot].owner=PSB_HELD; *t=b->frame[slot].token; *out=&b->frame[slot]; return PSB_OK;
}
enum psb_rc psb_frame_release(struct psb_bridge *b, struct psb_token t) {
 if (!b || t.slot>=PSB_FRAMES) return PSB_REJECT;
 struct psb_frame *f=&b->frame[t.slot];
 if (!same(t,f->token) || f->owner==PSB_FREE || (f->owner!=PSB_HELD && !f->revoked)) return PSB_REJECT;
 f->owner=PSB_FREE; return PSB_OK;
}
enum psb_rc psb_result_begin(struct psb_bridge *b, struct psb_token ft, struct psb_token *out) {
 if (!b || !out || !b->active || b->failed || ft.slot>=PSB_FRAMES) return PSB_REJECT;
 struct psb_frame *f=&b->frame[ft.slot];
 if (!same(ft,f->token) || f->owner!=PSB_HELD || f->revoked || f->result_issued) return PSB_REJECT;
 if (b->config.ttl_samples>UINT64_MAX-f->desc.last_id) return PSB_REJECT;
 unsigned slot;
 for (slot=0;slot<PSB_RESULTS;slot++) {
  if (b->result[slot].owner!=PSB_FREE && b->result[slot].desc.session==f->desc.session && b->result[slot].desc.frame==f->desc.frame) return PSB_REJECT;
 }
 for (slot=0;slot<PSB_RESULTS;slot++) if (b->result[slot].owner==PSB_FREE) break;
 if (slot==PSB_RESULTS) { global_fault(b,PSB_QUEUE); return PSB_FULL; }
 struct psb_result *r=&b->result[slot]; if (!token_new(b,slot,&r->token)) return PSB_FAULT;
 r->desc=f->desc; r->status=0; r->payload=0; r->was_committed=false; r->expiry=f->desc.last_id+b->config.ttl_samples; r->owner=PSB_PENDING; f->result_issued=true; *out=r->token; return PSB_OK;
}
static void stop(struct psb_bridge *b, enum psb_control control) {
 struct psb_event e={0}; e.kind=control==PSB_CONTROL_RESET ? PSB_RESET : PSB_STOP;
 e.session=b->session; e.row=b->rows; e.id=b->previous; e.previous=b->previous; e.have_previous=b->have_previous; e.unused_tail=tail(b);
 revoke(b); b->active=false; b->fill=0; b->new_count=0;
 /* Normal stop discards not-yet-accepted copied packets, explicitly, never accepts tail as a new session. */
 if (!b->failed) { for (unsigned i=0;i<PSB_INPUTS;i++) { if (b->input[i].owner!=PSB_FREE) e.discarded_rows+=b->input[i].count; b->input[i].owner=PSB_FREE; } b->input_count=0; }
 record(b,e);
}
enum psb_rc psb_dispatch(struct psb_bridge *b, const struct psb_batch *batch) {
 if (!b || !batch || (batch->count && !batch->items) || batch->count>PSB_RESULTS || batch->control<PSB_NO_CONTROL || batch->control>PSB_CONTROL_RESET) return PSB_REJECT;
 bool rejected=false; uint32_t terminal=batch->fatal ? PSB_EXTERNAL_FATAL : 0;
 /* First pass: all error causes, before ANY commit; scan also after STOP. */
 for (size_t i=0;i<batch->count;i++) {
  const struct psb_completion *c=&batch->items[i];
  if (c->token.session!=b->session || c->token.slot>=PSB_RESULTS) { rejected=true; continue; }
  struct psb_result *r=&b->result[c->token.slot];
  bool known=same(c->token,r->token) && r->owner!=PSB_FREE;
  if (c->error) {
   struct psb_event e={0}; e.kind=PSB_LATE_ERROR; e.session=b->session; e.row=b->rows; e.id=b->previous;
   e.reasons=PSB_UPSTREAM; e.fatal=!known || r->was_committed;
   if (e.fatal) { terminal|=PSB_LATE; e.reasons|=PSB_LATE; }
   if (known) r->owner=PSB_INVALID;
   record(b,e);
  }
  if (!known) rejected=true;
 }
 if (terminal) global_fault(b,terminal);
 if (batch->control!=PSB_NO_CONTROL) stop(b,batch->control);
 if (b->failed) return PSB_FAULT;
 if (!b->active) return (rejected || batch->control==PSB_NO_CONTROL) ? PSB_REJECT : PSB_OK;
 for (size_t i=0;i<batch->count;i++) {
  const struct psb_completion *c=&batch->items[i];
  if (c->token.session!=b->session || c->token.slot>=PSB_RESULTS) continue;
  struct psb_result *r=&b->result[c->token.slot];
  if (!same(c->token,r->token) || r->owner!=PSB_PENDING) { rejected=true; continue; }
  if (memcmp(c->binding,r->desc.binding,PSB_BINDING) || r->desc.interval!=b->interval || (c->status&~b->config.required_status)) { r->owner=PSB_INVALID; rejected=true; continue; }
  r->status|=c->status; r->payload=c->payload;
  if (r->status==b->config.required_status) {
   uint64_t now;
   if (!b->hooks.clock || !b->hooks.clock(b->hooks.context,&now)) continue;
   if (now<r->desc.last_id) { rejected=true; continue; }
   if (now>r->expiry) { r->owner=PSB_INVALID; rejected=true; continue; }
   r->owner=PSB_COMMITTED; r->was_committed=true;
  }
 }
 return rejected ? PSB_REJECT : PSB_OK;
}
enum psb_rc psb_result_take(struct psb_bridge *b, struct psb_token t, uint64_t *payload) {
 if (!b || !payload || !b->active || b->failed || t.slot>=PSB_RESULTS) return PSB_REJECT;
 struct psb_result *r=&b->result[t.slot];
 if (!same(t,r->token) || r->owner!=PSB_COMMITTED || r->desc.session!=b->session || r->desc.interval!=b->interval) return PSB_REJECT;
 uint64_t now; if (!b->hooks.clock || !b->hooks.clock(b->hooks.context,&now)) return PSB_WAIT;
 if (now<r->desc.last_id) return PSB_REJECT;
 if (now>r->expiry) { r->owner=PSB_INVALID; return PSB_EXPIRED; }
 *payload=r->payload; r->owner=PSB_USED; return PSB_OK;
}
enum psb_rc psb_result_release(struct psb_bridge *b, struct psb_token t) {
 if (!b || t.slot>=PSB_RESULTS) return PSB_REJECT;
 struct psb_result *r=&b->result[t.slot];
 if (!same(t,r->token) || (r->owner!=PSB_USED && r->owner!=PSB_INVALID)) return PSB_REJECT;
 r->owner=PSB_FREE; return PSB_OK;
}
void psb_audit_clear(struct psb_bridge *b) { if (b) b->audit_count=0; }
