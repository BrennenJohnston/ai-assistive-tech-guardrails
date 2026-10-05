#!/usr/bin/env python3
"""NVDA walk driver: send real keys to a browser window and read back what NVDA said.

Windows only. Python 3.8+ standard library only. NVDA must be running with its
logging level set to "input/output" (see docs/SCREEN_READER_STANDARD.md, part N).

Keys go to the foreground window through the Windows SendInput API, so NVDA
handles them exactly like keys typed on a keyboard. NVDA's own log is then read
back: every key NVDA received ("KEY") and every piece of text it sent to the
voice ("SAY"), with NVDA's own timestamps. That log is the evidence; nothing is
transcribed by ear.

Usage:
    python nvda-walk.py check
    python nvda-walk.py fg
    python nvda-walk.py focus --title "My App"
    python nvda-walk.py mark NAME
    python nvda-walk.py since NAME [--save FILE]
    python nvda-walk.py count NAME TEXT
    python nvda-walk.py keys --title "My App" [--gap MS] [--chargap MS]
                             [--tail MS] [--out FILE] [--allow TEXT] TOKENS...

Options for every command:
    --log PATH     NVDA's log (default: %TEMP%\\nvda.log)
    --marks PATH   where marks are kept (default: nvda-walk-marks.json here)
    --exe NAMES    browser process names the guard accepts, comma-separated
                   (default: chrome.exe,msedge.exe,firefox.exe)
    --title TEXT   text the foreground window title must contain
                   (default: the NVDA_WALK_TITLE environment variable)

Key tokens for "keys":
    tab  shift+tab  enter  space  escape  backspace  delete
    up  down  left  right  home  end  pageup  pagedown  f1 .. f12
    ctrl+home  ctrl+a  ctrl+f5  alt+...  shift+...   (any + combination)
    nvda+down    the NVDA key (Insert) with another key; nvda+tab, nvda+f7 ...
    numpad5      Numpad 5 with Num Lock off (NVDA+numpad5 = report object)
    a .. z, 0 .. 9       single keys
    text:hello world     typed one key at a time, --chargap ms apart
    wait:1500            pause, in milliseconds
    @label               start a new step in the transcript

Safety: before EVERY key the foreground window must belong to one of the
accepted browser processes and its title must contain --title (or an --allow
text). If not, the script stops at once, sends nothing more, and exits with
code 2. Never weaken this check: it is what stops keys landing in another
program (a mail client, a terminal, a password field).

Exit codes: 0 done, 1 usage or log error, 2 stopped by the safety check.

License: MIT
"""
import ast
import ctypes
import json
import os
import re
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    # Speech can hold any Unicode (braille cells, arrows); a cp1252 console
    # would otherwise stop the listing mid-way.
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DEFAULT_LOG = os.path.join(os.environ.get('TEMP', ''), 'nvda.log')
DEFAULT_MARKS = 'nvda-walk-marks.json'
DEFAULT_EXES = 'chrome.exe,msedge.exe,firefox.exe'

# ------------------------------------------------------------------ the log

# NVDA writes a header line, then the message on the next line:
#   IO - speech.speech.speak (13:24:09.728) - MainThread (33448):
#   Speaking [LangChangeCommand ('en_US'), 'Both cylinders are ready.']
#   IO - inputCore.InputManager.executeGesture (13:24:08.101) - winInputHook (1234):
#   Input: kb(desktop):tab
HEADER = re.compile(r'^(\w+) - ([\w.]+) \((\d\d:\d\d:\d\d\.\d+)\)')
QUOTED = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
VERSION = re.compile(r'Starting NVDA version (\S+)')


def speech_pieces(inner):
    """The spoken strings of one 'Speaking [...]' list, directives dropped."""
    pieces = []
    for m in QUOTED.finditer(inner):
        # A quoted string right after '(' is a directive's argument, such as
        # LangChangeCommand ('en_US'), not something spoken.
        if inner[:m.start()].rstrip().endswith('('):
            continue
        try:
            s = ast.literal_eval(m.group(0))
        except (ValueError, SyntaxError):
            s = m.group(0)[1:-1]
        if isinstance(s, str) and s.strip():
            pieces.append(s)
    return pieces


