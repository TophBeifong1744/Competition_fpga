"""Narrow Windows GCC argv comparison; never casefold flags or macro values."""
import ctypes
from ctypes import wintypes
import ntpath
import os


def command_argv(command):
    if os.name != 'nt':
        raise ValueError('Only the pinned Windows command format is supported')
    if not command.strip() or any(c in command for c in '\x00\r\n'):
        raise ValueError('Empty/multiline command')
    # Prepend argv[0] so every actual token uses the same quoted-argument rules.
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    count = ctypes.c_int()
    ptr = shell.CommandLineToArgvW('placeholder.exe ' + command, ctypes.byref(count))
    if not ptr:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return [ptr[i] for i in range(1, count.value)]
    finally:
        kernel.LocalFree(ptr)


def normalize_command(command, app, bsp):
    """Only recognized filesystem operands use Windows path normalization."""
    def path(value):
        result = ntpath.normcase(ntpath.normpath(value)).replace('\\', '/')
        for root, marker in ((bsp, '$bsp'), (app, '$app')):
            base = ntpath.normcase(ntpath.normpath(str(root))).replace('\\', '/').rstrip('/')
            if result == base or result.startswith(base + '/'):
                return marker + result[len(base):]
        return result
    argv = command_argv(command)
    result, next_path = [], False
    for i, arg in enumerate(argv):
        if i == 0 or next_path:
            result.append(path(arg))
            next_path = False
        elif arg in ('-isystem', '-o', '-c', '-I', '-L', '-T'):
            result.append(arg)
            next_path = True
        elif arg.startswith(('-I', '-L')) and len(arg) > 2:
            result.append(arg[:2] + path(arg[2:]))
        elif arg.startswith('-specs='):
            result.append('-specs=' + path(arg[7:]))
        elif arg.startswith('-Wl,') and ntpath.isabs(arg[4:]):
            result.append('-Wl,' + path(arg[4:]))
        elif not arg.startswith('-') and arg.endswith('.obj'):
            result.append(path(arg))
        else:
            # -D/-U/-u/-Wl and macro/string operands remain case-sensitive.
            result.append(arg)
    if next_path:
        raise ValueError('Missing path operand')
    return tuple(result)


def link_command(ninja_output):
    prefix = 'cmd.exe /C "cd . && '
    lines = [line for line in ninja_output.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise ValueError('Unsupported/ambiguous Ninja link command')
    pieces = lines[0][len(prefix):].split(' && ', 1)
    if len(pieces) != 2 or not pieces[1]:
        raise ValueError('Missing post-link command')
    return pieces[0]
