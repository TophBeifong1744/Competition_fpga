"""Bind the fixed four-mic PS contract to the actual compiled object and ELF.

No C evaluator: GCC evaluates the constants in the SAME translation unit as
main. Only the known capture body (seven single-line macro expressions excepted)
is supported. Unknown source forms fail closed. This module never operates a board.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile

BODY_SHA256 = "1b863f27c979e81ac5ee692bb499916af905664818eb4bba03857dc8ddbbe35f"
MACROS = ("BASE", "LIMIT", "GROUPS", "WORDS_PER_GROUP", "BYTES", "PACKET", "GUARD")
FIELDS = MACROS + ("DDR_BASE", "DDR_HIGH", "WORD_BYTES", "POINTER_BYTES")
FIXED = dict(BASE=0x01000000, LIMIT=0x01100000, GROUPS=32000,
             WORDS_PER_GROUP=8, BYTES=1024000, PACKET=8000, GUARD=64)
SYMBOL = "ss_build_ps_contract"
MAGIC = 0x53535043


class ContractError(RuntimeError):
    pass


def need(condition, message):
    if not condition:
        raise ContractError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_shape(source):
    """Recognize exactly the known body; macro values are evaluated ONLY by GCC."""
    text = source.decode("utf-8").replace("\r\n", "\n")
    expressions = {}
    token = re.compile(r"\s+|0[xX][0-9a-fA-F]+[uUlL]*|[0-9]+[uUlL]*|"
                       r"UINTPTR\b|" + "|".join(n + r"\b" for n in MACROS) + r"|[()+*/%-]")
    for name in MACROS:
        pattern = r"^#define " + name + r" ([^\n]*)$"
        found = re.findall(pattern, text, flags=re.M)
        need(len(found) == 1, "Unsupported PS macro definition: " + name)
        value = found[0]
        need(not any(x in value for x in ("/*", "*/", "//")),
             "Comments in contract expressions are unsupported: " + name)
        position = 0
        while position < len(value):
            match = token.match(value, position)
            need(match is not None, "Unsupported PS macro expression: " + name)
            position = match.end()
        need(value.strip(), "Empty PS macro: " + name)
        expressions[name] = value
        text = re.sub(pattern, "#define " + name + " <COMPILED_VALUE>", text, flags=re.M)
    need(hashlib.sha256(text.encode()).hexdigest() == BODY_SHA256,
         "Unsupported PS source body; review required, no buffer contract assumed")
    return {"body_sha256": BODY_SHA256, "macro_expressions": expressions}


class Elf32:
    """Small bounds-checked reader for ordinary little-endian ARM ELF32 only."""
    def __init__(self, path, expected_type):
        self.data = Path(path).read_bytes()
        need(self.data[:7] == b"\x7fELF\x01\x01\x01", "Expected little-endian ELF32")
        h = self.unpack("<HHIIIIIHHHHHH", 16)
        need(h[0] == expected_type and h[1] == 40 and h[2] == 1, "Wrong ELF type/ARM machine")
        need(h[7] == 52 and h[10] == 40 and h[11] > 0, "Unsupported ELF section layout")
        self.entry = h[3]
        self.sections = [self.unpack("<IIIIIIIIII", h[5] + i * 40) for i in range(h[11])]
        need(0 < h[12] < len(self.sections), "Missing ELF section strings")
        names = self.section_data(h[12])
        self.section_names = [self.string(names, s[0]) for s in self.sections]
        self.symbols = {}
        for section in self.sections:
            if section[1] != 2:
                continue
            need(section[9] == 16 and section[5] % 16 == 0, "Unsupported symbol table")
            strings = self.section_data(section[6])
            for offset in range(section[4], section[4] + section[5], 16):
                symbol = self.unpack("<IIIBBH", offset)
                if symbol[5] and symbol[3] >> 4 in (1, 2):
                    name = self.string(strings, symbol[0])
                    need(name not in self.symbols, "Ambiguous ELF symbol: " + name)
                    self.symbols[name] = symbol
        self.loads = []
        need(h[9] == 0 or h[8] == 32, "Unsupported program headers")
        for i in range(h[9]):
            p = self.unpack("<IIIIIIII", h[4] + i * 32)
            if p[0] == 1 and p[5]:
                need(p[4] <= p[5] and p[2] == p[3], "Unsupported nonidentity LOAD mapping")
                self.slice(p[1], p[4])
                self.loads.append({"name": "PT_LOAD", "start": p[2], "end": p[2] + p[5]})
        self.allocated = [{"name": name, "start": s[3], "end": s[3] + s[5]}
                          for name, s in zip(self.section_names, self.sections)
                          if s[2] & 2 and s[5]]
        if expected_type == 2:
            need(self.loads and self.allocated, "Executable has no LOAD/allocated ranges")
            need(".heap" in self.section_names and ".stack" in self.section_names,
                 "Unsupported linker layout: explicit heap and stack required")

    def slice(self, offset, size):
        need(offset >= 0 and size >= 0 and offset + size <= len(self.data), "Truncated ELF")
        return self.data[offset:offset + size]

    def unpack(self, fmt, offset):
        return struct.unpack(fmt, self.slice(offset, struct.calcsize(fmt)))

    @staticmethod
    def string(data, offset):
        need(0 <= offset < len(data), "Bad ELF string offset")
        end = data.find(b"\0", offset)
        need(end >= 0, "Unterminated ELF string")
        return data[offset:end].decode("utf-8")

    def section_data(self, index):
        need(0 <= index < len(self.sections), "Bad ELF section index")
        s = self.sections[index]
        need(s[1] != 8, "Cannot read NOBITS as file data")
        return self.slice(s[4], s[5])

    def symbol_value(self, name):
        need(name in self.symbols, "Missing ELF symbol: " + name)
        return self.symbols[name][1]

    def contract(self):
        need(SYMBOL in self.symbols, "Missing bound PS contract in ELF")
        sym = self.symbols[SYMBOL]
        need(sym[2] == 4 * (2 + len(FIELDS)), "Wrong PS contract size")
        need(0 < sym[5] < len(self.sections), "Contract has no concrete section")
        section = self.sections[sym[5]]
        need(section[2] & 2 and section[1] != 8, "Contract is not allocated file data")
        offset = sym[1] - section[3]
        need(0 <= offset and offset + sym[2] <= section[5], "Contract lies outside section")
        raw = self.section_data(sym[5])[offset:offset + sym[2]]
        words = struct.unpack("<" + "I" * (2 + len(FIELDS)), raw)
        need(words[:2] == (MAGIC, 1), "Bad PS contract magic/schema")
        return dict(zip(FIELDS, words[2:]))


def hardware_contract(bd_path, xsa_path):
    bd = json.loads(Path(bd_path).read_text(encoding="utf-8"))["design"]
    p = bd["components"]["four_mic_top_0"]["parameters"]
    with zipfile.ZipFile(xsa_path) as archive:
        root = ET.fromstring(archive.read("system.hwh"))
    ps = root.findall("./MODULES/MODULE[@INSTANCE='processing_system7_0']")
    dma = root.findall("./MODULES/MODULE[@INSTANCE='axi_dma_0']")
    need(len(ps) == 1 and len(dma) == 1, "Unknown HWH PS/DMA instance")
    def number(module, name):
        nodes = module.findall("./PARAMETERS/PARAMETER[@NAME='" + name + "']")
        need(len(nodes) == 1, "Missing/ambiguous HWH parameter: " + name)
        return int(nodes[0].get("VALUE"), 0)
    ranges = [n for n in root.iter("MEMRANGE") if n.get("INSTANCE") == "processing_system7_0"
              and n.get("MASTERBUSINTERFACE") == "M_AXI_S2MM"
              and n.get("SLAVEBUSINTERFACE") == "S_AXI_HP0"]
    need(len(ranges) == 1, "Missing/ambiguous S2MM to DDR address range")
    return {"groups": int(p["TOTAL_SAMPLES"]["value"]),
            "groups_per_packet": int(p["SAMPLES_PER_PACKET"]["value"]),
            "ddr_base": number(ps[0], "PCW_DDR_RAM_BASEADDR"),
            "ddr_high": number(ps[0], "PCW_DDR_RAM_HIGHADDR"),
            "dma_length_bits": number(dma[0], "C_SG_LENGTH_WIDTH"),
            "dma_base": int(ranges[0].get("BASEVALUE"), 0),
            "dma_high": int(ranges[0].get("HIGHVALUE"), 0)}


def validate_values(c, hw, ranges=(), program_end=None):
    need(set(c) == set(FIELDS) and all(type(v) is int and 0 <= v < 2**32 for v in c.values()),
         "Malformed compiled contract")
    base, limit = c["BASE"], c["LIMIT"]
    need(c["WORD_BYTES"] == 4 and c["POINTER_BYTES"] == 4, "Unsupported ABI/word size")
    need(c["DDR_BASE"] == hw["ddr_base"] and c["DDR_HIGH"] == hw["ddr_high"],
         "Compiled BSP DDR bounds differ from XSA")
    need(c["DDR_BASE"] <= base < limit <= c["DDR_HIGH"] + 1, "RX reservation outside DDR")
    need(hw["dma_base"] <= base and limit <= hw["dma_high"] + 1, "RX outside DMA DDR range")
    need(c["GROUPS"] > 0 and c["WORDS_PER_GROUP"] == 8, "Unsupported H1 group layout")
    need(c["BYTES"] == c["GROUPS"] * c["WORDS_PER_GROUP"] * c["WORD_BYTES"],
         "BYTES differs from compiled group geometry")
    need(c["GUARD"] >= 64 and c["GUARD"] % 64 == 0, "Invalid guard size/alignment")
    data_end = base + c["BYTES"]
    guard_end = data_end + c["GUARD"]
    need(guard_end <= limit and guard_end <= 2**32, "Data/guard exceeds RX reservation")
    need(base % 64 == 0 and limit % 64 == 0, "RX alignment")
    need(c["PACKET"] > 0 and c["PACKET"] % 32 == 0 and c["BYTES"] % c["PACKET"] == 0,
         "Packet/cache alignment or partial packet")
    need(1 <= hw["dma_length_bits"] <= 32 and c["PACKET"] < 2**hw["dma_length_bits"],
         "Packet exceeds DMA length register")
    need(c["GROUPS"] == hw["groups"] and
         c["PACKET"] == hw["groups_per_packet"] * c["WORDS_PER_GROUP"] * c["WORD_BYTES"],
         "PS packet/groups differ from BD")
    need(all(c[k] == v for k, v in FIXED.items()), "Unsupported changed fixed PS contract")
    for r in ranges:
        need(c["DDR_BASE"] <= r["start"] < r["end"] <= c["DDR_HIGH"] + 1,
             "Program allocation outside DDR: " + r["name"])
        need(r["end"] <= base, "Program allocation overlaps/escapes area before RX: " + r["name"])
    if program_end is not None:
        need(c["DDR_BASE"] < program_end <= base, "Program end overlaps RX")
        need(ranges and max(r["end"] for r in ranges) <= program_end,
             "Program end fails to cover linked allocations")
    return {"rx_start": base, "rx_limit_exclusive": limit, "rx_data_end_exclusive": data_end,
            "rx_guard_end_exclusive": guard_end, "bytes": c["BYTES"],
            "packet_bytes": c["PACKET"], "packets": c["BYTES"] // c["PACKET"],
            "program_end": program_end}


def compile_bound_ps(plan, out, run_command, write_json):
    """Preprocess once -> same TU object -> link that object -> inspect actual ELF."""
    work = out / "ps_check"
    work.mkdir()
    src = out / "inputs/ps/main_four_capture.c"
    shape = source_shape(src.read_bytes())
    bds = [out / "inputs" / rel for rel in plan["input_files"].values()
           if rel.endswith("/system.bd")]
    need(len(bds) == 1, "Unknown staged BD")
    bd_snapshot = work / "contract_input.bd"
    shutil.copyfile(bds[0], bd_snapshot)
    hw = hardware_contract(bd_snapshot, out / "inputs/bsp-reference.xsa")
    wrapper = (
        '#include "../inputs/ps/main_four_capture.c"\n'
        '_Static_assert(sizeof(u32) == 4 && sizeof(UINTPTR) == 4, "ARM32 ABI");\n'
        '__attribute__((used, section(".rodata.ss_build_ps_contract")))\n'
        'const unsigned int ' + SYMBOL + '[] = {\n'
        '0x53535043U, 1U, ' + ", ".join(MACROS) + ',\n'
        'XPAR_PS7_DDR_0_BASEADDRESS, XPAR_PS7_DDR_0_HIGHADDRESS, sizeof(u32), sizeof(UINTPTR)\n};\n')
    with (work / "ps_build_unit.c").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(wrapper)
    common = [plan["gcc"], "-DSDT", "-mcpu=cortex-a9", "-mfpu=vfpv3",
              "-mfloat-abi=hard", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0", "-g3",
              "-specs=../inputs/bsp/Xilinx.spec", "-I../inputs/bsp/include"]
    run_command(common + ["-E", "ps_build_unit.c", "-o", "ps_build_unit.i"],
                out, "ps-preprocess", work)
    run_command(common + ["-x", "cpp-output", "-c", "ps_build_unit.i", "-o", "ps_build_unit.o"],
                out, "ps-compile", work)
    obj = Elf32(work / "ps_build_unit.o", 1)
    compiled = obj.contract()
    write_json(work / "compiled-contract.json",
               {"source_shape": shape, "compiled_values": compiled, "hardware": hw})
    validate_values(compiled, hw)
    argv = common + ["ps_build_unit.o", "-o", "four_mic_capture.elf",
                     "-L../inputs/bsp/lib", "-Wl,-T,../inputs/ps/lscript.ld",
                     "-Wl,-Map,four_mic_capture.map,--cref", "-Wl,--start-group",
                     "-lxilstandalone", "-lxiltimer", "-lxil", "-lgcc", "-lc", "-Wl,--end-group"]
    run_command(argv, out, "ps-build", work)
    exe = Elf32(work / "four_mic_capture.elf", 2)
    need(exe.contract() == compiled, "Linked ELF contract differs from compiled object")
    ranges = exe.allocated + exe.loads
    values = validate_values(compiled, hw, ranges, exe.symbol_value("end"))
    need(any(r["start"] <= exe.entry < r["end"] for r in exe.loads), "ELF entry outside LOAD")
    run_command([plan["size"], "four_mic_capture.elf"], out, "ps-size", work)
    run_command([plan["nm"], "-n", "four_mic_capture.elf"], out, "ps-symbols", work)
    bound_paths = [src, out / "inputs/ps/lscript.ld", out / "inputs/bsp-reference.xsa", bd_snapshot,
                   work / "ps_build_unit.c", work / "ps_build_unit.i", work / "ps_build_unit.o",
                   work / "four_mic_capture.elf", work / "four_mic_capture.map"]
    report = {"status": "PS_CONTRACT_PASS_NOT_BOARD_TEST", "values": values,
              "compiled_values": compiled, "hardware": hw, "allocated_ranges": ranges,
              "bindings_sha256": {p.relative_to(out).as_posix(): sha(p) for p in bound_paths},
              "source_shape": shape, "compiler": plan["gcc"],
              "compiler_sha256": sha(plan["gcc"]), "common_argv": common,
              "compile_commands": ["logs/ps-preprocess.command.json",
                                   "logs/ps-compile.command.json", "logs/ps-build.command.json"],
              "limits": ["Known source body and fixed contract only; not a general C parser",
                         "Metadata constant only; capture source unchanged; no board execution"]}
    write_json(work / "contract-result.json", report)
    return report
