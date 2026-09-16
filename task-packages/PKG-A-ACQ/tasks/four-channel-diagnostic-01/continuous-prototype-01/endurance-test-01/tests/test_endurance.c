#define main legacy_main
#include "test_core.c"
#undef main

static uint64_t jump_time(void *p){
    struct fake *f=p;
    if(f->completed==5 && f->time<LONG_RUN_US)f->time=LONG_RUN_US+TIMEOUT_US;
    return time_us(p);
}
int main(void){
    legacy_main(); /* Re-run all 16 existing actual-C-loop model cases. */
    struct fake f={0};
    struct session segments[SESSION_COUNT];
    struct io io={&f,time_us,source,sr,length,run,arm,prepare,acquire};
    uint64_t previous=0;
    f.id=0xfffffff0ULL;
    insist(SESSION_COUNT==11 && SHORT_SESSIONS==10,"profile count");
    for(unsigned n=0;n<SESSION_COUNT;n++){
        struct session *s=&segments[n];session_init(s);f.session=s;
        f.have_arm=0; /* Model checker expects each new session's slot zero; not a peripheral reset. */
        insist(endurance_schedule[n].run_us==(n?10000000U:300000000U),"schedule duration");
        insist(endurance_schedule[n].min_groups==(n?480000U:14400000U),"schedule groups");
        insist(session_run_config(s,&io,&endurance_schedule[n])==OK,"profile run");
        insist(s->stop_sent && s->stop_us-s->start_us>=endurance_schedule[n].run_us,"early stop");
        insist(s->groups>=endurance_schedule[n].min_groups,"insufficient groups");
        insist(s->last_id-s->first_id+1==s->groups,"within-session ID accounting");
        insist(!n || s->first_id>previous,"restart ID did not advance");previous=s->last_id;
        insist(s->owner[0]==FREE && s->owner[1]==FREE && s->active==-1,"not drained");
        insist(!f.running && !f.draining && !f.active && !f.queued,"model still active");
        printf("PROFILE session=%u PASS groups=%u packets=%u elapsed_us=%llu drain_us=%llu\n",n,
               s->groups,s->packets,(unsigned long long)(s->stop_us-s->start_us),
               (unsigned long long)(s->end_us-s->stop_us));
        if(n+1<SESSION_COUNT){f.time+=RESTART_GAP_US;f.id+=48000;}
    }
    struct session bad;session_init(&bad);
    struct segment_config wrong={LONG_RUN_US,SHORT_MIN_GROUPS};
    insist(session_run_config(&bad,&io,&wrong)==CONFIG_ERROR,"mismatched duration/groups accepted");
    insist(session_run_config(&bad,&io,&endurance_schedule[0])==CONFIG_ERROR,"failure hidden");
    session_init(&bad);insist(session_run_config(&bad,&io,0)==CONFIG_ERROR,"null accepted");
    struct fake stalled={0};session_init(&bad);stalled.session=&bad;
    io.ctx=&stalled;io.time_us=jump_time;
    insist(session_run_config(&bad,&io,&endurance_schedule[0])==SESSION_TIMEOUT,"total deadline absent");
    puts("ENDURANCE_MODEL_PASS: old16 + schedule11 + invalid/retry/null/deadline; simulated time/peripherals, NOT board");
    return 0;
}
