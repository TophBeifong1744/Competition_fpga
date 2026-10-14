"""Single-owner offline lifecycle with conservative exception disposition."""
from dataclasses import dataclass
import json
import threading
import uuid
from .contracts import Identity, ProtocolError, require, keys, integer, boolean, text
from .records import decode_raw, native_record
from .dma_rx import TestTransport


def confirmed(reply, names):
    # 中文用途：确认字段必须是真bool，不能以整数1冒充硬件证明。
    return isinstance(reply, dict) and set(reply) == set(names) and all(reply[name] is True for name in names)


@dataclass
class Slot:
    name: str
    address: int
    capacity: int
    state: str = "FREE"
    identity: Identity | None = None
    armed_tick: int | None = None
    archived: bool = False
    released: bool = False


class Session:
    def __init__(self, profile, transport, evidence):
        require(type(transport) is TestTransport and transport.scope == "SYNTHETIC_TEST" and
                transport.mode == "TEST_TRANSPORT", "qualified offline TestTransport only")
        self.profile, self.transport, self.evidence = profile, transport, evidence
        self.session_id = uuid.uuid4().hex
        self.boot = profile.data["boot"]
        self.epoch = profile.data["epoch"]
        self.generation = profile.data["generation"]
        self.transaction = 0
        self.state = "NEW"
        self.slots = {s["name"]: Slot(**s) for s in profile.data["dma"]["slots"]}
        self.active = None
        self.first_error = None
        self.pre_abort = None
        self.last_observations = {}
        self.sample_sequence = -1
        self.credits = set()
        self.native_seen = set()
        self.native_next = {}
        self.native_open = set()
        self.owed_native = {}
        self.last_raw_id = None
        self.started_source = False
        self.history = []
        self.lock = threading.RLock()
        self.busy = False
        transport.claim(self.session_id)
        self._log("claim", scope=transport.scope, transport=transport.mode,
                  ps_time_bound="UNKNOWN", identity=self.identity().as_dict())

    def identity(self, transaction=0):
        return Identity(self.boot, self.session_id, self.epoch, self.generation, transaction)

    def _log(self, kind, **value):
        self.history.append(dict(kind=kind, tick=self.transport.tick, **value))
        self.evidence.event(kind, tick=self.transport.tick, **value)

    def _failed(self, exc):
        # 中文用途：首错及处置先留内存，再尽力写审计；绝不在finally中猜测可释放。
        if self.first_error is None:
            self.first_error = {"type": type(exc).__name__, "message": str(exc),
                                "tick": self.transport.tick, "state": self.state}
        self.state = "FAULTED"
        try:
            self._log("fault", first_error=self.first_error, disposition=self.disposition())
        except BaseException as audit_error:
            self.history.append({"kind": "audit_failure", "message": str(audit_error)})

    def _execute(self, function):
        with self.lock:
            require(not self.busy, "reentrant session operation")
            self.busy = True
            try:
                return function()
            except BaseException as exc:
                self._failed(exc)
                raise
            finally:
                self.busy = False

    def _call(self, op, deadline, identity=None, **args):
        identity = identity or self.identity()
        before = self.transport.tick
        self._log("operation", operation=op, identity=identity.as_dict(), arguments=args)
        reply = self.transport.call(op, identity.as_dict(), **args)
        self.last_observations[op] = {"tick": self.transport.tick, "identity": identity.as_dict(), "reply": reply}
        self._log("observation", operation=op, identity=identity.as_dict(), reply=reply)
        require(self.transport.tick - before <= self.profile.deadline(deadline), op + " deadline")
        return reply

    def _fresh(self, reply, identity):
        require(isinstance(reply, dict), "observation object required")
        observed = reply.get("identity")
        # 中文用途：先核原生身份字段与uint64类型，拒绝bool/float弱相等后才判新鲜。
        keys(observed, ("boot", "session", "epoch", "generation", "transaction"))
        text(observed["session"], "identity.session")
        for name in ("boot", "epoch", "generation", "transaction"):
            integer(observed[name], "identity." + name, 0, (1 << 64) - 1)
        require(observed == identity.as_dict(), "stale/foreign identity")
        sequence = integer(reply.get("sample_sequence"), "sample_sequence", 0)
        require(sequence > self.sample_sequence, "duplicate/stale status sequence")
        self.sample_sequence = sequence

    def _status(self, deadline="poll"):
        result = self._call("status", deadline)
        keys(result, ("identity", "sample_sequence", "clean", "drained", "pending_packets", "owed_records", "error"))
        self._fresh(result, self.identity())
        for name in ("clean", "drained"):
            boolean(result[name], name)
        for name in ("pending_packets", "owed_records"):
            integer(result[name], name, 0, self.profile.data["queue_limit"])
        require(result["error"] is None, "source status error: " + str(result["error"]))
        return result

    def start(self):
        def operation():
            require(self.state == "NEW", "start requires new session")
            for slot in self.slots.values():
                require(confirmed(self._call("allocate", "arm", slot=slot.name, address=slot.address,
                                            capacity=slot.capacity), ("allocated",)), "initial allocation incomplete")
            status = self._status()
            require(status["clean"] and status["drained"] and status["pending_packets"] == 0 and
                    status["owed_records"] == 0, "initial source not clean")
            self.state = "RUNNING"
            self._log("start_ready", identity=self.identity().as_dict())
        return self._execute(operation)

    def _submit(self, slot_name):
        require(self.state in {"RUNNING", "DRAINING"} and self.first_error is None, "submission blocked")
        require(self.active is None, "single active S2MM required")
        require(slot_name in self.slots, "unknown slot")
        slot = self.slots[slot_name]
        require(slot.state == "FREE" and not slot.released, "slot unavailable")
        require(self.transaction < (1 << 64) - 1, "transaction overflow")
        self.transaction += 1
        identity = self.identity(self.transaction)
        # 中文用途：credit必须为本epoch新观测的完整包；不挂空DMA或伪造EOF。
        credit = self._call("credit", "poll", identity)
        keys(credit, ("identity", "sample_sequence", "credit_id", "packet_bytes"))
        self._fresh(credit, identity)
        number = integer(credit["credit_id"], "credit_id", 0)
        key = (self.epoch, number)
        require(key not in self.credits and type(credit["packet_bytes"]) is int and
                credit["packet_bytes"] == self.profile.data["dma"]["packet_bytes"], "duplicate/inexact packet credit")
        self.credits.add(key)
        slot.identity = identity
        slot.archived = False
        arm_begin = self.transport.tick
        prepare = self._call("prepare_rx", "arm", identity, slot=slot.name, address=slot.address, capacity=slot.capacity)
        require(confirmed(prepare, ("cache_prepared", "barrier")), "RX prepare/cache barrier missing")
        # 中文用途：在arm调用前标可能DMA持有，部分arm异常仍保留活动交易和缓冲。
        slot.state = "DMA_MAY_OWN"
        slot.armed_tick = self.transport.tick
        self.active = slot.name
        self._log("dma_may_own", slot=slot.name, identity=identity.as_dict())
        armed = self._call("arm", "arm", identity, slot=slot.name,
                           address=slot.address, length=credit["packet_bytes"], credit_id=number)
        require(confirmed(armed, ("armed",)), "arm not confirmed")
        slot.state = "DMA_OWNED"
        if self.state == "RUNNING" and not self.started_source:
            require(confirmed(self._call("run", "arm"), ("enabled",)), "source RUN not confirmed")
            self.started_source = True
        require(self.transport.tick - arm_begin <= self.profile.deadline("arm"), "combined arm deadline")
        return identity

    def submit(self, slot_name):
        return self._execute(lambda: self._submit(slot_name))

    def _retired(self, reply, slot):
        keys(reply, ("identity", "sample_sequence", "slot", "buffer_retired", "all_writers_retired", "barrier"))
        self._fresh(reply, slot.identity)
        require(reply["slot"] == slot.name and reply["buffer_retired"] is True and
                reply["all_writers_retired"] is True and reply["barrier"] is True,
                "buffer/all-writers retirement proof missing")

    def _archive(self, label, payload, metadata, identity=None):
        gate = self._call("archive", "archive", identity, label=label, bytes=len(payload))
        require(confirmed(gate, ("permitted",)), "archive boundary failure")
        result = self.evidence.snapshot(label, payload, dict(metadata, scope="SYNTHETIC_TEST",
                                        transport="TEST_TRANSPORT", ps_time_bound="UNKNOWN"))
        self._log("archived", archive=result)
        return result

    def _complete(self):
        require(self.first_error is None and self.state in {"RUNNING", "DRAINING"}, "CPU read blocked")
        require(self.active is not None, "no active transaction")
        slot = self.slots[self.active]
        require(slot.state == "DMA_OWNED", "arm completion unknown")
        while True:
            reply = self._call("completion", "poll", slot.identity, slot=slot.name)
            keys(reply, ("identity", "sample_sequence", "done", "ioc", "actual_length", "error"))
            self._fresh(reply, slot.identity)
            boolean(reply["done"], "done")
            boolean(reply["ioc"], "ioc")
            integer(reply["actual_length"], "actual_length")
            require(reply["error"] is None, "DMA error: " + str(reply["error"]))
            require(self.transport.tick - slot.armed_tick <= self.profile.deadline("transfer"), "transfer deadline")
            if reply["done"]:
                require(reply["actual_length"] == self.profile.data["dma"]["packet_bytes"], "inexact actual_length")
                break
        # 中文用途：IOC不构成CPU所有权；先逐buffer写退休，再invalidate和读屏障。
        self._retired(self._call("retired", "poll", slot.identity, slot=slot.name), slot)
        slot.state = "CPU_READY"
        cache = self._call("invalidate", "poll", slot.identity, slot=slot.name)
        require(confirmed(cache, ("invalidated", "barrier")), "invalidate/cache barrier missing")
        slot.state = "CPU_OWNED"
        read = self._call("read", "poll", slot.identity, slot=slot.name)
        keys(read, ("data_hex",))
        require(isinstance(read["data_hex"], str), "raw hex required")
        try:
            raw = bytes.fromhex(read["data_hex"])
        except ValueError as exc:
            raise ProtocolError("invalid raw hex") from exc
        require(len(raw) == self.profile.data["dma"]["packet_bytes"], "read byte count mismatch")
        # 先原样归档，解析失败也不丢唯一原件且不回收槽。
        archive = self._archive("raw", raw, {"identity": slot.identity.as_dict(), "raw_schema": "raw32-le-s24-v1"}, slot.identity)
        slot.archived = True
        frames = decode_raw(raw)
        prior = self.last_raw_id
        for frame in frames:
            require(prior is None or frame.source_id > prior, "duplicate/backwards source ID")
            if prior is not None and frame.source_id != prior + 1:
                self._log("source_id_gap", previous=prior, current=frame.source_id,
                          epoch=self.epoch, drop_semantics="UNKNOWN")
            prior = frame.source_id
        self.last_raw_id = prior
        self._archive("integer-export", json.dumps([f.as_dict() for f in frames], sort_keys=True).encode("utf-8"),
                      {"identity": slot.identity.as_dict(), "source_archive": archive["raw_file"]}, slot.identity)
        slot.state = "FREE"
        self.active = None
        self._log("slot_recycled", slot=slot.name, identity=slot.identity.as_dict())
        return frames

    def complete(self):
        return self._execute(self._complete)

    def _native(self):
        require(self.first_error is None and self.state in {"RUNNING", "DRAINING"}, "native read blocked")
        reply = self._call("native", "poll")
        keys(reply, ("identity", "sample_sequence", "record_id", "record"))
        self._fresh(reply, self.identity())
        record_id = integer(reply["record_id"], "test host-journal record_id", 0)
        key = (self.epoch, record_id)
        require(key not in self.native_seen, "duplicate test-native envelope")
        record = native_record(reply["record"])
        if record["kind"] == "diagnostic_word":
            fields = record["fields"]
            sequence_key = (self.epoch, fields["bank"], fields["sequence"])
            expected = self.native_next.get(sequence_key, 0)
            require(fields["word"] == expected, "out-of-order native diagnostic word")
            self.native_open.add(sequence_key)
        require(len(self.owed_native) < self.profile.data["queue_limit"], "native archive backpressure")
        self.native_seen.add(key)
        self.owed_native[key] = record
        self._archive("test-native", json.dumps(reply, sort_keys=True).encode("utf-8"),
                      {"identity": self.identity().as_dict(), "wire_schema": "UNBOUND",
                       "ack_semantics": "TEST_TRANSPORT_HOST_JOURNAL_ONLY"})
        ack = self._call("ack_native", "poll", record_id=record_id, record=record)
        require(confirmed(ack, ("acked",)), "test native ACK incomplete")
        del self.owed_native[key]
        if record["kind"] == "diagnostic_word":
            self.native_next[sequence_key] = expected + 1
            if fields["last"]:
                self.native_open.remove(sequence_key)
        return record

    def consume_native(self):
        return self._execute(self._native)

    def _release(self, slot):
        require(slot.state == "FREE" and not slot.released and slot.archived, "release not safe/archived")
        # 中文用途：先标释放未知，release异常禁止第二次调用或隐式重试。
        slot.state = "RELEASE_UNKNOWN"
        reply = self._call("release", "poll", slot.identity or self.identity(), slot=slot.name)
        require(confirmed(reply, ("released",)), "release outcome unknown")
        slot.released = True
        slot.state = "RELEASED"

    def stop(self):
        def operation():
            require(self.state == "RUNNING" and self.first_error is None, "normal STOP blocked")
            self.state = "DRAINING"
            start_tick = self.transport.tick
            require(confirmed(self._call("stop", "stop"), ("stop_requested",)), "STOP request failed")
            while True:
                require(self.transport.tick - start_tick < self.profile.deadline("stop"), "STOP deadline")
                if self.active is not None:
                    self._complete()
                status = self._status("poll")
                if status["pending_packets"]:
                    available = next((s.name for s in self.slots.values() if s.state == "FREE"), None)
                    require(available is not None, "no drain slot available")
                    self._submit(available)
                elif status["owed_records"]:
                    self._native()
                elif status["clean"] and status["drained"]:
                    require(self.active is None and not self.owed_native and not self.native_open, "unretired stop obligations")
                    break
            require(self.transport.tick - start_tick <= self.profile.deadline("stop"), "STOP deadline")
            # 空闲未用槽也须得到本会话全路径退休证明，然后存档处置才release。
            for slot in self.slots.values():
                require(slot.state == "FREE", "unretired slot")
                slot.identity = slot.identity or self.identity()
                self._retired(self._call("retired", "poll", slot.identity, slot=slot.name), slot)
                self._archive("slot-disposition", b"", {"slot": slot.name, "identity": slot.identity.as_dict(),
                                                         "retired": True}, slot.identity)
                slot.archived = True
                self._release(slot)
            require(self.transport.tick - start_tick <= self.profile.deadline("stop"), "STOP cleanup deadline")
            self.started_source = False
            self.state = "STOPPED"
            self._log("clean_stop", identity=self.identity().as_dict(), disposition=self.disposition())
        return self._execute(operation)

    def restart(self):
        def operation():
            require(self.state == "STOPPED" and self.first_error is None and not self.owed_native and
                    not self.native_open and self.active is None and all(s.released for s in self.slots.values()),
                    "restart requires clean stopped and retired slots")
            require(self.epoch < (1 << 64) - 1 and self.generation < (1 << 64) - 1, "epoch/generation overflow")
            self.epoch += 1
            self.generation += 1
            self.state = "NEW"
            # 新epoch重新分配描述，不清历史或原始帧号；allocation是显式模拟事件。
            for slot in self.slots.values():
                allocation = self._call("allocate", "arm", slot=slot.name, address=slot.address, capacity=slot.capacity)
                require(confirmed(allocation, ("allocated",)), "allocation incomplete")
                slot.state, slot.identity, slot.armed_tick = "FREE", None, None
                slot.archived = slot.released = False
            status = self._status()
            require(status["clean"] and status["drained"] and status["pending_packets"] == 0 and
                    status["owed_records"] == 0, "restart source not clean")
            self.state = "RUNNING"
            self._log("restart_ready", identity=self.identity().as_dict())
        return self._execute(operation)

    def abort(self, authorized):
        def operation():
            require(authorized is True and self.state == "FAULTED", "explicit authorized abort after failure required")
            self.pre_abort = {"first_error": dict(self.first_error), "disposition": self.disposition(),
                              "tick": self.transport.tick,
                              "last_observations": json.loads(json.dumps(self.last_observations))}
            self._log("pre_abort", snapshot=self.pre_abort)
            begin = self.transport.tick
            identity = self.slots[self.active].identity if self.active else self.identity()
            require(confirmed(self._call("abort", "abort", identity), ("abort_requested",)), "abort not confirmed")
            # 中文用途：abort后的新匹配全路径静止才可退休；未知仍pin，禁止读数据。
            quiet = self._call("quiescence", "abort", identity)
            keys(quiet, ("identity", "sample_sequence", "all_writers_retired", "source_stopped", "owed_records", "error"))
            self._fresh(quiet, identity)
            require(quiet["all_writers_retired"] is True and quiet["source_stopped"] is True and
                    type(quiet["owed_records"]) is int and quiet["owed_records"] == 0 and
                    not self.owed_native and not self.native_open, "abort quiescence/record obligations unknown")
            require(self.transport.tick - begin <= self.profile.deadline("abort"), "abort deadline")
            self._log("abort_status", status=quiet, preserved_first_error=self.first_error)
            for slot in self.slots.values():
                require(slot.state != "RELEASE_UNKNOWN", "release outcome remains unknown; cannot retry")
                if slot.released:
                    continue
                slot.identity = slot.identity or self.identity()
                self._retired(self._call("retired", "abort", slot.identity, slot=slot.name), slot)
                self._archive("aborted-disposition", b"", {"slot": slot.name, "identity": slot.identity.as_dict(),
                              "pre_abort": self.pre_abort, "payload": "NOT_READ_AFTER_ERROR"}, slot.identity)
                slot.archived = True
                slot.state = "FREE"
                self._release(slot)
            require(self.transport.tick - begin <= self.profile.deadline("abort"), "abort cleanup deadline")
            self.active = None
            self.state = "ABORTED"
            self.started_source = False
            self._log("abort_retired", first_error=self.first_error, disposition=self.disposition())
        return self._execute(operation)

    def close(self):
        def operation():
            require(self.state in {"STOPPED", "ABORTED"} and self.active is None and
                    all(s.released for s in self.slots.values()) and not self.owed_native and not self.native_open,
                    "cannot close/pin unknown ownership")
            self.transport.relinquish(self.session_id)
            self.state = "CLOSED"
            self._log("owner_released")
        return self._execute(operation)

    def disposition(self):
        return {name: {"state": slot.state, "address": slot.address, "capacity": slot.capacity,
                      "identity": slot.identity.as_dict() if slot.identity else None,
                      "archived": slot.archived, "released": slot.released}
                for name, slot in self.slots.items()}

    def summary(self):
        return {"scope": "SYNTHETIC_TEST", "transport": "TEST_TRANSPORT", "hardware": "NOT_RUN",
                "ps_time_bound": "UNKNOWN", "state": self.state, "identity": self.identity().as_dict(),
                "first_error": self.first_error, "pre_abort": self.pre_abort, "active": self.active,
                "slots": self.disposition(), "owed_native": len(self.owed_native),
                "incomplete_native_records": len(self.native_open), "last_original_source_id": self.last_raw_id}
