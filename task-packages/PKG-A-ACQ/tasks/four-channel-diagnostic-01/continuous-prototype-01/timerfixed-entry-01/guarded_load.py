"""Pipe lock keeper; never executes XSDB or operates hardware."""
import argparse
import base64
from pathlib import Path
import sys
from contextlib import ExitStack
import check_entry as gate
from artifact_guard import locked_files, sealed_snapshot

def session(args, out):
    app = gate.safe.no_links(args.app)
    paths = {k:Path(v) for k,v in gate.launch_paths(app,app.parent).items()}
    proof = [app/'build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj',
             app/'build/memory.map',app/'build/compile_commands.json',
             app/'build/build.ninja',app/'build/CMakeFiles/rules.ninja',
             app/'_ide/launch.json',app/'vitis-comp.json',app/'src/CMakeLists.txt']
    proof += [app/'src'/p for p in gate.POLICY['source_sha256']]
    with ExitStack() as sealed:
        with locked_files([*paths.values(),*proof]):
            report = gate.verify(args,out)
            gate.need({k:str(v) for k,v in paths.items()} == report['load_paths'],
                      'Launch changed while acquiring locks')
            expected = dict(elf=report['compiled']['elf_sha256'],
                            bit=gate.POLICY['hardware_sha256']['system_continuous_20260915.bit'],
                            init=gate.POLICY['hardware_sha256']['ps7_init.tcl'])
            snapshot = sealed.enter_context(sealed_snapshot(paths,expected,out/'sealed'))
            gate.safe.write_json(out/'receipt.json',dict(status='SEALED_NOT_BOARD_TEST',
                original_paths=report['load_paths'], snapshot={k:str(v) for k,v in snapshot.items()},
                sha256=expected, gate=report))
        # Rebuilds may now replace active files, never the sealed set used by Tcl.
        print(' '.join(['GUARD_READY_V1'] + [
            base64.b64encode(str(snapshot[k]).encode()).decode() for k in ('elf','bit','init')]),flush=True)
        for command in sys.stdin:
            if command.strip() == 'PING':
                print('GUARD_ALIVE',flush=True)
            elif command.strip() == 'RELEASE':
                print('GUARD_RELEASED',flush=True)
                gate.safe.write_json(out/'closed.json',{'status':'RELEASED_BY_CALLER'})
                return
            else:
                raise ValueError('Unknown guard command')
        raise ValueError('Loader pipe closed without release; no completion attested')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('app','platform','tools-bin','record-root'):
        p.add_argument('--'+name, required=True)
    args = p.parse_args()
    args.stage = 'load'
    out = gate.record_directory(args, 'guard')
    try:
        session(args,out)
    except Exception as exc:
        gate.safe.write_json(out/'failure.json',{'status':'REJECTED','error':str(exc)})
        print('GUARD_REJECTED: '+str(exc),file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
