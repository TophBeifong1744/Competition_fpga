# Same-clock PCM window storage (WC-1.1)

Task: I17-WINDOW-CONSUMER-PRODUCT-20261007. Parent:
`f8367f5bd2bd7d52348c9259a9051ff050c4f1ab`.
Approved design: frozen WC-1.1 `ARCHITECTURE.md`, SHA256
`006dda23d0ad0aadb253fa856d3600351b763543a25c01ed1bc9b16ed062211e`.
Additive read-status priority clarification SHA256:
`0fa274d06219b87fdb4bb77a77e17eea96add69bfab9d9f52f479a7b19b0b597`.
Mode: FULL / RTL_IMPLEMENTATION. This source is pending independent validation
and review; documentation is not an acceptance result.

`pcm4_window_consumer.sv` owns one actual 1024 x 432-bit raw record RAM
(442368 bits / 55296 bytes), a separate 416-bit terminal register, one descriptor,
one development reader lease, and one retirement audit register.
`pcm4_h3_window_entry.v` is a pure Verilog flat shell: original A m/e payload
names and widths enter packed wiring to the SystemVerilog core. It adds no state
or latency. `SOURCES.txt` is the local source list, relative to this directory;
compile the `.sv` as SystemVerilog. No whole A handoff replacement or complete
H3 manager is supplied, and no formal vendor project/file list is changed.

Only INPUT_COMPLETE is published. There is no numerical backend, algorithm
success/fresh/53-item status, result availability, commit, or production take.
The producer already supplies 1024/512 overlapping windows; this module stores
each window without reframing or rejecting an otherwise legal overlapping ID
range. Neither source status nor terminal codes imply local cancellation.

## Payload layouts

These are internal concatenations, MSB first, retaining raw bits. They do not
define a serialized public ABI. The descriptor's `desc_first`, audit raw records,
and successful read payload use the same 432-bit layout.

| A m field | Packed bits | Width |
| --- | --- | --- |
| m_pcm | 431:304 | 128 |
| m_id | 303:240 | 64 |
| m_flags | 239:236 | 4 |
| m_session_id | 235:204 | 32 |
| m_frame_index | 203:172 | 32 |
| m_interval_index | 171:140 | 32 |
| m_sample_index | 139:130 | 10 |
| m_first_id | 129:66 | 64 |
| m_last_id | 65:2 | 64 |
| m_reset_before | 1 | 1 |
| m_last | 0 | 1 |

`m_pcm[31:0]` is mic0, `[63:32]` mic1, `[95:64]` mic2, `[127:96]`
mic3. Each lane is S24 sign-extended to S32. IDs remain unsigned 64-bit raw
integers; no truncation or conversion to floating point occurs. Flags are stored
without choosing a clipping policy.

| A e field | Packed bits | Width |
| --- | --- | --- |
| e_code | 415:408 | 8 |
| e_parent_code | 407:400 | 8 |
| e_source_status | 399:368 | 32 |
| e_source_drained | 367 | 1 |
| e_session_id | 366:335 | 32 |
| e_id | 334:271 | 64 |
| e_prev_id | 270:207 | 64 |
| e_id_valid | 206 | 1 |
| e_prev_id_valid | 205 | 1 |
| e_raw_flags | 204:173 | 32 |
| e_source_flags | 172:165 | 8 |
| e_unused_tail | 164:154 | 11 |
| e_interval_index | 153:122 | 32 |
| e_packet_index | 121:90 | 32 |
| e_word_index | 89:79 | 11 |
| e_packet_words | 78:68 | 11 |
| e_tdata | 67:36 | 32 |
| e_tkeep | 35:32 | 4 |
| e_tlast | 31 | 1 |
| e_drop_buffered_groups | 30:23 | 8 |
| e_drop_verified_groups | 22:15 | 8 |
| e_framer_code | 14:12 | 3 |
| e_framer_error_tail | 11:1 | 11 |
| e_stop_truncated | 0 | 1 |

## Port groups and handshakes

All ports use one `clk`. A transaction is accepted on a rising edge when its
valid and ready are high. Input sources must hold the complete request/payload
through stall. Predicates use pre-edge state. Cold `rst_n=0` disables all ready
and output-valid handshakes; reset register updates occur on the clock edge.

