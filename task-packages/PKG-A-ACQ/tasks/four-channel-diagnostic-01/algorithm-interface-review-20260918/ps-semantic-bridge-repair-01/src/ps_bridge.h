#ifndef PS_BRIDGE_H
#define PS_BRIDGE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Independent host candidate. No DMA/BSP/production ABI or algorithm defaults. */
#define PSB_N 1024u
#define PSB_H 512u
#define PSB_PACKET 250u
#define PSB_INPUTS 8u
#define PSB_FRAMES 2u
#define PSB_RESULTS 4u
#define PSB_AUDIT 64u
#define PSB_BINDING 96u /* config, geometry, numeric-profile SHA-256, separately */

enum psb_reason {
 PSB_UPSTREAM=1u, PSB_QUEUE=2u, PSB_DUP=4u, PSB_REVERSE=8u,
 PSB_WRAP=16u, PSB_FLAGS=32u, PSB_RESERVED=64u, PSB_RANGE=128u,
 PSB_CLIP=256u, PSB_DROP=512u, PSB_COUNTER=1024u, PSB_LATE=2048u,
 PSB_AUDIT_FULL=4096u, PSB_EXTERNAL_FATAL=8192u, PSB_STALE=16384u,
 PSB_COMPLETION_CONFLICT=32768u, PSB_TOKEN_PROTOCOL=65536u
};
#define PSB_FATAL_MASK (PSB_UPSTREAM|PSB_QUEUE|PSB_DUP|PSB_REVERSE|PSB_WRAP|PSB_FLAGS|PSB_RESERVED|PSB_RANGE|PSB_COUNTER|PSB_LATE|PSB_AUDIT_FULL|PSB_EXTERNAL_FATAL|PSB_TOKEN_PROTOCOL)
enum psb_rc { PSB_OK, PSB_WAIT, PSB_REJECT, PSB_FAULT, PSB_FULL, PSB_EXPIRED };
enum psb_event_kind { PSB_ROW_ERROR=1, PSB_STOP, PSB_RESET, PSB_FATAL, PSB_LATE_ERROR, PSB_COMMIT_EVENT, PSB_STALE_EVENT, PSB_COMPLETION_ERROR, PSB_TOKEN_PROTOCOL_ERROR=9 };
enum psb_owner { PSB_FREE, PSB_READY, PSB_HELD, PSB_PENDING, PSB_COMMITTED, PSB_INVALID, PSB_USED };
enum psb_control { PSB_NO_CONTROL, PSB_CONTROL_STOP, PSB_CONTROL_RESET };
struct psb_group { uint64_t id; int32_t pcm[4]; uint32_t flags, reserved; };
struct psb_desc {
 uint64_t session, row_start, row_stop, first_id, last_id;
 uint32_t frame, interval; bool reset_before;
 uint8_t binding[PSB_BINDING];
};
struct psb_token { uint64_t session, generation; uint32_t slot; };
struct psb_event {
 enum psb_event_kind kind; uint32_t reasons, flags, upstream;
 uint64_t session, row, id, previous; bool have_previous, fatal;
 uint32_t unused_tail; uint64_t discarded_rows;
 struct psb_token transaction; uint32_t frame, interval; bool have_transaction_desc;
};
struct psb_config {
 uint8_t binding[PSB_BINDING];
 uint64_t ttl_samples, max_rows;
 uint32_t max_frame, max_interval, required_status;
};
struct psb_hooks {
 void *context;
 void (*frame)(void *, const struct psb_desc *, const struct psb_group *);
 void (*event)(void *, const struct psb_event *);
 bool (*clock)(void *, uint64_t *); /* current sample upper bound in SAME session */
};
struct psb_input { uint8_t bytes[PSB_PACKET*32u]; uint32_t upstream[PSB_PACKET]; size_t count; enum psb_owner owner; struct psb_token token; };
struct psb_frame { struct psb_desc desc; struct psb_group data[PSB_N]; enum psb_owner owner; struct psb_token token; bool revoked, result_issued; };
struct psb_result { struct psb_desc desc; struct psb_token token; enum psb_owner owner; uint64_t expiry, payload; uint32_t status; bool was_committed, payload_present; };
struct psb_bridge {
 struct psb_config config; struct psb_hooks hooks;
 struct psb_input input[PSB_INPUTS]; struct psb_frame frame[PSB_FRAMES]; struct psb_result result[PSB_RESULTS];
 struct psb_group window[PSB_N];
 struct psb_event audit[PSB_AUDIT], last_event;
 size_t audit_count, input_head, input_count, fill;
 uint64_t session, last_session, generation, rows, previous;
 uint32_t frame_count, interval, new_count, reasons;
 bool active, failed, have_previous, segment_open, have_interval, have_frame, next_reset;
};
struct psb_completion {
 struct psb_token token; uint32_t status; bool error; uint64_t payload;
 uint8_t binding[PSB_BINDING];
};
/* A batch is a software simultaneity contract, not hardware timing proof. */
struct psb_batch { enum psb_control control; bool fatal; const struct psb_completion *items; size_t count; };

enum psb_rc psb_init(struct psb_bridge *, const struct psb_config *, const struct psb_hooks *);
enum psb_rc psb_start(struct psb_bridge *, uint64_t session);
enum psb_rc psb_enqueue(struct psb_bridge *, const void *bytes, size_t length, const uint32_t *upstream, size_t upstream_count, struct psb_token *);
enum psb_rc psb_pump(struct psb_bridge *); /* consume exactly one owned copied packet */
enum psb_rc psb_frame_acquire(struct psb_bridge *, struct psb_token *, const struct psb_frame **);
enum psb_rc psb_frame_release(struct psb_bridge *, struct psb_token);
enum psb_rc psb_result_begin(struct psb_bridge *, struct psb_token frame, struct psb_token *result);
enum psb_rc psb_dispatch(struct psb_bridge *, const struct psb_batch *);
enum psb_rc psb_result_take(struct psb_bridge *, struct psb_token, uint64_t *payload);
enum psb_rc psb_result_release(struct psb_bridge *, struct psb_token);
void psb_audit_clear(struct psb_bridge *); /* acknowledge retained audit; does NOT clear failure */
#endif
