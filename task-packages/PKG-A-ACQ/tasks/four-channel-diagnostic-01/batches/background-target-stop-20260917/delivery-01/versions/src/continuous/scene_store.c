#include "scene_store.h"
#include <string.h>
void scene_store_init(struct scene_store *a,uint32_t *allocation,uint32_t capacity) {
    a->allocation=allocation;a->data=allocation+SCENE_GUARD_WORDS;
    a->capacity_groups=capacity;a->saved_groups=0;
    /* Called only before START. CPU owns all archive storage; DMA never targets it. */
    for(uint32_t i=0;i<capacity*WORDS_PER_GROUP+2U*SCENE_GUARD_WORDS;i++)
        allocation[i]=SENTINEL;
}
int scene_guards_ok(const struct scene_store *a) {
    for(unsigned i=0;i<SCENE_GUARD_WORDS;i++)
        if(a->allocation[i]!=SENTINEL ||
           a->data[a->capacity_groups*WORDS_PER_GROUP+i]!=SENTINEL)return 0;
    return 1;
}
enum failure scene_append(struct scene_store *a,const uint32_t *packet) {
    if(!scene_guards_ok(a))return SAVE_GUARD_ERROR;
    if(a->saved_groups>a->capacity_groups ||
       a->capacity_groups-a->saved_groups<GROUPS_PER_PACKET)return SAVE_OVERFLOW;
    memcpy(a->data+a->saved_groups*WORDS_PER_GROUP,packet,PACKET_BYTES);
    a->saved_groups+=GROUPS_PER_PACKET;
    return scene_guards_ok(a)?OK:SAVE_GUARD_ERROR;
}
uint32_t scene_fnv1a(const struct scene_store *a) {
    const unsigned char *p=(const unsigned char*)a->data;
    uint32_t h=2166136261U;
    for(uint32_t i=0;i<a->saved_groups*WORDS_PER_GROUP*4U;i++)h=(h^p[i])*16777619U;
    return h;
}
