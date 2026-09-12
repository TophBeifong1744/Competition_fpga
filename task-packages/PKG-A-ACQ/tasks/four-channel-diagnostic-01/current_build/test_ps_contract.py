"""New author tests, independent of B's unavailable 21 checks. No real tools."""
import copy
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import ps_contract as pc
import build_current as bc
import test_build_current as original_tests


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.c = dict(pc.FIXED, DDR_BASE=0x100000, DDR_HIGH=0x3fffffff,
                      WORD_BYTES=4, POINTER_BYTES=4)
        self.hw = dict(groups=32000, groups_per_packet=250, ddr_base=0x100000,
                       ddr_high=0x3fffffff, dma_base=0, dma_high=0x3fffffff,
                       dma_length_bits=14)
        self.ranges = [dict(name=".text+.heap+.stack", start=0x100000, end=0x112630)]

    def check(self, c=None, hw=None, ranges=None, end=0x112630):
        return pc.validate_values(c or self.c, hw or self.hw,
                                  self.ranges if ranges is None else ranges, end)

    def reject(self, **changes):
        c = dict(self.c, **changes)
        with self.assertRaises(pc.ContractError):
            self.check(c=c)

    def test_current_values_report_actual_bounds(self):
        r = self.check()
        self.assertEqual(r["rx_guard_end_exclusive"], self.c["BASE"] + self.c["BYTES"] + self.c["GUARD"])
        self.assertEqual(r["packets"], 128)

    def test_base_changed_version_not_part_of_decision(self):
        self.reject(BASE=0x00100000)

    def test_limit_changed_but_math_still_safe(self):
        self.reject(LIMIT=0x01200000)

    def test_limit_cuts_through_data(self):
        self.reject(LIMIT=0x01080000)

    def test_guard_overflow(self):
        self.reject(GUARD=32768)

    def test_guard_missing(self):
        self.reject(GUARD=0)

    def test_bytes_overflow(self):
        self.reject(BYTES=1048576)

    def test_bytes_disagree_with_groups(self):
        self.reject(BYTES=1023968)

    def test_words_per_group_mismatch(self):
        self.reject(WORDS_PER_GROUP=4, BYTES=512000)

    def test_groups_mismatch_with_bd(self):
        self.reject(GROUPS=31750, BYTES=1016000)

    def test_packet_mismatch_with_bd(self):
        self.reject(PACKET=4000)

    def test_packet_zero(self):
        self.reject(PACKET=0)

    def test_packet_partial(self):
        self.reject(PACKET=8032)

    def test_dma_length_too_small(self):
        with self.assertRaises(pc.ContractError):
            self.check(hw=dict(self.hw, dma_length_bits=12))

    def test_bd_total_changed(self):
        with self.assertRaises(pc.ContractError):
            self.check(hw=dict(self.hw, groups=16000))

    def test_bd_packet_changed(self):
        with self.assertRaises(pc.ContractError):
            self.check(hw=dict(self.hw, groups_per_packet=125))

    def test_bsp_ddr_changed(self):
        self.reject(DDR_HIGH=0x1fffffff)

    def test_dma_ddr_does_not_cover_rx(self):
        with self.assertRaises(pc.ContractError):
            self.check(hw=dict(self.hw, dma_high=0x001fffff))

    def test_pointer_abi_mismatch(self):
        self.reject(POINTER_BYTES=8)

    def test_legal_program_end_equals_rx_start(self):
        r = self.check(ranges=[dict(name=".stack", start=0x100000, end=self.c["BASE"])],
                       end=self.c["BASE"])
        self.assertEqual(r["program_end"], self.c["BASE"])

    def test_program_end_one_word_into_rx(self):
        with self.assertRaises(pc.ContractError):
            self.check(end=self.c["BASE"] + 4)

    def test_low_end_symbol_cannot_hide_load_overlap(self):
        with self.assertRaises(pc.ContractError):
            self.check(ranges=[dict(name="PT_LOAD", start=0x100000, end=self.c["BASE"] + 4)])

    def test_low_end_symbol_cannot_hide_heap(self):
        with self.assertRaises(pc.ContractError):
            self.check(end=0x110000)

    def test_unknown_source_with_same_version_rejected(self):
        with self.assertRaises(pc.ContractError):
            pc.source_shape(b'four-channel-c-adapter-v1')

    def test_forged_text_is_not_an_elf(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "fake.elf"
            p.write_bytes(b"00112630 B end\nPS_CONTRACT_PASS_NOT_BOARD_TEST")
            with self.assertRaises(pc.ContractError):
                pc.Elf32(p, 2)

    def test_full_build_cannot_bypass_ps_contract_failure(self):
        f = original_tests.SafetyTests()
        f.setUp()
        try:
            plan = bc.preflight(f.args)
            with patch.object(bc, "compile_bound_ps", side_effect=pc.ContractError("invalid RX")), \
                 patch.object(bc, "run_command", return_value="mock version") as tool:
                result = bc.build(plan)
            self.assertEqual(result["status"], "BUILD_FAILED")
            self.assertIn("invalid RX", result["error"])
            self.assertEqual([call.args[2] for call in tool.call_args_list], ["gcc-version"])
        finally:
            f.doCleanups()


def object_fixture(values):
    """ELF32 relocatable fixture with the bound global const symbol."""
    names = b"\0.rodata\0.strtab\0.symtab\0.shstrtab\0"
    strings = b"\0" + pc.SYMBOL.encode() + b"\0"
    data = struct.pack("<" + "I" * (2 + len(pc.FIELDS)), pc.MAGIC, 1,
                       *(values[k] for k in pc.FIELDS))
    sym = bytes(16) + struct.pack("<IIIBBH", 1, 0, len(data), 17, 0, 1)
    parts = [data, strings, sym, names]
    offsets=[]; raw=bytearray(bytes(52))
    for part in parts:
        offsets.append(len(raw));raw.extend(part)
    shoff=len(raw)
    sections=[(0,)*10,
              (names.index(b".rodata"),1,2,0,offsets[0],len(data),0,0,4,0),
              (names.index(b".strtab"),3,0,0,offsets[1],len(strings),0,0,1,0),
              (names.index(b".symtab"),2,0,0,offsets[2],len(sym),2,1,4,16),
              (names.index(b".shstrtab"),3,0,0,offsets[3],len(names),0,0,1,0)]
    for s in sections:raw.extend(struct.pack("<IIIIIIIIII",*s))
    raw[:52]=struct.pack("<16sHHIIIIIHHHHHH",b"\x7fELF\x01\x01\x01"+bytes(9),
                         1,40,1,0,0,shoff,0,52,0,0,40,5,4)
    return raw


class ElfBindingTests(unittest.TestCase):
    def test_object_contract_decoded_from_bytes(self):
        c=dict(pc.FIXED,DDR_BASE=0x100000,DDR_HIGH=0x3fffffff,WORD_BYTES=4,POINTER_BYTES=4)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"contract.o";p.write_bytes(object_fixture(c))
            self.assertEqual(pc.Elf32(p,1).contract(),c)

    def test_changed_binary_base_is_not_hidden_by_log(self):
        c=dict(pc.FIXED,BASE=0x100000,DDR_BASE=0x100000,DDR_HIGH=0x3fffffff,WORD_BYTES=4,POINTER_BYTES=4)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"contract.o";p.write_bytes(object_fixture(c))
            self.assertEqual(pc.Elf32(p,1).contract()["BASE"],0x100000)

    def test_truncated_elf_rejected(self):
        c=dict(pc.FIXED,DDR_BASE=0x100000,DDR_HIGH=0x3fffffff,WORD_BYTES=4,POINTER_BYTES=4)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"contract.o";p.write_bytes(object_fixture(c)[:-1])
            with self.assertRaises(pc.ContractError):pc.Elf32(p,1)


if __name__ == "__main__":
    unittest.main()