def events_from(log, offset):
    """[(byte_pos, time, 'KEY' | 'SAY', text)] from offset to the end of the log."""
    with open(log, 'rb') as fh:
        fh.seek(offset)
        data = fh.read()
    lines, pos = [], offset
    for raw in data.split(b'\n'):
        lines.append((pos, raw.decode('utf-8', errors='replace').rstrip('\r')))
        pos += len(raw) + 1
    out = []
    for i, (bpos, line) in enumerate(lines):
        m = HEADER.match(line)
        if not m or i + 1 >= len(lines):
            continue
        source, stamp, body = m.group(2), m.group(3), lines[i + 1][1]
        if source == 'speech.speech.speak' and body.startswith('Speaking ['):
            pieces = speech_pieces(body[len('Speaking ['):])
            if pieces:
                out.append((bpos, stamp, 'SAY', ' | '.join(pieces)))
        elif body.startswith('Input: '):
            out.append((bpos, stamp, 'KEY', body[len('Input: '):]))
    return out


def format_events(evts):
    return ['  %s  %s  %s' % (t, k, s) for _, t, k, s in evts]


def load_marks(path):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    return {}


def save_marks(path, marks):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(marks, fh, indent=1)


def mark_offset(opts, name):
    marks = load_marks(opts['marks'])
    if name not in marks:
        raise SystemExit('no mark named %r in %s' % (name, opts['marks']))
    offset = marks[name]
    if offset > os.path.getsize(opts['log']):
        raise SystemExit('the log is shorter than mark %r: NVDA was restarted and '
                         'started a new log; take a new mark' % name)
    return offset

# ------------------------------------------------------------------ windows

