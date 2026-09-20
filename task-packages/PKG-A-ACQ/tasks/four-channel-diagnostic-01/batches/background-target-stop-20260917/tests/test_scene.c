#define main reused_main
#include "reused_core_cases.c"
#undef main
#include "scene_store.h"
static uint32_t saved[SCENE_TOTAL_WORDS];
static struct scene_store store;
static unsigned slow_copy;
static enum failure archive_packet(void *ctx,const uint32_t *p) {
    struct fake *f=ctx;
    insist(f->session->owner[0]==CPU_OWNED || f->session->owner[1]==CPU_OWNED,"copy ownership");
    enum failure result=scene_append(&store,p);
    if(slow_copy && f->completed==5)f->time+=50000;
    return result;
}
static void setup(struct fake *f,struct session *s,struct io *io,unsigned mode,unsigned cap) {
    memset(f,0,sizeof(*f));session_init(s);f->session=s;f->mode=mode;f->id=0xfffffff0ULL;
    *io=(struct io){f,time_us,source,sr,length,run,arm,prepare,acquire,archive_packet};
    scene_store_init(&store,saved,cap);slow_copy=0;
}
int main(void) {
    reused_main();
    struct fake f;struct session s;struct io io;
    setup(&f,&s,&io,0,SCENE_CAP_GROUPS);
    insist(session_run(&s,&io)==OK,"save full six seconds");
    insist(store.saved_groups==s.groups && s.groups>=288000 && s.groups<=300000,"saved group extent");
    insist(s.owner[0]==FREE && s.owner[1]==FREE && !f.running && !f.draining,"stop fully drained");
    for(unsigned g=0;g<store.saved_groups;g++){
        const uint32_t *p=store.data+g*8;uint64_t id=0xfffffff0ULL+g;
        insist(p[0]==(uint32_t)id && p[1]==(uint32_t)(id>>32),"archived original ID and order");
        for(unsigned c=0;c<4;c++)insist(p[c+2]==(uint32_t)(int32_t)((int)(id%1000)*(c+1)*(c&1?-1:1)),"raw lane code unchanged");
        insist(p[6]==0 && p[7]==0,"raw flags unchanged");
    }
    insist(scene_guards_ok(&store),"full archive guards");
    printf("SCENE full_raw_copy PASS groups=%u fnv=%08x\n",store.saved_groups,scene_fnv1a(&store));
    setup(&f,&s,&io,0,500);
    insist(session_run(&s,&io)==SAVE_OVERFLOW && store.saved_groups==500,"reject full archive without overwrite");
    insist(s.owner[0]==CPU_OWNED || s.owner[1]==CPU_OWNED,"overflow slot not recycled");
    puts("SCENE capacity_failure_retained PASS");
    setup(&f,&s,&io,0,250);
    uint32_t packet[PACKET_BYTES/4U]={0};
    insist(scene_append(&store,packet)==OK && store.saved_groups==250,"exact capacity accepted");
    insist(scene_append(&store,packet)==SAVE_OVERFLOW && scene_guards_ok(&store),"one more packet rejected");
    puts("SCENE exact_capacity_and_next_packet PASS");
    for(unsigned side=0;side<2;side++){
        setup(&f,&s,&io,0,500);
        saved[side?SCENE_GUARD_WORDS+500*8:0]=0;
        insist(scene_append(&store,packet)==SAVE_GUARD_ERROR && store.saved_groups==0,"guard fail before copy");
    }
    puts("SCENE leading_and_trailing_guards PASS");
    setup(&f,&s,&io,2,SCENE_CAP_GROUPS);
    insist(session_run(&s,&io)==ID_ERROR && store.saved_groups==500,"bad packet never archived as verified");
    puts("SCENE failed_packet_preserves_prefix PASS");
    setup(&f,&s,&io,14,SCENE_CAP_GROUPS);slow_copy=1;
    insist(session_run(&s,&io)==SOURCE_ERROR,"slow copy overrun cannot pass");
    puts("SCENE slow_copy_overflow PASS");
    setup(&f,&s,&io,1,SCENE_CAP_GROUPS);
    insist(session_run(&s,&io)==DMA_TIMEOUT && store.saved_groups==0,"timeout no invented data");
    puts("SCENE timeout_empty_archive PASS");
    setup(&f,&s,&io,0,SCENE_CAP_GROUPS);
    insist(session_run(&s,&io)==OK,"first segment");
    uint64_t last=s.last_id;
    f.have_arm=0;f.id+=1000;session_init(&s);scene_store_init(&store,saved,SCENE_CAP_GROUPS);
    insist(session_run(&s,&io)==OK && s.first_id>last && store.saved_groups==s.groups,"independent restart not stitching");
    puts("SCENE restart_explicit_new_archive PASS");
    puts("SCENE_MODEL_PASS 16 reused scenarios + 8 scene scenarios; simulated IO only");
    return 0;
}