| Group | Ports and widths | Meaning |
| --- | --- | --- |
| Core PCM | m_valid, m_ready, m_payload[431:0] | Store one raw row on acceptance |
| Core terminal | e_valid, e_ready, e_payload[415:0] | Save one terminal independently of PCM |
| Saved terminal | terminal_valid, terminal_ready, terminal_payload[415:0] | ACK clears only the saved terminal |
| Descriptor | desc_valid, desc_ready, desc_token[63:0], desc_first[431:0] | Immutable INPUT_COMPLETE; ACK grants the single lease |
| Read request | rd_valid, rd_ready, rd_token[63:0], rd_index[9:0] | Request a row for an established lease |
| Read response | rd_rsp_valid, rd_rsp_ready, rd_rsp_token[63:0], rd_rsp_index[9:0], rd_rsp_status[1:0], rd_rsp_payload[431:0] | Registered echo/status/raw response |
| Local command | cmd_valid, cmd_ready, cmd_op[1:0], cmd_token[63:0], cmd_reason[7:0] | Explicit development retirement/revoke/reset |
| Command response | cmd_rsp_valid, cmd_rsp_ready, cmd_rsp_token[63:0], cmd_rsp_status[2:0] | Registered echoed-token status |
| Retirement audit | audit_valid, audit_ready, audit_token[63:0], audit_count[10:0], audit_first[431:0], audit_bad_valid, audit_bad[431:0], audit_error[3:0], audit_revoked, audit_reason[7:0], audit_retire_op[1:0] | Saved preclear slot facts; ACK clears only audit |
| Diagnostics | reset_barrier, token_exhausted, slot_active, slot_token[63:0], slot_count[10:0], slot_state[2:0], slot_error[3:0], slot_revoked | Observation only; no read ownership granted |

No output entry has lookthrough or replacement on an ACK edge. All valid
descriptor/response/terminal/audit payloads remain unchanged through stall.
`rd_ready = rst_n && !rd_rsp_valid_q && !cmd_valid`: any offered command suppresses
reads, including a command stalled by its response register. Each accepted read
or command at edge E produces its registered response after E; its earliest ACK
is E+1. With immediate ACKs, requests can be accepted once every two edges.
Rejections echo token/index and have zero read data with no RAM access.

The 1024th legal row accepted at E publishes a descriptor after E; earliest
descriptor ACK is E+1. Ownership is established at that ACK, so a request on the
same edge sees no pre-edge lease. The earliest eligible read request is E+2 and
its earliest response ACK E+3. Revocation never withdraws a historical descriptor
or changes a pending read response, including an already successful response.

PCM accepts up to one row each edge while EMPTY with allocation capacity, or
RECEIVING/DRAIN with count below 1024. COMPLETE and QUARANTINED deassert m_ready.
An accepted WARM_RESET command deasserts m_ready on that edge even when the
command will report rejection. RELEASE has no simultaneous new allocation;
after successful retirement at E, earliest allocation is E+1. Saved e has its
own capacity: e_ready is high only when its register is empty, with no ACK
lookthrough. PCM and e may otherwise handshake independently.

## Validation and bounded malformed drain

Physical RAM write address is accepted count, never m_sample_index. Count is
11 bits (0..1024), and no write is accepted at count 1024. The first accepted
record allocates a token, saves the complete raw first record, and emits one
registered reset_barrier pulse iff its m_reset_before is high. This attribute
must match on later rows; it never resets storage on every high row.

| slot_state | Code | Meaning |
| --- | --- | --- |
| EMPTY | 0 | No live slot; diagnostics token/count/error/revoked are zero |
| RECEIVING | 1 | Legal partial capture |
| DRAIN | 2 | Malformed or locally revoked partial capture |
| QUARANTINED | 3 | Drain ended; explicit audited recovery required |
| COMPLETE | 4 | Legal 1024 rows; descriptor/reader obligations retained |

On each accepted record the ordered checks are: index equals pre-edge accepted
count; incoming first+1023 fits 64 bits and equals incoming last, and incoming ID
equals incoming first+count; session/frame/interval/first/last/reset_before match
the captured first record; m_last is high iff expected count is 1023; all four
PCM lanes have correct sign extension. The two additions use 65-bit arithmetic.
Incoming row arithmetic precedes comparison to captured attributes, following
the frozen diagnostic priority.

| slot_error / audit_error | Code |
| --- | --- |
| NONE | 0 |
| INDEX | 1 |
| ID_OR_RANGE | 2 |
| FRAME_IDENTITY | 3 |
| LAST | 4 |
| PCM_EXTENSION | 5 |

The earliest bad raw row and its first category are preserved; later bad rows
cannot replace them. These are internal diagnostics, not A's public errors.
Malformed rows remain raw transport records. DRAIN ends at observed m_last or
the 1024-row capacity, then becomes QUARANTINED. An incomplete legal capture can
wait indefinitely and never publishes completion. There is no timeout, padding,
automatic allocation of another slot, or cross-window uniqueness/hop policy.
Unexpected state codes fail closed for capture and successful reads; recovery
uses a legal audited warm reset if there are no outstanding reader obligations.

## Ownership, commands, and audit

