"""Explicit internal injection; not a claim about a native standalone CLI fault."""
import sys
from soundsight_h3_evidence import __main__ as dut
from soundsight_h3_evidence.contracts import Issue
def fail(self):raise Issue(4,'TEST_INJECTED_POST_FAILURE')
dut.SourceStore.verify_post=fail
sys.exit(dut.main(sys.argv[1:]))
