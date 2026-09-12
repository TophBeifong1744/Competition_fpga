"""Safety tests use tiny local fixtures; never launch Vivado/GCC or touch one."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile
import build_current as bc


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ss-build-safety-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "current project/one.xpr"
        self.bsp = self.root / "bsp"
        self.ps = self.root / "ps"
        self.tools = self.root / "tools"
        for d in (self.project.parent, self.bsp, self.ps, self.tools):
            d.mkdir()
        for tool in ("vivado.bat", "arm-none-eabi-gcc.exe", "arm-none-eabi-size.exe", "arm-none-eabi-nm.exe"):
            (self.tools / tool).write_text("fixture only: must not execute\n")
        src = self.project.parent / "one.srcs"
        bd = src / "sources_1/bd/system/system.bd"
        bd.parent.mkdir(parents=True)
        self.design = {"design": {
            "design_info": {"tool_version": "2025.2", "device": bc.PART},
            "components": {"four_mic_top_0": {"parameters": {
                k: {"value": v} for k, v in
                {"TOTAL_SAMPLES": "32000", "SAMPLES_PER_PACKET": "250",
                 "WARMUP_SAMPLES": "4096", "FIFO_LOG2": "10"}.items()}}},
            "ports": {k: {} for k in ("pdm_data", "pdm_clk1", "pdm_clk2", "pdm_clk3", "pdm_clk4")}}}
        self.bd = bd
        self.save_bd()
        self.project.write_text(
            '<?xml version="1.0"?><!-- Vivado v2025.2 -->'
            '<Project><Configuration><Option Name="Part" Val="' + bc.PART +
            '"/></Configuration><FileSets><FileSet Name="sources_1">'
            '<File Path="$PSRCDIR/sources_1/bd/system/system.bd"/>'
            '</FileSet></FileSets><Runs><Run Id="synth_1" '
            'AutoIncrementalCheckpoint="true"/></Runs></Project>')
        for rel in ("Xilinx.spec", "include/xparameters.h", "include/xaxidma.h",
                    "include/xgpio.h", "lib/libxil.a", "lib/libxilstandalone.a",
                    "lib/libxiltimer.a", "hw_artifacts/ps7_init.c"):
            p = self.bsp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"fixture\n")
        (self.bsp / "cortexa9_toolchain.cmake").write_text("-mcpu=cortex-a9")
        (self.ps / "main_four_capture.c").write_text("four-channel-c-adapter-v1")
        (self.ps / "lscript.ld").write_text("fixture")
        self.xsa = self.root / "reference.xsa"
        self.make_xsa()
        self.args = argparse.Namespace(
            project=self.project, vivado=self.tools / "vivado.bat",
            gcc=self.tools / "arm-none-eabi-gcc.exe", bsp=self.bsp,
            bsp_xsa=self.xsa, ps_source=self.ps, output=self.root / "fresh output",
            jobs=4, mode="check")

    def save_bd(self):
        self.bd.write_text(json.dumps(self.design))

    def make_xsa(self, init=b"fixture\n"):
        with zipfile.ZipFile(self.xsa, "w") as z:
            z.writestr("system.hwh", '<EDKSYSTEM TIMESTAMP="a"><SYSTEMINFO DEVICE="7z020" PACKAGE="clg400" SPEEDGRADE="-2"/></EDKSYSTEM>')
            z.writestr("ps7_init.c", init)

    def check(self):
        # Enforce no executable launch by check, not just conventional behavior.
        with patch.object(bc.subprocess, "run", side_effect=AssertionError("check launched tool")):
            return bc.preflight(self.args)

    def refused(self, contains):
        with self.assertRaises((bc.BuildError, FileNotFoundError)) as result:
            self.check()
        self.assertIn(contains, str(result.exception))

    def test_check_read_only_no_tool_or_output(self):
        before = {str(p): bc.sha(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(self.check()["status"], "CHECK_PASS_NOT_BUILD")
        after = {str(p): bc.sha(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(self.args.output.exists())

    def test_existing_nonempty_directory_preserved(self):
        self.args.output.mkdir()
        marker = self.args.output / "keep.txt"
        marker.write_text("do not overwrite")
        self.refused("Output exists")
        self.assertEqual(marker.read_text(), "do not overwrite")

    def test_existing_empty_directory_refused(self):
        self.args.output.mkdir()
        self.refused("Output exists")

    def test_existing_file_refused(self):
        self.args.output.write_text("existing")
        self.refused("Output exists")
        self.assertEqual(self.args.output.read_text(), "existing")

    def test_project_child_output_refused(self):
        self.args.output = self.project.parent / "new"
        self.refused("overlaps")

    def test_bsp_child_output_refused(self):
        self.args.output = self.bsp / "new"
        self.refused("overlaps")

    def test_ps_child_output_refused(self):
        self.args.output = self.ps / "new"
        self.refused("overlaps")

    def test_missing_output_parent_no_mkdir(self):
        self.args.output = self.root / "missing/child"
        self.refused("parent must")
        self.assertFalse(self.args.output.parent.exists())

    def test_missing_tool(self):
        self.args.gcc = self.tools / "absent.exe"
        self.refused("absent")

    def test_missing_library(self):
        (self.bsp / "lib/libxil.a").unlink()
        self.refused("libxil.a")

    def test_missing_source(self):
        (self.ps / "main_four_capture.c").unlink()
        self.refused("main_four_capture.c")

    def test_wrong_bsp_pair(self):
        self.make_xsa(b"different")
        self.refused("does not match")

    def test_wrong_part(self):
        self.project.write_text(self.project.read_text().replace(bc.PART, "xc7z010clg400-1"))
        self.refused("part")

    def test_wrong_tool_generation(self):
        self.project.write_text(self.project.read_text().replace("2025.2", "2018.3"))
        self.refused("2025.2")

    def test_old_mono_is_not_migrated(self):
        d = self.design["design"]["components"]
        d["single_mic_top_0"] = d.pop("four_mic_top_0")
        self.save_bd()
        before = bc.sha(self.bd)
        self.refused("migration")
        self.assertEqual(bc.sha(self.bd), before)

    def test_changed_capture_contract(self):
        self.design["design"]["components"]["four_mic_top_0"]["parameters"]["TOTAL_SAMPLES"]["value"] = "48000"
        self.save_bd()
        self.refused("parameters")

    def test_missing_four_clock(self):
        del self.design["design"]["ports"]["pdm_clk4"]
        self.save_bd()
        self.refused("ports")

    def test_external_registered_source(self):
        external = self.root / "external.v"
        external.write_text("fixture")
        tree = ET.parse(self.project)
        ET.SubElement(tree.find(".//FileSet"), "File", Path=external.as_posix())
        tree.write(self.project)
        # Keep the tool-version declaration needed by the current-XPR check.
        self.project.write_text('<!--2025.2-->' + self.project.read_text())
        self.refused("External project")

    def test_old_importpath_is_provenance_not_dependency(self):
        text = self.project.read_text().replace("</Configuration>",
            '<Option Name="ImportPath" Val="Q:/deleted/old-source.v"/></Configuration>')
        self.project.write_text(text)
        self.assertEqual(self.check()["status"], "CHECK_PASS_NOT_BUILD")

    def test_pre_hook_refused(self):
        self.project.write_text(self.project.read_text().replace("</Configuration>",
            '<Option Name="STEPS.SYNTH_DESIGN.TCL.PRE" Val="change.tcl"/></Configuration>'))
        self.refused("hook")

    def test_absolute_run_directory_refused_before_tool(self):
        self.project.write_text(self.project.read_text().replace(
            'Id="synth_1"', 'Id="synth_1" Dir="F:/actual-one/one.runs/synth_1"'))
        self.refused("output setting")

    def test_metacharacters_rejected(self):
        self.args.output = self.root / "new&unsafe"
        self.refused("metacharacter")

    def test_relative_output_rejected(self):
        self.args.output = Path("relative-output")
        self.refused("absolute")

    def test_claim_race_never_overwrites(self):
        plan = self.check()
        self.args.output.mkdir()
        marker = self.args.output / "racer.txt"
        marker.write_text("other process")
        with self.assertRaises(FileExistsError):
            bc.build(plan)
        self.assertEqual(marker.read_text(), "other process")

    def test_stage_copies_and_preserves_inputs(self):
        plan = self.check()
        self.args.output.mkdir()
        cloned = bc.stage(plan, self.args.output)
        self.assertNotEqual(cloned, self.project)
        self.assertEqual(bc.unchanged(plan), [])
        x = ET.parse(cloned)
        self.assertEqual(x.find("./Runs/Run").get("AutoIncrementalCheckpoint"), "false")
        self.assertFalse("IncrementalCheckpoint" in x.find("./Runs/Run").attrib)
        self.assertEqual(bc.sha(self.args.output / "inputs/project/one.srcs/sources_1/bd/system/system.bd"), bc.sha(self.bd))

    def test_changed_input_blocks_snapshot(self):
        plan = self.check()
        self.bd.write_text(self.bd.read_text() + "\n")
        self.args.output.mkdir()
        with self.assertRaisesRegex(bc.BuildError, "changed"):
            bc.stage(plan, self.args.output)

    def test_hwh_timestamp_only_normalization(self):
        a = b'<X TIMESTAMP="a"><Y VALUE="1"/></X>'
        b = b'<X TIMESTAMP="b"><Y VALUE="1"/></X>'
        c = b'<X TIMESTAMP="b"><Y VALUE="2"/></X>'
        self.assertEqual(bc.hwh_signature(a), bc.hwh_signature(b))
        self.assertNotEqual(bc.hwh_signature(a), bc.hwh_signature(c))

    def test_reparse_flag_refused_without_windows_link_privilege(self):
        actual = bc.Path.lstat
        target = self.args.output
        def fake_stat(p, *a, **k):
            if p == target:
                return type("FakeStat", (), {"st_mode": 0, "st_file_attributes": 0x400})()
            return actual(p, *a, **k)
        with patch.object(bc.Path, "lstat", fake_stat):
            self.refused("reparse")

    def test_only_inactive_cti_sentinels_are_equivalent(self):
        a = ('<EDKSYSTEM><MODULES><MODULE VLNV="xilinx.com:ip:processing_system7:5.5">'
             '<PARAMETERS><PARAMETER NAME="PCW_USE_CROSS_TRIGGER" VALUE="0"/>'
             '<PARAMETER NAME="PCW_P2F_CTI_INTR" VALUE="0"/>'
             '<PARAMETER NAME="PCW_FTM_CTI_IN0" VALUE="DISABLED"/>'
             '<PARAMETER NAME="DMA_ADDRESS" VALUE="0x40400000"/>'
             '</PARAMETERS><PORTS/></MODULE></MODULES></EDKSYSTEM>')
        b = a.replace('VALUE="DISABLED"', 'VALUE="&lt;Select&gt;"')
        sig = lambda data: bc.hwh_signature(data.encode(), normalize_disabled_cti=True)
        self.assertEqual(sig(a), sig(b))
        self.assertNotEqual(bc.hwh_signature(a.encode()), bc.hwh_signature(b.encode()))
        self.assertNotEqual(sig(a), sig(b.replace('0x40400000', '0x40410000')))
        self.assertNotEqual(sig(a), sig(b.replace('&lt;Select&gt;', 'TRIGGER_IN_0')))
        for key in ('PCW_USE_CROSS_TRIGGER', 'PCW_P2F_CTI_INTR'):
            x = a.replace('NAME="' + key + '" VALUE="0"', 'NAME="' + key + '" VALUE="1"')
            y = b.replace('NAME="' + key + '" VALUE="0"', 'NAME="' + key + '" VALUE="1"')
            self.assertNotEqual(sig(x), sig(y))
        self.assertNotEqual(sig(a.replace('<PORTS/>', '<PORTS><PORT NAME="FTMT_F2P_TRIG_0"/></PORTS>')),
                            sig(b.replace('<PORTS/>', '<PORTS><PORT NAME="FTMT_F2P_TRIG_0"/></PORTS>')))

    def test_bsp_init_mismatch_never_allowed(self):
        a = {"hwh_compat_signature": "same", "ps7_init_sha256": "before"}
        b = {"hwh_compat_signature": "same", "ps7_init_sha256": "after"}
        self.assertFalse(bc.bsp_contract_matches(a, b))

    def test_generated_wrapper_comment_only_difference(self):
        a = b"//Date        : yesterday\r\n//Host        : old\r\nmodule t; endmodule\r\n"
        b = b"//Date        : today\n//Host        : new\nmodule t; endmodule\n"
        self.assertTrue(bc.generated_wrapper_equal(a, b))
        self.assertFalse(bc.generated_wrapper_equal(a, b.replace(b"module t;", b"module changed;")))

    def test_timing_summary_includes_pulse_width(self):
        text = "\n  4.640 0.000 0 8561 0.056 0.000 0 8457 7.888 0.000 0 4592\n"
        values = bc.timing_summary_values(text)
        self.assertEqual(values["WPWS"], 7.888)
        self.assertEqual(bc.timing_summary_values(text.replace("7.888", "-0.010"))["WPWS"], -0.010)
        with self.assertRaises(bc.BuildError):
            bc.timing_summary_values("no timing summary")

    def test_bd_allows_only_original_xci_value_expansion(self):
        old = {"design": {"components": {"ps": {"xci_name": "ps0",
                "parameters": {"explicit": {"value": "1"}}}}, "nets": {"wire": ["a", "b"]}}}
        new = json.loads(json.dumps(old))
        new["design"]["components"]["ps"]["parameters"]["default"] = {"value": "2"}
        values = {"ps0": {"default": [{"value": "2"}]}}
        self.assertEqual(bc.bd_materialization(json.dumps(old), json.dumps(new), values), ["ps/default"])
        self.assertIsNone(bc.bd_materialization(json.dumps(old), json.dumps(new), {}))
        new["design"]["nets"]["wire"] = ["a", "different"]
        self.assertIsNone(bc.bd_materialization(json.dumps(old), json.dumps(new), values))

    def test_bd_rejects_changed_existing_parameter(self):
        old = {"design": {"components": {"ps": {"xci_name": "ps0",
                "parameters": {"explicit": {"value": "1"}}}}}}
        new = json.loads(json.dumps(old))
        new["design"]["components"]["ps"]["parameters"]["explicit"]["value"] = "2"
        self.assertIsNone(bc.bd_materialization(json.dumps(old), json.dumps(new), {}))


if __name__ == "__main__":
    unittest.main()
