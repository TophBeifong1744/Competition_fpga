#ifndef SCENE_STORE_H
#define SCENE_STORE_H
#include "continuous_core.h"
#define SCENE_CAP_GROUPS 300000U
#define SCENE_CAP_BYTES (SCENE_CAP_GROUPS*WORDS_PER_GROUP*4U)
#define SCENE_GUARD_WORDS (GUARD_BYTES/4U)
#define SCENE_TOTAL_WORDS (SCENE_CAP_BYTES/4U+2U*SCENE_GUARD_WORDS)
struct scene_store {
    uint32_t *allocation, *data;
    uint32_t capacity_groups, saved_groups;
};
void scene_store_init(struct scene_store *a,uint32_t *allocation,uint32_t capacity);
int scene_guards_ok(const struct scene_store *a);
enum failure scene_append(struct scene_store *a,const uint32_t *packet);
uint32_t scene_fnv1a(const struct scene_store *a);
#endif
