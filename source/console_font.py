"""Temporary font selection for the classic Windows console host."""
import ctypes
from ctypes import wintypes


class Coord(ctypes.Structure):
    _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]


class FontInfo(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.ULONG), ('nFont', wintypes.DWORD),
                ('dwFontSize', Coord), ('FontFamily', wintypes.UINT),
                ('FontWeight', wintypes.UINT), ('FaceName', wintypes.WCHAR * 32)]


class ConsoleFont:
    def __init__(self, handle):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(FontInfo)]
        self.api.GetCurrentConsoleFontEx.restype = wintypes.BOOL
        self.api.SetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(FontInfo)]
        self.api.SetCurrentConsoleFontEx.restype = wintypes.BOOL
        self.handle = handle
        self.original = None
        self.codepages = None
        self.result = {'status': 'not_applied'}

    def read(self):
        info = FontInfo(); info.cbSize = ctypes.sizeof(FontInfo)
        if not self.api.GetCurrentConsoleFontEx(self.handle, False, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        return info

    @staticmethod
    def describe(info):
        return {'face': info.FaceName, 'weight': info.FontWeight,
                'cell_width': info.dwFontSize.X, 'cell_height': info.dwFontSize.Y}

    def apply(self, face='Lucida Console', height=22, weight=400):
        try:
            self.original = self.read()
            self.codepages = (self.api.GetConsoleCP(), self.api.GetConsoleOutputCP())
            self.api.SetConsoleCP(65001)
            self.api.SetConsoleOutputCP(65001)
            info = FontInfo(); info.cbSize = ctypes.sizeof(FontInfo)
            info.FaceName = face[:31]
            info.dwFontSize = Coord(0, height)
            info.FontFamily = 54
            info.FontWeight = weight
            if not self.api.SetCurrentConsoleFontEx(self.handle, False, ctypes.byref(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            actual = self.read()
            self.result = {'status': 'applied' if actual.FaceName.casefold() == face.casefold() and actual.FontWeight == weight and actual.dwFontSize.Y == height else 'host_substituted',
                           'before': self.describe(self.original), 'after': self.describe(actual),
                           'requested': {'face': face, 'height': height, 'weight': weight}}
        except OSError as error:
            self.result = {'status': 'host_unsupported', 'detail': str(error)}
        return self.result

    def restore(self):
        if self.codepages is not None:
            self.api.SetConsoleCP(self.codepages[0])
            self.api.SetConsoleOutputCP(self.codepages[1])
        if self.original is not None:
            ok = bool(self.api.SetCurrentConsoleFontEx(self.handle, False, ctypes.byref(self.original)))
            self.result['restore_succeeded'] = ok
            if ok:
                self.result['restored'] = self.describe(self.read())
