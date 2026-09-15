/* Execute the actual portable PS loop against a deterministic peripheral model.
 * This is simulated software evidence, not XAxiDma/cache hardware validation.
 */
#include "continuous_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct fake {
    uint64_t time,id,next_packet,done_at; int running,draining,active;
    uint32_t buffers[2][SLOT_STRIDE/4],sr,length;
    unsigned queued,completed,mode,prepares[2],acquires[2],prepared[2];
    unsigned slot,last_arm;int have_arm;struct session *session;
};
static void insist(int ok,const char *msg){if(!ok){fprintf(stderr,"MODEL FAILURE %s\n",msg);exit(2);}}
static void advance(struct fake *f){
    f->time+=20;
    while((f->running || f->draining) && f->time>=f->next_packet){f->queued++;f->next_packet+=5209;if(f->draining && f->mode!=10)f->draining=0;}
    if(f->active && f->time>=f->done_at && f->mode!=1){
        uint32_t *p=f->buffers[f->slot];
        insist(f->session->owner[f->slot]==DMA_OWNED,"DMA wrote a CPU owned slot");
        for(unsigned g=0;g<250;g++){
            uint64_t id=f->id++;p[g*8]=(uint32_t)id;p[g*8+1]=(uint32_t)(id>>32);
            for(unsigned c=0;c<4;c++)p[g*8+c+2]=(uint32_t)(int32_t)((int)(id%1000)*(c+1)*(c&1?-1:1));
            p[g*8+6]=0;p[g*8+7]=0;
        }
        if(f->completed==2){
            if(f->mode==2)p[0]--;if(f->mode==3)p[PACKET_BYTES/4]=0;
            if(f->mode==4)p[2]=0x800000;if(f->mode==5)p[6]=0x10;
            if(f->mode==6)p[7]=1;
        }
        f->active=0;f->queued--;f->sr=DMA_DONE;f->length=f->mode==7?7996:8000;f->completed++;
    }
}
static uint64_t time_us(void *p){struct fake *f=p;advance(f);return f->time;}
static uint32_t source(void *p){struct fake *f=p;
    if(f->mode==8)return 0xa;
    uint32_t v=SOURCE_SIGNATURE|2U|(f->running?1U:0U)|(f->queued?0x40U:0U);
    if(!f->running&&!f->draining&&!f->queued)v|=8;
    if(f->draining)v|=0x80;
    if(f->mode==9&&f->completed>3)v|=0x124;
    if(f->mode==14&&f->queued>4)v|=0x104;
    if(f->mode==10&&f->draining)v&=~8U;
    if(f->mode==11&&f->running)v&=~0x40U;
    return v;
}
static uint32_t sr(void *p){struct fake *f=p;return f->mode==12&&f->completed>3?0x4000:f->sr;}
static uint32_t length(void *p){return ((struct fake*)p)->length;}
static void run(void *p,int v){struct fake *f=p;
    if(v){f->running=1;f->next_packet=f->time+5209;}
    else if(f->running){f->running=0;f->draining=1;}
}
static void prepare(void *p,unsigned s){struct fake *f=p;
    insist(f->session->owner[s]==FREE,"prepare overwritten CPU or DMA owner");
    for(unsigned i=0;i<SLOT_STRIDE/4;i++)f->buffers[s][i]=SENTINEL;
    f->prepared[s]=1;f->prepares[s]++;
}
static int arm(void *p,unsigned s,uint32_t bytes){struct fake *f=p;
    insist(!f->active && f->queued && bytes==8000 && f->prepared[s],"arm contract/credit");
    if(f->have_arm)insist(s!=f->last_arm,"not alternating slots");
    f->have_arm=1;f->last_arm=s;
    if(f->mode==13)return 1;
    f->prepared[s]=0;f->active=1;f->slot=s;f->sr=0;f->done_at=f->time+60;return 0;
}
static const uint32_t *acquire(void *p,unsigned s){struct fake *f=p;
    insist(f->session->owner[s]==CPU_OWNED && (!f->active || f->slot!=s),"acquire before DMA complete");
    f->acquires[s]++;
    if(f->mode==14 && f->completed==5)f->time+=50000; // deliberate slow consumer exceeds FIFO budget
    return f->buffers[s];
}
int main(void){
    const enum failure expect[]={OK,DMA_TIMEOUT,ID_ERROR,GUARD_ERROR,RANGE_ERROR,FLAGS_ERROR,FLAGS_ERROR,
        LENGTH_ERROR,ABI,SOURCE_ERROR,STOP_TIMEOUT,PACKET_TIMEOUT,DMA_ERROR,ARM_ERROR,SOURCE_ERROR,OWNERSHIP};
    for(unsigned m=0;m<sizeof(expect)/sizeof(expect[0]);m++){
        struct fake f={0};struct session s;session_init(&s);f.session=&s;f.mode=m;f.id=0xfffffff0ULL;
        if(m==15)s.owner[0]=CPU_OWNED;
        struct io io={&f,time_us,source,sr,length,run,arm,prepare,acquire};
        enum failure got=session_run(&s,&io);
        insist(got==expect[m],failure_name(got));
        if(got==OK){
            insist(s.groups>=480000 && s.stop_us-s.start_us>=10000000,"less than ten seconds");
            uint64_t last=s.last_id;f.have_arm=0;f.id+=1000;session_init(&s);
            insist(session_run(&s,&io)==OK && s.first_id>last,"restart continuity");
        }else{
            uint32_t before=s.last_source;insist(session_run(&s,&io)==got && s.last_source==before,"fault hidden by retry");
        }
        printf("CASE %u PASS expected=%s packets=%u groups=%u trace=%u\n",m,failure_name(got),s.packets,s.groups,s.trace_count);
    }
    puts("PS_CORE_MODEL_PASS (actual C loop; simulated IO/time/cache callbacks)");return 0;
}
