#include "ps_bridge.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct psb_bridge b;
static uint64_t now_sample; static bool clock_known=true;
static unsigned assertions;
#define CHECK(x) do { assertions++; if (!(x)) { fprintf(stderr,"FAIL line=%d expression=%s\n",__LINE__,#x); exit(3); } } while (0)
static bool clock_read(void *ctx, uint64_t *out) { (void)ctx; *out=now_sample; return clock_known; }
static void self_trace(void *ctx,const struct psb_event *e) {
 (void)ctx;
 printf("TRACE kind=%u reason=%u fatal=%u session=%"PRIu64" row=%"PRIu64" id=%"PRIu64" tx_session=%"PRIu64" tx_generation=%"PRIu64" tx_slot=%u frame=%u interval=%u discarded=%"PRIu64"\n",(unsigned)e->kind,e->reasons,e->fatal,e->session,e->row,e->id,e->transaction.session,e->transaction.generation,e->transaction.slot,e->frame,e->interval,e->discarded_rows);
}
static struct psb_config config(void) {
 struct psb_config c={0}; for (unsigned i=0;i<PSB_BINDING;i++) c.binding[i]=(uint8_t)(i+1u);
 c.ttl_samples=512; c.max_rows=UINT64_MAX; c.max_frame=UINT32_MAX-1u; c.max_interval=UINT32_MAX-1u; c.required_status=3;
 return c; /* Explicit TEST configuration, not a production default. */
}
static void reset_test(void) { struct psb_config c=config(); struct psb_hooks h={0}; h.clock=clock_read;h.event=self_trace; CHECK(psb_init(&b,&c,&h)==PSB_OK); CHECK(psb_start(&b,1)==PSB_OK); now_sample=1023; clock_known=true; }
static void put32(uint8_t *p,uint32_t x) { for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(x>>(8u*i)); }
static void row(uint8_t *p,uint64_t id,uint32_t flags) {
 put32(p,(uint32_t)id);put32(p+4,(uint32_t)(id>>32));
 put32(p+8,0);put32(p+12,1);put32(p+16,UINT32_C(0xff800000));put32(p+20,8388607);
 put32(p+24,flags);put32(p+28,0);
}
static enum psb_rc one(uint64_t id,uint32_t flags) { uint8_t bytes[33];struct psb_token t;row(bytes+1,id,flags);enum psb_rc rc=psb_enqueue(&b,bytes+1,32,NULL,0,&t);return rc==PSB_OK ? psb_pump(&b) : rc; }
static void feed(uint64_t first,unsigned count) { for (unsigned i=0;i<count;i++) CHECK(one(first+i,0)==PSB_OK); }
static struct psb_token frame(void) { struct psb_token t;const struct psb_frame *f=NULL;CHECK(psb_frame_acquire(&b,&t,&f)==PSB_OK);CHECK(f && f->data[0].pcm[2]==-8388608);return t; }
static struct psb_token result(struct psb_token f) { struct psb_token r;CHECK(psb_result_begin(&b,f,&r)==PSB_OK);return r; }
static struct psb_completion completion(struct psb_token r,uint32_t status,bool error) { struct psb_completion c={0};c.token=r;c.status=status;c.error=error;c.payload=12345;memcpy(c.binding,b.config.binding,PSB_BINDING);return c; }
static enum psb_rc dispatch(struct psb_completion *c,size_t n,enum psb_control control,bool fatal) { struct psb_batch batch={control,fatal,c,n};return psb_dispatch(&b,&batch); }

