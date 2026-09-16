"""Local NTFS mandatory sharing locks; no admin/process-termination guarantee."""
from contextlib import ExitStack, contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def api():
    if os.name != 'nt':
        raise OSError('Protected loading supports local Windows NTFS only')
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
                             ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    k.CreateFileW.restype = wintypes.HANDLE
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    k.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    k.GetDriveTypeW.restype = wintypes.UINT
    k.GetVolumeInformationW.argtypes = [wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.DWORD,
        ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.LPWSTR,wintypes.DWORD]
    k.GetVolumeInformationW.restype = wintypes.BOOL
    return k

def local_path(path):
    path = Path(os.path.abspath(path))
    k = api()
    if path.drive.startswith('\\\\') or k.GetDriveTypeW(path.anchor) != 3:
        raise OSError('Only local fixed drives are supported')
    fs = ctypes.create_unicode_buffer(32)
    if not k.GetVolumeInformationW(path.anchor,None,0,None,None,None,fs,len(fs)):
        raise ctypes.WinError(ctypes.get_last_error())
    if fs.value != 'NTFS':
        raise OSError('Unvalidated filesystem: ' + fs.value)
    for part in [*reversed(path.parents),path]:
        if part.lstat().st_file_attributes & 0x400:
            raise OSError('Reparse point not allowed: ' + str(part))
    return path

@contextmanager
def lock(path, directory=False):
    path = local_path(path)
    k = api()
    # Directory handles prohibit rename/delete; file handles additionally
    # prohibit writes/truncation. Normal readers can reopen sealed files.
    h = k.CreateFileW('\\\\?\\' + str(path), 0 if directory else 0x80000000,
                     3 if directory else 1, None, 3,
                     0x02200000 if directory else 0x00200000, None)
    if h == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        yield path
    finally:
        k.CloseHandle(h)

@contextmanager
def locked_files(files):
    with ExitStack() as stack:
        paths = [local_path(p) for p in files]
        dirs = sorted({p for f in paths for p in f.parents}, key=lambda p:len(p.parts))
        for d in dirs:
            stack.enter_context(lock(d,True))
        for f in paths:
            stack.enter_context(lock(f))
        yield

@contextmanager
def sealed_snapshot(files, expected, out):
    """Caller holds source locks; verify copied bytes AFTER acquiring seals."""
    out = Path(out)
    out.mkdir(exist_ok=False)
    names = {'elf':'firmware.elf','bit':'system.bit','init':'ps7_init.tcl'}
    if set(files) != set(names) or set(expected) != set(names):
        raise ValueError('Incomplete artifact set')
    copied = {}
    for key,name in names.items():
        target = out/name
        with target.open('xb') as stream:
            stream.write(Path(files[key]).read_bytes())
        copied[key] = target
    with locked_files(copied.values()):
        for key,path in copied.items():
            if sha(path) != expected[key]:
                raise ValueError('Snapshot not the checked bytes: ' + key)
        yield copied
