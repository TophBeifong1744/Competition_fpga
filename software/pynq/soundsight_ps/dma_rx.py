"""No hardware driver: strictly labelled, finite transcript transport."""
import copy
from .contracts import ProtocolError, keys, require, integer, text


class TestTransport:
    scope = "SYNTHETIC_TEST"
    mode = "TEST_TRANSPORT"
    _claimed = set()

    def __init__(self, script):
        keys(script, ("schema_version", "scope", "transport", "resource_id", "max_events", "events", "actions"))
        require(type(script["schema_version"]) is int and script["schema_version"] == 1, "script version")
        require(script["scope"] == self.scope and script["transport"] == self.mode, "explicit test transport required")
        self.resource_id = text(script["resource_id"], "resource_id")
        limit = integer(script["max_events"], "max_events", 1)
        require(isinstance(script["events"], list) and len(script["events"]) <= limit, "bounded script events required")
        require(isinstance(script["actions"], list) and len(script["actions"]) <= limit, "bounded script actions required")
        self.events = copy.deepcopy(script["events"])
        self.actions = copy.deepcopy(script["actions"])
        self.index = 0
        self.tick = 0
        self.owner = None

    def claim(self, owner):
        # 中文用途：同一模拟资源仅准一名会话持有，异常不自动解除占用。
        require(self.owner is None and self.resource_id not in self._claimed, "resource already owned")
        self._claimed.add(self.resource_id)
        self.owner = owner

    def relinquish(self, owner):
        require(self.owner == owner, "owner mismatch")
        self._claimed.remove(self.resource_id)
        self.owner = None

    @staticmethod
    def _expand(value, identity):
        if value == "$current":
            return copy.deepcopy(identity)
        if isinstance(value, dict):
            return {key: TestTransport._expand(item, identity) for key, item in value.items()}
        if isinstance(value, list):
            return [TestTransport._expand(item, identity) for item in value]
        return value

    def call(self, operation, identity, **arguments):
        require(self.owner == identity["session"], "unclaimed transport")
        require(self.index < len(self.events), "transcript exhausted at " + operation)
        event = self.events[self.index]
        self.index += 1
        keys(event, ("op", "tick"), ("reply", "error", "expect"))
        require(event["op"] == operation, "unexpected operation: " + operation)
        tick = integer(event["tick"], "event tick", self.tick + 1)
        self.tick = tick
        if "expect" in event:
            expected = self._expand(event["expect"], identity)
            require(isinstance(expected, dict) and all(arguments.get(k) == v for k, v in expected.items()),
                    "operation argument mismatch")
        require(("reply" in event) != ("error" in event), "reply xor error required")
        if "error" in event:
            text(event["error"], "error")
            if event["error"] == "KeyboardInterrupt":
                raise KeyboardInterrupt("scripted interruption")
            raise ProtocolError("TEST_TRANSPORT: " + event["error"])
        return self._expand(event["reply"], identity)

    def exhausted(self):
        return self.index == len(self.events)


class ActualTransport:
    """Intentional refusal; cannot be turned into a board adapter by an argument."""
    def __init__(self, *_args, **_kwargs):
        from .contracts import hardware_admission
        hardware_admission()