static void test_config_and_length(void) {
 reset_test();uint8_t raw[33];row(raw+1,0,0);struct psb_token t;
 CHECK(psb_enqueue(&b,raw+1,31,NULL,0,&t)==PSB_REJECT);
 CHECK(psb_enqueue(&b,raw+1,8001,NULL,0,&t)==PSB_REJECT);
 CHECK(psb_enqueue(&b,raw+1,SIZE_MAX,NULL,0,&t)==PSB_REJECT);
 CHECK(psb_enqueue(&b,raw+1,0,NULL,0,&t)==PSB_REJECT);
 CHECK(psb_enqueue(&b,NULL,32,NULL,0,&t)==PSB_REJECT);
 uint32_t u=1;CHECK(psb_enqueue(&b,raw+1,32,&u,0,&t)==PSB_REJECT);
 CHECK(psb_enqueue(&b,raw+1,32,NULL,1,&t)==PSB_REJECT);
 struct psb_config c=config();struct psb_hooks h={0};c.required_status=0;CHECK(psb_init(&b,&c,&h)==PSB_REJECT);
 c=config();c.binding[0]=0;memset(c.binding,0,32);CHECK(psb_init(&b,&c,&h)==PSB_REJECT);
 c=config();c.max_frame=UINT32_MAX;CHECK(psb_init(&b,&c,&h)==PSB_REJECT);
 puts("PASS config_and_buffer_length");
}
static void test_input_ownership(void) {
 reset_test();uint8_t raw[32];row(raw,99,0);struct psb_token t;
 CHECK(psb_enqueue(&b,raw,32,NULL,0,&t)==PSB_OK);memset(raw,0xff,sizeof(raw));
 CHECK(psb_pump(&b)==PSB_OK && b.previous==99 && b.window[0].pcm[3]==8388607);
 CHECK(psb_pump(&b)==PSB_WAIT);
 reset_test();row(raw,1,0);
 for (unsigned i=0;i<PSB_INPUTS;i++) CHECK(psb_enqueue(&b,raw,32,NULL,0,&t)==PSB_OK);
 CHECK(psb_enqueue(&b,raw,32,NULL,0,&t)==PSB_FULL);
 CHECK(b.failed && b.input_count==PSB_INPUTS && (b.reasons&PSB_QUEUE));
 CHECK(b.input[0].bytes[0]==1 && psb_pump(&b)==PSB_REJECT);
 puts("PASS copied_input_and_full_queue");
}
static void test_frames(void) {
 reset_test();feed(0,1024);struct psb_token f=frame();
 CHECK(psb_frame_release(&b,(struct psb_token){1,f.generation+1,f.slot})==PSB_REJECT);
 feed(1024,512);struct psb_token second=frame();
 CHECK(b.frame[f.slot].data[0].id==0 && b.frame[second.slot].data[0].id==512);
 for(unsigned i=0;i<PSB_N;i++) CHECK(b.frame[f.slot].data[i].id==i && b.frame[f.slot].data[i].pcm[2]==-8388608);
 for (unsigned i=0;i<511;i++) CHECK(one(1536+i,0)==PSB_OK);
 CHECK(one(2047,0)==PSB_FULL && b.failed && (b.reasons&PSB_QUEUE));
 CHECK(b.frame[f.slot].data[0].id==0);CHECK(psb_frame_release(&b,f)==PSB_OK);CHECK(psb_frame_release(&b,f)==PSB_REJECT);
 CHECK(psb_frame_release(&b,second)==PSB_OK);
 puts("PASS frame_consumer_stall_and_tokens");
}
static void test_recovery_and_union(void) {
 reset_test();CHECK(one(100,0)==PSB_OK);CHECK(one(103,1)==PSB_OK);CHECK(b.previous==103);
 CHECK(one(105,2)==PSB_OK);CHECK(b.interval==0);CHECK(one(106,0)==PSB_OK && b.interval==1);
 CHECK(b.audit[0].reasons==(PSB_DROP|PSB_CLIP));CHECK(b.audit[1].reasons==(PSB_DROP|PSB_CLIP));
 uint8_t raw[32];row(raw,106,17);put32(raw+8,8388608);put32(raw+28,1);uint32_t u=99;struct psb_token t;
 CHECK(psb_enqueue(&b,raw,32,&u,1,&t)==PSB_OK);CHECK(psb_pump(&b)==PSB_FAULT);
 CHECK(b.last_event.reasons==(PSB_UPSTREAM|PSB_DUP|PSB_FLAGS|PSB_RESERVED|PSB_RANGE|PSB_CLIP));
 CHECK(b.previous==106 && b.rows==5 && b.input[b.input_head].owner==PSB_HELD);
 CHECK(one(107,0)==PSB_REJECT);
 puts("PASS accepted_row_recovery_complete_reason_union");
}
static void test_boundaries(void) {
 reset_test();CHECK(one(UINT64_MAX,0)==PSB_OK);CHECK(one(0,0)==PSB_FAULT && b.last_event.reasons==PSB_WRAP);
 reset_test();CHECK(one(12,1)==PSB_OK);CHECK(one(11,0)==PSB_FAULT && b.last_event.reasons==PSB_REVERSE);
 reset_test();b.config.max_rows=1;CHECK(one(0,0)==PSB_OK);CHECK(one(1,0)==PSB_FAULT && b.rows==1);
 reset_test();b.rows=UINT64_MAX-1;CHECK(one(0,0)==PSB_OK);CHECK(one(1,0)==PSB_FAULT && b.rows==UINT64_MAX);
 reset_test();b.config.max_interval=0;CHECK(one(0,0)==PSB_OK);CHECK(one(1,1)==PSB_OK);CHECK(one(2,0)==PSB_FAULT);
 reset_test();b.config.max_frame=0;feed(0,1024);struct psb_token f=frame();CHECK(psb_frame_release(&b,f)==PSB_OK);
 feed(1024,511);CHECK(one(1535,0)==PSB_FAULT && b.frame_count==1);
 reset_test();b.generation=UINT64_MAX;CHECK(one(0,0)==PSB_FAULT);
 reset_test();b.generation=UINT64_MAX-1;CHECK(one(0,0)==PSB_OK);CHECK(one(1,0)==PSB_FAULT);
 reset_test();b.frame_count=UINT32_MAX-1;feed(0,1024);CHECK(b.frame_count==UINT32_MAX);f=frame();CHECK(psb_frame_release(&b,f)==PSB_OK);
 feed(1024,511);CHECK(one(1535,0)==PSB_FAULT && b.frame_count==UINT32_MAX);
 reset_test();CHECK(one(0,0)==PSB_OK);b.interval=UINT32_MAX-1;CHECK(one(1,1)==PSB_OK);CHECK(one(2,0)==PSB_FAULT);
 reset_test();for (unsigned i=0;i<PSB_AUDIT;i++) CHECK(one(i,1)==PSB_OK);
 CHECK(one(PSB_AUDIT,1)==PSB_FAULT && (b.last_event.reasons&(PSB_CLIP|PSB_AUDIT_FULL))==(PSB_CLIP|PSB_AUDIT_FULL));
 psb_audit_clear(&b);CHECK(b.failed && psb_start(&b,2)==PSB_REJECT);
 puts("PASS finite_counters_wrap_audit_overflow");
}
static void test_results(void) {
 reset_test();feed(0,1024);struct psb_token f=frame(),r=result(f),dummy;uint64_t payload;
 CHECK(psb_result_begin(&b,f,&dummy)==PSB_REJECT);CHECK(psb_result_release(&b,r)==PSB_REJECT);
 struct psb_completion c=completion(r,1,false);CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);
 CHECK(psb_result_take(&b,r,&payload)==PSB_REJECT);
 c.status=2;clock_known=false;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);
 CHECK(b.result[r.slot].owner==PSB_PENDING);clock_known=true;now_sample=1535;
 c.status=0;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);
 CHECK(psb_result_take(&b,r,&payload)==PSB_OK && payload==12345);
 CHECK(psb_result_take(&b,r,&payload)==PSB_REJECT);CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT);
 CHECK(psb_result_release(&b,r)==PSB_OK);CHECK(psb_result_release(&b,r)==PSB_REJECT);
 CHECK(psb_result_begin(&b,f,&dummy)==PSB_REJECT); /* releasing result must not allow second commit of frame */
 c.error=true;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_FAULT && (b.reasons&PSB_LATE));
 puts("PASS result_status_barrier_once_only_and_retired_late_error");
}
static void test_ttl_and_binding(void) {
 reset_test();feed(0,1024);struct psb_token f=frame(),r=result(f);struct psb_completion c=completion(r,3,false);uint64_t payload;
 now_sample=100;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT && b.result[r.slot].owner==PSB_PENDING);
 now_sample=1536;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT && b.result[r.slot].owner==PSB_INVALID);
 reset_test();feed(0,1024);f=frame();r=result(f);c=completion(r,3,false);CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);
 now_sample=1536;CHECK(psb_result_take(&b,r,&payload)==PSB_EXPIRED);
 reset_test();feed(0,1024);f=frame();r=result(f);c=completion(r,3,false);c.binding[33]^=1;
 CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT && b.result[r.slot].owner==PSB_INVALID);
 reset_test();feed(UINT64_MAX-1023,1024);f=frame();CHECK(psb_result_begin(&b,f,&r)==PSB_REJECT);
 reset_test();feed(0,1024);f=frame();r=result(f);c=completion(r,1,false);CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);
 c.status=2;c.payload++;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT && b.result[r.slot].owner==PSB_INVALID);
 reset_test();feed(0,1024);f=frame();r=result(f);c=completion(r,4,false);CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT);
 reset_test();b.config.ttl_samples=0;feed(0,1024);f=frame();r=result(f);c=completion(r,3,false);
 CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);CHECK(psb_result_take(&b,r,&payload)==PSB_OK);
 puts("PASS ttl_clock_config_and_addition_bounds");
}
static void test_controls(void) {
 reset_test();feed(0,1024);struct psb_token f=frame(),r=result(f);struct psb_completion c=completion(r,3,false);uint64_t v;
 CHECK(dispatch(&c,1,PSB_CONTROL_STOP,false)==PSB_OK);CHECK(psb_result_take(&b,r,&v)==PSB_REJECT);
 CHECK(psb_start(&b,2)==PSB_REJECT);CHECK(psb_frame_release(&b,f)==PSB_OK);CHECK(psb_result_release(&b,r)==PSB_OK);
 CHECK(psb_start(&b,1)==PSB_REJECT);CHECK(psb_start(&b,2)==PSB_OK);
 CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT && !b.failed);CHECK(b.last_event.kind==PSB_STALE_EVENT);
 c.error=true;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT && !b.failed && b.last_event.upstream==1);c.error=false;CHECK(one(0,0)==PSB_OK);
 CHECK(dispatch(NULL,0,PSB_CONTROL_RESET,false)==PSB_OK);CHECK(one(1,0)==PSB_REJECT);
 CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_REJECT);
 reset_test();feed(0,1024);f=frame();r=result(f);struct psb_completion both[2]={completion(r,3,false),completion(r,0,true)};
 CHECK(dispatch(both,2,PSB_NO_CONTROL,false)==PSB_REJECT && b.result[r.slot].owner==PSB_INVALID);
 reset_test();feed(0,1024);f=frame();r=result(f);c=completion(r,3,false);
 CHECK(dispatch(&c,1,PSB_NO_CONTROL,true)==PSB_FAULT && b.result[r.slot].owner==PSB_INVALID);
 reset_test();feed(0,1024);f=frame();r=result(f);c=completion(r,3,false);CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_OK);
 CHECK(dispatch(NULL,0,PSB_CONTROL_STOP,false)==PSB_OK);c.error=true;CHECK(dispatch(&c,1,PSB_NO_CONTROL,false)==PSB_FAULT);
 bool found=false;for(size_t i=0;i<b.audit_count;i++) if(b.audit[i].kind==PSB_LATE_ERROR && b.audit[i].transaction.generation==r.generation && b.audit[i].have_transaction_desc) found=true;
 CHECK(found);
 for(unsigned order=0;order<2;order++) {
  reset_test();feed(0,1024);f=frame();r=result(f);
  both[order]=completion(r,3,false);both[1u-order]=completion(r,0,true);
  CHECK(dispatch(both,2,PSB_CONTROL_RESET,true)==PSB_FAULT);
  CHECK(b.result[r.slot].owner==PSB_INVALID && (b.reasons&PSB_EXTERNAL_FATAL) && (b.reasons&PSB_UPSTREAM));
 }
 puts("PASS simultaneous_control_fault_completion_and_old_session");
}
static void test_result_full_and_restart(void) {
 reset_test();uint64_t next=0;struct psb_token r={0};
 for (unsigned i=0;i<PSB_RESULTS;i++) {
  unsigned count=i ? 512 : 1024;feed(next,count);next+=count;struct psb_token f=frame();r=result(f);CHECK(psb_frame_release(&b,f)==PSB_OK);
 }
 feed(next,512);struct psb_token f=frame();CHECK(psb_result_begin(&b,f,&r)==PSB_FULL && b.failed);
 reset_test();feed(0,600);CHECK(dispatch(NULL,0,PSB_CONTROL_STOP,false)==PSB_OK && b.last_event.unused_tail==600);
 CHECK(psb_start(&b,2)==PSB_OK);feed(600,600);CHECK(b.frame_count==0);
 uint8_t raw[32];row(raw,1200,0);struct psb_token t;CHECK(psb_enqueue(&b,raw,32,NULL,0,&t)==PSB_OK);
 CHECK(dispatch(NULL,0,PSB_CONTROL_STOP,false)==PSB_OK && b.last_event.discarded_rows==1);
 CHECK(psb_start(&b,UINT64_MAX)==PSB_OK);CHECK(dispatch(NULL,0,PSB_CONTROL_STOP,false)==PSB_OK);CHECK(psb_start(&b,0)==PSB_REJECT);
 reset_test();feed(0,1024);f=frame();CHECK(psb_frame_release(&b,f)==PSB_OK);CHECK(dispatch(NULL,0,PSB_CONTROL_STOP,false)==PSB_OK);
 CHECK(psb_start(&b,2)==PSB_OK);feed(5000,1024);f=frame();
 CHECK(b.frame[f.slot].desc.session==2 && b.frame[f.slot].desc.frame==0 && b.frame[f.slot].desc.interval==0);
 CHECK(b.frame[f.slot].desc.first_id==5000 && b.frame[f.slot].desc.row_start==0 && b.frame[f.slot].desc.reset_before);
 puts("PASS result_full_stop_tail_new_session");
}
static void memory_report(void) {
 CHECK(sizeof(b.input)+sizeof(b.frame)+sizeof(b.result)+sizeof(b.window)+sizeof(b.audit)<=sizeof(b));
 CHECK(sizeof(b)<1048576u && sizeof(struct psb_group)==32u);
 printf("MEMORY {\"bridge\":%zu,\"bridge_align\":%zu,\"group\":%zu,\"descriptor\":%zu,\"input\":%zu,\"inputs\":%zu,\"frame\":%zu,\"frames\":%zu,\"result\":%zu,\"results\":%zu,\"window\":%zu,\"audit\":%zu}\n",sizeof(b),_Alignof(struct psb_bridge),sizeof(struct psb_group),sizeof(struct psb_desc),sizeof(struct psb_input),sizeof(b.input),sizeof(struct psb_frame),sizeof(b.frame),sizeof(struct psb_result),sizeof(b.result),sizeof(b.window),sizeof(b.audit));
}
struct files { FILE *frames,*events; unsigned frames_count,events_count; };
static void write64(FILE *f,uint64_t x) { uint8_t p[8];put32(p,(uint32_t)x);put32(p+4,(uint32_t)(x>>32));CHECK(fwrite(p,1,8,f)==8); }
static void frame_out(void *ctx,const struct psb_desc *d,const struct psb_group *g) {
 struct files *f=ctx;uint64_t header[]={d->session,d->frame,d->interval,d->row_start,d->row_stop,d->first_id,d->last_id,d->reset_before};
 for (unsigned i=0;i<8;i++) write64(f->frames,header[i]);
 CHECK(fwrite(d->binding,1,PSB_BINDING,f->frames)==PSB_BINDING);
 for (unsigned i=0;i<PSB_N;i++) { uint8_t p[32];row(p,g[i].id,g[i].flags);for(unsigned j=0;j<4;j++) put32(p+8+4*j,(uint32_t)g[i].pcm[j]);put32(p+28,g[i].reserved);CHECK(fwrite(p,1,32,f->frames)==32); }
 f->frames_count++;
}
static void event_out(void *ctx,const struct psb_event *e) {
 struct files *f=ctx;
 fprintf(f->events,"{\"kind\":%u,\"reasons\":%u,\"session\":\"%"PRIu64"\",\"row\":\"%"PRIu64"\",\"id\":\"%"PRIu64"\",\"previous\":\"%"PRIu64"\",\"have_previous\":%u,\"flags\":%u,\"upstream\":%u,\"fatal\":%u,\"unused_tail\":%u,\"discarded_rows\":\"%"PRIu64"\"}\n",(unsigned)e->kind,e->reasons,e->session,e->row,e->id,e->previous,e->have_previous,e->flags,e->upstream,e->fatal,e->unused_tail,e->discarded_rows);
 f->events_count++;
}
static int replay(int argc,char **argv) {
 if (argc!=6) return 2;
 FILE *input=fopen(argv[2],"rb"),*meta=fopen(argv[3],"rb");
 struct files files={fopen(argv[4],"wb"),fopen(argv[5],"w"),0,0};
 if (!input || !meta || !files.frames || !files.events) return 2;
 struct psb_config c=config();struct psb_hooks h={&files,frame_out,event_out,clock_read};CHECK(psb_init(&b,&c,&h)==PSB_OK);CHECK(psb_start(&b,1)==PSB_OK);
 uint8_t raw[PSB_PACKET*32u+1],ub[PSB_PACKET*4u]; uint32_t u[PSB_PACKET];
 while (true) {
  size_t n=fread(raw+1,1,PSB_PACKET*32u,input);if (!n) break;CHECK(n%32u==0);
  CHECK(fread(ub,1,n/8,meta)==n/8);
  for(size_t i=0;i<n/32u;i++) u[i]=(uint32_t)ub[i*4]|(uint32_t)ub[i*4+1]<<8|(uint32_t)ub[i*4+2]<<16|(uint32_t)ub[i*4+3]<<24;
  struct psb_token t;CHECK(psb_enqueue(&b,raw+1,n,u,n/32u,&t)==PSB_OK);memset(raw,0xAA,sizeof(raw));
  enum psb_rc rc=psb_pump(&b);
  if(b.failed) { CHECK(rc==PSB_FAULT || rc==PSB_FULL);break; }
  CHECK(rc==PSB_OK);
  for(unsigned i=0;i<PSB_FRAMES;i++) if(b.frame[i].revoked && b.frame[i].owner!=PSB_FREE) CHECK(psb_frame_release(&b,b.frame[i].token)==PSB_OK);
  const struct psb_frame *out;while(psb_frame_acquire(&b,&t,&out)==PSB_OK) CHECK(psb_frame_release(&b,t)==PSB_OK);
  psb_audit_clear(&b);
 }
 if(b.active) CHECK(dispatch(NULL,0,PSB_CONTROL_STOP,false)==PSB_OK);
 printf("REPLAY {\"frames\":%u,\"events\":%u,\"failed\":%u,\"rows\":\"%"PRIu64"\",\"reason_union\":%u}\n",files.frames_count,files.events_count,b.failed,b.rows,b.reasons);
 fclose(input);fclose(meta);fclose(files.frames);fclose(files.events);return 0;
}
int main(int argc,char **argv) {
 if(argc>1 && strcmp(argv[1],"replay")==0) return replay(argc,argv);
 test_config_and_length();test_input_ownership();test_frames();test_recovery_and_union();test_boundaries();test_results();test_ttl_and_binding();test_controls();test_result_full_and_restart();memory_report();
 printf("HOST_SELFTEST_PASS groups=9 assertions=%u\n",assertions);return 0;
}
