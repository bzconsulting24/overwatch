import ctypes
import ctypes.wintypes

def list_windows():
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                                         ctypes.wintypes.HWND,
                                         ctypes.wintypes.LPARAM)
    titles = []
    def foreach(hwnd, lParam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buff = ctypes.create_unicode_buffer(length+1)
            user32.GetWindowTextW(hwnd, buff, length+1)
            titles.append(buff.value)
        return True
    EnumWindows(EnumWindowsProc(foreach), 0)
    return titles

for t in list_windows():
    if any(k in t for k in ("Tracked", "HOG", "Aligned", "Action")):
        print(repr(t))