| rd_rsp_status | Code | Ordered eligibility |
| --- | --- | --- |
| OK | 0 | Matching live token, established lease, COMPLETE, not revoked |
| STALE_OR_NO_OWNER | 1 | No live slot, token mismatch, or no lease; also ineligible state |
| REVOKED | 2 | Matching live token and established lease, revoked |
| Reserved | 3 | Not emitted |

Lease/live/token checks precede revoked status. Only successful eligible reads
access RAM. Descriptor ACK grants one development reader; there is no multireader
or DAS lifetime contract. A read request alone cannot acquire ownership.

| cmd_op / audit_retire_op | Code | Preconditions and effect |
| --- | --- | --- |
| RELEASE | 0 | Matching token, lease owned, pre-edge descriptor/read response absent, audit empty. Caller promises no future access or callbacks. Snapshot then clear slot. |
| REVOKE | 1 | Matching active token. Mark revoked; preserve first reason and all raw data/diagnostics. Partial capture enters DRAIN; COMPLETE preserves its descriptor/lease. |
| WARM_RESET | 2 | Matching token, no descriptor/lease/read response, audit empty if active. Snapshot then clear slot. EMPTY accepts only token0 and creates no audit. |
| Bad operation | 3 | Rejected without changing slot |

| cmd_rsp_status | Code | Priority |
| --- | --- | --- |
| OK | 0 | All operation preconditions satisfied |
| STALE | 1 | Missing/mismatched token for a valid op |
| BUSY | 2 | Required ownership or absent-obligation condition failed |
| AUDIT_FULL | 3 | Retirement needs occupied audit entry |
| BAD_OP | 4 | Invalid operation; before token checks |

For valid operations, token checks precede BUSY, then AUDIT_FULL. A rejected
command changes no slot facts. Audit ACK and read-response ACK do not satisfy
retirement predicates on the same edge: pre-edge fullness/obligations apply.
An already pending descriptor may ACK concurrently with REVOKE; that historical
lease is retained. Last PCM row plus accepted matching REVOKE stores/counts the
row, marks revoked, and suppresses creation of a new descriptor. Repeated revoke
preserves the first reason. No e ACK, e content, audit ACK, or read-response ACK
automatically releases PCM.

The audit stores preclear token/count/raw first/raw first bad/error/revoked/reason
and retirement op. WARM_RESET preserves terminal storage, allocator/exhaustion,
existing audit history, and other pending responses. Partial nonzero reset is
permitted only when its reader/descriptor/read-response obligations are absent.
No old read obligation is silently discarded.

## Reset and token lifetime

Cold rst_n is synchronous, active low, and must span a clk edge. External global
invalidation of every prior reader/callback is a precondition for cold reset.
Cold reset clears all validity/control/response/audit registers, resets allocation
to token1, and does not reset RAM contents. Runtime retirement uses the commands;
cold reset must not be used to conceal live reader obligations. reset_barrier is
an informational pulse for the first accepted row, not a backend cold reset.

TOKEN_LIMIT is an unsigned 64-bit parameter, default U64max. Allocation is
1..TOKEN_LIMIT, without wrap or reuse before cold reset. Allocation of the last
token sets sticky token_exhausted while that slot remains serviceable. Warm
reset and release preserve the allocator and exhaustion. TOKEN_LIMIT=0 fails
closed for PCM allocation while independent terminal/management interfaces
remain available. Reduced values 2 and 0 are developmental elaborations for
bounded exhaustion tests, not observations of U64max allocations.

## Integration and evidence limits

This is one clock domain with no CDC, CSR/IRQ/DMA, primitives/IP, constraints,
BD, firmware, or electrical changes. Inputs must already be synchronous to clk;
physical clock/reset distribution, RDC and timing are integration responsibilities.
No production cancel mapping from A source/parent/arm/status is defined. The local
explicit command inputs require a caller authorized to manage this reader's
obligations. STOP/closing/fault e remains transport evidence only.

The validation cone contains 65-bit additions/comparisons, raw identity equality,
fixed four-lane extension checks, and state/control selection. No pipeline was
added; mapping, actual RAM primitive choice, area, critical paths, Fmax, STA,
CDC/RDC, implementation and board evidence are NOT RUN/UNVERIFIED. Power is
NOT APPLICABLE. The RAM declaration establishes logical capacity only.
One slot and indefinite consumer stalls cannot prove production losslessness,
continuous throughput, service bounds, or timely terminal processing.

This product writer supplies no test assets or EDA result. After source freeze,
the sequential verification writer owns diagnostic compile/simulation assets;
original B-REVIEW owns independent validation and nonauthor review of the frozen
candidate. No functional acceptance, engineering run, merge, or hardware approval
is implied by this source delivery.
