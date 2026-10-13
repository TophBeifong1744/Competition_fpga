"""只读解析已有 XSA/HWH；输出历史配置材料，不调用 EDA 或硬件。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def xml_node(node):
    result = {"tag": node.tag, "attributes": dict(node.attrib)}
    if len(node):
        result["children"] = [xml_node(child) for child in node]
    if node.text and node.text.strip():
        result["text"] = node.text.strip()
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xsa", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--bsp", type=Path, help="可选，旧 xparameters.h；仅比对元数据")
    args = parser.parse_args()
    if args.out.resolve() == args.xsa.resolve().parent or args.xsa.resolve().is_relative_to(args.out.resolve()):
        parser.error("输出目录须与原件目录分开")
    original = args.xsa.read_bytes()
    bsp_bytes = args.bsp.read_bytes() if args.bsp else None
    args.out.mkdir(parents=True, exist_ok=True)
    inputs = [{"path": str(args.xsa.resolve()), "bytes": len(original), "sha256": digest(original)}]
    if args.bsp:
        inputs.append({"path": str(args.bsp.resolve()), "bytes": len(bsp_bytes), "sha256": digest(bsp_bytes)})
    with zipfile.ZipFile(args.xsa) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError("XSA CRC failure: " + bad)
        members = [{"name": entry.filename, "bytes": entry.file_size,
                    "sha256": digest(archive.read(entry.filename)), "crc32": f"{entry.CRC:08x}"}
                   for entry in archive.infolist()]
        # 顶层 HWH 与 SmartConnect scoped HWH 分开；不能要求每个 HWH 都含 PS7。
        root = ET.fromstring(archive.read("system.hwh"))
        modules = root.findall("./MODULES/MODULE")
        by_name = {module.get("INSTANCE"): module for module in modules}
        ps = by_name["processing_system7_0"]
        parameters = {p.get("NAME"): p.get("VALUE") for p in ps.findall("./PARAMETERS/PARAMETER")}
        mio_peripherals = parameters["PCW_MIO_TREE_PERIPHERALS"].split("#")
        mio_signals = parameters["PCW_MIO_TREE_SIGNALS"].split("#")
        if len(mio_peripherals) != 54 or len(mio_signals) != 54:
            raise ValueError("Unexpected MIO table length")
        config = {"scope": "HISTORICAL_C1_CONFIG_ONLY_NOT_CURRENT_OVERLAY_OR_PHYSICAL_READBACK",
                  "source_xsa_sha256": digest(original), "top_hwh": "system.hwh",
                  "scoped_hwh": "system_axi_smc_1.hwh", "hwh_attributes": root.attrib,
                  "system_info": root.find("SYSTEMINFO").attrib,
                  "xsa_metadata": json.loads(archive.read("xsa.json")),
                  "sysdef": xml_node(ET.fromstring(archive.read("sysdef.xml"))),
                  "ps7_instance": ps.attrib, "ps7_parameter_count": len(parameters),
                  "ps7_parameters": parameters,
                  "mio": [{"index": i, "peripheral": peripheral, "signal": signal}
                          for i, (peripheral, signal) in enumerate(zip(mio_peripherals, mio_signals))],
                  "modules": []}
        for module in modules:
            entry = {"attributes": module.attrib}
            for name in ("PARAMETERS", "PORTS", "BUSINTERFACES", "MEMORYMAP"):
                child = module.find(name)
                if child is not None:
                    entry[name.lower()] = xml_node(child)
            config["modules"].append(entry)
        config["external_ports"] = xml_node(root.find("EXTERNALPORTS"))
        config["external_interfaces"] = xml_node(root.find("EXTERNALINTERFACES"))
        checks = []
        if bsp_bytes is not None:
            definitions = dict(re.findall(r"^#define\s+(\w+)\s+(0x[0-9a-fA-F]+|\d+)\s*$",
                                          bsp_bytes.decode(), re.MULTILINE))
            bindings = {
                "axi_dma_0": {"BASEADDR": "C_BASEADDR", "HIGHADDR": "C_HIGHADDR",
                              "INCLUDE_MM2S": "C_INCLUDE_MM2S", "INCLUDE_S2MM": "C_INCLUDE_S2MM",
                              "INCLUDE_S2MM_DRE": "C_INCLUDE_S2MM_DRE", "S2MM_DATA_WIDTH": "C_M_AXI_S2MM_DATA_WIDTH",
                              "SG_LENGTH_WIDTH": "C_SG_LENGTH_WIDTH"},
                "axi_gpio_0": {"BASEADDR": "C_BASEADDR", "HIGHADDR": "C_HIGHADDR",
                               "IS_DUAL": "C_IS_DUAL", "INTERRUPT_PRESENT": "C_INTERRUPT_PRESENT"}}
            for instance, mapping in bindings.items():
                params = {p.get("NAME"): p.get("VALUE") for p in by_name[instance].findall("./PARAMETERS/PARAMETER")}
                for suffix, parameter in mapping.items():
                    macro = "XPAR_" + instance.upper() + "_" + suffix
                    actual = definitions.get(macro)
                    matches = actual is not None and int(actual, 0) == int(params[parameter], 0)
                    checks.append({"macro": macro, "bsp": actual, "hwh_parameter": parameter,
                                   "hwh": params[parameter], "matches": matches})
            if not all(check["matches"] for check in checks):
                raise ValueError("BSP/HWH metadata mismatch")
        selected = ("system.hwh", "system_axi_smc_1.hwh", "ps7_init.tcl", "ps7_init.c", "ps7_init.h",
                    "sysdef.xml", "system.bda", "xsa.json", "xsa.xml")
        reference = args.out / "historical-ps-reference.zip"
        with zipfile.ZipFile(reference, "w", zipfile.ZIP_DEFLATED) as package:
            for name in selected:
                info = zipfile.ZipInfo(name, (2026, 9, 15, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                package.writestr(info, archive.read(name))
        with zipfile.ZipFile(reference) as package:
            if package.testzip() or any(package.read(name) != archive.read(name) for name in selected):
                raise ValueError("Extracted original bytes mismatch")
    if args.xsa.read_bytes() != original or (args.bsp and args.bsp.read_bytes() != bsp_bytes):
        raise ValueError("Source changed during inspection")
    manifest = {"scope": "METADATA_IDENTITY_CHECKS_ONLY_NO_OLD_TEST_RERUN", "inputs": inputs,
                "xsa_members": members, "crc_checked": True, "sources_unchanged": True,
                "bsp_hwh_checks": checks, "reference_package": {"file": reference.name,
                "bytes": reference.stat().st_size, "sha256": digest(reference.read_bytes()),
                "members": list(selected), "byte_exact": True, "deployable_overlay": False},
                "not_run": ["EDA", "ps7_init execution", "old tests", "board access", "PYNQ runtime"]}
    write_json(args.out / "ps-config.json", config)
    write_json(args.out / "source-manifest.json", manifest)
    print(json.dumps({"ps7_parameters": len(parameters), "xsa_members": len(members),
                      "bsp_metadata_checks": len(checks), "output": str(args.out.resolve())}))


if __name__ == "__main__":
    main()