if sys.platform == 'win32':
    import ctypes.wintypes as wt

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    INPUT_KEYBOARD = 1
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [('wVk', wt.WORD), ('wScan', wt.WORD), ('dwFlags', wt.DWORD),
                    ('time', wt.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [('dx', wt.LONG), ('dy', wt.LONG), ('mouseData', wt.DWORD),
                    ('dwFlags', wt.DWORD), ('time', wt.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [('uMsg', wt.DWORD), ('wParamL', wt.WORD), ('wParamH', wt.WORD)]

    class _UNION(ctypes.Union):
        _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT), ('hi', HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [('type', wt.DWORD), ('u', _UNION)]

    user32.SendInput.argtypes = (wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wt.UINT
    user32.MapVirtualKeyW.argtypes = (wt.UINT, wt.UINT)
    user32.MapVirtualKeyW.restype = wt.UINT
    user32.GetForegroundWindow.restype = wt.HWND
    user32.GetWindowTextLengthW.argtypes = (wt.HWND,)
    user32.GetWindowTextW.argtypes = (wt.HWND, wt.LPWSTR, ctypes.c_int)
    user32.GetWindowThreadProcessId.argtypes = (wt.HWND, ctypes.POINTER(wt.DWORD))
    user32.GetWindowThreadProcessId.restype = wt.DWORD
    user32.IsWindowVisible.argtypes = (wt.HWND,)
    user32.IsIconic.argtypes = (wt.HWND,)
    user32.ShowWindow.argtypes = (wt.HWND, ctypes.c_int)
    user32.BringWindowToTop.argtypes = (wt.HWND,)
    user32.SetForegroundWindow.argtypes = (wt.HWND,)
    user32.AttachThreadInput.argtypes = (wt.DWORD, wt.DWORD, wt.BOOL)
    kernel32.OpenProcess.argtypes = (wt.DWORD, wt.BOOL, wt.DWORD)
    kernel32.OpenProcess.restype = wt.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = (wt.HANDLE, wt.DWORD, wt.LPWSTR,
                                                    ctypes.POINTER(wt.DWORD))
    kernel32.CloseHandle.argtypes = (wt.HANDLE,)
    kernel32.GetCurrentThreadId.restype = wt.DWORD

VK = {'tab': 0x09, 'enter': 0x0D, 'escape': 0x1B, 'space': 0x20, 'backspace': 0x08,
      'delete': 0x2E, 'insert': 0x2D, 'home': 0x24, 'end': 0x23, 'pageup': 0x21,
      'pagedown': 0x22, 'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
      'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'capslock': 0x14,
      # Numpad 5 with Num Lock off; NVDA's desktop layout calls it numpad5.
      'numpad5': 0x0C}
for _n in range(1, 13):
    VK['f%d' % _n] = 0x6F + _n
EXTENDED = {'delete', 'insert', 'home', 'end', 'pageup', 'pagedown',
            'left', 'up', 'right', 'down'}
ALIASES = {'nvda': 'insert', 'control': 'ctrl', 'esc': 'escape', 'return': 'enter',
           'clear': 'numpad5'}


def window_title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def window_exe(hwnd):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(0x1000, False, pid.value)
    if not h:
        return ''
    try:
        size = wt.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
        return ''
    finally:
        kernel32.CloseHandle(h)


def foreground():
    hwnd = user32.GetForegroundWindow()
    return hwnd, window_title(hwnd), window_exe(hwnd)


def guard(opts):
    _, title, exe = foreground()
    if exe not in opts['exes'] or not any(a in title for a in opts['allow']):
        print('STOPPED: the foreground window is %r (%s); no more keys sent' % (title, exe))
        sys.stdout.flush()
        sys.exit(2)


def app_windows(opts):
    found = []
    proto = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            title = window_title(hwnd)
            if any(a in title for a in opts['allow']) and window_exe(hwnd) in opts['exes']:
                found.append((hwnd, title))
        return True

    user32.EnumWindows(proto(cb), 0)
    return found


def bring_to_front(hwnd):
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None)
    me = kernel32.GetCurrentThreadId()
    attached = bool(fg_tid and fg_tid != me and user32.AttachThreadInput(me, fg_tid, True))
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(me, fg_tid, False)
    time.sleep(0.6)
    return user32.GetForegroundWindow() == hwnd

# ------------------------------------------------------------------ keys


def vk_of(name):
    name = ALIASES.get(name, name)
    if name in VK:
        return name, VK[name]
    if len(name) == 1 and name.isascii() and (name.isalpha() or name.isdigit()):
        return name, ord(name.upper())
    raise SystemExit('unknown key: %r' % name)


def send_one(inp):
    arr = (INPUT * 1)(inp)
    if user32.SendInput(1, arr, ctypes.sizeof(INPUT)) != 1:
        raise SystemExit('SendInput failed (Windows error %d)' % ctypes.get_last_error())


def key_input(name, up):
    name, vk = vk_of(name)
    flags = KEYEVENTF_KEYUP if up else 0
    if name in EXTENDED:
        flags |= KEYEVENTF_EXTENDEDKEY
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = KEYBDINPUT(wVk=vk, wScan=user32.MapVirtualKeyW(vk, 0), dwFlags=flags,
                          time=0, dwExtraInfo=0)
    return inp


def unicode_input(ch, up):
    inp = INPUT(type=INPUT_KEYBOARD)
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0)
    inp.u.ki = KEYBDINPUT(wVk=0, wScan=ord(ch), dwFlags=flags, time=0, dwExtraInfo=0)
    return inp


def press(combo, opts):
    parts = combo.split('+')
    mods, key = parts[:-1], parts[-1]
    for part in parts:
        vk_of(part)
    guard(opts)
    for m in mods:
        send_one(key_input(m, False))
        time.sleep(0.03)
    send_one(key_input(key, False))
    time.sleep(0.03)
    send_one(key_input(key, True))
    time.sleep(0.03)
    for m in reversed(mods):
        send_one(key_input(m, True))
        time.sleep(0.03)


def type_text(text, opts, chargap):
    for ch in text:
        if ch == ' ':
            press('space', opts)
        elif ch.isascii() and ch.isalpha():
            press(('shift+' + ch.lower()) if ch.isupper() else ch, opts)
        elif ch.isascii() and ch.isdigit():
            press(ch, opts)
        else:
            guard(opts)
            send_one(unicode_input(ch, False))
            send_one(unicode_input(ch, True))
        time.sleep(chargap / 1000.0)

# ------------------------------------------------------------------ commands


def take(args, name, default=None, cast=str):
    if name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            raise SystemExit('%s needs a value' % name)
        value = args[i + 1]
        del args[i:i + 2]
        return cast(value)
    return default


def cmd_check(opts):
    print('platform:', sys.platform)
    if not os.path.exists(opts['log']):
        raise SystemExit('no NVDA log at %s: is NVDA running?' % opts['log'])
    size = os.path.getsize(opts['log'])
    with open(opts['log'], 'rb') as fh:
        head = fh.read(200000).decode('utf-8', errors='replace')
        fh.seek(max(0, size - 400000))
        tail = fh.read().decode('utf-8', errors='replace')
    version = VERSION.search(head)
    print('log:', opts['log'], '(%d bytes)' % size)
    print('NVDA version:', version.group(1) if version else 'not found in the log head')
    io_lines = tail.count('\nIO - ')
    print('IO entries in the last 400 kB:', io_lines)
    if io_lines == 0:
        print('WARNING: no input/output entries. Set NVDA menu > Preferences > Settings > '
              'General > Logging level to "input/output", then press a key and run check again.')
    if sys.platform == 'win32':
        _, title, exe = foreground()
        print('foreground window: %r (%s)' % (title, exe))


def cmd_keys(args, opts):
    gap = take(args, '--gap', 700, int)
    chargap = take(args, '--chargap', 150, int)
    tail = take(args, '--tail', 2500, int)
    out = take(args, '--out')
    while '--allow' in args:
        opts['allow'].append(take(args, '--allow'))
    if not opts['allow']:
        raise SystemExit('keys needs --title (or NVDA_WALK_TITLE): the text the browser '
                         'window title must contain before any key is sent')
    tokens = args
    for tok in tokens:
        if not tok.startswith(('@', 'wait:', 'text:')):
            for part in tok.lower().split('+'):
                vk_of(part)
    _, title, exe = foreground()
    header = ['foreground at start: %r (%s)' % (title, exe)]
    guard(opts)
    start = os.path.getsize(opts['log'])
    steps = [('(start)', start)]
    for tok in tokens:
        if tok.startswith('@'):
            steps.append((tok[1:], os.path.getsize(opts['log'])))
        elif tok.startswith('wait:'):
            time.sleep(int(tok[5:]) / 1000.0)
        elif tok.startswith('text:'):
            type_text(tok[5:], opts, chargap)
            time.sleep(gap / 1000.0)
        else:
            press(tok.lower(), opts)
            time.sleep(gap / 1000.0)
    time.sleep(tail / 1000.0)
    evts = events_from(opts['log'], start)
    lines = list(header)
    bounds = [s[1] for s in steps] + [float('inf')]
    for k, (label, off) in enumerate(steps):
        chunk = [e for e in evts if off <= e[0] < bounds[k + 1]]
        if label == '(start)' and not chunk:
            continue
        lines.append('== %s' % label)
        lines.extend(format_events(chunk) or ['  (nothing)'])
    text = '\n'.join(lines)
    print(text)
    if out:
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(text + '\n')


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help', 'help'):
        print(__doc__)
        return 0
    cmd, args = args[0], args[1:]
    title = take(args, '--title', os.environ.get('NVDA_WALK_TITLE', ''))
    opts = {
        'log': take(args, '--log', DEFAULT_LOG),
        'marks': take(args, '--marks', DEFAULT_MARKS),
        'exes': [e.strip().lower() for e in take(args, '--exe', DEFAULT_EXES).split(',') if e.strip()],
        'allow': [title] if title else [],
    }
    needs_windows = cmd in ('fg', 'focus', 'keys')
    if needs_windows and sys.platform != 'win32':
        raise SystemExit('%s needs Windows (SendInput and window checks)' % cmd)
    if cmd == 'check':
        cmd_check(opts)
    elif cmd == 'fg':
        _, title, exe = foreground()
        print('foreground: %r (%s)' % (title, exe))
    elif cmd == 'focus':
        if not opts['allow']:
            raise SystemExit('focus needs --title')
        wins = app_windows(opts)
        if not wins:
            raise SystemExit('no browser window shows %r in its title' % opts['allow'][0])
        ok = bring_to_front(wins[0][0])
        _, title, exe = foreground()
        print('brought to front: %s; foreground now %r (%s)' % (ok, title, exe))
    elif cmd == 'mark':
        if not args:
            raise SystemExit('mark needs a NAME')
        marks = load_marks(opts['marks'])
        marks[args[0]] = os.path.getsize(opts['log'])
        save_marks(opts['marks'], marks)
        print('marked %s at byte %d of %s' % (args[0], marks[args[0]], opts['log']))
    elif cmd == 'since':
        save = take(args, '--save')
        if not args:
            raise SystemExit('since needs a NAME')
        text = '\n'.join(format_events(events_from(opts['log'], mark_offset(opts, args[0]))))
        print(text or '  (nothing)')
        if save:
            with open(save, 'w', encoding='utf-8') as fh:
                fh.write(text + '\n')
    elif cmd == 'count':
        if len(args) < 2:
            raise SystemExit('count needs a NAME and the TEXT to count')
        needle = args[1].lower()
        said = [e for e in events_from(opts['log'], mark_offset(opts, args[0]))
                if e[2] == 'SAY' and needle in e[3].lower()]
        print('%d utterance(s) containing %r since %s' % (len(said), args[1], args[0]))
        for line in format_events(said):
            print(line)
    elif cmd == 'keys':
        cmd_keys(args, opts)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
