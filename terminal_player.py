"""Windows terminal player: stdlib only, ANSI frames + native PCM audio clock.

Animation choreography: yym8224961/world.execute-me-ascii. Song: Mili.
Windows adaptation: Codex. Run with Python 3.10+ in a real terminal.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source'))
try:
    from engine import Film, CHAPTERS, crop, DIM, WHITE
except ModuleNotFoundError as error:
    if error.name not in ('engine', 'scenes'):
        raise
    print('Animation dependency is missing. Run setup.cmd first.', file=sys.stderr)
    raise SystemExit(1)
from console_font import ConsoleFont


from win_audio import WindowsAudio


class SilentClock:
    def __init__(self, duration):
        self.duration = duration
        self.saved = 0.
        self.begin = None

    def position(self):
        return min(self.duration, self.saved + (time.monotonic() - self.begin if self.begin is not None else 0))

    def playing(self):
        return self.begin is not None and self.position() < self.duration

    def play(self):
        if self.begin is None:
            self.begin = time.monotonic()

    def pause(self):
        self.saved = self.position()
        self.begin = None

    def seek(self, value):
        running = self.playing()
        self.saved = max(0, min(value, self.duration - .02))
        self.begin = time.monotonic() if running else None

    def volume(self, value):
        pass

    def close(self):
        pass


class Terminal:
    def __init__(self, args):
        self.args = args
        self.font = None

    def __enter__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetStdHandle.argtypes = [wintypes.DWORD]
        self.api.GetStdHandle.restype = wintypes.HANDLE
        self.api.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.api.GetConsoleMode.restype = wintypes.BOOL
        self.api.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.api.SetConsoleMode.restype = wintypes.BOOL
        self.restores = []
        output = self.api.GetStdHandle(wintypes.DWORD(-11).value)
        mode = wintypes.DWORD()
        if not self.api.GetConsoleMode(output, ctypes.byref(mode)):
            raise RuntimeError('请在 Windows Terminal / PowerShell / CMD 中运行，不要重定向输出。')
        if not self.api.SetConsoleMode(output, mode.value | 0x0004 | 0x0001):
            raise RuntimeError('当前终端不支持 ANSI 显示，请使用 Windows Terminal。')
        self.restores.append((output, mode.value))
        self.font = ConsoleFont(output)
        if not self.args.keep_font:
            self.font.apply(self.args.font, self.args.font_size, self.args.font_weight)
        input_handle = self.api.GetStdHandle(wintypes.DWORD(-10).value)
        input_mode = wintypes.DWORD()
        if self.api.GetConsoleMode(input_handle, ctypes.byref(input_mode)):
            # Avoid legacy console Quick Edit freezing the video on a click.
            if self.api.SetConsoleMode(input_handle, (input_mode.value | 0x0080) & ~0x0040):
                self.restores.append((input_handle, input_mode.value))
        sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[2J')
        sys.stdout.flush()
        return self

    def __exit__(self, *exc):
        try:
            sys.stdout.write('\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l')
            sys.stdout.flush()
        finally:
            if self.font is not None:
                self.font.restore()
            for handle, mode in reversed(self.restores):
                self.api.SetConsoleMode(handle, mode)
            if self.args.font_report:
                Path(self.args.font_report).write_text(json.dumps(self.font.result, ensure_ascii=False, indent=2), encoding='utf-8')


def check(film):
    report = {'platform': sys.platform, 'render': [], 'audio': {}}
    for w, h in [(64, 24), (128, 44), (180, 55)]:
        for t in [0, 15.9, 24, 35, 65, 81, 108, 115, 132, 152, 168, 182, 199, 211]:
            c = film.render(t, w, h)
            assert len(c.cells) == h and all(len(row) == w for row in c.cells)
            assert c.ansi().startswith('\x1b[H')
        report['render'].append({'columns': w, 'rows': h, 'samples': 14, 'status': 'passed'})
    audio = WindowsAudio(ROOT / 'media/song.wav')
    try:
        audio.volume(0)
        assert 210 < audio.duration < 214
        audio.seek(30)
        assert abs(audio.position() - 30) < .1
        audio.play()
        time.sleep(.25)
        playing_position = audio.position()
        assert audio.playing() and playing_position > 30
        audio.pause()
        paused_position = audio.position()
        time.sleep(.15)
        assert not audio.playing() and abs(audio.position() - paused_position) < .04
        audio.seek(177.246)
        assert abs(audio.position() - 177.246) < .1
        audio.play()
        time.sleep(.15)
        assert audio.playing() and audio.position() > 177.246
        report['audio'] = {'duration': audio.duration, 'open': 'passed', 'muted_playback': 'passed',
                           'pause_clock': 'passed', 'seek_30s': 'passed', 'seek_chapter_5': 'passed',
                           'resume': 'passed'}
    finally:
        audio.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


def run(args, film):
    import msvcrt
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError('请在终端中运行，不能将动画输出重定向到文件。检查环境可用 --check。')
    audio = SilentClock(film.config['duration']) if args.silent else WindowsAudio(ROOT / 'media/song.wav')
    try:
        audio.seek(args.start)
        started = args.autoplay or args.start > 0
        if args.autoplay:
            audio.play()
        volume = .75
        help_on = False
        last_size = None
        wall_start = time.monotonic()
        with Terminal(args):
            while True:
                frame_start = time.monotonic()
                while msvcrt.kbhit():
                    key = msvcrt.getwch()
                    if key in ('\x00', '\xe0'):
                        ext = msvcrt.getwch()
                        if ext in ('K', 'M'):
                            audio.seek(audio.position() + (5 if ext == 'M' else -5))
                            started = True
                        continue
                    key = key.lower()
                    if key in ('q', '\x1b', '\x03'):
                        return
                    if key in (' ', '\r'):
                        started = True
                        if audio.playing():
                            audio.pause()
                        else:
                            if audio.position() >= audio.duration - .1:
                                audio.seek(0)
                            audio.play()
                    elif key == 'r':
                        started = True
                        audio.seek(0)
                        audio.play()
                    elif key in ('1', '2', '3', '4', '5'):
                        started = True
                        audio.seek(CHAPTERS[int(key) - 1][0])
                        audio.play()
                    elif key == 'h':
                        help_on = not help_on
                    elif key in ('+', '=', '-'):
                        volume = max(0, min(1, volume + (-.05 if key == '-' else .05)))
                        audio.volume(volume)
                size = shutil.get_terminal_size((128, 44))
                w, h = min(240, size.columns - 1), min(85, size.lines)
                if (w, h) != last_size:
                    sys.stdout.write('\x1b[2J')
                    last_size = (w, h)
                t = audio.position()
                paused = not audio.playing()
                c = film.render(t, w, h, paused=paused, ready=not started)
                if w >= 64 and h >= 24:
                    c.put(0, h - 1, ' ' * w, DIM)
                    hint = 'SPACE play/pause  <- -> 5s  R restart  1-5 chapter  +/- vol  H help  Q quit'
                    c.center(h - 1, crop(hint, w - 2), DIM)
                if help_on:
                    lines = ['WINDOWS TERMINAL / CONTROLS', 'SPACE / ENTER  play / pause',
                             'LEFT / RIGHT   seek 5 seconds', '1 2 3 4 5      chapter',
                             'R              restart', '+ / -          volume',
                             'H              close help', 'Q / ESC        quit',
                             f'Audio: {"SILENT" if args.silent else "PCM CLOCK"}  Volume: {volume:.0%}']
                    box_w = min(w - 2, 48)
                    x, y = (w - box_w) // 2, max(0, (h - len(lines) - 2) // 2)
                    for dy in range(len(lines) + 2):
                        c.put(x, y + dy, ' ' * box_w, DIM)
                    c.box(x, y, box_w, len(lines) + 2, WHITE)
                    for i, line in enumerate(lines):
                        c.put(x + 2, y + 1 + i, crop(line, max(1, box_w - 4)), WHITE)
                sys.stdout.write(c.ansi())
                sys.stdout.flush()
                if args.stop_after is not None and time.monotonic() - wall_start >= args.stop_after:
                    return
                time.sleep(max(0, 1 / args.fps - (time.monotonic() - frame_start)))
    finally:
        audio.close()


def main():
    ap = argparse.ArgumentParser(description='world.execute(me); Windows 终端 ASCII 动画')
    ap.add_argument('--start', type=float, default=0, help='从指定秒数开始')
    ap.add_argument('--autoplay', action='store_true', help='直接播放；默认按空格开始')
    ap.add_argument('--silent', action='store_true', help='无声运行')
    ap.add_argument('--fps', type=int, choices=range(1, 61), default=24, metavar='1..60')
    ap.add_argument('--check', action='store_true', help='检查场景和 Windows 音频时钟，不播放出声')
    ap.add_argument('--font', default='Lucida Console', help='传统 Windows 控制台字体，默认 Lucida Console')
    ap.add_argument('--font-size', type=int, choices=range(12, 41), default=22, metavar='12..40', help='字体像素高度，默认 22')
    ap.add_argument('--font-weight', type=int, choices=[400, 700], default=400, help='字重，默认常规体 400')
    ap.add_argument('--keep-font', action='store_true', help='保持终端原来的字体')
    ap.add_argument('--font-report', help=argparse.SUPPRESS)
    ap.add_argument('--stop-after', type=float, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if sys.platform != 'win32':
        ap.error('此入口适用于 Windows 10/11；其他系统请使用 HTML 播放版。')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    try:
        film = Film()
        if args.check:
            check(film)
        else:
            run(args, film)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f'\n播放失败：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
