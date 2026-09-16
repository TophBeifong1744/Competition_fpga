"""Independent NTFS protection tests. No hardware tools or actual project."""
import ctypes
import json
import mmap
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
ENTRY = Path('F:/NUEC/review-worktrees/timerfixed-repair-17afe32/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01')
sys.path.insert(0, str(ENTRY))
import artifact_guard as guard


def mapped_writer():
    target = ROOT / 'mapped-writer.bin'
    target.write_bytes(b'original')
    with target.open('r+b') as stream:
        view = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_WRITE)
    result = {'source_handle_closed': True}
    try:
        try:
            with guard.locked_files([target]):
                result['lock_acquired'] = True
                view[:] = b'changed!'
                view.flush()
                result['bytes_changed_while_locked'] = target.read_bytes() == b'changed!'
        except OSError as exc:
            result.update(lock_rejected=str(exc), winerror=getattr(exc, 'winerror', None))
    finally:
        view.close()
    return result


def partial_lock_failure():
    first, second = ROOT / 'first.bin', ROOT / 'second.bin'
    first.write_bytes(b'first')
    second.write_bytes(b'second')
    result = {}
    with second.open('r+b'):
        try:
            with guard.locked_files([first, second]):
                result['unexpected_success'] = True
        except OSError as exc:
            result['rejected'] = str(exc)
        first.write_bytes(b'released after second lock failed')
        result['earlier_lock_released'] = True
    return result


def hardlink_writer():
    target, alias = ROOT / 'hardlink-original.bin', ROOT / 'hardlink-alias.bin'
    target.write_bytes(b'original')
    os.link(target, alias)
    result = {}
    with guard.locked_files([target]):
        try:
            alias.write_bytes(b'changed!')
            result['unexpected_write'] = True
        except OSError as exc:
            result['alias_write_rejected'] = str(exc)
    alias.write_bytes(b'released')
    result['released_after_context'] = True
    return result


results = {}
for name, test in [('mapped_writer', mapped_writer), ('partial_lock_failure', partial_lock_failure), ('hardlink_writer', hardlink_writer)]:
    try:
        results[name] = test()
    except Exception:
        results[name] = {'unexpected_error': traceback.format_exc()}
    print(name, json.dumps(results[name]), flush=True)
(ROOT / 'independent-guard-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
