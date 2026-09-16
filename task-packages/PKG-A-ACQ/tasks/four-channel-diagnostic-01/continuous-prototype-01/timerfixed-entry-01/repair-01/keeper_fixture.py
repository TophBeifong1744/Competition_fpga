"""TEST ONLY: real lock keeper and ELF checks, remaining Vitis prerequisites mocked.

Not a deployment entry; all hardware calls are mocked in the Tcl harness.
"""
import os
from pathlib import Path
import sys
entry=Path(os.environ['TF_REPAIR_ENTRY'])
sys.path.insert(0,str(entry))
import guarded_load
import check_entry as gate
def fixture_verify(args,out):
    app=Path(args.app)
    checked=gate.verify_elf(app/'build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj',
                            app/'build/four_mic_continuous.elf')
    return dict(compiled=checked,load_paths=gate.launch_paths(app,app.parent),
                scope='TEST: real ELF and file locks; other gate prerequisites simulated')
gate.verify=fixture_verify
sys.exit(guarded_load.main())
