"""Native Windows PCM playback with a device-reported byte clock (stdlib only)."""
import ctypes
from ctypes import wintypes
import wave


class Format(ctypes.Structure):
    _fields_ = [('tag', wintypes.WORD), ('channels', wintypes.WORD),
                ('rate', wintypes.DWORD), ('bytes_per_second', wintypes.DWORD),
                ('align', wintypes.WORD), ('bits', wintypes.WORD), ('extra', wintypes.WORD)]


class Header(ctypes.Structure):
    _fields_ = [('data', ctypes.c_void_p), ('length', wintypes.DWORD),
                ('recorded', wintypes.DWORD), ('user', ctypes.c_size_t),
                ('flags', wintypes.DWORD), ('loops', wintypes.DWORD),
                ('next', ctypes.c_void_p), ('reserved', ctypes.c_size_t)]


class TimeUnion(ctypes.Union):
    _fields_ = [('value', wintypes.DWORD), ('padding', ctypes.c_byte * 8)]


class MediaTime(ctypes.Structure):
    _fields_ = [('type', wintypes.UINT), ('u', TimeUnion)]


class WindowsAudio:
    def __init__(self, path):
        with wave.open(str(path), 'rb') as wav:
            assert wav.getsampwidth() == 2 and wav.getcomptype() == 'NONE'
            self.rate, self.channels = wav.getframerate(), wav.getnchannels()
            pcm = wav.readframes(wav.getnframes())
        self.align = self.channels * 2
        self.bytes_per_second = self.rate * self.align
        self.duration = len(pcm) / self.bytes_per_second
        self.data = ctypes.create_string_buffer(pcm)
        self.data_length = len(pcm)
        self.handle = wintypes.HANDLE()
        self.api = ctypes.WinDLL('winmm')
        self.api.waveOutOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT,
                                        ctypes.POINTER(Format), ctypes.c_size_t, ctypes.c_size_t, wintypes.DWORD]
        for name in ['waveOutPause', 'waveOutRestart', 'waveOutReset', 'waveOutClose']:
            getattr(self.api, name).argtypes = [wintypes.HANDLE]
        for name in ['waveOutPrepareHeader', 'waveOutUnprepareHeader', 'waveOutWrite']:
            getattr(self.api, name).argtypes = [wintypes.HANDLE, ctypes.POINTER(Header), wintypes.UINT]
        self.api.waveOutGetPosition.argtypes = [wintypes.HANDLE, ctypes.POINTER(MediaTime), wintypes.UINT]
        self.api.waveOutSetVolume.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.api.waveOutGetErrorTextW.argtypes = [wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
        fmt = Format(1, self.channels, self.rate, self.bytes_per_second, self.align, 16, 0)
        self._check(self.api.waveOutOpen(ctypes.byref(self.handle), 0xffffffff, ctypes.byref(fmt), 0, 0, 0))
        self.header = None
        self.offset = 0
        self.active = False
        try:
            self.volume(.75)
        except Exception:
            self.close()
            raise

    def _check(self, code):
        if code:
            message = ctypes.create_unicode_buffer(512)
            self.api.waveOutGetErrorTextW(code, message, len(message))
            raise RuntimeError(f'Windows PCM 音频错误 {code}: {message.value}')

    def position(self):
        if self.header is None:
            return self.offset / self.bytes_per_second
        t = MediaTime();t.type = 4  # TIME_BYTES
        self._check(self.api.waveOutGetPosition(self.handle, ctypes.byref(t), ctypes.sizeof(t)))
        if t.type == 4:
            elapsed = t.u.value / self.bytes_per_second
        elif t.type == 2:  # TIME_SAMPLES
            elapsed = t.u.value / self.rate
        elif t.type == 1:  # TIME_MS
            elapsed = t.u.value / 1000
        else:
            raise RuntimeError('音频驱动未返回可识别的播放时钟。')
        if self.header.flags & 1:  # WHDR_DONE: some devices reset the clock at EOF.
            return self.duration
        return min(self.duration, self.offset / self.bytes_per_second + elapsed)

    def playing(self):
        return self.active and self.header is not None and not self.header.flags & 1

    def play(self):
        if self.header is None:
            self.header = Header()
            self.header.data = ctypes.addressof(self.data) + self.offset
            self.header.length = self.data_length - self.offset
            self._check(self.api.waveOutPrepareHeader(self.handle, ctypes.byref(self.header), ctypes.sizeof(Header)))
            self._check(self.api.waveOutWrite(self.handle, ctypes.byref(self.header), ctypes.sizeof(Header)))
        self._check(self.api.waveOutRestart(self.handle))
        self.active = True

    def pause(self):
        self._check(self.api.waveOutPause(self.handle))
        self.active = False

    def seek(self, value):
        running = self.playing()
        self._reset()
        self.offset = int(max(0, min(value, self.duration - .02)) * self.rate) * self.align
        if running:
            self.play()

    def _reset(self):
        self._check(self.api.waveOutReset(self.handle))
        if self.header is not None:
            self._check(self.api.waveOutUnprepareHeader(self.handle, ctypes.byref(self.header), ctypes.sizeof(Header)))
            self.header = None
        self.active = False

    def volume(self, value):
        level = round(max(0, min(1, value)) * 65535)
        self._check(self.api.waveOutSetVolume(self.handle, level | (level << 16)))

    def close(self):
        if self.handle:
            try:
                self._reset()
            finally:
                self._check(self.api.waveOutClose(self.handle))
                self.handle = wintypes.HANDLE()
