#ifndef CONTINUOUS_CORE_H
#define CONTINUOUS_CORE_H
#include <stdint.h>
#include <stddef.h>
#define RX_BASE 0x01000000U
#define RX_LIMIT 0x01100000U
#define GROUPS_PER_PACKET 250U
#define WORDS_PER_GROUP 8U
#define PACKET_BYTES (GROUPS_PER_PACKET*WORDS_PER_GROUP*4U)
#define GUARD_BYTES 64U
#define SLOT_STRIDE (PACKET_BYTES+GUARD_BYTES)
#define SLOT_COUNT 2U
#define RX_USED (SLOT_COUNT*SLOT_STRIDE)
#define SENTINEL 0xa5a55a5aU
#define SOURCE_SIGNATURE 0xc1000000U
#define SOURCE_FATAL 0x24U
#define SOURCE_REJECTED 0x00ffff00U
#define DMA_ERRORS 0x00004770U
#define DMA_DONE 0x00001002U
#define MIN_GROUPS 480000U
#define RUN_US 10000000U
#define TIMEOUT_US 2000000U
#define LONG_RUN_US 300000000U
#define LONG_MIN_GROUPS 14400000U
#define SHORT_RUN_US RUN_US
#define SHORT_MIN_GROUPS MIN_GROUPS
#define SHORT_SESSIONS 10U
#define SESSION_COUNT (1U+SHORT_SESSIONS)
#define RESTART_GAP_US 1000000U
struct segment_config { uint32_t run_us, min_groups; };
extern const struct segment_config endurance_schedule[SESSION_COUNT];
_Static_assert(PACKET_BYTES==8000 && SLOT_STRIDE==8064, "fixed packet/slot ABI");
_Static_assert(RX_BASE+RX_USED<=RX_LIMIT && RX_BASE%64==0 && SLOT_STRIDE%64==0, "RX bounds/alignment");
enum owner { FREE=0, DMA_OWNED, CPU_READY, CPU_OWNED };
enum failure { OK=0, ABI, SOURCE_ERROR, DMA_ERROR, DMA_TIMEOUT, PACKET_TIMEOUT,
    STOP_TIMEOUT, OWNERSHIP, ARM_ERROR, LENGTH_ERROR, GUARD_ERROR, ID_ERROR,
    RANGE_ERROR, FLAGS_ERROR, COUNTER_ERROR, START_STATE, CONFIG_ERROR, SESSION_TIMEOUT };
struct io {
    void *ctx;
    uint64_t (*time_us)(void*);
    uint32_t (*source)(void*);
    uint32_t (*dma_status)(void*);
    uint32_t (*dma_length)(void*);
    void (*run)(void*,int);
    int (*arm)(void*,unsigned,uint32_t);
    void (*prepare)(void*,unsigned);
    const uint32_t *(*acquire)(void*,unsigned);
};
struct trace { uint32_t packet,slot,sr,source,length; };
struct session {
    enum owner owner[2]; int active; unsigned next_slot;
    enum failure failed; unsigned bad_group,bad_lane;
    uint32_t bad_value,packets,groups,clips[4],zeros[4];
    int32_t minimum[4],maximum[4];
    uint64_t first_id,last_id,start_us,stop_us,end_us,last_progress,armed_us;
    uint64_t max_check_us,max_arm_gap_us;
    uint32_t last_sr,last_source,last_length,trace_count;
    struct trace recent[16];
    int stop_sent,have_id;
};
const char *failure_name(enum failure f);
void session_init(struct session *s);
// One synchronous session, no UART in the realtime loop; no reset on failure.
enum failure session_run(struct session *s, const struct io *io);
enum failure session_run_config(struct session *s, const struct io *io,
                                const struct segment_config *config);
#endif
