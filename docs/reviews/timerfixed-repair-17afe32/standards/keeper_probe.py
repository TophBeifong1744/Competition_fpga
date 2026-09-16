"""TEST ONLY: real keeper/ELF/locks, other Vitis gate preconditions mocked."""
import json
import os
from pathlib import Path
import sys

ENTRY = Path('F:/NUEC/review-worktrees/timerfixed-repair-17afe32/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01')
sys.path.insert(0, str(ENTRY))
import guarded_load
import check_entry as gate


def fixture_verify(args, out):
    app = Path(args.app)
    paths = gate.launch_paths(app, app.parent)
    probes = []
    for relative in ('build/four_mic_continuous.elf', 'build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj',
                     'src/main.c', 'src/continuous/main_continuous.c', '_ide/launch.json',
                     '_ide/bitstream/system_continuous_20260915.bit', '_ide/psinit/ps7_init.tcl'):
        target = app / relative
        try:
            with target.open('r+b'):
                pass
        except OSError as exc:
            probes.append({'path': str(target), 'denied': str(exc)})
        else:
            raise AssertionError('active gate input was writable: ' + str(target))
    renamed = app.parent / 'renamed-during-gate'
    allowed_root = Path(__file__).resolve().parent
    assert app.resolve().is_relative_to(allowed_root) and renamed.resolve().is_relative_to(allowed_root)
    try:
        app.rename(renamed)
    except OSError as exc:
        probes.append({'path': str(app), 'rename_denied': str(exc)})
    else:
        raise AssertionError('application ancestor renamed during gate')
    (out / 'active-lock-probes.json').write_text(json.dumps(probes, indent=2), encoding='utf-8')
    checked = gate.verify_elf(app/'build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj',
                            app/'build/four_mic_continuous.elf')
    return dict(compiled=checked, load_paths=paths, scope='TEST ONLY: real ELF/locks; other Vitis prerequisites mocked')


gate.verify = fixture_verify
sys.exit(guarded_load.main())
