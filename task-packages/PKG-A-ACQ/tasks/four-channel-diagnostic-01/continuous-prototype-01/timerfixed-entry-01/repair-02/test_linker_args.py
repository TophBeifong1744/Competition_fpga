"""TF-B-02-R1: actual archived command comparison, no compiler or hardware."""
import json
from pathlib import Path
import sys
import unittest

ENTRY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENTRY))
import check_entry as gate
import command_contract as cc

APP = Path(gate.POLICY['reference_app'])
BSP = Path(gate.POLICY['reference_bsp'])
ARCHIVE = json.loads((ENTRY / 'user-build-20260916-01/verification-01/ninja-commands.json').read_text())['stdout']
TOKEN = '-Wl,"' + APP.as_posix() + '/src/lscript.ld"'


class LinkerArgumentTests(unittest.TestCase):
    def check(self, output, app=APP, bsp=BSP):
        return gate.verify_link_output(output, app, bsp)

    def reject_token(self, replacement):
        self.assertEqual(ARCHIVE.count(TOKEN), 1)
        with self.assertRaises(ValueError):
            self.check(ARCHIVE.replace(TOKEN, replacement))

    def test_archived_command_passes(self):
        self.check(ARCHIVE)

    def test_four_b_counterexamples_rejected(self):
        for extra in ('', ',-e,0x01000000', ',--defsym,REVIEW_MARKER=1', ',--wrap=XAxiDma_SimpleTransfer'):
            with self.subTest(extra=extra):
                self.reject_token(TOKEN[:-1] + extra + ',-L,/../lscript.ld"')

    def test_additional_composite_paths_rejected(self):
        for suffix in (',-L,/../lscript.ld', ',--wrap,foo/../../lscript.ld',
                       ',--defsym,Foo=1', ',--entry=0', ',@response.txt', ',,', ','):
            with self.subTest(suffix=suffix):
                self.reject_token(TOKEN[:-1] + suffix + '"')

    def test_legal_path_variants(self):
        path = APP.as_posix() + '/src/lscript.ld'
        for value in (path.upper(), path.replace('/', '\\'), path.replace('/src/', '/src/./'),
                      path.replace('/src/', '/src/../src/')):
            with self.subTest(path=value):
                self.assertEqual(self.check(ARCHIVE), self.check(ARCHIVE.replace(TOKEN, '-Wl,"' + value + '"')))

    def test_equivalent_outer_quoting(self):
        path = APP.as_posix() + '/src/lscript.ld'
        for token in ('-Wl,' + path, '"-Wl,' + path + '"'):
            with self.subTest(token=token):
                self.assertEqual(self.check(ARCHIVE), self.check(ARCHIVE.replace(TOKEN, token)))

    def test_unknown_wl_layout_rejected(self):
        for arg in ('-Wl,', '-Wl,-Map=memory.map,--cref,-e,0', '-Wl,--end-group,--wrap=foo',
                    '-Wl,--unknown', '-Wl,-T,F:/test.ld', '-Wl,--start-group,-lc',
                    '-Wl,-Map=memory.map,--CREF'):
            with self.subTest(arg=arg), self.assertRaises(ValueError):
                cc.normalize_command('gcc ' + arg, APP, BSP)

    def test_script_operand_requires_single_path(self):
        for value in ('-Wl,-T', '-Wl,-T -Wl,-e,0', '-Wl,-T -Wl,relative.ld',
                      '-Wl,-T -Wl,', '-Wl,-T -o output -Wl,F:/script.ld'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cc.normalize_command('gcc ' + value, APP, BSP)

    def test_unbound_linker_path_rejected(self):
        with self.assertRaises(ValueError):
            cc.normalize_command('gcc -Wl,F:/script.ld', APP, BSP)

    def test_double_script_or_new_option_rejected(self):
        for addition in (' -Wl,-T -Wl,F:/other.ld', ' -Wl,-e,0', ' -Wl,--wrap=x',
                         ' -u__clang__', ' -Wl,--end-group'):
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                self.check(ARCHIVE.replace(TOKEN, TOKEN + addition))

    def test_library_order_and_case_preserved(self):
        for before, after in (('-lxilstandalone,-lxiltimer', '-lxiltimer,-lxilstandalone'),
                              ('-lxilstandalone', '-lXilstandalone'),
                              ('--start-group', '--START-group')):
            with self.subTest(after=after), self.assertRaises(ValueError):
                self.check(ARCHIVE.replace(before, after))

    def test_macros_and_argument_boundaries_preserved(self):
        for left, right in (('gcc -DMSG=Value', 'gcc -DMSG=value'),
                            ('gcc "-DMSG=Hello World"', 'gcc -DMSG=Hello World'),
                            ('gcc -U__clang__', 'gcc -u__clang__'),
                            ('gcc -DSDT', 'gcc -Dsdt')):
            with self.subTest(left=left):
                self.assertNotEqual(cc.normalize_command(left, APP, BSP), cc.normalize_command(right, APP, BSP))

    def test_split_preserves_comma_inside_quotes(self):
        # GCC still splits the comma after Windows shell quoting is removed.
        self.reject_token('"' + TOKEN.replace('"', '') + ',-L,/../lscript.ld"')


if __name__ == '__main__':
    unittest.main(verbosity=2)
