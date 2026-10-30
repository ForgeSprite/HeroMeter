"""
Hero Meter - a Details!-style damage meter for City of Heroes (Homecoming).

Reads the game's chat log live. Main bar window, breakdown window,
MOBA-style death recap, segments, display modes, report-to-clipboard.
"""
import ctypes
import json
import os
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog

import cohparse as cp
import mids
import pettypes

APP_NAME = "Hero Meter"
VERSION = "2.0.0"
REPO = "ForgeSprite/HeroMeter"            # GitHub owner/name: update check + About links
FROZEN = getattr(sys, "frozen", False)


def app_dir():
    if FROZEN:
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def res_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def data_dir():
    """Where settings live. Portable mode: a config (or 'portable.txt') next to the exe keeps everything there.
    Otherwise %APPDATA%\\Hero Meter, so the exe can sit anywhere - even a read-only folder."""
    here = app_dir()
    if any(os.path.isfile(os.path.join(here, n)) for n in
           ("hero_meter_config.json", "portable.txt", "paragon_meter_config.json", "coh_details_config.json")):
        return here
    d = os.path.join(os.environ.get("APPDATA") or here, APP_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        return here
    return d


DATA_DIR = data_dir()
CONFIG_PATH = os.path.join(DATA_DIR, "hero_meter_config.json")
OLD_CONFIG_PATHS = [os.path.join(app_dir(), n) for n in ("paragon_meter_config.json", "coh_details_config.json")]
ERROR_LOG = os.path.join(DATA_DIR, "hero_meter_error.log")

DEFAULTS = {
    "geometry": "",
    "bd_geometry": "",
    "recap_geometry": "",
    "opt_geometry": "",
    "alpha": 1.0,
    "topmost": True,
    "mode": "damage",
    "row_height": 21,
    "font_size": 15,
    "combat_timeout": 10,
    "max_segments": 30,
    "recap_window": 12,
    "merge_pets": False,
    "abbreviate": True,
    "show_rank": True,
    "show_icons": True,
    "load_history": True,
    "log_auto": True,
    "log_path": "",
    "logs_dir": "",
    "recap_show_misses": True,
    "show_pet_type": True,
    "tier_order": True,
    "no_focus": True,
    "ui_scale": 1.0,
    "auto_dpi": True,
    "opt_page": "page_display",
    "theme": "minimal",
    "custom_themes": {},
    "views": [],
    "snap_windows": True,
    "tabs_always": False,
    # display
    "num_format": "short",
    "update_interval": 0.3,
    "wheel_speed": 1,
    "time_measure": "effective",
    "realtime_dps": False,
    "overall_clear": "manual",
    "erase_trash": False,
    "trash_seconds": 5,
    "self_color_on": False,
    "self_color": "#f0b429",
    # combat log
    "recap_events": 40,
    "recap_min_heal": 0,
    "recap_reverse": False,
    "dot_separate": False,
    "merge_crits": False,
    # bars
    "row_spacing": 1,
    "grow_up": False,
    "bar_texture": "gloss",
    "bar_color_mode": "pet",
    "bar_single_color": "#3fc7eb",
    "bar_bg_color": "#232125",
    "row_border": False,
    "total_bar": False,
    "aligned_cols": False,
    # texts
    "row_font": "Oswald",
    "text_style": "shadow",
    "rt_total": True,
    "rt_ps": True,
    "rt_pct": True,
    "bracket": "(",
    # title bar
    "title_height": 22,
    "title_font_size": 14,
    "btn_segments": True,
    "btn_report": True,
    "btn_reset": True,
    "btn_min": True,
    "autohide_buttons": False,
    "title_bottom": False,
    # window body
    "body_bg": "#2b292d",
    "border_on": True,
    "border_color": "#0c0c0d",
    "click_through": False,
    "click_through_combat": False,
    # statusbar
    "statusbar": False,
    "sb_left": "segment",
    "sb_center": "timer",
    "sb_right": "dps",
    # automation
    "ooc_fade": False,
    "ooc_alpha": 0.4,
    "combat_alpha": 1.0,
    "hover_fade": False,
    "hover_alpha": 0.35,
    "auto_current": True,
    # tooltips
    "tip_enabled": True,
    "tip_font_size": 13,
    "tip_lines": 10,
    "tip_side": "cursor",
    # rename / merge powers
    "renames": {},
    "collapsed": ["@other", "@t1", "@t2", "@t3"],
    "pet_types": {},
    # profiles & skins
    "profiles": {},
    "active_profile": "Default",
    "char_profiles": {},
    "auto_profile": True,
    "skin": "default",
    "custom_skins": {},
    # Mids' Reloaded
    "build_geometry": "",
    "char_builds": {},
    "auto_build": True,
    "build_source": "overall",
    # install / updates
    "game_dir": "",
    "check_updates": True,
    "last_update_check": 0,
}

# Settings that belong to the whole app rather than to a profile.
GLOBAL_KEYS = {"bd_geometry", "recap_geometry", "opt_geometry", "log_path", "logs_dir", "log_auto",
               "load_history", "opt_page", "custom_themes", "renames", "pet_types", "profiles",
               "active_profile", "char_profiles", "auto_profile", "custom_skins",
               "build_geometry", "char_builds", "auto_build", "build_source",
               "game_dir", "check_updates", "last_update_check"}

# Skins = the shape of the meter (sizes, fonts, layout); themes = its colors.
SKIN_KEYS = ["row_height", "font_size", "row_spacing", "row_font", "text_style", "show_icons", "show_rank",
             "row_border", "aligned_cols", "total_bar", "title_height", "title_font_size", "title_bottom",
             "autohide_buttons", "statusbar", "border_on", "grow_up"]
SKINS = {
    "default": {"label": "Default", "row_height": 21, "font_size": 15, "row_spacing": 1, "row_font": "Oswald",
                "text_style": "shadow", "show_icons": True, "show_rank": True, "row_border": False,
                "aligned_cols": False, "total_bar": False, "title_height": 22, "title_font_size": 14,
                "title_bottom": False, "autohide_buttons": False, "statusbar": False, "border_on": True,
                "grow_up": False},
    "compact": {"label": "Compact", "row_height": 16, "font_size": 12, "row_spacing": 0, "row_font": "Oswald",
                "text_style": "shadow", "show_icons": False, "show_rank": True, "row_border": False,
                "aligned_cols": False, "total_bar": False, "title_height": 18, "title_font_size": 12,
                "title_bottom": False, "autohide_buttons": True, "statusbar": False, "border_on": True,
                "grow_up": False},
    "minimal": {"label": "Minimalist", "row_height": 18, "font_size": 13, "row_spacing": 1,
                "row_font": "Segoe UI Semibold", "text_style": "outline", "show_icons": False, "show_rank": False,
                "row_border": True, "aligned_cols": False, "total_bar": False, "title_height": 18,
                "title_font_size": 12, "title_bottom": False, "autohide_buttons": True, "statusbar": False,
                "border_on": True, "grow_up": False},
    "classic": {"label": "Classic Details", "row_height": 22, "font_size": 14, "row_spacing": 1,
                "row_font": "Oswald", "text_style": "shadow", "show_icons": True, "show_rank": True,
                "row_border": False, "aligned_cols": True, "total_bar": True, "title_height": 24,
                "title_font_size": 15, "title_bottom": False, "autohide_buttons": False, "statusbar": True,
                "border_on": True, "grow_up": False},
    "large": {"label": "Large & Bold", "row_height": 28, "font_size": 19, "row_spacing": 2, "row_font": "Oswald",
              "text_style": "outline", "show_icons": True, "show_rank": True, "row_border": False,
              "aligned_cols": False, "total_bar": True, "title_height": 26, "title_font_size": 16,
              "title_bottom": False, "autohide_buttons": False, "statusbar": True, "border_on": True,
              "grow_up": False},
    "hud": {"label": "Bottom HUD", "row_height": 19, "font_size": 14, "row_spacing": 1, "row_font": "Oswald",
            "text_style": "outline", "show_icons": True, "show_rank": False, "row_border": False,
            "aligned_cols": False, "total_bar": False, "title_height": 20, "title_font_size": 13,
            "title_bottom": True, "autohide_buttons": True, "statusbar": False, "border_on": False,
            "grow_up": True},
}


def profile_snapshot(cfg):
    import copy
    return {k: copy.deepcopy(cfg[k]) for k in DEFAULTS if k not in GLOBAL_KEYS and k in cfg}


# --------------------------------------------------------------------------
# Theme (taken from the look of the Details! "Minimalistic" skin)
# --------------------------------------------------------------------------
C = {
    "title": "#1d1c1f", "bg": "#2b292d", "bar_bg": "#232125", "border": "#0c0c0d",
    "text": "#ffffff", "dim": "#a8a4ad", "faint": "#6f6b75", "icon": "#e8e6ea", "icon_hover": "#ffd100",
    "menu_bg": "#19181b", "menu_hover": "#37343c", "menu_head": "#ffd100", "sep": "#34313a",
    "block": "#1f1e22", "block_head": "#2e2b33", "row_alt": "#262428", "sel": "#3d3944",
    "red": "#e2483d", "green": "#3fd06f", "blue": "#4aa8ff", "teal": "#3cc8b4", "gold": "#ffcc33",
    "enemy": "#b8322e",
}
PLAYER_COLOR = "#f0b429"
PET_COLORS = ["#3fc7eb", "#aad372", "#8788ee", "#ff7c0a", "#c41e3a", "#00ff98",
              "#fff468", "#0070dd", "#a330c9", "#33937f", "#f48cba", "#c69b6d"]
DTYPE_COLORS = {"Smashing": "#c9a66b", "Lethal": "#b9bcc2", "Fire": "#ff6a2b", "Cold": "#66c8ff",
                "Energy": "#f2e35c", "Negative Energy": "#9a5bd6", "Psionic": "#ff66cc",
                "Toxic": "#79d45e", "Unique": "#ffffff"}

MODES = [
    ("damage", "Damage Done", "DAMAGE"),
    ("dps", "DPS", "DAMAGE"),
    ("taken", "Damage Taken", "DAMAGE"),
    ("enemies", "Enemy Damage Taken", "DAMAGE"),
    ("abilities", "Damage Taken by Ability", "DAMAGE"),
    ("protect", "Bodyguard Protection", "DAMAGE"),
    ("kills", "Kills", "DAMAGE"),
    ("heal", "Healing Done", "HEAL"),
    ("hps", "HPS", "HEAL"),
    ("healed", "Healing Taken", "HEAL"),
    ("absorb", "Absorbs Granted", "HEAL"),
    ("accuracy", "Accuracy", "MISC"),
    ("defense", "Avoidance", "MISC"),
    ("deaths", "Deaths", "MISC"),
    ("xp", "Experience", "MISC"),
]
MODE_LABEL = {m: l for m, l, _ in MODES}

# glyphs (Segoe Fluent Icons / Segoe MDL2 Assets)
G_OPTIONS, G_SEGMENTS, G_MODE, G_REPORT, G_RESET = "", "", "", "", ""
G_CLOSE, G_MIN, G_PREV, G_NEXT, G_SKULL = "", "", "", "", ""

S = 1.0          # UI scale (monitor DPI x the user's UI scale)
FONT_BASE = {"title": 14, "title_small": 12, "big": 24, "head_big": 18, "head": 13, "ui": 13, "uib": 13,
             "small": 12, "tiny": 10, "icon": 13, "icon_s": 11, "icon_big": 34, "tip": 13}
FONTS = {}


def px(v):
    return max(1, int(round(v * S)))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def hex2rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb2hex(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))


def shade(color, f):
    r, g, b = hex2rgb(color)
    return rgb2hex(r * f, g * f, b * f)


def mix(c1, c2, t):
    a, b = hex2rgb(c1), hex2rgb(c2)
    return rgb2hex(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


_GRAD = {}


def gradient(color, h, bright=1.0):
    """Vertical glossy gradient like the Details! bar texture."""
    key = (color, h, bright)
    g = _GRAD.get(key)
    if g is None:
        r, gg, b = hex2rgb(color)
        g = []
        for y in range(h):
            t = y / max(1, h - 1)
            f = (1.12 - 0.40 * t) * bright
            if y == 0:
                f = 1.40 * bright
            elif y == 1:
                f = 1.22 * bright
            g.append(rgb2hex(r * f, gg * f, b * f))
        _GRAD[key] = g
    return g


COLOR_OPTS = {"mode": "pet", "single": "#3fc7eb", "self_on": False, "self": PLAYER_COLOR, "typer": None}


def actor_color(name, kind):
    o = COLOR_OPTS
    if kind == "player":
        return o["self"] if o["self_on"] else PLAYER_COLOR
    if kind == "enemy":
        return C["enemy"]
    if o["mode"] == "single":
        return o["single"]
    if o["mode"] == "tier" and o["typer"] is not None:
        info = o["typer"].get(name)
        if info and info[1] in TIER_COLORS:
            return TIER_COLORS[info[1]]
        return "#8d8a93"
    return PET_COLORS[sum(ord(c) for c in name) % len(PET_COLORS)]


def bar_lines(color, h, style="gloss", bright=1.0):
    """Line colors (top to bottom) for one bar, in the chosen texture."""
    key = (color, h, bright, style)
    g = _GRAD.get(key)
    if g is not None:
        return g
    if style == "gloss":
        g = gradient(color, h, bright)
    else:
        r, gg, b = hex2rgb(color)
        g = []
        for y in range(h):
            t = y / max(1, h - 1)
            if style == "flat":
                f = 0.95 * bright
            elif style == "smooth":
                f = (1.05 - 0.28 * t) * bright
            elif style == "raised":       # bevel: bright top edge, dark bottom edge
                f = 0.95 * bright
                if y <= 1:
                    f = (1.55 if y == 0 else 1.3) * bright
                elif y >= h - 2:
                    f = (0.42 if y == h - 1 else 0.6) * bright
            elif style == "inset":        # sunken: dark top edge, light bottom edge
                f = 0.8 * bright
                if y <= 1:
                    f = (0.35 if y == 0 else 0.55) * bright
                elif y >= h - 2:
                    f = (1.35 if y == h - 1 else 1.1) * bright
            elif style == "glass":        # shiny upper half, darker lower half
                f = ((1.38 - 0.3 * t * 2) if t < 0.5 else (0.82 - 0.12 * t)) * bright
            elif style == "split":        # two-tone, hard split in the middle
                f = (1.1 if t < 0.5 else 0.78) * bright
            elif style == "outline":
                f = 0.32 * bright
            else:  # dark
                f = (0.62 - 0.12 * t) * bright
                if y == 0:
                    f = 1.0 * bright
            g.append(rgb2hex(r * f, gg * f, b * f))
    _GRAD[key] = g
    return g


def dtype_color(dtype):
    return DTYPE_COLORS.get(dtype or "", "#8d8a93")


class Fmt:
    abbreviate = True
    mode = "short"


def fmt(v):
    if Fmt.mode == "plain":
        return ("%.0f" % v) if abs(v) >= 100 else ("%.1f" % v)
    if Fmt.mode == "full":
        return "{:,.0f}".format(v) if v >= 100 else "{:,.1f}".format(v)
    a = abs(v)
    if a >= 1e6:
        return "%.2fM" % (v / 1e6)
    if a >= 1e4:
        return "%.1fK" % (v / 1e3)
    if a >= 1e3:
        return "%.2fK" % (v / 1e3)
    if a >= 100:
        return "%.0f" % v
    return "%.1f" % v


def fps(v):
    if v >= 1000:
        return fmt(v)
    return "%.1f" % v


def mmss(sec):
    sec = int(max(0, sec))
    return "%02d:%02d" % (sec // 60, sec % 60)


def clock(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))


def truncate(font, text, width):
    if width <= 0:
        return ""
    if font.measure(text) <= width:
        return text
    ell = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.measure(text[:mid] + ell) <= width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ell


def shadow_text(cv, x, y, text, font, fill="#ffffff", anchor="w", tags=()):
    cv.create_text(x + 1, y + 1, text=text, font=font, fill="#000000", anchor=anchor, tags=tags)
    return cv.create_text(x, y, text=text, font=font, fill=fill, anchor=anchor, tags=tags)


# --------------------------------------------------------------------------
# Windows niceties (DPI, private font, taskbar entry for borderless windows)
# --------------------------------------------------------------------------
def win_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


USER_FONT_DIR = os.path.join(DATA_DIR, "fonts")


def load_user_fonts(root):
    """Load every .ttf/.otf in the meter's own fonts folder (private to this app).
    Returns the font family names they added."""
    before = set(tkfont.families(root))
    try:
        for fn in os.listdir(USER_FONT_DIR):
            if fn.lower().endswith((".ttf", ".otf")):
                win_load_font(os.path.join(USER_FONT_DIR, fn))
    except OSError:
        pass
    return set(tkfont.families(root)) - before


def win_load_font(path):
    try:
        return ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0) > 0
    except Exception:
        return False


def win_appwindow(top):
    """Give a borderless (overrideredirect) window a taskbar button."""
    try:
        GWL_EXSTYLE, WS_EX_APPWINDOW, WS_EX_TOOLWINDOW = -20, 0x40000, 0x80
        hwnd = ctypes.windll.user32.GetParent(top.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        top.withdraw()
        top.after(10, top.deiconify)
    except Exception:
        pass


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", _RECT), ("rcWork", _RECT), ("dwFlags", ctypes.c_ulong)]


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def monitor_area(x, y, root=None):
    """Work area (left, top, right, bottom) of the monitor under (x, y)."""
    try:
        u = ctypes.windll.user32
        u.MonitorFromPoint.argtypes = [_POINT, ctypes.c_ulong]
        u.MonitorFromPoint.restype = ctypes.c_void_p
        u.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_MONITORINFO)]
        hmon = u.MonitorFromPoint(_POINT(int(x), int(y)), 2)
        mi = _MONITORINFO()
        mi.cbSize = ctypes.sizeof(_MONITORINFO)
        if hmon and u.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            r = mi.rcWork
            return r.left, r.top, r.right, r.bottom
    except Exception:
        pass
    if root is not None:
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()
    return 0, 0, 1920, 1080


def place_popup(x, y, w, h, root=None, dx=0, dy=0):
    """Top-left for a w*h popup opened at the mouse (x, y), flipped/clamped so it
    is fully visible on the monitor the mouse is on."""
    L, T, R, B = monitor_area(x, y, root)
    nx = x + dx
    if nx + w > R:
        nx = x - w - dx            # not enough room on the right: open to the left
    ny = y + dy
    if ny + h > B:
        ny = y - h - dy            # not enough room below: open upwards
    nx = max(L, min(nx, R - w))
    ny = max(T, min(ny, B - h))
    return int(nx), int(ny)


GAME_EXES = ("cityofheroes.exe",)
_EXE_CACHE = {}


def _u32():
    u = ctypes.windll.user32
    if not getattr(u, "_cohd_ready", False):
        u.GetForegroundWindow.restype = ctypes.c_void_p
        u.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        u.GetParent.restype = ctypes.c_void_p
        u.GetParent.argtypes = [ctypes.c_void_p]
        u.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        u.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        u._cohd_ready = True
    return u


def hwnd_of(top):
    try:
        return _u32().GetParent(top.winfo_id()) or top.winfo_id()
    except Exception:
        return None


def exe_of_hwnd(hwnd):
    try:
        u, k = _u32(), ctypes.windll.kernel32
        pid = ctypes.c_ulong()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        name = _EXE_CACHE.get(pid.value)
        if name is None:
            name = ""
            h = k.OpenProcess(0x1000, False, pid.value)       # PROCESS_QUERY_LIMITED_INFORMATION
            if h:
                buf = ctypes.create_unicode_buffer(520)
                n = ctypes.c_ulong(520)
                if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                    name = os.path.basename(buf.value).lower()
                k.CloseHandle(h)
            if len(_EXE_CACHE) > 200:
                _EXE_CACHE.clear()
            _EXE_CACHE[pid.value] = name
        return name
    except Exception:
        return ""


def game_is_active():
    fg = _u32().GetForegroundWindow()
    return bool(fg) and exe_of_hwnd(fg) in GAME_EXES


def force_topmost(top):
    h = hwnd_of(top)
    if h:
        # HWND_TOPMOST, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER
        _u32().SetWindowPos(h, ctypes.c_void_p(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0200)


def monitor_scale(x, y):
    """Windows display scaling (1.0 = 100%, 1.5 = 150%) of the monitor under (x, y)."""
    try:
        u = ctypes.windll.user32
        u.MonitorFromPoint.argtypes = [_POINT, ctypes.c_ulong]
        u.MonitorFromPoint.restype = ctypes.c_void_p
        hmon = u.MonitorFromPoint(_POINT(int(x), int(y)), 2)
        dx, dy = ctypes.c_uint(), ctypes.c_uint()
        ctypes.windll.shcore.GetDpiForMonitor.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                                          ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
        if ctypes.windll.shcore.GetDpiForMonitor(hmon, 0, ctypes.byref(dx), ctypes.byref(dy)) == 0 and dx.value:
            return dx.value / 96.0
    except Exception:
        pass
    return None


def force_topmost_hwnd(h):
    _u32().SetWindowPos(h, ctypes.c_void_p(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0200 | 0x0400)


def covered_by_game(h):
    """True when a City of Heroes window sits above window h in the z-order."""
    u = _u32()
    u.GetWindow.restype = ctypes.c_void_p
    u.GetWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    u.IsWindowVisible.argtypes = [ctypes.c_void_p]
    p = u.GetWindow(h, 3)                   # GW_HWNDPREV: the window just above
    n = 0
    while p and n < 500:
        if u.IsWindowVisible(p) and exe_of_hwnd(p) in GAME_EXES:
            return True
        p = u.GetWindow(p, 3)
        n += 1
    return False


def set_noactivate(top, on):
    """WS_EX_NOACTIVATE: clicking the window does not take keyboard focus away from the game."""
    try:
        u = _u32()
        h = hwnd_of(top)
        ex = u.GetWindowLongW(h, -20)
        ex = (ex | 0x08000000) if on else (ex & ~0x08000000)
        u.SetWindowLongW(h, -20, ex)
    except Exception:
        pass


def key_down(vk):
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


def set_clickthrough(top, on):
    """WS_EX_TRANSPARENT: mouse clicks pass straight through the window to the game."""
    try:
        u = _u32()
        h = hwnd_of(top)
        ex = u.GetWindowLongW(h, -20)
        ex = (ex | 0x20 | 0x80000) if on else (ex & ~0x20)
        u.SetWindowLongW(h, -20, ex)
    except Exception:
        pass


def game_process_dir():
    """Folder of the running cityofheroes.exe (works whatever launcher or install folder)."""
    hwnd, _t = find_game_window()
    if not hwnd:
        return None
    try:
        u, k = _u32(), ctypes.windll.kernel32
        pid = ctypes.c_ulong()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = k.OpenProcess(0x1000, False, pid.value)
        if not h:
            return None
        buf = ctypes.create_unicode_buffer(1024)
        n = ctypes.c_ulong(1024)
        ok = k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
        k.CloseHandle(h)
        return os.path.dirname(buf.value) if ok else None
    except Exception:
        return None


GAME_FOLDERS = ["Games\\Homecoming", "Homecoming", "Program Files\\Homecoming", "Program Files (x86)\\Homecoming",
                "Games\\City of Heroes", "City of Heroes", "Program Files\\City of Heroes",
                "Program Files (x86)\\City of Heroes", "Games\\CoH", "CoH", "Games\\Homecoming City of Heroes"]


def common_game_dirs():
    """Usual install spots on every local drive (+ user folders)."""
    out = []
    try:
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if not mask & (1 << i):
                continue
            root = "%s:\\" % chr(65 + i)
            if ctypes.windll.kernel32.GetDriveTypeW(root) != 3:       # local fixed disks only
                continue
            for rel in GAME_FOLDERS:
                p = os.path.join(root, rel)
                if os.path.isdir(p):
                    out.append(p)
    except Exception:
        pass
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("USERPROFILE")):
        for rel in ("Homecoming", "Games\\Homecoming", "City of Heroes"):
            if base and os.path.isdir(os.path.join(base, rel)):
                out.append(os.path.join(base, rel))
    return out


def game_root_of(path):
    """Walk up from any folder inside the install to the one that has 'accounts' (or 'bin')."""
    p = os.path.abspath(path or "")
    for _ in range(6):
        if os.path.isdir(os.path.join(p, "accounts")):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return None


def find_game_window():
    """(hwnd, title) of the City of Heroes window, or (None, None)."""
    u = _u32()
    found = []
    proc_t = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    u.IsWindowVisible.argtypes = [ctypes.c_void_p]

    def cb(h, _l):
        if u.IsWindowVisible(h) and exe_of_hwnd(h) in GAME_EXES:
            found.append(h)
            return False
        return True
    try:
        u.EnumWindows(proc_t(cb), 0)
    except Exception:
        return None, None
    if not found:
        return None, None
    buf = ctypes.create_unicode_buffer(256)
    u.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    u.GetWindowTextW(found[0], buf, 256)
    return found[0], buf.value


def send_chat_command(hwnd, text):
    """Bring the game forward and type a slash command into its chat (Enter, text, Enter)."""
    u = _u32()
    u.SetForegroundWindow.argtypes = [ctypes.c_void_p]
    u.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ulong, ctypes.c_void_p]
    try:
        u.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.3)

    def tap(vk, shift=False):
        sc = u.MapVirtualKeyW(vk, 0) & 0xFF
        if shift:
            u.keybd_event(0x10, u.MapVirtualKeyW(0x10, 0) & 0xFF, 0, None)
        u.keybd_event(vk, sc, 0, None)
        time.sleep(0.02)
        u.keybd_event(vk, sc, 2, None)
        if shift:
            u.keybd_event(0x10, u.MapVirtualKeyW(0x10, 0) & 0xFF, 2, None)
        time.sleep(0.03)
    tap(0x0D)
    time.sleep(0.15)
    for ch in text:
        r = u.VkKeyScanW(ord(ch))
        if r == -1:
            continue
        tap(r & 0xFF, bool(r & 0x100))
    time.sleep(0.05)
    tap(0x0D)


def on_wheel(widget, cb):
    widget.bind("<MouseWheel>", lambda e: cb(-1 if e.delta > 0 else 1))


# --------------------------------------------------------------------------
# Data shaping: rows for the main window
# --------------------------------------------------------------------------
class Row:
    __slots__ = ("key", "name", "value", "right", "short", "color", "kind", "glyph", "cols")

    def __init__(self, key, name, value, right, short, color, kind="pet", glyph=None):
        self.key, self.name, self.value, self.right, self.short = key, name, value, right, short
        self.color, self.kind, self.glyph = color, kind, glyph
        self.cols = None


TIER_COLORS = {3: "#a335ee", 2: "#0070dd", 1: "#1eff00"}

# ---------------------------------------------------------------------- themes
BASE_C = dict(C)
BASE_PETS = list(PET_COLORS)
BASE_TIERS = dict(TIER_COLORS)
BASE_PLAYER = PLAYER_COLOR


def _theme(label, texture, player, tiers, pets, **c):
    return {"label": label, "texture": texture, "player": player, "tiers": tiers, "pets": pets, "C": c}


THEMES = {
    "minimal": _theme("Minimalistic (Details)", "gloss", BASE_PLAYER, dict(BASE_TIERS), list(BASE_PETS)),
    "hero": _theme(
        "Hero \u2014 Paragon Blue", "raised", "#ffd34d", {3: "#ffd34d", 2: "#4fa3ff", 1: "#a9d8ff"},
        ["#4fa3ff", "#7ec8ff", "#2f6fd6", "#a9d8ff", "#5ad1c8", "#e8f1ff", "#3b8eea", "#89b4ff", "#1fb6ff",
         "#c3e4ff", "#4f7cff", "#6fe0ff"],
        title="#0f2340", bg="#13223a", bar_bg="#0e1a2d", border="#06101f", dim="#9fb3d1", faint="#5d7397",
        icon="#e6eefc", icon_hover="#ffd34d", menu_bg="#0b1628", menu_hover="#1f3a63", menu_head="#ffd34d",
        sep="#22385c", block="#0f1d33", block_head="#1a3157", row_alt="#12233d", sel="#24467a", gold="#ffd34d"),
    "villain": _theme(
        "Villain \u2014 Arachnos", "glass", "#ff9e00", {3: "#b5179e", 2: "#d7263d", 1: "#ff7a1a"},
        ["#d7263d", "#ff7a1a", "#8f1d2c", "#ff4a3d", "#b5179e", "#f46036", "#7b0d1e", "#ff9e00", "#c1121f",
         "#e85d75", "#9d0208", "#ffba08"],
        title="#1a0505", bg="#1c0d0f", bar_bg="#140809", border="#000000", dim="#c79a9a", faint="#7a5555",
        icon="#f3dede", icon_hover="#ff4a3d", menu_bg="#120606", menu_hover="#3a1215", menu_head="#ff4a3d",
        sep="#3a1a1c", block="#170a0b", block_head="#2c1013", row_alt="#1f0e10", sel="#4a1418", gold="#ff4a3d"),
    "praetorian": _theme(
        "Praetorian \u2014 Steel & Teal", "split", "#3fe0d0", {3: "#ffffff", 2: "#3fe0d0", 1: "#7f97ad"},
        ["#e8edf2", "#3fe0d0", "#9fb4c7", "#62d2ff", "#c9d6e2", "#2bb3a3", "#7f97ad", "#b8f2ec", "#5e7a92",
         "#d8f3ff", "#4fc3b8", "#aebfcf"],
        title="#24292e", bg="#2d3238", bar_bg="#23272c", border="#111316", dim="#b6c2cc", faint="#78848e",
        icon="#eef2f5", icon_hover="#3fe0d0", menu_bg="#1d2125", menu_hover="#3a434c", menu_head="#3fe0d0",
        sep="#3c444c", block="#262b30", block_head="#353c44", row_alt="#2a2f35", sel="#3b4650", gold="#3fe0d0"),
    "rikti": _theme(
        "Rikti \u2014 Alien Green", "inset", "#c6ff7a", {3: "#5cffb0", 2: "#8cff4f", 1: "#1fa35c"},
        ["#8cff4f", "#36d17f", "#c6ff7a", "#1fa35c", "#5cffb0", "#b0e03a", "#0f8a4a", "#7dffc8", "#4ec24e",
         "#d9ff9e", "#2fe08a", "#a0d65a"],
        title="#0c1a12", bg="#101f17", bar_bg="#0b1510", border="#030805", dim="#9cc9a8", faint="#557a62",
        icon="#e3f5e8", icon_hover="#8cff4f", menu_bg="#08120c", menu_hover="#1b3a26", menu_head="#8cff4f",
        sep="#1d3527", block="#0d1912", block_head="#183022", row_alt="#12241a", sel="#23472f", gold="#8cff4f"),
    "shadow": _theme(
        "Shadow \u2014 Midnight Purple", "smooth", "#e0aaff", {3: "#ff77e1", 2: "#c77dff", 1: "#7b2cbf"},
        ["#9d4edd", "#c77dff", "#7b2cbf", "#e0aaff", "#5a189a", "#b5179e", "#8f5cff", "#f3c4fb", "#6a4c93",
         "#d0a2f7", "#4c1d95", "#ff77e1"],
        title="#160f24", bg="#1b1429", bar_bg="#130e1d", border="#07040c", dim="#b7a6d6", faint="#6e5f8c",
        icon="#efe6fb", icon_hover="#c792ff", menu_bg="#110b1b", menu_hover="#2e2248", menu_head="#c792ff",
        sep="#2c2241", block="#171024", block_head="#261c3b", row_alt="#1d1530", sel="#3a2a5c", gold="#c792ff"),
    "phoenix": _theme(
        "Phoenix \u2014 Ember", "glass", "#ffe08a", {3: "#ffd166", 2: "#ff8c1a", 1: "#e63946"},
        ["#ff8c1a", "#ffd166", "#ef476f", "#ff5e00", "#ffb347", "#e63946", "#f4a261", "#ffe08a", "#d62828",
         "#fca311", "#e76f51", "#ffc300"],
        title="#1f1208", bg="#24160b", bar_bg="#1a1007", border="#0a0502", dim="#d9b48c", faint="#8a6a48",
        icon="#fbeee0", icon_hover="#ffb347", menu_bg="#160d05", menu_hover="#3d2510", menu_head="#ffb347",
        sep="#3a2612", block="#1d1209", block_head="#33200e", row_alt="#2a1a0c", sel="#4d2e12", gold="#ffb347"),
    "frost": _theme(
        "Frost \u2014 Ice", "raised", "#e0fbfc", {3: "#e0fbfc", 2: "#5bc0eb", 1: "#0077b6"},
        ["#9be7ff", "#5bc0eb", "#e0fbfc", "#3a86ff", "#a8dadc", "#00b4d8", "#caf0f8", "#48cae4", "#90e0ef",
         "#0077b6", "#b8f3ff", "#4ea8de"],
        title="#0d1b24", bg="#10222d", bar_bg="#0b1820", border="#040a0e", dim="#a9d3e6", faint="#5f8799",
        icon="#e8f7fc", icon_hover="#9be7ff", menu_bg="#08141b", menu_hover="#1b3a4a", menu_head="#9be7ff",
        sep="#1c3644", block="#0d1c25", block_head="#17303d", row_alt="#122733", sel="#22485c", gold="#9be7ff"),
    "neon": _theme(
        "Neon \u2014 Synthwave", "outline", "#fcee0a", {3: "#ff2bd6", 2: "#00f0ff", 1: "#7b2cff"},
        ["#ff2bd6", "#00f0ff", "#fcee0a", "#7b2cff", "#ff6ec7", "#39ff14", "#ff9f1c", "#4d96ff", "#f72585",
         "#4cc9f0", "#b5179e", "#80ffdb"],
        title="#120a1f", bg="#150c24", bar_bg="#0e0718", border="#2b0f45", dim="#c9b3e6", faint="#6d5a8c",
        icon="#f5ecff", icon_hover="#00f0ff", menu_bg="#0d0617", menu_hover="#2d1650", menu_head="#ff2bd6",
        sep="#2b1745", block="#120a20", block_head="#241140", row_alt="#190e2c", sel="#3b1a66", gold="#00f0ff"),
}

BAR_STYLES = [("gloss", "Glossy (Details)"), ("smooth", "Smooth"), ("flat", "Flat"), ("dark", "Dark"),
              ("raised", "Raised edges"), ("inset", "Inset (sunken)"), ("glass", "Glass"),
              ("split", "Split two-tone"), ("outline", "Outline (neon)")]


def theme_copy(t):
    """Full, independent copy of a theme (every window color filled in)."""
    full = dict(BASE_C)
    full.update(t.get("C", {}))
    return {"label": t.get("label", "Custom"), "texture": t.get("texture", "gloss"),
            "player": t.get("player", BASE_PLAYER), "tiers": {int(k): v for k, v in t.get("tiers", BASE_TIERS).items()},
            "pets": (list(t.get("pets", BASE_PETS)) + list(BASE_PETS))[:12], "C": full}


def theme_serialize(t):
    t = theme_copy(t)
    t["tiers"] = {str(k): v for k, v in t["tiers"].items()}
    return t


def load_custom_themes(store):
    """Put the user's saved themes (from the config) into THEMES."""
    for k in [k for k in THEMES if k.startswith("custom:") or k.startswith("__")]:
        del THEMES[k]
    for k, t in (store or {}).items():
        try:
            THEMES[k] = theme_copy(t)
        except Exception:
            pass


def apply_theme_palette(name):
    """Swap the live color tables to a theme. Returns the old window colors (for re-coloring widgets)."""
    global PLAYER_COLOR
    t = THEMES.get(name) or THEMES["minimal"]
    old = dict(C)
    C.clear()
    C.update(BASE_C)
    C.update(t["C"])
    PET_COLORS[:] = t["pets"]
    TIER_COLORS.clear()
    TIER_COLORS.update(t["tiers"])
    PLAYER_COLOR = t["player"]
    _GRAD.clear()
    return old


def recolor(w, mapping):
    """Walk a widget tree and swap old theme colors for new ones."""
    for opt in ("bg", "fg", "activebackground", "activeforeground", "selectcolor", "highlightbackground",
                "insertbackground", "troughcolor"):
        try:
            v = str(w.cget(opt)).lower()
            if v in mapping:
                w.configure(**{opt: mapping[v]})
        except Exception:
            pass
    for ch in w.winfo_children():
        recolor(ch, mapping)
FRIENDLY_MODES = {"damage", "dps", "taken", "heal", "hps", "healed", "absorb", "protect", "kills",
                  "accuracy", "defense", "xp"}
GROUPINGS = [
    ("Show every pet", []),
    ("Group pets by tier", ["@other", "@t1", "@t2", "@t3"]),
    ("Group all pets together", ["@pets"]),
    ("Merge everything (you + pets)", ["@all"]),
]


def group_nodes(app, seg):
    """Builds the collapse tree:  @all -> [you, @pets];  @pets -> [@hench, @other];
    @hench -> [@t3, @t2, @t1];  @tN -> that tier's pets;  @other -> non-henchman pets."""
    nodes, parents, ranks = {}, {}, {}
    if seg is None:
        return nodes, parents, ranks
    typer = app.parser.typer
    player = None
    tiers = {3: [], 2: [], 1: []}
    other = []
    for a in seg.actors.values():
        if a.kind == "player":
            player = a
            continue
        info = typer.get(a.name)
        if info and info[1] in tiers:
            tiers[info[1]].append(a)
        else:
            other.append(a)

    def tname(m):
        i = typer.get(m.name)
        return i[0] if i else m.name

    def counted(label, n):
        return label if n == 1 else "%s \u00d7%d" % (label, n)

    def leaf(a, rank):
        nodes[a.name] = {"name": a.name, "color": actor_color(a.name, a.kind), "children": None,
                         "actor": a, "kind": a.kind, "members": [a.name]}
        ranks[a.name] = rank
        return a.name

    def group(key, name, color, child_keys, members, prefix, rank):
        act = cp.Actor(key, "group")
        for m in members:
            act.merge_from(m, prefix(m))
        nodes[key] = {"name": name, "color": color, "children": child_keys, "actor": act, "kind": "group",
                      "members": [m.name for m in members]}
        ranks[key] = rank
        for c in child_keys:
            parents[c] = key
        return key

    hench_keys, hench_members = [], []
    for t in (3, 2, 1):
        ms = tiers[t]
        if not ms:
            continue
        rank = 4 - t
        ks = [leaf(m, rank) for m in ms]
        types = sorted(set(tname(m) for m in ms))
        label = types[0] if len(types) == 1 else "Tier %d" % t
        hench_keys.append(group("@t%d" % t, counted(label, len(ms)), TIER_COLORS[t], ks, ms, lambda m: "", rank))
        hench_members += ms
    pet_keys, pet_members = [], []
    if hench_keys:
        pet_keys.append(group("@hench", counted("Henchmen", len(hench_members)), "#c79c6e", hench_keys,
                              hench_members, lambda m: tname(m) + ": ", 1))
        pet_members += hench_members
    if other:
        ks = [leaf(m, 5) for m in other]
        pet_keys.append(group("@other", counted("Other Pets", len(other)), "#8d8a93", ks, other,
                              lambda m: m.name + ": ", 5))
        pet_members += other
    top = []
    if player is not None:
        top.append(leaf(player, 0))
    if pet_keys:
        top.append(group("@pets", counted("All Pets", len(pet_members)), "#3fc7eb", pet_keys, pet_members,
                         lambda m: tname(m) + ": ", 1))
    if top:
        everyone = ([player] if player is not None else []) + pet_members
        pname = player.name if player is not None else app.parser.player
        group("@all", ("%s + Pets" % pname) if pet_members else pname, PLAYER_COLOR, top, everyone,
              lambda m: "" if m.kind == "player" else tname(m) + ": ", 0)
    return nodes, parents, ranks


def actor_view(app, seg, which="rows"):
    """rows: what the meter shows with the current collapse state;
    all: every node (pets + groups);  leaves: just the real combatants."""
    nodes, parents, ranks = group_nodes(app, seg)
    app.nodes, app.parents, app.ranks = nodes, parents, ranks
    if seg is None:
        return {}
    if which == "leaves":
        return dict(seg.actors)
    if which == "all":
        return {k: n["actor"] for k, n in nodes.items()}
    out = {}

    def emit(k):
        n = nodes[k]
        if n["children"] and k not in app.collapsed:
            for c in n["children"]:
                emit(c)
        else:
            out[k] = n["actor"]
    if "@all" in nodes:
        emit("@all")
    return out


def taken_by_ability(actors):
    agg = {}
    for a in actors.values():
        for (src, power), s in a.taken_by.items():
            st = agg.get(power)
            if st is None:
                st = agg[power] = cp.Stat()
            st.merge(s)
            st.sources[src] = st.sources.get(src, 0.0) + s.total
            st.targets[a.name] = st.targets.get(a.name, 0.0) + s.total
    return agg


def adur(app, a, seg_dur):
    """Seconds used for per-second numbers: the whole fight, or only this actor's active time."""
    if app.cfg["time_measure"] == "active" and getattr(a, "active", 0) > 0:
        return max(1.0, min(a.active, seg_dur))
    return seg_dur


def realtime(app, a, window=5.0):
    now = app.parser.last_line_ts or time.time()
    return sum(x for t, x in a.recent if t >= now - window) / window


def rparts(app, main, extras):
    """Right-hand bar text, honoring the Show total / per second / percent and bracket options."""
    c = app.cfg
    keys = {"total": "rt_total", "ps": "rt_ps", "pct": "rt_pct"}
    parts = [v for k, v in extras if c.get(keys[k], True)]
    cols = [main] + parts
    if not parts:
        return main, cols
    o, cl = {"(": ("(", ")"), "[": ("[", "]")}.get(c.get("bracket"), ("", ""))
    sep = ", " if o else "   "
    return "%s %s%s%s" % (main, o, sep.join(parts), cl), cols


def build_rows(app, seg, mode=None):
    mode = mode or app.cfg["mode"]
    rows = []
    if seg is None:
        return rows
    dur = seg.duration()
    actors = actor_view(app, seg, "rows")

    def friendly(a, value, right, short, cols=None):
        _friendly(a, value, right, short)
        if rows:
            rows[-1].cols = cols

    def _friendly(a, value, right, short):
        node = app.nodes.get(a.name)
        if node is not None and node["kind"] == "group":
            r = Row(a.name, node["name"], value, right, short, node["color"], "group")
            r.glyph = ("T" + a.name[2]) if a.name.startswith("@t") else "\u03a3"
            rows.append(r)
            return
        shown = a.name
        info = app.parser.typer.get(a.name) if a.kind == "pet" else None
        if info and app.cfg["show_pet_type"]:
            shown = "%s (%s)" % (a.name, info[0])
        r = Row(a.name, shown, value, right, short, actor_color(a.name, a.kind), a.kind)
        if info and info[1]:
            r.glyph = "T%d" % info[1]
        rows.append(r)

    if mode in ("damage", "dps", "taken", "heal", "hps", "healed", "absorb", "protect"):
        attr = {"damage": "damage", "dps": "damage", "taken": "taken", "heal": "heal", "hps": "heal",
                "healed": "healed", "absorb": "absorb", "protect": "protect"}[mode]
        total = sum(getattr(a, attr) for a in actors.values()) or 1.0
        for a in actors.values():
            v = getattr(a, attr)
            if v <= 0:
                continue
            pct = 100.0 * v / total
            d_a = adur(app, a, dur)
            if mode in ("dps", "hps"):
                ps = v / d_a
                if mode == "dps" and app.cfg["realtime_dps"] and seg is app.parser.current:
                    ps = realtime(app, a)
                txt, cols = rparts(app, fps(ps), [("total", fmt(v)), ("pct", "%.1f%%" % pct)])
                friendly(a, ps, txt, fps(ps), cols)
            elif mode == "protect":
                friendly(a, v, "%s (%d hits)" % (fmt(v), a.protect_n), fmt(v))
            else:
                txt, cols = rparts(app, fmt(v), [("ps", fps(v / d_a)), ("pct", "%.1f%%" % pct)])
                friendly(a, v, txt, fmt(v), cols)
    elif mode == "enemies":
        total = sum(e.received for e in seg.enemies.values()) or 1.0
        for e in seg.enemies.values():
            if e.received > 0:
                rows.append(Row(e.name, e.name, e.received, "%s (%.1f%%)" % (fmt(e.received), 100 * e.received / total),
                                fmt(e.received), C["enemy"], "enemy"))
    elif mode == "abilities":
        agg = taken_by_ability(actor_view(app, seg, "leaves"))
        total = sum(s.total for s in agg.values()) or 1.0
        for power, s in agg.items():
            if s.total > 0:
                rows.append(Row(power, power, s.total, "%s (%.1f%%)" % (fmt(s.total), 100 * s.total / total),
                                fmt(s.total), dtype_color(s.top_dtype), "ability"))
    elif mode == "kills":
        for a in actors.values():
            n = a.kill_count
            if n:
                friendly(a, n, str(n), str(n))
    elif mode == "accuracy":
        for a in actors.values():
            if a.rolls:
                p = 100.0 * a.roll_hits / a.rolls
                friendly(a, p, "%.1f%% (%d/%d)" % (p, a.roll_hits, a.rolls), "%.1f%%" % p)
    elif mode == "defense":
        for a in actors.values():
            if a.def_rolls:
                p = 100.0 * a.def_miss / a.def_rolls
                friendly(a, p, "%.1f%% dodged (%d/%d)" % (p, a.def_miss, a.def_rolls), "%.1f%%" % p)
    elif mode == "xp":
        for a in actors.values():
            if a.xp > 0:
                friendly(a, a.xp, "%s (%s/min)" % (fmt(a.xp), fmt(a.xp * 60 / dur)), fmt(a.xp))
    elif mode == "deaths":
        all_deaths = app.parser.deaths
        for d in reversed(seg.deaths):
            idx = all_deaths.index(d) if d in all_deaths else -1
            killer = d.killer or ("Manual recap" if d.manual else "Unknown")
            rows.append(Row(idx, "%s  %s" % (clock(d.ts), d.victim), 1.0, killer, killer, "#8e1f1f", "death", G_SKULL))
        return rows
    if app.cfg["tier_order"] and mode in FRIENDLY_MODES:
        rows.sort(key=lambda r: (app.ranks.get(r.key, 9), -r.value))
    else:
        rows.sort(key=lambda r: -r.value)
    return rows


# --------------------------------------------------------------------------
# Breakdown data
# --------------------------------------------------------------------------
class BD:
    """Everything the breakdown window needs to draw one actor/enemy/ability."""

    def __init__(self):
        self.title = ""
        self.color = "#888888"
        self.kind = "pet"
        self.summary = []        # [(label, value)]
        self.preset = "damage"
        self.per = "DPS"
        self.total = 1.0
        self.dur = 1.0
        self.tabs = []           # [(label, 'stats'|'list', data)]
        self.members = []


def build_breakdown(app, seg, mode, key):
    if seg is None:
        return None
    bd = BD()
    dur = bd.dur = seg.duration()
    actors = actor_view(app, seg, "leaves" if mode == "abilities" else "all")

    def stats_items(d, color_by_dtype=True, label=None):
        out = []
        for k, s in d.items():
            name = label(k) if label else k
            out.append((k, name, s, dtype_color(s.top_dtype) if color_by_dtype else C["green"]))
        return out

    def target_list(stats, which="targets"):
        agg = {}
        for s in stats:
            for t, v in getattr(s, which).items():
                agg[t] = agg.get(t, 0.0) + v
        return [(t, v, actor_color(t, "pet") if t in actors else C["enemy"]) for t, v in agg.items()]

    if mode in ("damage", "dps", "accuracy", "kills", "xp", "protect", "taken", "defense",
                "heal", "hps", "healed", "absorb"):
        a = actors.get(key)
        if a is None:
            return None
        bd.title, bd.color, bd.kind = a.name, actor_color(a.name, a.kind), a.kind
        if app.cfg["time_measure"] == "active" and getattr(a, "active", 0) > 0:
            dur = bd.dur = max(1.0, min(a.active, dur))
        node = app.nodes.get(key)
        if node is not None and node["kind"] == "group":
            bd.title, bd.color, bd.kind = node["name"], node["color"], "group"
            bd.members = node["members"]
        if mode in ("damage", "dps"):
            bd.total = a.damage or 1.0
            bd.summary = [("Damage", fmt(a.damage)), ("DPS", fps(a.damage / dur)),
                          ("Accuracy", "%.1f%%" % (100.0 * a.roll_hits / a.rolls) if a.rolls else "-"),
                          ("Kills", str(a.kill_count))]
            bd.tabs = [("Powers", "stats", stats_items(a.powers)),
                       ("Targets", "list", target_list(a.powers.values()))]
        elif mode in ("taken", "defense"):
            bd.total = a.taken or 1.0
            bd.preset = "taken" if mode == "taken" else "avoid"
            dodge = "%.1f%%" % (100.0 * a.def_miss / a.def_rolls) if a.def_rolls else "-"
            bd.summary = [("Damage Taken", fmt(a.taken)), ("Per Second", fps(a.taken / dur)),
                          ("Dodged", dodge), ("Healed", fmt(a.healed))]
            items = stats_items(a.taken_by, label=lambda k: "%s  •  %s" % (k[1], k[0]))
            if mode == "defense":
                items = [i for i in items if i[2].rolls]
            src = {}
            for (s_name, _p), s in a.taken_by.items():
                src[s_name] = src.get(s_name, 0.0) + s.total
            bd.tabs = [("Enemy Powers", "stats", items),
                       ("Enemies", "list", [(k, v, C["enemy"]) for k, v in src.items()])]
        elif mode in ("heal", "hps"):
            bd.total = a.heal or 1.0
            bd.preset, bd.per = "heal", "HPS"
            bd.summary = [("Healing", fmt(a.heal)), ("HPS", fps(a.heal / dur)),
                          ("Absorbs", fmt(a.absorb)), ("Healed", fmt(a.healed))]
            bd.tabs = [("Powers", "stats", stats_items(a.heal_powers, False)),
                       ("Targets", "list", target_list(a.heal_powers.values()))]
        elif mode == "healed":
            bd.total = a.healed or 1.0
            bd.preset, bd.per = "heal", "HPS"
            bd.summary = [("Healing Taken", fmt(a.healed)), ("Per Second", fps(a.healed / dur)),
                          ("Absorbed", fmt(a.absorbed)), ("Damage Taken", fmt(a.taken))]
            items = stats_items(a.healed_by, False, label=lambda k: "%s  •  %s" % (k[1], k[0]))
            src = {}
            for (s_name, _p), s in a.healed_by.items():
                src[s_name] = src.get(s_name, 0.0) + s.total
            bd.tabs = [("Powers", "stats", items),
                       ("Healers", "list", [(k, v, PLAYER_COLOR if k == app.parser.player else C["green"])
                                            for k, v in src.items()])]
        elif mode == "absorb":
            bd.total = a.absorb or 1.0
            bd.preset, bd.per = "heal", "Per Sec"
            bd.summary = [("Absorbs", fmt(a.absorb)), ("Per Second", fps(a.absorb / dur)),
                          ("Healing", fmt(a.heal)), ("", "")]
            bd.tabs = [("Powers", "stats", stats_items(a.absorb_powers, False)),
                       ("Targets", "list", target_list(a.absorb_powers.values()))]
        elif mode == "accuracy":
            bd.preset = "accuracy"
            bd.total = a.damage or 1.0
            bd.summary = [("Accuracy", "%.1f%%" % (100.0 * a.roll_hits / a.rolls) if a.rolls else "-"),
                          ("Attack Rolls", str(a.rolls)), ("Misses", str(a.rolls - a.roll_hits)),
                          ("Avg To-Hit", "%.1f%%" % (a.chance_sum / a.chance_n) if a.chance_n else "-")]
            bd.tabs = [("Powers", "stats", [i for i in stats_items(a.powers) if i[2].rolls])]
        elif mode == "kills":
            bd.summary = [("Kills", str(a.kill_count)), ("Damage", fmt(a.damage)), ("", ""), ("", "")]
            bd.tabs = [("Defeated", "list", [(k, float(v), C["enemy"]) for k, v in a.kills.items()])]
        elif mode == "protect":
            bd.summary = [("Protected", fmt(a.protect)), ("Redirects", str(a.protect_n)),
                          ("Damage Taken", fmt(a.taken)), ("", "")]
            pets = [(x.name, x.taken, actor_color(x.name, x.kind)) for x in seg.actors.values()
                    if x.kind == "pet" and x.taken > 0]
            bd.tabs = [("Pets Took Damage", "list", pets)]
        elif mode == "xp":
            bd.summary = [("Experience", fmt(a.xp)), ("Per Minute", fmt(a.xp * 60 / dur)),
                          ("Kills", str(a.kill_count)), ("", "")]
            bd.tabs = [("Defeated", "list", [(k, float(v), C["enemy"]) for k, v in a.kills.items()])]
        return bd

    if mode == "enemies":
        e = seg.enemies.get(key)
        if e is None:
            return None
        bd.title, bd.color, bd.kind = e.name, C["enemy"], "enemy"
        bd.total = e.received or 1.0
        bd.summary = [("Damage Received", fmt(e.received)), ("Per Second", fps(e.received / dur)),
                      ("Damage Dealt", fmt(e.dealt)), ("Defeated", str(e.kills))]
        by_actor = {}
        for (who, _p), s in e.received_by.items():
            by_actor[who] = by_actor.get(who, 0.0) + s.total
        player = app.parser.player
        bd.tabs = [("Hit By", "stats", stats_items(e.received_by, label=lambda k: "%s  •  %s" % (k[0], k[1]))),
                   ("Attackers", "list", [(k, v, actor_color(k, "player" if k == player else "pet"))
                                          for k, v in by_actor.items()]),
                   ("Its Powers", "stats", stats_items(e.dealt_by))]
        bd.preset = "damage"
        return bd

    if mode == "abilities":
        agg = taken_by_ability(actors)
        s = agg.get(key)
        if s is None:
            return None
        bd.title, bd.color, bd.kind = key, dtype_color(s.top_dtype), "ability"
        bd.total = s.total or 1.0
        bd.preset = "taken"
        bd.summary = [("Damage", fmt(s.total)), ("Hits", str(s.count)),
                      ("Dodged", "%.1f%%" % (100.0 * s.roll_miss / s.rolls) if s.rolls else "-"),
                      ("Type", s.top_dtype or "-")]
        per_src = {}
        for a in actors.values():
            for (src, power), st in a.taken_by.items():
                if power == key:
                    x = per_src.get(src)
                    if x is None:
                        x = per_src[src] = cp.Stat()
                    x.merge(st)
                    x.targets[a.name] = x.targets.get(a.name, 0.0) + st.total
        bd.tabs = [("By Enemy", "stats", stats_items(per_src)),
                   ("Victims", "list", [(k, v, actor_color(k, "pet")) for k, v in s.targets.items()])]
        return bd
    return None


# --------------------------------------------------------------------------
# Popup menu (dark, Details-like)
# --------------------------------------------------------------------------
class DMenu:
    current = None

    def __init__(self, app, x, y, items, min_width=170):
        if DMenu.current:
            DMenu.current.close()
        DMenu.current = self
        self.app = app
        self.items = items
        self.top = t = tk.Toplevel(app.root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.configure(bg=C["sep"])
        f, fr = FONTS["ui"], FONTS["small"]
        self.ih = px(22)
        self.hh = px(20)
        w = px(min_width)
        for it in items:
            lw = f.measure(it.get("label", "")) + px(44)
            if it.get("right"):
                lw += fr.measure(it["right"]) + px(18)
            w = max(w, lw)
        h = 0
        for it in items:
            h += px(7) if it.get("sep") else (self.hh if it.get("header") else self.ih)
        self.cv = cv = tk.Canvas(t, width=w, height=h, bg=C["menu_bg"], highlightthickness=0, bd=0)
        cv.pack(padx=1, pady=1)
        x, y = place_popup(x, y, w + 2, h + 2, app.root, dx=2, dy=2)
        t.geometry("+%d+%d" % (x, y))
        self.w = w
        self.slots = []
        self.hover = -1
        self.draw()
        cv.bind("<Motion>", self._motion)
        cv.bind("<Leave>", lambda e: self._set_hover(-1))
        cv.bind("<Button-1>", self._click)
        t.bind("<Escape>", lambda e: self.close())
        t.bind("<FocusOut>", lambda e: t.after(80, self._maybe_close))
        t.after(30, t.focus_force)
        # close when the mouse is clicked anywhere outside the menu (any app, any button)
        self._prev = self._buttons()
        t.after(40, self._watch)

    @staticmethod
    def _buttons():
        try:
            state = ctypes.windll.user32.GetAsyncKeyState
            return tuple(bool(state(vk) & 0x8000) for vk in (0x01, 0x02, 0x04))   # left, right, middle
        except Exception:
            return (False, False, False)

    def _watch(self):
        if DMenu.current is not self:
            return
        try:
            now = self._buttons()
            new_press = any(n and not p for n, p in zip(now, self._prev))
            self._prev = now
            if new_press:
                mx, my = self.top.winfo_pointerxy()
                x, y = self.top.winfo_rootx(), self.top.winfo_rooty()
                w, h = self.top.winfo_width(), self.top.winfo_height()
                if not (x <= mx < x + w and y <= my < y + h):
                    self.close()
                    return
            self.top.after(40, self._watch)
        except Exception:
            self.close()

    def draw(self):
        cv, f, fr = self.cv, FONTS["ui"], FONTS["small"]
        cv.delete("all")
        self.slots = []
        y = 0
        for i, it in enumerate(self.items):
            if it.get("sep"):
                cv.create_line(px(8), y + px(3), self.w - px(8), y + px(3), fill=C["sep"])
                y += px(7)
                continue
            if it.get("header"):
                cv.create_text(px(10), y + self.hh // 2, text=it["label"], font=FONTS["head"],
                               fill=C["menu_head"], anchor="w")
                y += self.hh
                continue
            h = self.ih
            if i == self.hover and not it.get("disabled"):
                cv.create_rectangle(1, y, self.w - 1, y + h, fill=C["menu_hover"], width=0)
            if it.get("check"):
                cv.create_text(px(14), y + h // 2, text="", font=FONTS["icon"], fill=C["gold"])
            color = C["faint"] if it.get("disabled") else it.get("color", C["text"])
            cv.create_text(px(28), y + h // 2, text=it["label"], font=f, fill=color, anchor="w")
            if it.get("right"):
                cv.create_text(self.w - px(10), y + h // 2, text=it["right"], font=fr, fill=C["dim"], anchor="e")
            self.slots.append((y, y + h, i))
            y += h

    def _index(self, y):
        for a, b, i in self.slots:
            if a <= y < b:
                return i
        return -1

    def _set_hover(self, i):
        if i != self.hover:
            self.hover = i
            self.draw()

    def _motion(self, e):
        self._set_hover(self._index(e.y))

    def _click(self, e):
        i = self._index(e.y)
        if i < 0:
            return
        it = self.items[i]
        if it.get("disabled"):
            return
        self.close()
        cb = it.get("cmd")
        if cb:
            self.app.root.after(1, cb)

    def _maybe_close(self):
        try:
            if self.top.focus_displayof() is None:
                self.close()
        except Exception:
            self.close()

    def close(self):
        if DMenu.current is self:
            DMenu.current = None
        try:
            self.top.destroy()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Tooltip (hover a bar)
# --------------------------------------------------------------------------
class Tip:
    def __init__(self, app):
        self.app = app
        self.top = None
        self.key = None

    def show(self, mx, my, title, color, lines, key):
        if DMenu.current:
            return
        if self.top is None:
            self.top = tk.Toplevel(self.app.root)
            self.top.overrideredirect(True)
            self.top.attributes("-topmost", True)
            self.top.configure(bg=C["border"])
            self.cv = tk.Canvas(self.top, bg=C["menu_bg"], highlightthickness=0, bd=0)
            self.cv.pack(padx=1, pady=1)
        self.key = key
        cv = self.cv
        cv.delete("all")
        f, fs, fh = FONTS["tip"], FONTS["small"], FONTS["uib"]
        lh = max(px(19), f.metrics("linespace") + px(3))
        w = px(250)
        for l, r, _f, _c in lines:
            w = max(w, f.measure(l) + fs.measure(r) + px(40))
        h = px(26) + lh * max(1, len(lines)) + px(6)
        cv.configure(width=w, height=h)
        cv.create_rectangle(0, 0, w, px(24), fill=C["block_head"], width=0)
        cv.create_rectangle(0, 0, px(4), px(24), fill=color, width=0)
        cv.create_text(px(10), px(12), text=title, font=fh, fill=C["text"], anchor="w")
        y = px(28)
        if not lines:
            cv.create_text(px(10), y + lh // 2, text="No details", font=fs, fill=C["dim"], anchor="w")
        for l, r, frac, c in lines:
            bw = int((w - px(12)) * max(0.0, min(1.0, frac)))
            cv.create_rectangle(px(6), y + 1, px(6) + bw, y + lh - 2, fill=shade(c, 0.38), width=0)
            cv.create_text(px(10), y + lh // 2, text=truncate(f, l, w - fs.measure(r) - px(30)),
                           font=f, fill=C["text"], anchor="w")
            cv.create_text(w - px(10), y + lh // 2, text=r, font=fs, fill=C["text"], anchor="e")
            y += lh
        if self.app.cfg["tip_side"] == "window":
            mt = self.app.main.top
            right_edge = mt.winfo_rootx() + mt.winfo_width()
            x, y = place_popup(right_edge, my - h // 2, w + 2, h + 2, self.app.root, dx=px(6), dy=0)
            if x < right_edge:          # no room on the right: put it on the left of the meter
                x = max(0, mt.winfo_rootx() - w - px(8))
        else:
            x, y = place_popup(mx, my, w + 2, h + 2, self.app.root, dx=px(18), dy=px(10))
        self.top.geometry("+%d+%d" % (x, y))
        self.top.deiconify()

    def move(self, x, y):
        pass

    def hide(self):
        self.key = None
        if self.top is not None:
            self.top.withdraw()


# --------------------------------------------------------------------------
# Base dark borderless window
# --------------------------------------------------------------------------
class DarkWin:
    def __init__(self, app, title, geom_key, default_geom, toplevel=None, min_size=(160, 70)):
        self.app = app
        self.geom_key = geom_key
        self.title = title
        self._min_base = min_size
        self.min_size = (px(min_size[0]), px(min_size[1]))
        self.top = t = toplevel if toplevel is not None else tk.Toplevel(app.root)
        t.overrideredirect(True)
        t.configure(bg=C["border"])
        t.title(title)
        geom = app.cfg.get(geom_key) or default_geom
        t.geometry(geom)
        self.th = px(self._th_base())
        self.tb = tk.Canvas(t, height=self.th, bg=C["title"], highlightthickness=0, bd=0)
        self.tb.pack(side="top", fill="x", padx=1, pady=(1, 0))
        self.body = tk.Frame(t, bg=C["bg"], bd=0, highlightthickness=0)
        self.body.pack(side="top", fill="both", expand=True, padx=1, pady=(0, 1))
        self.left_buttons = []
        self.right_buttons = []
        self.title_right = ""
        self.title_menu = None          # callback(x, y) for right-clicking the title word
        self._shown = False
        self.tb.bind("<Button-3>", self._title_rclick)
        self._btn_hover = None
        self.tb.bind("<ButtonPress-1>", self._drag_start)
        self.tb.bind("<B1-Motion>", self._drag_move)
        self.tb.bind("<ButtonRelease-1>", self._drag_end)
        self.tb.bind("<Configure>", lambda e: self.draw_title())
        gs = px(13)
        self.grip = tk.Canvas(t, width=gs, height=gs, bg=C["bg"], highlightthickness=0, bd=0, cursor="size_nw_se")
        self._draw_grip()
        self.grip.place(relx=1.0, rely=1.0, anchor="se", x=-1, y=-1)
        self.grip.bind("<ButtonPress-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_move)
        self.grip.bind("<ButtonRelease-1>", lambda e: self.save_geom())
        t.attributes("-topmost", bool(app.cfg["topmost"]))
        self.apply_alpha()

    def _th_base(self):
        return int(self.app.cfg.get("title_height", 22)) if getattr(self, "IS_MAIN", False) else 22

    def _visible_right(self):
        if (getattr(self, "IS_MAIN", False) and self.app.cfg.get("autohide_buttons")
                and not getattr(self, "_hovering", False)):
            return []
        return self.right_buttons

    def _draw_grip(self):
        gs = px(13)
        self.grip.configure(width=gs, height=gs)
        self.grip.delete("all")
        for i in range(3):
            o = px(3) + i * px(3)
            self.grip.create_line(gs - 2, o, o, gs - 2, fill=C["faint"])

    def rescale(self):
        self.min_size = (px(self._min_base[0]), px(self._min_base[1]))
        self.th = px(self._th_base())
        self.tb.configure(height=self.th)
        self._draw_grip()
        self.draw_title()
        self.after_rescale()

    def after_rescale(self):
        pass

    def _drag_end(self, e):
        self._drag = None
        self.save_geom()
        if self is getattr(self.app, "main", None):
            self.app.check_monitor()

    def apply_alpha(self):
        try:
            self.top.attributes("-alpha", float(self.app.cfg["alpha"]))
        except Exception:
            pass

    # --- title bar ---------------------------------------------------------
    def draw_title(self):
        tb = self.tb
        tb.delete("all")
        w = tb.winfo_width()
        h = self.th
        tb.create_rectangle(0, h - 1, w, h, fill="#000000", width=0)
        x = px(6)
        bw = px(22)
        for i, (g, cb, tip) in enumerate(self.left_buttons):
            tag = "btnL%d" % i
            col = C["icon_hover"] if self._btn_hover == tag else C["icon"]
            tb.create_text(x + bw // 2, h // 2, text=g, font=FONTS["icon"], fill=col, tags=("btn", tag))
            tb.create_rectangle(x, 0, x + bw, h, outline="", fill="", tags=("btn", tag))
            self._bind_btn(tag, cb)
            x += bw
        if self.left_buttons:
            x += px(4)
        xr = w - px(4)
        for i, (g, cb, tip) in enumerate(self._visible_right()):
            tag = "btnR%d" % i
            window_ctl = g in (G_CLOSE, G_MIN)
            if self._btn_hover == tag:
                col = C["red"] if g == G_CLOSE else C["icon_hover"]
            else:
                col = C["dim"] if window_ctl else C["icon"]
            tb.create_text(xr - bw // 2, h // 2, text=g, font=FONTS["icon_s" if window_ctl else "icon"], fill=col,
                           tags=("btn", tag))
            tb.create_rectangle(xr - bw, 0, xr, h, outline="", fill="", tags=("btn", tag))
            self._bind_btn(tag, cb)
            xr -= bw
            if g == G_MIN and i + 1 < len(self._visible_right()):
                xr -= px(6)             # small gap between the tools and the window controls
        right = self.title_right
        if right:
            tid = tb.create_text(xr - px(4), h // 2, text=right, font=FONTS["title_small"], fill=C["dim"], anchor="e")
            xr = tb.bbox(tid)[0] - px(6)
        text = self.title
        if self.title_menu is not None:
            text += "  \u25be"
        hot = self._btn_hover == "titleword"
        tb.create_text(x, h // 2 + 1, text=truncate(FONTS["title"], text, xr - x), font=FONTS["title"],
                       fill=C["icon_hover"] if hot else C["text"], anchor="w", tags=("titleword",))
        if self.title_menu is not None:
            tb.tag_bind("titleword", "<Enter>", lambda e: self._hover_btn("titleword"))
            tb.tag_bind("titleword", "<Leave>", lambda e: self._hover_btn(None))

    def _bind_btn(self, tag, cb):
        tb = self.tb
        tb.tag_bind(tag, "<Enter>", lambda e, t=tag: self._hover_btn(t))
        tb.tag_bind(tag, "<Leave>", lambda e: self._hover_btn(None))
        tb.tag_bind(tag, "<Button-1>", lambda e, c=cb, t=tag: self._click_btn(e, c, t))

    def _hover_btn(self, tag):
        if tag != self._btn_hover:
            self._btn_hover = tag
            self.draw_title()

    def _click_btn(self, e, cb, tag):
        cb(e.x_root, e.y_root)          # menus open right at the mouse

    def _title_rclick(self, e):
        if self.title_menu is not None and not self._on_btn():
            self.title_menu(e.x_root, e.y_root)

    def _on_btn(self):
        cur = self.tb.find_withtag("current")
        return bool(cur) and "btn" in self.tb.gettags(cur[0])

    def _drag_start(self, e):
        self._drag = None if self._on_btn() else (e.x_root - self.top.winfo_x(), e.y_root - self.top.winfo_y())

    def _drag_move(self, e):
        if getattr(self, "_drag", None):
            dx, dy = self._drag
            self.top.geometry("+%d+%d" % (e.x_root - dx, e.y_root - dy))

    def _resize_start(self, e):
        self._rs = (e.x_root, e.y_root, self.top.winfo_width(), self.top.winfo_height())

    def _resize_move(self, e):
        x0, y0, w0, h0 = self._rs
        w = max(self.min_size[0], w0 + e.x_root - x0)
        h = max(self.min_size[1], h0 + e.y_root - y0)
        self.top.geometry("%dx%d" % (w, h))

    def save_geom(self):
        try:
            self.app.cfg[self.geom_key] = "%dx%d+%d+%d" % (self.top.winfo_width(), self.top.winfo_height(),
                                                         self.top.winfo_x(), self.top.winfo_y())
            self.app.save_cfg()
        except Exception:
            pass

    def _size(self):
        import re
        m = re.match(r"(\d+)x(\d+)", self.top.geometry())
        w, h = (int(m.group(1)), int(m.group(2))) if m else (px(600), px(450))
        if w < 50 or h < 50:
            w, h = px(600), px(450)
        return w, h

    def place_near(self, anchor):
        """Put this window right beside the anchor window (the meter), on the same monitor."""
        a = anchor.top
        a.update_idletasks()
        ax, ay, aw, ah = a.winfo_rootx(), a.winfo_rooty(), a.winfo_width(), a.winfo_height()
        L, T, R, B = monitor_area(ax + aw // 2, ay + ah // 2, self.app.root)
        w, h = self._size()
        w, h = min(w, R - L), min(h, B - T)
        gap = px(6)
        if ax + aw + gap + w <= R:          # room on the right of the meter
            x = ax + aw + gap
        elif ax - gap - w >= L:             # room on the left
            x = ax - gap - w
        else:                               # overlap, but stay on this monitor
            x = max(L, min(ax, R - w))
        y = max(T, min(ay, B - h))
        self.top.geometry("%dx%d+%d+%d" % (w, h, x, y))

    def lift(self):
        main = getattr(self.app, "main", None)
        if main is not None and main is not self and (not self._shown or self.top.state() == "withdrawn"):
            self.place_near(main)
        self._shown = True
        self.top.deiconify()
        self.top.lift()

    def close(self, *_):
        self.save_geom()
        self.top.withdraw()


# --------------------------------------------------------------------------
# Main bar window
# --------------------------------------------------------------------------
def nlines_default(app):
    return 999 if key_down(0x10) else int(app.cfg["tip_lines"])


def build_drill_rows(app, seg, drill):
    """Rows for one actor/enemy/ability: its powers (or targets) with their share of the total."""
    mode, key = drill
    bd = build_breakdown(app, seg, mode, key)
    if bd is None or not bd.tabs:
        return None, []
    _label, kind, data = bd.tabs[0]
    rows = []
    if kind == "stats":
        if bd.preset in ("accuracy", "avoid"):
            for k, name, s, color in data:
                if not s.rolls:
                    continue
                n_ok = s.roll_hits if bd.preset == "accuracy" else s.roll_miss
                p = 100.0 * n_ok / s.rolls
                r = Row(k, name, p, "%.1f%% (%d/%d)" % (p, n_ok, s.rolls), "%.1f%%" % p, color, "power")
                r.cols = ["%.1f%%" % p, "%d/%d" % (n_ok, s.rolls)]
                rows.append(r)
        else:
            total = sum(it[2].total for it in data) or 1.0
            for k, name, s, color in data:
                if s.total <= 0:
                    continue
                pct = 100.0 * s.total / total
                txt, cols = rparts(app, fmt(s.total), [("ps", fps(s.total / bd.dur)), ("pct", "%.1f%%" % pct)])
                r = Row(k, name, s.total, txt, fmt(s.total), color, "power")
                r.cols = cols
                rows.append(r)
    else:
        total = sum(v for _n, v, _c in data) or 1.0
        for n, v, color in data:
            shown = ("%d" % v) if v == int(v) and v < 1000 else fmt(v)
            txt, cols = rparts(app, shown, [("pct", "%.1f%%" % (100.0 * v / total))])
            r = Row(n, n, v, txt, shown, color, "power")
            r.cols = cols
            rows.append(r)
    rows.sort(key=lambda r: -r.value)
    return bd, rows


TOTAL_MODES = ("damage", "dps", "taken", "heal", "hps", "healed", "absorb", "protect", "kills", "xp")


def touching(a, b, tol):
    """Two window rects share an edge (side by side or stacked)."""
    vov = min(a[3], b[3]) - max(a[1], b[1]) > 0
    hov = min(a[2], b[2]) - max(a[0], b[0]) > 0
    return ((vov and (abs(a[2] - b[0]) <= tol or abs(a[0] - b[2]) <= tol))
            or (hov and (abs(a[3] - b[1]) <= tol or abs(a[1] - b[3]) <= tol)))


def snap_offset(r, others, thr):
    """How far to nudge rect r so its edges click onto nearby windows."""
    bx = by = None
    for o in others:
        near_v = min(r[3], o[3]) - max(r[1], o[1]) > -thr          # vertical ranges overlap / nearly
        near_h = min(r[2], o[2]) - max(r[0], o[0]) > -thr
        stacked = abs(r[3] - o[1]) <= thr or abs(r[1] - o[3]) <= thr
        beside = abs(r[2] - o[0]) <= thr or abs(r[0] - o[2]) <= thr
        xs, ys = [], []
        if near_v:
            xs += [o[2] - r[0], o[0] - r[2]]                          # left->right edge, right->left edge
        if near_h and stacked:
            xs += [o[0] - r[0], o[2] - r[2]]                          # line up left / right sides
        if near_h:
            ys += [o[3] - r[1], o[1] - r[3]]                          # top->bottom edge, bottom->top edge
        if near_v and beside:
            ys += [o[1] - r[1], o[3] - r[3]]                          # line up tops / bottoms
        for d in xs:
            if abs(d) <= thr and (bx is None or abs(d) < abs(bx)):
                bx = d
        for d in ys:
            if abs(d) <= thr and (by is None or abs(d) < abs(by)):
                by = d
    return bx or 0, by or 0


class MainWindow(DarkWin):
    IS_MAIN = True

    def __init__(self, app, view=None):
        self.is_main = view is None
        if view is None:
            views = app.cfg.get("views") or []
            view = views[0] if views else {}
        tabs = [m for m in (view.get("tabs") or []) if m in MODE_LABEL] or \
            [app.cfg["mode"] if app.cfg["mode"] in MODE_LABEL else "damage"]
        self.tabs = tabs
        self.tab = max(0, min(int(view.get("tab", 0)), len(tabs) - 1))
        self.mode = tabs[self.tab]
        self.seg_choice = "current"
        default = "%dx%d+%d+%d" % (px(310), px(232), px(120), px(120))
        if self.is_main:
            super().__init__(app, MODE_LABEL[self.mode], "geometry", default, toplevel=app.root, min_size=(170, 60))
        else:
            super().__init__(app, MODE_LABEL[self.mode], None, view.get("geom") or default, min_size=(170, 60))
        self.tabbar = tk.Canvas(self.body, height=px(18), bg=C["title"], highlightthickness=0, bd=0)
        self.tabbar.bind("<Configure>", lambda e: self.draw_tabs())
        self.tabbar.bind("<Button-1>", self._tab_click)
        self.tabbar.bind("<Button-2>", self._tab_mclick)
        self.tabbar.bind("<Button-3>", self._tab_rclick)
        self.left_buttons = []
        self.build_buttons()
        self.title_menu = self.menu_modes
        self.cv = tk.Canvas(self.body, bg=C["bg"], highlightthickness=0, bd=0)
        self.status = tk.Canvas(self.body, height=px(18), bg=C["title"], highlightthickness=0, bd=0)
        self.status.bind("<Configure>", lambda e: self.draw_status())
        self.apply_layout()
        self.rows = []
        self.headers = []
        self.drill = None
        self.scroll = 0
        self.hover = -1
        self.flash = None
        self.cv.bind("<Configure>", lambda e: self.refresh())
        self.cv.bind("<Motion>", self._motion)
        self.cv.bind("<Leave>", self._leave)
        self.cv.bind("<Button-1>", self._click)
        self.cv.bind("<Button-3>", self._rclick)
        on_wheel(self.cv, self._wheel)
        self.top.title(APP_NAME)

    def build_buttons(self):
        """Title-bar buttons, drawn right-to-left:
        [title word] ...  #31 00:41  segments  report  reset  settings | minimize  close"""
        c = self.app.cfg
        if self.is_main:
            b = [(G_CLOSE, lambda x, y: self.app.quit(), "Close")]
        else:
            b = [(G_CLOSE, lambda x, y: self.close_meter(), "Close")]
        if c["btn_min"] and self.is_main:
            b.append((G_MIN, lambda x, y: self.minimize(), "Minimize"))
        b.append((G_OPTIONS, self.menu_options, "Options"))
        if c["btn_reset"]:
            b.append((G_RESET, lambda x, y: self.app.reset_data(), "Reset"))
        if c["btn_report"]:
            b.append((G_REPORT, self.menu_report, "Report"))
        if c["btn_segments"]:
            b.append((G_SEGMENTS, self.menu_segments, "Segments"))
        self.right_buttons = b

    def apply_layout(self):
        c = self.app.cfg
        self.top.configure(bg=c["border_color"] if c["border_on"] else c["body_bg"])
        for w in (self.tb, self.body, self.status, self.cv, self.tabbar):
            w.pack_forget()
        if c["title_bottom"]:
            self.tb.pack(side="bottom", fill="x", padx=1, pady=(0, 1))
            self.body.pack(side="top", fill="both", expand=True, padx=1, pady=(1, 0))
        else:
            self.tb.pack(side="top", fill="x", padx=1, pady=(1, 0))
            self.body.pack(side="top", fill="both", expand=True, padx=1, pady=(0, 1))
        self.body.configure(bg=c["body_bg"])
        self.cv.configure(bg=c["body_bg"])
        if c["statusbar"]:
            self.status.configure(height=px(18))
            self.status.pack(side="bottom", fill="x")
        if self.show_tabs():
            self.tabbar.configure(height=px(18), bg=C["title"])
            self.tabbar.pack(side="top", fill="x")
        self.cv.pack(fill="both", expand=True)
        tk.Misc.lift(self.grip)
        self.draw_tabs()

    # --- tabs ----------------------------------------------------------------
    def show_tabs(self):
        return len(self.tabs) > 1 or bool(self.app.cfg.get("tabs_always"))

    def draw_tabs(self):
        tb = self.tabbar
        tb.delete("all")
        if not self.show_tabs():
            return
        W, h = tb.winfo_width(), int(tb.cget("height"))
        n = len(self.tabs)
        plus = px(20)
        tw = max(px(30), min(px(120), (W - plus) // max(1, n)))
        self._tabw = tw
        for i, m in enumerate(self.tabs):
            on = i == self.tab
            x0 = i * tw
            tb.create_rectangle(x0, 0, x0 + tw - 1, h, fill=C["sel"] if on else C["title"], width=0)
            if on:
                tb.create_rectangle(x0, h - px(2), x0 + tw - 1, h, fill=C["gold"], width=0)
            tb.create_line(x0 + tw - 1, px(3), x0 + tw - 1, h - px(3), fill=C["sep"])
            tb.create_text(x0 + tw // 2, h // 2, text=truncate(FONTS["small"], MODE_LABEL[m], tw - px(8)),
                           font=FONTS["small"], fill=C["gold"] if on else C["dim"])
        tb.create_text(n * tw + plus // 2, h // 2, text="+", font=FONTS["uib"], fill=C["icon"])

    def _tab_index(self, x):
        tw = getattr(self, "_tabw", px(60))
        i = int(x // tw)
        if i < len(self.tabs):
            return i
        return "plus" if x < len(self.tabs) * tw + px(20) else None

    def _tab_click(self, e):
        i = self._tab_index(e.x)
        if i == "plus":
            self.add_tab()
        elif i is not None:
            self.select_tab(i)

    def _tab_mclick(self, e):
        i = self._tab_index(e.x)
        if isinstance(i, int):
            self.close_tab(i)

    def _tab_rclick(self, e):
        i = self._tab_index(e.x)
        if isinstance(i, int):
            self.select_tab(i)
        self.menu_modes(e.x_root, e.y_root)

    def select_tab(self, i):
        self.tab = max(0, min(i, len(self.tabs) - 1))
        self.mode = self.tabs[self.tab]
        self.drill = None
        self.scroll = 0
        self.hover = -1
        self.app.use(self)
        self.draw_tabs()
        self.refresh()
        self.app.save_views()

    def add_tab(self):
        pick = next((m for m in ("heal", "taken", "dps", "kills", "healed", "damage", "absorb", "deaths")
                     if m not in self.tabs), "damage")
        self.tabs.append(pick)
        self.apply_layout()
        self.select_tab(len(self.tabs) - 1)
        self.flash_title("New tab \u2014 right-click it to pick what it shows", 2.5)

    def close_tab(self, i=None):
        if len(self.tabs) < 2:
            return
        i = self.tab if i is None else i
        del self.tabs[i]
        if self.tab >= i and self.tab > 0:
            self.tab -= 1
        self.apply_layout()
        self.select_tab(self.tab)

    # --- windows / snapping ---------------------------------------------------
    def view_dict(self):
        t = self.top
        return {"tabs": list(self.tabs), "tab": self.tab,
                "geom": "%dx%d+%d+%d" % (t.winfo_width(), t.winfo_height(), t.winfo_x(), t.winfo_y())}

    def save_geom(self):
        if self.is_main:
            DarkWin.save_geom(self)
        self.app.save_views()

    def rect(self):
        t = self.top
        x, y = t.winfo_rootx(), t.winfo_rooty()
        return (x, y, x + t.winfo_width(), y + t.winfo_height())

    def close_meter(self):
        app = self.app
        if self.is_main:
            app.quit()
            return
        if self in app.meters:
            app.meters.remove(self)
        if getattr(app, "bd_src", None) is self:
            app.bd_src = app.main
        app.use(app.main)
        self.top.destroy()
        app.save_views()

    def _drag_start(self, e):
        if self._on_btn():
            self._drag = None
            return
        alone = key_down(0x12) or not self.app.cfg.get("snap_windows", True)
        group = [self] if alone else self.app.snap_group(self)
        if alone and len(self.app.snap_group(self)) > 1:
            self.flash_title("Unsnapped", 1.2)
        self._drag = (e.x_root, e.y_root, [(m, m.top.winfo_rootx(), m.top.winfo_rooty()) for m in group])

    def _drag_move(self, e):
        d = getattr(self, "_drag", None)
        if not d:
            return
        x0, y0, group = d
        ox, oy = group[0][1], group[0][2]
        nx, ny = ox + e.x_root - x0, oy + e.y_root - y0
        if self.app.cfg.get("snap_windows", True):
            moving = [g[0] for g in group]
            others = [m for m in self.app.meters if m not in moving and m.top.state() == "normal"]
            w, h = self.top.winfo_width(), self.top.winfo_height()
            sx, sy = snap_offset((nx, ny, nx + w, ny + h), [m.rect() for m in others], px(12))
            nx, ny = nx + sx, ny + sy
        dx, dy = nx - ox, ny - oy
        for m, mx, my in group:
            m.top.geometry("+%d+%d" % (mx + dx, my + dy))

    def _drag_end(self, e):
        d = getattr(self, "_drag", None)
        self._drag = None
        if self.is_main:
            DarkWin.save_geom(self)
        self.app.save_views()
        if self.is_main:
            self.app.check_monitor()

    def apply_alpha(self):
        try:
            self.top.attributes("-alpha", self.app.current_alpha(getattr(self, "_hovering", True)))
        except Exception:
            pass

    def draw_status(self):
        self.app.use(self)
        st = self.status
        st.delete("all")
        if not self.app.cfg["statusbar"]:
            return
        W, h = st.winfo_width(), int(st.cget("height"))
        seg = self.app.get_segment()
        for key, anchor, x in ((self.app.cfg["sb_left"], "w", px(6)), (self.app.cfg["sb_center"], "center", W // 2),
                               (self.app.cfg["sb_right"], "e", W - px(16))):
            st.create_text(x, h // 2, text=self.app.status_value(key, seg), font=FONTS["title_small"],
                           fill=C["dim"], anchor=anchor)

    # --- title / status ---------------------------------------------------
    def update_title(self):
        app = self.app
        app.use(self)
        self.title = MODE_LABEL[self.mode]
        seg = app.get_segment()
        if self.flash and time.time() < self.flash[1]:
            self.title_right = self.flash[0]
        elif app.seg_choice == "overall":
            self.title_right = "Overall  " + mmss(seg.duration() if seg else 0)
        elif seg is None:
            self.title_right = ""
        else:
            live = "● " if (seg is app.parser.current) else ""
            self.title_right = "%s#%d  %s" % (live, seg.number, mmss(seg.duration()))
        self.draw_title()

    def flash_title(self, text, secs=1.6):
        self.flash = (text, time.time() + secs)
        self.update_title()
        self.top.after(int(secs * 1000) + 50, self.update_title)

    # --- drawing -----------------------------------------------------------
    def _slot(self):
        return px(self.app.cfg["row_height"]) + int(self.app.cfg["row_spacing"])

    def _row_y(self, v, H):
        slot = self._slot()
        if self.app.cfg["grow_up"]:
            return H - (v + 1) * slot + int(self.app.cfg["row_spacing"])
        return v * slot

    def _text(self, cv, x, y, text, font, anchor="w"):
        style = self.app.cfg["text_style"]
        if style == "outline":
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cv.create_text(x + dx, y + dy, text=text, font=font, fill="#000000", anchor=anchor)
        elif style == "shadow":
            cv.create_text(x + 1, y + 1, text=text, font=font, fill="#000000", anchor=anchor)
        cv.create_text(x, y, text=text, font=font, fill="#ffffff", anchor=anchor)

    def _draw_row(self, cv, r, v, W, H, rh, frac, idx, hov):
        c = self.app.cfg
        y = self._row_y(v, H)
        if y + rh < 0 or y > H:
            return
        cv.create_rectangle(0, y, W, y + rh, fill=c["bar_bg_color"], width=0)
        x0 = 0
        if c["show_icons"]:
            x0 = rh
            cv.create_rectangle(0, y, rh, y + rh, fill=shade(r.color, 0.42), width=0)
            if r.glyph and (r.glyph.startswith("T") or ord(r.glyph[0]) < 0xE000):
                cv.create_text(rh // 2, y + rh // 2, text=r.glyph, font=FONTS["tiny"], fill=r.color)
            elif r.glyph:
                cv.create_text(rh // 2, y + rh // 2, text=r.glyph, font=FONTS["icon"], fill=r.color)
            else:
                letter = "\u2605" if r.kind == "player" else (r.name.strip()[:1] or "?").upper()
                cv.create_text(rh // 2, y + rh // 2, text=letter, font=FONTS["uib"], fill=r.color)
        bw = int((W - x0) * frac)
        if bw > 0:
            lines = bar_lines(r.color, rh, c["bar_texture"], 1.18 if hov else 1.0)
            if c["bar_texture"] == "flat":
                cv.create_rectangle(x0, y, x0 + bw, y + rh, fill=lines[0], width=0)
            elif c["bar_texture"] == "outline":
                cv.create_rectangle(x0, y, x0 + bw - 1, y + rh - 1, fill=lines[0], outline=r.color, width=1)
            else:
                for gy, col in enumerate(lines):
                    cv.create_line(x0, y + gy, x0 + bw, y + gy, fill=col)
        if c["row_border"]:
            cv.create_rectangle(0, y, W - 1, y + rh - 1, outline="#000000", width=1)
        if hov:
            cv.create_rectangle(x0, y, W - 1, y + rh - 1, outline="#ffffff", width=1)
        f = FONTS["row"]
        if c["aligned_cols"] and r.cols:
            cw = f.measure("888.8K") + px(10)
            rw = cw * len(r.cols)
            xr = W - px(4)
            for col in reversed(r.cols):
                self._text(cv, xr, y + rh // 2, col, f, anchor="e")
                xr -= cw
        else:
            rw = f.measure(r.right)
            self._text(cv, W - px(4), y + rh // 2, r.right, f, anchor="e")
        if idx is not None and c["show_rank"] and r.kind != "death":
            left = "%d. %s" % (idx + 1, r.name)
        else:
            left = r.name
        left = truncate(f, left, W - x0 - rw - px(16))
        self._text(cv, x0 + px(4), y + rh // 2, left, f)

    def _total_row(self, rows, seg):
        mode = self.app.cfg["mode"]
        tot = sum(r.value for r in rows)
        if mode in ("dps", "hps"):
            right = fps(tot)
        elif mode in ("kills",):
            right = "%d" % tot
        else:
            right = "%s (%s)" % (fmt(tot), fps(tot / (seg.duration() if seg else 1)))
        r = Row("@total", "Total", tot, right, right, "#6b6874", "total", "\u03a3")
        r.cols = [right]
        return r

    def refresh(self):
        app = self.app
        app.use(self)
        c = app.cfg
        cv = self.cv
        cv.delete("all")
        if self.show_tabs():
            self.draw_tabs()
        self.draw_status()
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 10 or H < 10:
            return
        seg = app.get_segment()
        headers = []
        if app.log_warning():
            headers.append(Row("@warn", "Chat log isn't updating \u2014 click to fix", 1.0, "", "",
                               "#9a6a12", "header", "!"))
        drill = self.drill if (self.drill and self.drill[0] == c["mode"]) else None
        rows = None
        if drill is not None:
            bd, rows = build_drill_rows(app, seg, drill)
            if bd is None:
                drill, rows = None, None
            else:
                back = Row("@back", "\u25c0  " + bd.title, 1.0, fmt(bd.total) if bd.total > 1 else "",
                           "", bd.color, "header", "\u25c0")
                headers.append(back)
        self.drill = drill
        if rows is None:
            rows = build_rows(app, seg)
            if c["total_bar"] and rows and c["mode"] in TOTAL_MODES:
                headers.append(self._total_row(rows, seg))
        self.rows = rows
        self.headers = headers
        rh = px(c["row_height"])
        slot = self._slot()
        self.offset = len(headers)
        vis = max(1, H // slot - self.offset)
        self.vis = vis
        self.scroll = max(0, min(self.scroll, len(rows) - vis))
        for i, hrow in enumerate(headers):
            self._draw_row(cv, hrow, i, W, H, rh, 1.0, None, self.hover == -2 - i)
        if not rows:
            msg = app.status_message(seg)
            top_y = len(headers) * slot
            cv.create_text(W // 2, top_y + (H - top_y) // 2, text=msg, font=FONTS["small"], fill=C["dim"],
                           justify="center", width=W - px(16))
            self.update_title()
            return
        top = max(r.value for r in rows) or 1.0
        for i, r in enumerate(rows[self.scroll:self.scroll + vis + 1]):
            idx = self.scroll + i
            self._draw_row(cv, r, i + self.offset, W, H, rh, max(0.0, min(1.0, r.value / top)), idx,
                           idx == self.hover)
        if len(rows) > vis:
            th = max(px(12), int(H * vis / len(rows)))
            ty = int((H - th) * self.scroll / max(1, len(rows) - vis))
            cv.create_rectangle(W - px(3), ty, W, ty + th, fill=C["faint"], width=0)
        self.update_title()

    # --- interaction -------------------------------------------------------
    def _slot_at(self, y):
        slot = self._slot()
        H = self.cv.winfo_height()
        return int((H - y) // slot) if self.app.cfg["grow_up"] else int(y // slot)

    def _header_at(self, y):
        v = self._slot_at(y)
        return v if 0 <= v < len(getattr(self, "headers", [])) else None

    def _row_at(self, y):
        v = self._slot_at(y)
        off = getattr(self, "offset", 0)
        if v < off:
            return -1
        idx = self.scroll + v - off
        return idx if 0 <= idx < len(self.rows) else -1

    def _motion(self, e):
        self.app.use(self)
        idx = self._row_at(e.y)
        h = self._header_at(e.y)
        hv = (-2 - h) if h is not None else idx
        if hv != self.hover:
            self.hover = hv
            self.refresh()
        if idx >= 0:
            self.app.show_tip(self.rows[idx], e.x_root, e.y_root)
        else:
            self.app.tip.hide()

    def _leave(self, e):
        self.hover = -1
        self.app.tip.hide()
        self.refresh()

    def _click(self, e):
        self.app.use(self)
        self.app.tip.hide()
        h = self._header_at(e.y)
        if h is not None:
            key = self.headers[h].key
            if key == "@warn":
                self.app.chatlog_menu(e.x_root, e.y_root)
            elif key == "@back":
                self.drill = None
                self.scroll = 0
                self.refresh()
            return
        idx = self._row_at(e.y)
        if idx < 0:
            if self.app.log_warning():
                self.app.chatlog_menu(e.x_root, e.y_root)
            elif not self.app.log_path and not self.app.game_root():
                self.app.browse_game_dir()
            return
        row = self.rows[idx]
        if self.drill:
            # a power inside the drill-down: open the full breakdown on that power
            self.app.open_breakdown_at(self.drill[0], self.drill[1], row.key)
        elif row.kind == "death" or (e.state & 0x0001):
            self.app.open_breakdown(row)            # Shift+click: straight to the breakdown window
        else:
            self.drill = (self.app.cfg["mode"], row.key)
            self.scroll = 0
            self.hover = -1
            self.refresh()

    def _wheel(self, d):
        self.scroll = max(0, self.scroll + d * int(self.app.cfg["wheel_speed"]))
        self.refresh()

    def after_rescale(self):
        self.refresh()

    def _rclick(self, e):
        self.app.use(self)
        if self.drill:
            self.drill = None
            self.scroll = 0
            self.app.tip.hide()
            self.refresh()
            return
        idx = self._row_at(e.y)
        if idx >= 0 and self.rows[idx].kind in ("player", "pet", "group"):
            self.app.tip.hide()
            self.app.group_click(self.rows[idx].key, bool(e.state & 0x0001))
        else:
            self.menu_modes(e.x_root, e.y_root)

    def minimize(self):
        t = self.top
        others = [m for m in self.app.meters if m is not self]
        for m in others:
            m.top.withdraw()
        t.overrideredirect(False)
        t.iconify()

        def on_map(e):
            if t.state() == "normal":
                t.unbind("<Map>")
                t.overrideredirect(True)
                t.after(20, lambda: win_appwindow(t))
                for m in others:
                    if m in self.app.meters:
                        m.top.deiconify()
        t.bind("<Map>", on_map)

    # --- menus -----------------------------------------------------------
    def menu_modes(self, x, y):
        app = self.app
        items = []
        last = None
        for m, label, cat in MODES:
            if cat != last:
                if last is not None:
                    items.append({"sep": True})
                items.append({"header": True, "label": cat})
                last = cat
            items.append({"label": label, "check": self.mode == m, "cmd": lambda m=m: app.set_mode(m, self)})
        items.append({"sep": True})
        items.append({"header": True, "label": "WINDOW"})
        items.append({"label": "New tab", "cmd": self.add_tab})
        if len(self.tabs) > 1:
            items.append({"label": "Close this tab", "cmd": self.close_tab})
        items.append({"label": "New window", "cmd": lambda: app.new_meter(self)})
        if not self.is_main:
            items.append({"label": "Close this window", "cmd": self.close_meter})
        items.append({"sep": True})
        items.append({"label": "Recap Last Moments (manual)", "color": C["red"], "cmd": app.manual_recap})
        DMenu(app, x, y, items)

    def menu_segments(self, x, y):
        app = self.app
        p = app.parser
        items = [{"header": True, "label": "SEGMENTS"},
                 {"label": "Overall Data", "check": app.seg_choice == "overall",
                  "right": mmss(p.overall.duration()), "cmd": lambda: app.set_segment("overall", self)},
                 {"label": "Current Segment", "check": app.seg_choice == "current",
                  "cmd": lambda: app.set_segment("current", self)},
                 {"sep": True}]
        segs = list(reversed(p.segments))
        if not segs:
            items.append({"label": "No fights yet", "disabled": True})
        for s in segs[:30]:
            live = "● " if s is p.current else ""
            items.append({"label": "%s#%d  %s" % (live, s.number, s.name),
                          "right": "%s  %s" % (mmss(s.duration()), time.strftime("%H:%M", time.localtime(s.start))),
                          "check": app.seg_choice == s.number,
                          "cmd": lambda n=s.number: app.set_segment(n, self)})
        DMenu(app, x, y, items, min_width=240)

    def menu_report(self, x, y):
        app = self.app
        items = [{"header": True, "label": "REPORT (copies to clipboard)"},
                 {"label": "Top 5 - one line for game chat", "cmd": lambda: app.report(5, True, self)},
                 {"label": "Top 10 - one line for game chat", "cmd": lambda: app.report(10, True, self)},
                 {"label": "Full report (multi-line)", "cmd": lambda: app.report(40, False, self)}]
        DMenu(app, x, y, items)

    def menu_options(self, x, y):
        app = self.app
        log = os.path.basename(app.log_path) if app.log_path else "none"
        items = [{"header": True, "label": APP_NAME.upper() + "  v" + VERSION}]
        if getattr(app, "update_info", None):
            items.append({"label": "\u2b06  Update available: %s" % app.update_info[0], "color": C["gold"],
                          "cmd": lambda: app.open_url(app.update_info[1])})
        items += [{"label": "Options…", "cmd": app.open_options},
                 {"label": "Mids' Build \u2014 planned vs actual\u2026", "cmd": app.open_build},
                 {"sep": True},
                 {"label": "Use today's log automatically", "check": app.cfg["log_auto"],
                  "cmd": lambda: app.set_log_auto(not app.cfg["log_auto"])},
                 {"label": "Choose log file…", "cmd": app.browse_log},
                 {"label": log, "disabled": True},
                 {"sep": True},
                 {"label": "Show pet type on bars", "check": app.cfg["show_pet_type"],
                  "cmd": lambda: app.toggle("show_pet_type")},
                 {"label": "Order pets by tier", "check": app.cfg["tier_order"],
                  "cmd": lambda: app.toggle("tier_order")},
                 {"sep": True}] + app.grouping_items() + [{"header": True, "label": "PROFILE"}] + [
                 {"label": n, "check": n == app.cfg.get("active_profile"),
                  "cmd": lambda n=n: app.root.after(10, lambda: app.apply_profile(n))}
                 for n in app.profile_names()] + [
                 {"sep": True},
                 {"label": "Always on top", "check": app.cfg["topmost"], "cmd": lambda: app.toggle("topmost")},
                 {"sep": True},
                 {"label": "About Hero Meter\u2026", "cmd": lambda: app.root.after(10, lambda: app.about_menu(x, y))},
                 {"label": "Exit", "cmd": app.quit}]
        DMenu(app, x, y, items, min_width=220)


# --------------------------------------------------------------------------
# Breakdown window
# --------------------------------------------------------------------------
PRESETS = {
    # (title, width, text_fn, sort_fn)    s=Stat, c=ctx dict(total, dur, per)
    "damage": [
        ("Amount", 62, lambda s, c: fmt(s.total), lambda s: s.total),
        ("{per}", 54, lambda s, c: fps(s.total / c["dur"]), lambda s: s.total),
        ("%", 50, lambda s, c: "%.1f%%" % (100 * s.total / c["total"]), lambda s: s.total),
        ("Hits", 44, lambda s, c: str(s.count), lambda s: s.count),
        ("Avg", 50, lambda s, c: fmt(s.total / s.count) if s.count else "-", lambda s: s.total / max(1, s.count)),
        ("Max", 50, lambda s, c: fmt(_smax(s)), lambda s: _smax(s)),
        ("Acc", 50, lambda s, c: ("%.0f%%" % (100.0 * s.roll_hits / s.rolls)) if s.rolls else "-",
         lambda s: (s.roll_hits / s.rolls) if s.rolls else -1),
    ],
    "taken": [
        ("Amount", 62, lambda s, c: fmt(s.total), lambda s: s.total),
        ("%", 50, lambda s, c: "%.1f%%" % (100 * s.total / c["total"]), lambda s: s.total),
        ("Hits", 44, lambda s, c: str(s.count), lambda s: s.count),
        ("Avg", 50, lambda s, c: fmt(s.total / s.count) if s.count else "-", lambda s: s.total / max(1, s.count)),
        ("Max", 50, lambda s, c: fmt(_smax(s)), lambda s: _smax(s)),
        ("Dodged", 56, lambda s, c: ("%.0f%%" % (100.0 * s.roll_miss / s.rolls)) if s.rolls else "-",
         lambda s: (s.roll_miss / s.rolls) if s.rolls else -1),
    ],
    "heal": [
        ("Amount", 62, lambda s, c: fmt(s.total), lambda s: s.total),
        ("{per}", 54, lambda s, c: fps(s.total / c["dur"]), lambda s: s.total),
        ("%", 50, lambda s, c: "%.1f%%" % (100 * s.total / c["total"]), lambda s: s.total),
        ("Count", 48, lambda s, c: str(s.count), lambda s: s.count),
        ("Avg", 50, lambda s, c: fmt(s.total / s.count) if s.count else "-", lambda s: s.total / max(1, s.count)),
        ("Max", 50, lambda s, c: fmt(_smax(s)), lambda s: _smax(s)),
    ],
    "accuracy": [
        ("Rolls", 50, lambda s, c: str(s.rolls), lambda s: s.rolls),
        ("Hits", 46, lambda s, c: str(s.roll_hits), lambda s: s.roll_hits),
        ("Misses", 52, lambda s, c: str(s.roll_miss), lambda s: s.roll_miss),
        ("Hit %", 54, lambda s, c: "%.1f%%" % (100.0 * s.roll_hits / s.rolls) if s.rolls else "-",
         lambda s: s.roll_hits / max(1, s.rolls)),
        ("To-Hit", 56, lambda s, c: "%.1f%%" % (s.chance_sum / s.chance_n) if s.chance_n else "auto",
         lambda s: s.chance_sum / s.chance_n if s.chance_n else 101),
    ],
    "avoid": [
        ("Attacks", 56, lambda s, c: str(s.rolls), lambda s: s.rolls),
        ("Hit You", 54, lambda s, c: str(s.roll_hits), lambda s: s.roll_hits),
        ("Missed", 52, lambda s, c: str(s.roll_miss), lambda s: s.roll_miss),
        ("Dodge %", 58, lambda s, c: "%.1f%%" % (100.0 * s.roll_miss / s.rolls) if s.rolls else "-",
         lambda s: s.roll_miss / max(1, s.rolls)),
        ("Their To-Hit", 76, lambda s, c: "%.1f%%" % (s.chance_sum / s.chance_n) if s.chance_n else "auto",
         lambda s: s.chance_sum / s.chance_n if s.chance_n else 101),
    ],
}


def _smax(s):
    m = max(s.nmax, s.tmax)
    for f in s.flairs.values():
        m = max(m, f[3])
    return m


class Breakdown(DarkWin):
    def __init__(self, app):
        super().__init__(app, "Breakdown", "bd_geometry",
                         "%dx%d+%d+%d" % (px(860), px(470), px(460), px(140)), min_size=(560, 300))
        self.right_buttons = [(G_CLOSE, lambda x, y: self.close(), "Close")]
        self.mode = None
        self.key = None
        self.tab = 0
        self.sel = None
        self.sort = (0, True)
        self.scroll = 0
        self.dscroll = 0
        self.data = None
        self.items_view = []
        self.header = tk.Canvas(self.body, height=px(62), bg=C["bg"], highlightthickness=0, bd=0)
        self.header.pack(side="top", fill="x")
        self.tabs = tk.Canvas(self.body, height=px(26), bg=C["bg"], highlightthickness=0, bd=0)
        self.tabs.pack(side="top", fill="x")
        main = tk.Frame(self.body, bg=C["bg"])
        main.pack(side="top", fill="both", expand=True)
        self.detail = tk.Canvas(main, width=px(300), bg=C["bg"], highlightthickness=0, bd=0)
        self.detail.pack(side="right", fill="y", padx=(px(4), px(6)), pady=(0, px(14)))
        self.table = tk.Canvas(main, bg=C["bg"], highlightthickness=0, bd=0)
        self.table.pack(side="left", fill="both", expand=True, padx=(px(6), 0), pady=(0, px(14)))
        tk.Misc.lift(self.grip)
        self.table.bind("<Configure>", lambda e: self.draw_table())
        self.detail.bind("<Configure>", lambda e: self.draw_detail())
        self.table.bind("<Button-1>", self._table_click)
        self.tabs.bind("<Button-1>", self._tab_click)
        on_wheel(self.table, self._wheel)
        on_wheel(self.detail, self._dwheel)
        self.tab_slots = []

    def after_rescale(self):
        self.header.configure(height=px(62))
        self.tabs.configure(height=px(26))
        self.detail.configure(width=px(300))
        self.refresh()

    def open(self, mode, key):
        if (mode, key) != (self.mode, self.key):
            self.tab, self.sel, self.scroll, self.dscroll, self.sort = 0, None, 0, 0, (0, True)
        self.mode, self.key = mode, key
        self.refresh()
        self.lift()

    def refresh(self):
        if self.mode is None:
            return
        app = self.app
        seg = app.get_segment()
        self.data = build_breakdown(app, seg, self.mode, self.key)
        segname = "Overall Data" if app.seg_choice == "overall" else (
            "#%d %s" % (seg.number, seg.name) if seg else "-")
        self.title = "%s  —  %s" % (MODE_LABEL.get(self.mode, ""), segname)
        self.draw_title()
        self.draw_header()
        self.draw_tabs()
        self.draw_table()
        self.draw_detail()

    # --- header ----------------------------------------------------------
    def draw_header(self):
        cv = self.header
        cv.delete("all")
        W = cv.winfo_width() or px(800)
        d = self.data
        if d is None:
            cv.create_text(px(12), px(30), text="Nothing to show for this segment.", font=FONTS["ui"],
                           fill=C["dim"], anchor="w")
            return
        s = px(44)
        cv.create_rectangle(px(10), px(9), px(10) + s, px(9) + s, fill=shade(d.color, 0.4), outline=d.color)
        glyph = {"player": "\u2605", "ability": "\u2694", "group": "\u03a3"}.get(d.kind, d.title[:1].upper())
        cv.create_text(px(10) + s // 2, px(9) + s // 2, text=glyph, font=FONTS["big"], fill=d.color)
        cv.create_text(px(64), px(22), text=d.title, font=FONTS["big"], fill=C["text"], anchor="w")
        kind = {"player": "You", "pet": "Pet", "enemy": "Enemy", "ability": "Enemy Ability"}.get(d.kind, "")
        if d.kind == "pet":
            kind = pettypes.describe(self.app.parser.typer.get(d.title))
        elif d.kind == "group":
            kind = "Group  \u2022  " + ", ".join(d.members)
        cv.create_text(px(64), px(46), text=kind, font=FONTS["small"], fill=C["dim"], anchor="w")
        x = W - px(10)
        for label, val in reversed(d.summary):
            if not label:
                continue
            w = max(FONTS["uib"].measure(val), FONTS["small"].measure(label)) + px(22)
            cv.create_text(x, px(22), text=val, font=FONTS["head_big"], fill=C["text"], anchor="e")
            cv.create_text(x, px(44), text=label, font=FONTS["small"], fill=C["dim"], anchor="e")
            x -= w + px(10)
        cv.create_line(px(8), px(61), W - px(8), px(61), fill=C["sep"])

    def draw_tabs(self):
        cv = self.tabs
        cv.delete("all")
        self.tab_slots = []
        d = self.data
        if d is None:
            return
        x = px(8)
        for i, (label, _k, _data) in enumerate(d.tabs):
            w = FONTS["uib"].measure(label) + px(22)
            on = i == self.tab
            cv.create_rectangle(x, px(3), x + w, px(25), fill=C["block_head"] if on else C["bg"],
                                outline=C["sep"])
            if on:
                cv.create_rectangle(x, px(23), x + w, px(25), fill=C["gold"], width=0)
            cv.create_text(x + w // 2, px(14), text=label, font=FONTS["uib"], fill=C["text"] if on else C["dim"])
            self.tab_slots.append((x, x + w, i))
            x += w + px(4)

    def _tab_click(self, e):
        for a, b, i in self.tab_slots:
            if a <= e.x < b:
                if i != self.tab:
                    self.tab, self.sel, self.scroll, self.sort = i, None, 0, (0, True)
                    self.draw_tabs()
                    self.draw_table()
                    self.draw_detail()
                return

    # --- table -----------------------------------------------------------
    def _cur_tab(self):
        d = self.data
        if d is None or not d.tabs:
            return None
        self.tab = min(self.tab, len(d.tabs) - 1)
        return d.tabs[self.tab]

    def draw_table(self):
        cv = self.table
        cv.delete("all")
        tab = self._cur_tab()
        if tab is None:
            return
        W, H = cv.winfo_width(), cv.winfo_height()
        d = self.data
        f, fs = FONTS["ui"], FONTS["small"]
        hh, rh = px(20), px(20)
        label, kind, data = tab
        ctx = {"total": d.total, "dur": d.dur}
        self.hit_slots = []
        if kind == "stats":
            cols = PRESETS[d.preset]
            colw = [px(c[1]) for c in cols]
            namew = max(px(80), W - sum(colw) - px(30))
            ci, desc = self.sort
            ci = min(ci, len(cols) - 1)
            items = sorted(data, key=lambda it: cols[ci][3](it[2]), reverse=desc)
            ctx["total"] = sum(it[2].total for it in data) or d.total
            self.items_view = items
            # header
            cv.create_rectangle(0, 0, W, hh, fill=C["header"] if "header" in C else C["title"], width=0)
            cv.create_rectangle(0, 0, W, hh, fill=C["title"], width=0)
            cv.create_text(px(6), hh // 2, text="#", font=fs, fill=C["dim"], anchor="w")
            cv.create_text(px(30), hh // 2, text="Name", font=fs, fill=C["dim"], anchor="w")
            x = px(30) + namew
            self.col_slots = []
            for i, (title, _w, _t, _s) in enumerate(cols):
                t = title.replace("{per}", d.per)
                if i == ci:
                    t += " ▼" if desc else " ▲"
                cv.create_text(x + colw[i] - px(4), hh // 2, text=t, font=fs,
                               fill=C["gold"] if i == ci else C["dim"], anchor="e")
                self.col_slots.append((x, x + colw[i], i))
                x += colw[i]
            vis = max(1, (H - hh) // rh)
            self.scroll = max(0, min(self.scroll, len(items) - vis))
            top = max((it[2].total for it in items), default=0) or 1.0
            if d.preset in ("accuracy", "avoid"):
                top = max((it[2].rolls for it in items), default=0) or 1
            for row, (k, name, s, color) in enumerate(items[self.scroll:self.scroll + vis]):
                y = hh + row * rh
                idx = self.scroll + row
                sel = k == self.sel
                cv.create_rectangle(0, y, W, y + rh - 1, fill=C["sel"] if sel else (C["row_alt"] if idx % 2 else C["bg"]),
                                    width=0)
                v = s.rolls if d.preset in ("accuracy", "avoid") else s.total
                bw = int((W - px(28)) * min(1.0, v / top))
                cv.create_rectangle(px(26), y + 2, px(26) + bw, y + rh - 3, fill=shade(color, 0.36), width=0)
                cv.create_rectangle(px(26), y + 2, px(29), y + rh - 3, fill=color, width=0)
                if sel:
                    cv.create_rectangle(0, y, px(3), y + rh - 1, fill=C["gold"], width=0)
                cv.create_text(px(6), y + rh // 2, text=str(idx + 1), font=fs, fill=C["dim"], anchor="w")
                cv.create_text(px(34), y + rh // 2, text=truncate(f, name, namew - px(8)), font=f,
                               fill=C["text"], anchor="w")
                x = px(30) + namew
                for i, (title, _w, tfn, _s) in enumerate(cols):
                    cv.create_text(x + colw[i] - px(4), y + rh // 2, text=tfn(s, ctx), font=f,
                                   fill=C["text"], anchor="e")
                    x += colw[i]
                self.hit_slots.append((y, y + rh, k))
            if not items:
                cv.create_text(W // 2, hh + px(30), text="No data", font=f, fill=C["dim"])
            if self.sel is None and items:
                self.sel = items[0][0]
                self.draw_table()
                return
        else:
            items = sorted(data, key=lambda it: -it[1])
            self.items_view = []
            self.col_slots = []
            total = sum(v for _n, v, _c in items) or 1.0
            cv.create_rectangle(0, 0, W, hh, fill=C["title"], width=0)
            cv.create_text(px(6), hh // 2, text="#", font=fs, fill=C["dim"], anchor="w")
            cv.create_text(px(30), hh // 2, text="Name", font=fs, fill=C["dim"], anchor="w")
            cv.create_text(W - px(70), hh // 2, text="Amount", font=fs, fill=C["dim"], anchor="e")
            cv.create_text(W - px(6), hh // 2, text="%", font=fs, fill=C["dim"], anchor="e")
            vis = max(1, (H - hh) // rh)
            self.scroll = max(0, min(self.scroll, len(items) - vis))
            top = items[0][1] if items else 1.0
            for row, (name, v, color) in enumerate(items[self.scroll:self.scroll + vis]):
                y = hh + row * rh
                idx = self.scroll + row
                cv.create_rectangle(0, y, W, y + rh - 1, fill=C["row_alt"] if idx % 2 else C["bg"], width=0)
                bw = int((W - px(28)) * min(1.0, v / (top or 1)))
                cv.create_rectangle(px(26), y + 2, px(26) + bw, y + rh - 3, fill=shade(color, 0.36), width=0)
                cv.create_rectangle(px(26), y + 2, px(29), y + rh - 3, fill=color, width=0)
                cv.create_text(px(6), y + rh // 2, text=str(idx + 1), font=fs, fill=C["dim"], anchor="w")
                cv.create_text(px(34), y + rh // 2, text=truncate(f, name, W - px(170)), font=f,
                               fill=C["text"], anchor="w")
                val = ("%d" % v) if self.data.preset in () or (v == int(v) and v < 1000 and label in ("Defeated",)) else fmt(v)
                cv.create_text(W - px(70), y + rh // 2, text=val, font=f, fill=C["text"], anchor="e")
                cv.create_text(W - px(6), y + rh // 2, text="%.1f%%" % (100 * v / total), font=f,
                               fill=C["dim"], anchor="e")
            if not items:
                cv.create_text(W // 2, hh + px(30), text="No data", font=f, fill=C["dim"])

    def _table_click(self, e):
        if e.y < px(20):
            for a, b, i in getattr(self, "col_slots", []):
                if a <= e.x < b:
                    ci, desc = self.sort
                    self.sort = (i, not desc) if ci == i else (i, True)
                    self.draw_table()
                    return
            return
        for a, b, k in getattr(self, "hit_slots", []):
            if a <= e.y < b:
                self.sel = k
                self.dscroll = 0
                self.draw_table()
                self.draw_detail()
                return

    def _wheel(self, d):
        self.scroll = max(0, self.scroll + d * 2)
        self.draw_table()

    def _dwheel(self, d):
        self.dscroll = max(0, self.dscroll + d * px(40))
        self.draw_detail()

    # --- detail blocks ---------------------------------------------------
    def draw_detail(self):
        cv = self.detail
        cv.delete("all")
        tab = self._cur_tab()
        W, H = cv.winfo_width(), cv.winfo_height()
        if tab is None or tab[1] != "stats":
            if tab is not None:
                cv.create_text(W // 2, px(40), text="Select the first tab\nfor power details",
                               font=FONTS["small"], fill=C["faint"], justify="center")
            return
        item = None
        for it in self.items_view:
            if it[0] == self.sel:
                item = it
                break
        if item is None:
            return
        _k, name, s, color = item
        d = self.data
        total_all = sum(it[2].total for it in self.items_view) or 1.0
        per = d.per
        blocks = []
        is_taken = d.preset in ("taken", "avoid")
        cnt = s.count
        blocks.append(("Summary", None, [
            ("Total", fmt(s.total)), ("% of All", "%.1f%%" % (100 * s.total / total_all)),
            ("Hits" if not d.preset == "heal" else "Count", str(cnt)),
            ("Average", fmt(s.total / cnt) if cnt else "-"),
            (per, fps(s.total / d.dur)), ("Max", fmt(_smax(s)) if cnt else "-"),
        ]))
        merge = bool(self.app.cfg["merge_crits"] and s.flairs)
        if merge and s.n_direct:
            mins = ([s.nmin] if s.nmin is not None else []) + [fl[2] for fl in s.flairs.values()]
            mx_all = max([s.nmax] + [fl[3] for fl in s.flairs.values()])
            blocks.append(("Direct Hits", "%d" % s.n_direct, [
                ("Minimum", fmt(min(mins) if mins else 0)), ("Maximum", fmt(mx_all)),
                ("Average", fmt(s.direct_total / s.n_direct)), ("Total", fmt(s.direct_total)),
            ]))
        if s.n_norm and not merge:
            blocks.append(("Normal Hits", "%d  [%.1f%%]" % (s.n_norm, 100.0 * s.n_norm / max(1, s.n_direct)), [
                ("Minimum", fmt(s.nmin or 0)), ("Maximum", fmt(s.nmax)),
                ("Average", fmt(s.norm_total / s.n_norm)), ("Total", fmt(s.norm_total)),
            ]))
        for flair, (n, tot, mn, mx) in ([] if merge else sorted(s.flairs.items(), key=lambda kv: -kv[1][1])):
            blocks.append((flair.title() + " Hits", "%d  [%.1f%%]" % (n, 100.0 * n / max(1, s.n_direct)), [
                ("Minimum", fmt(mn)), ("Maximum", fmt(mx)), ("Average", fmt(tot / n)), ("Total", fmt(tot)),
            ]))
        if s.n_tick:
            blocks.append(("Over Time", "%d ticks" % s.n_tick, [
                ("Total", fmt(s.tick_total)), ("% of Power", "%.1f%%" % (100 * s.tick_total / (s.total or 1))),
                ("Avg Tick", fmt(s.tick_total / s.n_tick)), ("Max Tick", fmt(s.tmax)),
            ]))
        if s.rolls:
            if is_taken:
                blocks.append(("Attacks vs You", "%d" % s.rolls, [
                    ("Hit You", str(s.roll_hits)), ("Dodged", str(s.roll_miss)),
                    ("Dodge %", "%.1f%%" % (100.0 * s.roll_miss / s.rolls)),
                    ("Their To-Hit", "%.1f%%" % (s.chance_sum / s.chance_n) if s.chance_n else "auto"),
                ]))
            else:
                blocks.append(("Accuracy", "%d rolls" % s.rolls, [
                    ("Hits", str(s.roll_hits)), ("Misses", str(s.roll_miss)),
                    ("Hit %", "%.1f%%" % (100.0 * s.roll_hits / s.rolls)),
                    ("Avg To-Hit", "%.1f%%" % (s.chance_sum / s.chance_n) if s.chance_n else "auto"),
                ]))
        y = px(4) - self.dscroll
        bw = W - px(2)
        f, fs, fh = FONTS["ui"], FONTS["small"], FONTS["uib"]
        lh = px(18)
        cv.create_rectangle(0, y, bw, y + px(24), fill=shade(color, 0.32), outline=color)
        cv.create_text(px(8), y + px(12), text=truncate(fh, name, bw - px(16)), font=fh, fill=C["text"], anchor="w")
        y += px(30)
        for title, right, lines in blocks:
            rows = (len(lines) + 1) // 2
            h = px(20) + rows * lh + px(4)
            cv.create_rectangle(0, y, bw, y + h, fill=C["block"], outline=C["sep"])
            cv.create_rectangle(0, y, bw, y + px(20), fill=C["block_head"], width=0)
            cv.create_text(px(8), y + px(10), text=title, font=fh, fill=C["gold"], anchor="w")
            if right:
                cv.create_text(bw - px(8), y + px(10), text=right, font=fs, fill=C["text"], anchor="e")
            for i, (k, v) in enumerate(lines):
                if not k:
                    continue
                colx = 0 if i % 2 == 0 else bw // 2
                ly = y + px(20) + (i // 2) * lh + lh // 2 + px(2)
                cv.create_text(colx + px(8), ly, text=k + ":", font=fs, fill=C["dim"], anchor="w")
                cv.create_text(colx + bw // 2 - px(8), ly, text=v, font=f, fill=C["text"], anchor="e")
            y += h + px(6)
        # damage types
        if s.dtypes:
            items = sorted(s.dtypes.items(), key=lambda kv: -kv[1])
            h = px(20) + len(items) * lh + px(4)
            cv.create_rectangle(0, y, bw, y + h, fill=C["block"], outline=C["sep"])
            cv.create_rectangle(0, y, bw, y + px(20), fill=C["block_head"], width=0)
            cv.create_text(px(8), y + px(10), text="Damage Types", font=fh, fill=C["gold"], anchor="w")
            ly = y + px(22)
            for t, v in items:
                frac = v / (s.total or 1)
                cv.create_rectangle(px(6), ly + 2, px(6) + int((bw - px(12)) * frac), ly + lh - 2,
                                    fill=shade(dtype_color(t), 0.45), width=0)
                cv.create_text(px(10), ly + lh // 2, text=t, font=fs, fill=C["text"], anchor="w")
                cv.create_text(bw - px(8), ly + lh // 2, text="%s  (%.0f%%)" % (fmt(v), 100 * frac), font=fs,
                               fill=C["text"], anchor="e")
                ly += lh
            y += h + px(6)
        # targets / sources of this power
        tgt = s.targets or s.sources
        if tgt:
            items = sorted(tgt.items(), key=lambda kv: -kv[1])[:8]
            title = "Victims" if is_taken and s.targets else ("Targets" if s.targets else "Sources")
            h = px(20) + len(items) * lh + px(4)
            cv.create_rectangle(0, y, bw, y + h, fill=C["block"], outline=C["sep"])
            cv.create_rectangle(0, y, bw, y + px(20), fill=C["block_head"], width=0)
            cv.create_text(px(8), y + px(10), text=title, font=fh, fill=C["gold"], anchor="w")
            ly = y + px(22)
            top = items[0][1] or 1
            for t, v in items:
                cv.create_rectangle(px(6), ly + 2, px(6) + int((bw - px(12)) * v / top), ly + lh - 2,
                                    fill=shade(C["enemy"] if not is_taken else C["blue"], 0.4), width=0)
                cv.create_text(px(10), ly + lh // 2, text=truncate(fs, t, bw - px(90)), font=fs, fill=C["text"],
                               anchor="w")
                cv.create_text(bw - px(8), ly + lh // 2, text=fmt(v), font=fs, fill=C["text"], anchor="e")
                ly += lh
            y += h + px(6)
        content_h = y + self.dscroll
        if self.dscroll and content_h < H:
            self.dscroll = 0


# --------------------------------------------------------------------------
# MOBA-style death recap
# --------------------------------------------------------------------------
class RecapWin(DarkWin):
    def __init__(self, app):
        super().__init__(app, "Death Recap", "recap_geometry",
                         "%dx%d+%d+%d" % (px(560), px(680), px(500), px(80)), min_size=(420, 320))
        self.right_buttons = [(G_CLOSE, lambda x, y: self.close(), "Close")]
        self.left_buttons = [(G_PREV, lambda x, y: self.step(-1), "Older death"),
                             (G_NEXT, lambda x, y: self.step(1), "Newer death")]
        self.cv = tk.Canvas(self.body, bg=C["bg"], highlightthickness=0, bd=0)
        self.cv.pack(fill="both", expand=True)
        tk.Misc.lift(self.grip)
        self.idx = -1
        self.scroll = 0
        self.cv.bind("<Configure>", lambda e: self.draw())
        self.cv.bind("<Button-1>", self._click)
        on_wheel(self.cv, self._wheel)
        self.toggle_box = None

    def after_rescale(self):
        self.draw()

    def show(self, idx):
        self.idx = idx
        self.scroll = 0
        self.draw()
        self.lift()

    def step(self, d):
        deaths = self.app.parser.deaths
        if not deaths:
            return
        self.idx = max(0, min(len(deaths) - 1, self.idx + d))
        self.scroll = 0
        self.draw()

    def _wheel(self, d):
        self.scroll = max(0, self.scroll + d * px(48))
        self.draw()

    def _click(self, e):
        b = self.toggle_box
        if b and b[0] <= e.x <= b[2] and b[1] <= e.y <= b[3]:
            self.app.cfg["recap_show_misses"] = not self.app.cfg["recap_show_misses"]
            self.app.save_cfg()
            self.draw()

    def draw(self):
        cv = self.cv
        cv.delete("all")
        W, H = cv.winfo_width(), cv.winfo_height()
        deaths = self.app.parser.deaths
        if not deaths or not (0 <= self.idx < len(deaths)):
            self.title = "Death Recap"
            self.draw_title()
            cv.create_text(W // 2, H // 2, text="No deaths recorded yet.\n\nUse 'Recap Last Moments' from the\n"
                           "display menu to capture what just happened.", font=FONTS["ui"], fill=C["dim"],
                           justify="center")
            return
        d = deaths[self.idx]
        self.title = "Death Recap  (%d of %d)" % (self.idx + 1, len(deaths))
        self.draw_title()
        f, fs, fh, fb = FONTS["ui"], FONTS["small"], FONTS["uib"], FONTS["big"]
        pad = px(12)
        y = -self.scroll
        ev = d.events
        dmg = [e for e in ev if e["kind"] == "dmg"]
        heals = [e for e in ev if e["kind"] == "heal"]
        shields = [e for e in ev if e["kind"] in ("absorb", "protect")]
        misses = [e for e in ev if e["kind"] == "miss"]
        total_dmg = sum(e["amount"] for e in dmg)
        span = (d.ts - dmg[0]["ts"]) if dmg else 0

        # ---- banner -------------------------------------------------------
        bh = px(96)
        for i in range(bh):
            t = i / bh
            cv.create_line(0, y + i, W, y + i, fill=mix("#5a1414", "#1f0d0f", t))
        cv.create_line(0, y + bh, W, y + bh, fill=C["red"], width=px(2))
        cv.create_text(pad + px(26), y + bh // 2, text=G_SKULL, font=FONTS["icon_big"], fill="#ff8a80")
        x = pad + px(62)
        if d.manual:
            cv.create_text(x, y + px(24), text="RECAP — LAST MOMENTS", font=fs, fill="#ffb3ad", anchor="w")
        else:
            who = "YOU WERE" if d.victim == self.app.parser.player else d.victim.upper() + " WAS"
            cv.create_text(x, y + px(24), text="%s DEFEATED BY" % who, font=fs, fill="#ffb3ad", anchor="w")
        cv.create_text(x, y + px(50), text=truncate(fb, d.killer or "Unknown", W - x - px(110)), font=fb,
                       fill=C["text"], anchor="w")
        if d.killing_power:
            kb = "Killing blow: %s  —  %s %s" % (d.killing_power, fmt(d.killing_amount), d.killing_type or "")
            cv.create_text(x, y + px(76), text=truncate(fs, kb, W - x - pad), font=fs, fill="#ffd2cf", anchor="w")
        cv.create_text(W - pad, y + px(24), text=clock(d.ts), font=fh, fill=C["text"], anchor="e")
        cv.create_text(W - pad, y + px(44), text="%s • %ds window" % (d.victim, d.window), font=fs,
                       fill="#ffb3ad", anchor="e")
        y += bh + px(10)

        # ---- stat tiles ---------------------------------------------------
        tiles = [("DAMAGE TAKEN", fmt(total_dmg), C["red"]),
                 ("HITS TAKEN", str(len(dmg)), C["red"]),
                 ("TIME TO DIE", ("%ds" % span) if dmg else "-", C["gold"]),
                 ("HEALED", fmt(sum(e["amount"] for e in heals)), C["green"]),
                 ("SHIELDED", fmt(sum(e["amount"] for e in shields)), C["blue"])]
        tw = (W - pad * 2 - px(6) * (len(tiles) - 1)) / len(tiles)
        for i, (lab, val, col) in enumerate(tiles):
            tx = pad + i * (tw + px(6))
            cv.create_rectangle(tx, y, tx + tw, y + px(52), fill=C["block"], outline=C["sep"])
            cv.create_rectangle(tx, y, tx + tw, y + px(3), fill=col, width=0)
            cv.create_text(tx + tw / 2, y + px(22), text=val, font=FONTS["head_big"], fill=C["text"])
            cv.create_text(tx + tw / 2, y + px(41), text=lab, font=FONTS["tiny"], fill=C["dim"])
        y += px(62)

        # ---- damage type split -------------------------------------------
        types = {}
        for e in dmg:
            types[e["dtype"] or "Unknown"] = types.get(e["dtype"] or "Unknown", 0.0) + e["amount"]
        cv.create_text(pad, y + px(8), text="DAMAGE BY TYPE", font=FONTS["head"], fill=C["gold"], anchor="w")
        y += px(18)
        if types and total_dmg > 0:
            x = pad
            bwid = W - pad * 2
            items = sorted(types.items(), key=lambda kv: -kv[1])
            for t, v in items:
                w = bwid * v / total_dmg
                g = gradient(dtype_color(t), px(16))
                for gy, col in enumerate(g):
                    cv.create_line(x, y + gy, x + w, y + gy, fill=col)
                x += w
            y += px(20)
            lx = pad
            for t, v in items:
                label = "%s %.0f%%" % (t, 100 * v / total_dmg)
                lw = fs.measure(label) + px(22)
                if lx + lw > W - pad:
                    lx = pad
                    y += px(18)
                cv.create_rectangle(lx, y + px(4), lx + px(10), y + px(14), fill=dtype_color(t), width=0)
                cv.create_text(lx + px(14), y + px(9), text=label, font=fs, fill=C["text"], anchor="w")
                lx += lw
            y += px(26)
        else:
            cv.create_text(pad, y + px(8), text="No damage recorded in this window.", font=fs, fill=C["dim"],
                           anchor="w")
            y += px(24)

        # ---- damage by enemy ---------------------------------------------
        cv.create_text(pad, y + px(8), text="DAMAGE BY ENEMY", font=FONTS["head"], fill=C["gold"], anchor="w")
        y += px(20)
        enemies = {}
        for e in dmg:
            en = enemies.setdefault(e["src"], {"total": 0.0, "powers": {}})
            en["total"] += e["amount"]
            p = en["powers"].setdefault(e["power"], [0, 0.0, e["dtype"]])
            p[0] += 1
            p[1] += e["amount"]
        top = max((v["total"] for v in enemies.values()), default=1) or 1
        for name, info in sorted(enemies.items(), key=lambda kv: -kv[1]["total"]):
            is_killer = name == d.killer
            ch = px(26) + px(17) * min(4, len(info["powers"])) + px(6)
            cv.create_rectangle(pad, y, W - pad, y + ch, fill=C["block"],
                                outline=C["gold"] if is_killer else C["sep"])
            bw = (W - pad * 2 - px(2)) * info["total"] / top
            g = gradient(C["enemy"], px(22), 0.95)
            for gy, col in enumerate(g):
                cv.create_line(pad + 1, y + 1 + gy, pad + 1 + bw, y + 1 + gy, fill=col)
            name_txt = ("☠ " if is_killer else "") + name
            shadow_text(cv, pad + px(8), y + px(12), truncate(fh, name_txt, W - pad * 2 - px(150)), fh)
            shadow_text(cv, W - pad - px(8), y + px(12),
                        "%s  (%.0f%%)" % (fmt(info["total"]), 100 * info["total"] / (total_dmg or 1)), fh, anchor="e")
            py = y + px(26)
            for pname, (n, amt, dt_) in sorted(info["powers"].items(), key=lambda kv: -kv[1][1])[:4]:
                cv.create_rectangle(pad + px(10), py + px(4), pad + px(18), py + px(12), fill=dtype_color(dt_),
                                    width=0)
                cv.create_text(pad + px(24), py + px(8), text="%s  ×%d" % (pname, n), font=fs,
                               fill=C["text"], anchor="w")
                cv.create_text(W - pad - px(8), py + px(8), text="%s %s" % (fmt(amt), dt_ or ""), font=fs,
                               fill=C["dim"], anchor="e")
                py += px(17)
            y += ch + px(6)
        if not enemies:
            y += px(4)

        # ---- final moments timeline --------------------------------------
        y += px(6)
        cv.create_text(pad, y + px(8), text="FINAL MOMENTS", font=FONTS["head"], fill=C["gold"], anchor="w")
        show_m = self.app.cfg["recap_show_misses"]
        tl = "☑ show misses" if show_m else "☐ show misses"
        tid = cv.create_text(W - pad, y + px(8), text=tl, font=fs, fill=C["dim"], anchor="e")
        bb = cv.bbox(tid)
        self.toggle_box = bb
        y += px(20)
        min_heal = float(self.app.cfg["recap_min_heal"])
        rows = [e for e in ev if (show_m or e["kind"] != "miss")
                and not (e["kind"] in ("heal", "absorb") and e["amount"] < min_heal)]
        rows = rows[-int(self.app.cfg["recap_events"]):]
        if self.app.cfg["recap_reverse"]:
            rows = list(reversed(rows))
        running = 0.0
        last_sec = None
        lh = px(22)
        for e in rows:
            k = e["kind"]
            killing = e.get("killing_blow")
            bg = "#3a2a10" if killing else C["block"]
            cv.create_rectangle(pad, y, W - pad, y + lh - 1, fill=bg, outline=C["gold"] if killing else "")
            rel = int(round(e["ts"] - d.ts))
            if rel != last_sec:
                cv.create_text(pad + px(6), y + lh // 2, text=("%+ds" % rel) if rel else "0s", font=fs,
                               fill=C["dim"], anchor="w")
                last_sec = rel
            if k == "dmg":
                col, sign = C["red"], "-"
                running += e["amount"]
                txt = "%s  •  %s" % (e["src"], e["power"])
                if e.get("flair"):
                    txt += "  (%s)" % e["flair"]
                if e.get("dot"):
                    txt += "  (DoT)"
            elif k == "heal":
                col, sign = C["green"], "+"
                txt = "%s  •  %s" % (e["src"], e["power"])
            elif k == "absorb":
                col, sign = C["blue"], "+"
                txt = "%s  •  %s  (absorb)" % (e["src"], e["power"])
            elif k == "protect":
                col, sign = C["teal"], "−"
                txt = "Bodyguard: henchmen took damage for you"
            else:
                col, sign = C["faint"], ""
                txt = "%s  •  %s  missed you" % (e["src"], e["power"])
            cv.create_rectangle(pad + px(46), y + px(5), pad + px(50), y + lh - px(6), fill=col, width=0)
            amount_txt = ("%s%s" % (sign, fmt(e["amount"]))) if k != "miss" else "MISS"
            aw = fh.measure(amount_txt) + px(60)
            cv.create_text(pad + px(58), y + lh // 2, text=truncate(f, txt, W - pad * 2 - px(70) - aw), font=f,
                           fill=C["text"] if k != "miss" else C["dim"], anchor="w")
            if killing:
                cv.create_text(W - pad - px(8) - fh.measure(amount_txt) - px(10), y + lh // 2, text="KILLING BLOW",
                               font=FONTS["tiny"], fill=C["gold"], anchor="e")
            cv.create_text(W - pad - px(8), y + lh // 2, text=amount_txt, font=fh, fill=col, anchor="e")
            if k == "dmg" and total_dmg > 0:
                cv.create_rectangle(pad, y + lh - px(3), pad + (W - pad * 2) * running / total_dmg, y + lh - 1,
                                    fill=shade(C["red"], 0.7), width=0)
            y += lh
        if not rows:
            cv.create_text(pad, y + px(10), text="Nothing logged in the final seconds.", font=fs, fill=C["dim"],
                           anchor="w")
            y += px(24)
        y += px(10)
        note = ("Detected from: \"%s\"" % d.trigger_text[:70]) if not d.manual else "Manual recap"
        cv.create_text(pad, y, text=note, font=FONTS["tiny"], fill=C["faint"], anchor="nw")
        total_h = y + self.scroll + px(24)
        if total_h < H + self.scroll and self.scroll:
            self.scroll = max(0, total_h - H)


# --------------------------------------------------------------------------
# Options window
# --------------------------------------------------------------------------
class BuildWin(DarkWin):
    """Mids' build vs. what the chat log shows."""
    TABS = ["Value Ranking", "Planned vs Actual", "Procs", "Not in Build"]

    def __init__(self, app):
        super().__init__(app, "Mids' Build", "build_geometry",
                         "%dx%d+%d+%d" % (px(860), px(560), px(220), px(120)), min_size=(560, 320))
        self.right_buttons = [(G_CLOSE, lambda x, y: self.close(), "Close")]
        self.build = None
        self.char = "You"
        self.tab = 0
        self.scroll = 0
        self.rows = []
        self.head = tk.Frame(self.body, bg=C["bg"])
        self.head.pack(side="top", fill="x")
        self.tabs_cv = tk.Canvas(self.body, height=px(26), bg=C["title"], highlightthickness=0, bd=0)
        self.tabs_cv.pack(side="top", fill="x")
        self.tabs_cv.bind("<Button-1>", self._tab_click)
        self.tabs_cv.bind("<Configure>", lambda e: self.draw_tabs())
        wrap = tk.Frame(self.body, bg=C["bg"])
        wrap.pack(side="top", fill="both", expand=True)
        self.cv = tk.Canvas(wrap, bg=C["bg"], highlightthickness=0, bd=0)
        self.cv.pack(side="left", fill="both", expand=True)
        self.cv.bind("<Configure>", lambda e: self.draw_table())
        self.cv.bind("<Motion>", self._motion)
        self.cv.bind("<Leave>", lambda e: self.app.tip.hide())
        on_wheel(self.cv, self._wheel)
        tk.Misc.lift(self.grip)

    # --- data ---------------------------------------------------------------------
    def load(self):
        a = self.app
        self.char = a.build_char()
        path = (a.cfg.get("char_builds") or {}).get(self.char)
        self.auto = False
        if not path and a.cfg.get("auto_build", True):
            path = mids.match_build(self.char, mids.find_builds())
            self.auto = bool(path)
        self.build, self.error = None, ""
        if path:
            try:
                self.build = mids.Build(path)
            except Exception as ex:
                self.error = "Couldn't read %s (%s)" % (os.path.basename(path), ex)
        self.scroll = 0
        self.build_head()
        self.refresh()

    def segment(self):
        a = self.app
        if a.cfg.get("build_source") == "view":
            a.use(a.main)
            return a.get_segment()
        return a.parser.overall

    def refresh(self):
        self.title = "Mids' Build \u2014 " + self.char
        self.draw_title()
        self.res = None
        if self.build is not None:
            seg = self.segment()
            actor = seg.actors.get(self.char) if seg else None
            if actor is None and seg is not None:
                actor = seg.actors.get(self.app.parser.player)
            self.res = mids.analyze(self.build, actor)
        self.draw_tabs()
        self.draw_table()

    # --- header ---------------------------------------------------------------------
    def build_head(self):
        for w in self.head.winfo_children():
            w.destroy()
        h = self.head
        top = tk.Frame(h, bg=C["bg"])
        top.pack(fill="x", padx=px(10), pady=(px(8), px(2)))
        if self.build is not None:
            b = self.build
            tk.Label(top, text=b.name, bg=C["bg"], fg=C["gold"], font=FONTS["head_big"]).pack(side="left")
            tk.Label(top, text="   %s  \u2022  %s  \u2022  level %s" % (b.archetype, " / ".join(b.sets[:2]), b.level),
                     bg=C["bg"], fg=C["dim"], font=FONTS["ui"]).pack(side="left")
        else:
            tk.Label(top, text="No build linked for %s" % self.char, bg=C["bg"], fg=C["gold"],
                     font=FONTS["head_big"]).pack(side="left")
        bar = tk.Frame(h, bg=C["bg"])
        bar.pack(fill="x", padx=px(10), pady=(0, px(8)))
        self._btn(bar, "Link build \u25be", self.menu_link)
        if self.build is not None:
            if mids.mids_exe():
                self._btn(bar, "Open in Mids", lambda e: self.open_in_mids())
            self._btn(bar, "Reload", lambda e: self.load())
        src = "Overall data" if self.app.cfg.get("build_source") != "view" else "Main window's segment"
        self._btn(bar, "Data: %s \u25be" % src, self.menu_source)
        if self.build is not None:
            how = "auto-matched by file name" if self.auto else "linked"
            tk.Label(bar, text="  %s: %s" % (how, os.path.basename(self.build.path)), bg=C["bg"], fg=C["faint"],
                     font=FONTS["small"]).pack(side="left", padx=px(6))
        if self.error:
            tk.Label(h, text=self.error, bg=C["bg"], fg=C["red"], font=FONTS["small"]).pack(anchor="w", padx=px(10))

    def _btn(self, parent, text, cb):
        b = tk.Label(parent, text=text, bg=C["block_head"], fg=C["text"], font=FONTS["ui"], padx=px(9), pady=px(2),
                     cursor="hand2")
        b.pack(side="left", padx=(0, px(6)))
        b.bind("<Button-1>", cb)
        b.bind("<Enter>", lambda e: b.configure(bg=C["sel"]))
        b.bind("<Leave>", lambda e: b.configure(bg=C["block_head"]))
        return b

    def menu_link(self, e):
        a = self.app
        cur = self.build.path if self.build else None
        items = [{"header": True, "label": "BUILD FOR " + self.char.upper()}]
        for p, t in mids.find_builds()[:25]:
            items.append({"label": os.path.splitext(os.path.basename(p))[0],
                          "right": time.strftime("%b %d", time.localtime(t)), "check": p == cur,
                          "cmd": lambda p=p: self.link(p)})
        items += [{"sep": True}, {"label": "Browse for a .mbd file\u2026", "cmd": self.browse}]
        if self.char in (a.cfg.get("char_builds") or {}):
            items.append({"label": "Unlink (go back to auto-match)", "cmd": lambda: self.link(None)})
        DMenu(a, e.x_root, e.y_root, items, min_width=320)

    def browse(self):
        p = filedialog.askopenfilename(parent=self.top, title="Choose a Mids build",
                                       initialdir=(mids.build_dirs() or [None])[0],
                                       filetypes=[("Mids Reborn build", "*.mbd"), ("All files", "*.*")])
        if p:
            self.link(p)

    def link(self, path):
        c = self.app.cfg.setdefault("char_builds", {})
        if path:
            c[self.char] = path
        else:
            c.pop(self.char, None)
        self.app.save_cfg()
        self.load()

    def menu_source(self, e):
        a = self.app

        def setsrc(v):
            a.cfg["build_source"] = v
            a.save_cfg()
            self.build_head()
            self.refresh()
        DMenu(a, e.x_root, e.y_root, [
            {"header": True, "label": "COMPARE AGAINST"},
            {"label": "Overall data (everything since the last reset)", "check": a.cfg.get("build_source") != "view",
             "cmd": lambda: setsrc("overall")},
            {"label": "The segment shown in the main window", "check": a.cfg.get("build_source") == "view",
             "cmd": lambda: setsrc("view")}], min_width=300)

    def open_in_mids(self):
        import subprocess
        try:
            subprocess.Popen([mids.mids_exe(), self.build.path], close_fds=True)
            self.app.main.flash_title("Opening Mids\u2026", 2)
        except Exception:
            self.app.main.flash_title("Couldn't start Mids", 2.5)

    # --- tabs ------------------------------------------------------------------------
    def draw_tabs(self):
        cv = self.tabs_cv
        cv.delete("all")
        x = px(8)
        self._tabx = []
        for i, t in enumerate(self.TABS):
            label = t
            if self.res is not None:
                planned, extra, procs, _tot = self.res
                n = {2: len(procs), 3: len(extra)}.get(i)
                if n is not None:
                    label += "  (%d)" % n
            w = FONTS["uib"].measure(label) + px(22)
            on = i == self.tab
            cv.create_rectangle(x, px(3), x + w, px(26), fill=C["bg"] if on else C["title"], width=0)
            if on:
                cv.create_rectangle(x, px(3), x + w, px(5), fill=C["gold"], width=0)
            cv.create_text(x + w // 2, px(15), text=label, font=FONTS["uib"], fill=C["gold"] if on else C["dim"])
            self._tabx.append((x, x + w))
            x += w + px(2)

    def _tab_click(self, e):
        for i, (x0, x1) in enumerate(getattr(self, "_tabx", [])):
            if x0 <= e.x <= x1:
                self.tab = i
                self.scroll = 0
                self.draw_tabs()
                self.draw_table()

    # --- table -------------------------------------------------------------------------
    def _vcolor(self, v):
        return {"good": C.get("green", "#5bd75b"), "bad": C["red"], "warn": C["gold"], "dim": C["dim"]}.get(v, C["text"])

    def table_spec(self):
        """-> (columns [(title, width, anchor)], rows [dict(cells, colors, bar, tip)], footnote)"""
        planned, extra, procs, total = self.res
        rows, note = [], ""
        if self.tab == 0:
            cols = [("#", 30, "e"), ("Power", 0, "w"), ("Slots", 46, "e"), ("Seen", 52, "e"), ("Output", 70, "e"),
                    ("Share", 120, "w"), ("Per use", 66, "e"), ("Per slot", 66, "e"), ("Verdict", 190, "w")]
            order = sorted(planned, key=lambda r: (-r.output, -(r.uses + r.seen), r.level))
            top = max([r.share for r in planned] or [1]) or 1
            for i, r in enumerate(order):
                vc = self._vcolor(r.vcolor)
                rows.append({"cells": [str(i + 1), r.name, str(r.slots), str(r.uses or r.seen or "") or "\u2014",
                                       fmt(r.output) if r.output else "\u2014", "%.1f%%" % r.share if r.output else "",
                                       fmt(r.output / r.uses) if r.uses and r.output else "",
                                       fmt(r.output / max(1, r.slots)) if r.output else "", r.verdict],
                             "colors": [C["dim"], C["text"] if r.active else C["dim"]] + [C["text"]] * 6 + [vc],
                             "bar": (5, r.share / top, vc) if r.output else None, "tip": self._tip(r)})
            note = "Output = damage + healing + absorbs from the chat log. Seen = times the log shows the power (each hit counts).  Total: %s" % fmt(total)
        elif self.tab == 1:
            cols = [("Lvl", 36, "e"), ("Power", 0, "w"), ("Slots", 46, "e"), ("Slotted with", 260, "w"),
                    ("In the log", 220, "w")]
            for r in sorted(planned, key=lambda r: (r.level, r.name)):
                sets = r.plan.sets()
                st = ", ".join("%s%s" % (s, " \u00d7%d" % n if n > 1 else "") for s, n in
                               sorted(sets.items(), key=lambda t: -t[1])) or ("%d slot%s" % (r.slots, "" if r.slots == 1 else "s"))
                if r.output:
                    log = "\u2714 %s%s" % (fmt(r.output), ("  \u2022  %d uses" % r.uses) if r.uses else "")
                    lc = C.get("green", "#5bd75b")
                elif r.uses or r.seen:
                    log = "\u2714 used %d\u00d7" % (r.uses or r.seen)
                    lc = C.get("green", "#5bd75b")
                else:
                    log = "\u2014 not seen"
                    lc = C["dim"]
                rows.append({"cells": [str(r.level), r.name, str(r.slots), st, log],
                             "colors": [C["dim"], C["text"], C["text"], C["dim"], lc], "bar": None, "tip": self._tip(r)})
            note = "Passive powers (Health, Stamina, most armors) never show in the log \u2014 that's normal."
        elif self.tab == 2:
            cols = [("Proc", 0, "w"), ("Slotted in", 170, "w"), ("Fired", 60, "e"), ("Output", 76, "e"),
                    ("Status", 170, "w")]
            for p in procs:
                ok = p["fires"] or p["output"]
                rows.append({"cells": [p["proc"], p["power"], str(p["fires"] or "") or "\u2014",
                                       fmt(p["output"]) if p["output"] else "",
                                       "\u2714 firing" if ok else "not seen yet"],
                             "colors": [C["text"], C["dim"], C["text"], C["text"],
                                        C.get("green", "#5bd75b") if ok else C["gold"]], "bar": None, "tip": None})
            note = "Some procs (debuffs, Build Up, confusion) don't print a line in the log, so 'not seen' can be normal."
        else:
            cols = [("Power", 0, "w"), ("Uses", 60, "e"), ("Output", 80, "e"), ("Share", 70, "e")]
            for r in extra:
                rows.append({"cells": [r.name, str(r.uses or "") or "\u2014", fmt(r.output) if r.output else "",
                                       "%.1f%%" % r.share if r.output else ""],
                             "colors": [C["text"], C["text"], C["text"], C["text"]], "bar": None, "tip": None})
            note = ("Used in game but missing from this build: a respec, temp powers, incarnates \u2014 "
                    "or the wrong build is linked.")
        return cols, rows, note

    def _tip(self, r):
        lines = [(lab, "", 0, C["dim"]) for lab in (r.plan.enh if r.plan else [])] or [("No enhancements", "", 0, C["dim"])]
        extra = []
        if r.dmg:
            extra.append(("Damage", fmt(r.dmg), 0, C["text"]))
        if r.heal:
            extra.append(("Healing", fmt(r.heal), 0, C["text"]))
        if r.absorb:
            extra.append(("Absorbs", fmt(r.absorb), 0, C["text"]))
        if r.rolls:
            extra.append(("Accuracy", "%.1f%% of %d" % (100.0 * r.hits / r.rolls, r.rolls), 0, C["text"]))
        return ("%s  (level %d, %d slots)" % (r.name, r.level, r.slots), extra + lines)

    def draw_table(self):
        cv = self.cv
        cv.delete("all")
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 20:
            return
        self._rows_y = []
        if self.build is None:
            msg = ("No Mids build is linked for %s.\n\nClick \u201cLink build\u201d above and pick one of your saved "
                   "builds,\nor save your build in Mids as \u201c%s - <anything>.mbd\u201d and it links itself."
                   % (self.char, self.char if self.char != "You" else "YourCharacter"))
            cv.create_text(W // 2, H // 2, text=msg, font=FONTS["ui"], fill=C["dim"], justify="center")
            return
        if self.res is None:
            return
        cols, rows, note = self.table_spec()
        f, fh = FONTS["ui"], FONTS["uib"]
        rh = max(px(22), f.metrics("linespace") + px(6))
        fixed = sum(px(w) for _t, w, _a in cols if w)
        flex = max(px(140), W - px(16) - fixed)
        xs, x = [], px(8)
        for _t, w, _a in cols:
            cw = px(w) if w else flex
            xs.append((x, cw))
            x += cw
        cv.create_rectangle(0, 0, W, rh, fill=C["block_head"], width=0)
        for (t, _w, anc), (x0, cw) in zip(cols, xs):
            tx = x0 + px(4) if anc == "w" else x0 + cw - px(6)
            cv.create_text(tx, rh // 2, text=t, font=fh, fill=C["dim"], anchor=anc)
        if not rows:
            cv.create_text(W // 2, rh * 3, text="Nothing to show yet \u2014 go fight something with %s!" % self.char
                           if self.tab != 3 else "Everything you used is in the build. \u2714",
                           font=f, fill=C["dim"])
        vis = max(1, (H - rh * 2) // rh)
        self.scroll = max(0, min(self.scroll, len(rows) - vis))
        y = rh
        self._shown = []
        for i, r in enumerate(rows[self.scroll:self.scroll + vis]):
            if i % 2:
                cv.create_rectangle(0, y, W, y + rh, fill=C["row_alt"], width=0)
            if r.get("bar"):
                ci, frac, col = r["bar"]
                x0, cw = xs[ci]
                cv.create_rectangle(x0 + px(2), y + px(5), x0 + px(2) + int((cw - px(8)) * max(0.02, min(1, frac))),
                                    y + rh - px(5), fill=shade(col, 0.55), width=0)
            for k, ((t, _w, anc), (x0, cw)) in enumerate(zip(cols, xs)):
                txt = truncate(f, r["cells"][k], cw - px(10))
                tx = x0 + px(4) if anc == "w" else x0 + cw - px(6)
                cv.create_text(tx, y + rh // 2, text=txt, font=f, fill=r["colors"][k], anchor=anc)
            self._shown.append((y, y + rh, r))
            y += rh
        if len(rows) > vis:
            th = max(px(16), int((H - rh * 2) * vis / len(rows)))
            ty = rh + int((H - rh * 2 - th) * self.scroll / max(1, len(rows) - vis))
            cv.create_rectangle(W - px(4), ty, W - 1, ty + th, fill=C["faint"], width=0)
        cv.create_rectangle(0, H - rh, W, H, fill=C["title"], width=0)
        cv.create_text(px(10), H - rh // 2, text=truncate(FONTS["small"], note, W - px(20)), font=FONTS["small"],
                       fill=C["dim"], anchor="w")

    def _motion(self, e):
        for y0, y1, r in getattr(self, "_shown", []):
            if y0 <= e.y < y1 and r.get("tip"):
                title, lines = r["tip"]
                self.app.tip.show(e.x_root, e.y_root, title, C["gold"], lines, ("build", title))
                return
        self.app.tip.hide()

    def _wheel(self, d):
        self.scroll = max(0, self.scroll + d * 3)
        self.draw_table()

    def after_rescale(self):
        self.tabs_cv.configure(height=px(26))
        self.build_head()
        self.draw_tabs()
        self.draw_table()


class DScroll(tk.Canvas):
    """Thin dark scrollbar for a scrollable canvas."""

    def __init__(self, parent, target):
        super().__init__(parent, width=px(9), bg=C["bg"], highlightthickness=0, bd=0, cursor="hand2")
        self.target = target
        self.first, self.last = 0.0, 1.0
        self._grab = (0, 0.0)
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)

    def set(self, first, last):
        self.first, self.last = float(first), float(last)
        self.redraw()

    def redraw(self):
        self.delete("all")
        h, w = self.winfo_height(), self.winfo_width()
        if self.last - self.first >= 0.999:
            return
        self.create_rectangle(0, 0, w, h, fill=C["menu_bg"], width=0)
        y0 = int(h * self.first)
        y1 = max(y0 + px(24), int(h * self.last))
        self.create_rectangle(1, y0, w - 1, y1, fill=C["faint"], width=0)

    def _press(self, e):
        h = max(1, self.winfo_height())
        span = self.last - self.first
        if not (self.first * h <= e.y <= self.last * h):
            self.target.yview_moveto(max(0.0, e.y / h - span / 2))
        self._grab = (e.y, self.first)

    def _drag(self, e):
        y0, f0 = self._grab
        h = max(1, self.winfo_height())
        self.target.yview_moveto(max(0.0, f0 + (e.y - y0) / h))


# Popular fonts (only the ones actually installed are offered)
POPULAR_FONTS = ["Oswald", "Bahnschrift", "Bahnschrift SemiBold", "Bahnschrift Condensed",
                 "Bahnschrift SemiBold Condensed", "Segoe UI", "Segoe UI Semibold", "Segoe UI Black",
                 "Segoe UI Variable Display Semib", "Calibri", "Candara", "Corbel", "Franklin Gothic Medium",
                 "Trebuchet MS", "Verdana", "Tahoma", "Arial", "Arial Black", "Arial Narrow", "Impact",
                 "Georgia", "Cambria", "Constantia", "Palatino Linotype", "Sitka Heading", "Consolas",
                 "Cascadia Code", "Lucida Console", "Comic Sans MS", "Ink Free", "Segoe Print", "Gabriola",
                 "Roboto", "Roboto Condensed", "Open Sans", "Montserrat", "Lato", "Rajdhani", "Teko",
                 "Bebas Neue", "Exo 2", "Titillium Web", "Orbitron"]
FONT_CHOICES = POPULAR_FONTS
SYMBOL_FONTS = {"Marlett", "Webdings", "Wingdings", "Wingdings 2", "Wingdings 3", "Symbol", "Segoe MDL2 Assets",
                "Segoe Fluent Icons", "Segoe UI Emoji", "Segoe UI Symbol", "MT Extra", "Cambria Math",
                "Sans Serif Collection", "HoloLens MDL2 Assets"}


class FontPicker:
    """Pop-up list of fonts, each drawn in its own typeface; click one to use it."""
    current = None

    def __init__(self, app, x, y, on_pick=None):
        if FontPicker.current is not None:
            FontPicker.current.close()
        FontPicker.current = self
        self.app = app
        self.on_pick = on_pick
        fams = getattr(app, "_fams", set())
        ok = lambda f: f == "Oswald" and getattr(app, "_oswald_ok", False) or f in fams
        self.popular = [f for f in POPULAR_FONTS if ok(f)]
        self.all = sorted((f for f in fams if not f.startswith("@") and f not in SYMBOL_FONTS),
                          key=str.lower)
        if getattr(app, "_oswald_ok", False) and "Oswald" not in self.all:
            self.all.insert(0, "Oswald")
        self.mine = sorted(getattr(app, "_user_fams", set()), key=str.lower)
        self.which = "popular"
        t = self.top = tk.Toplevel(app.root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.configure(bg=C["border"])
        W, H = px(340), px(440)
        L, T, R, B = monitor_area(x, y, app.root)
        t.geometry("%dx%d+%d+%d" % (W, H, max(L, min(x, R - W)), max(T, min(y, B - H))))
        head = tk.Frame(t, bg=C["title"])
        head.pack(fill="x", padx=1, pady=(1, 0))
        tk.Label(head, text="Choose a Font", bg=C["title"], fg=C["gold"], font=FONTS["head"]).pack(
            side="left", padx=px(8), pady=px(4))
        x_ = tk.Label(head, text="\u2715", bg=C["title"], fg=C["dim"], font=FONTS["uib"], cursor="hand2")
        x_.pack(side="right", padx=px(8))
        x_.bind("<Button-1>", lambda e: self.close())
        bar = tk.Frame(t, bg=C["bg"])
        bar.pack(fill="x", padx=1)
        self.tabs = {}
        for key, label in (("popular", "Popular (%d)" % len(self.popular)), ("all", "All (%d)" % len(self.all)),
                           ("mine", "My fonts (%d)" % len(self.mine))):
            b = tk.Label(bar, text=label, font=FONTS["uib"], padx=px(10), pady=px(3), cursor="hand2")
            b.pack(side="left", padx=(px(6), 0), pady=px(6))
            b.bind("<Button-1>", lambda e, k=key: self.show(k))
            self.tabs[key] = b
        self.search = tk.Entry(bar, bg=C["menu_bg"], fg=C["text"], insertbackground=C["text"], relief="flat",
                               font=FONTS["ui"], width=12)
        self.search.pack(side="right", padx=px(8))
        self.search.bind("<KeyRelease>", lambda e: self.draw())
        tk.Label(bar, text="Search", bg=C["bg"], fg=C["dim"], font=FONTS["small"]).pack(side="right")
        foot = tk.Frame(t, bg=C["title"])
        foot.pack(side="bottom", fill="x", padx=1, pady=(0, 1))
        add = tk.Label(foot, text="\uff0b  Add font file\u2026", bg=C["block_head"], fg=C["text"], font=FONTS["uib"],
                       padx=px(10), pady=px(3), cursor="hand2")
        add.pack(side="left", padx=px(6), pady=px(5))
        add.bind("<Button-1>", lambda e: self.add_font())
        tk.Label(foot, text=".ttf / .otf \u2014 copied into the meter's fonts folder", bg=C["title"], fg=C["dim"],
                 font=FONTS["small"]).pack(side="left")
        body = tk.Frame(t, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        self.cv = tk.Canvas(body, bg=C["bg"], highlightthickness=0, bd=0)
        self.sb = DScroll(body, self.cv)
        self.sb.pack(side="right", fill="y")
        self.cv.pack(side="left", fill="both", expand=True)
        self.cv.configure(yscrollcommand=self.sb.set)
        self.cv.bind("<MouseWheel>", lambda e: self.cv.yview_scroll(-3 if e.delta > 0 else 3, "units"))
        self.cv.bind("<Button-1>", self._click)
        self.cv.bind("<Motion>", self._motion)
        self.cv.bind("<Configure>", lambda e: self.draw())
        self.hover = None
        t.bind("<Escape>", lambda e: self.close())
        self.show("popular")
        self.search.focus_set()

    def show(self, which):
        self.which = which
        for k, b in self.tabs.items():
            on = k == which
            b.configure(bg=C["sel"] if on else C["block_head"], fg=C["gold"] if on else C["text"])
        self.cv.yview_moveto(0)
        self.draw()

    def items(self):
        q = self.search.get().strip().lower()
        src = {"popular": self.popular, "all": self.all, "mine": self.mine}[self.which]
        return [f for f in src if q in f.lower()] if q else src

    def draw(self):
        cv = self.cv
        cv.delete("all")
        W = cv.winfo_width()
        rh = px(32)
        cur = self.app.cfg.get("row_font")
        self._items = self.items()
        for i, fam in enumerate(self._items):
            y = i * rh
            on = fam == cur
            if on or i == self.hover:
                cv.create_rectangle(0, y, W, y + rh, fill=C["sel"] if on else C["menu_hover"], width=0)
            cv.create_text(px(10), y + rh // 2, text=fam, font=(fam, -px(16)), fill=C["gold"] if on else C["text"],
                           anchor="w")
            cv.create_text(W - px(10), y + rh // 2, text="12.3K", font=(fam, -px(14)), fill=C["dim"], anchor="e")
            cv.create_line(0, y + rh - 1, W, y + rh - 1, fill=C["sep"])
        if not self._items:
            msg = ("No fonts added yet.\n\nClick \u201cAdd font file\u2026\u201d below to use any .ttf or .otf\n"
                   "(Morpheus, Expressway, fonts from WoW addons\u2026)") if self.which == "mine" and \
                not self.search.get().strip() else "No fonts match"
            cv.create_text(W // 2, px(70), text=msg, font=FONTS["ui"], fill=C["dim"], justify="center")
        cv.configure(scrollregion=(0, 0, W, max(1, len(self._items) * rh)))

    def _index(self, e):
        i = int(self.cv.canvasy(e.y) // px(32))
        return i if 0 <= i < len(getattr(self, "_items", [])) else None

    def _motion(self, e):
        i = self._index(e)
        if i != self.hover:
            self.hover = i
            self.draw()

    def _click(self, e):
        i = self._index(e)
        if i is None:
            return
        fam = self._items[i]
        self.app.set_cfg("row_font", fam)
        if self.on_pick:
            self.on_pick(fam)
        self.draw()

    def add_font(self):
        import shutil
        paths = filedialog.askopenfilenames(parent=self.top, title="Add font files",
                                            filetypes=[("Fonts", "*.ttf *.otf *.TTF *.OTF"), ("All files", "*.*")])
        if not paths:
            return
        try:
            os.makedirs(USER_FONT_DIR, exist_ok=True)
        except OSError:
            pass
        before = set(tkfont.families(self.app.root))
        for p in paths:
            dest = os.path.join(USER_FONT_DIR, os.path.basename(p))
            try:
                if os.path.abspath(p) != os.path.abspath(dest):
                    shutil.copyfile(p, dest)
                win_load_font(dest)
            except Exception:
                pass
        new = set(tkfont.families(self.app.root)) - before
        self.app._user_fams = set(getattr(self.app, "_user_fams", set())) | new
        self.app._fams = set(tkfont.families(self.app.root))
        self.mine = sorted(self.app._user_fams, key=str.lower)
        self.all = sorted(set(self.all) | new, key=str.lower)
        self.tabs["mine"].configure(text="My fonts (%d)" % len(self.mine))
        self.tabs["all"].configure(text="All (%d)" % len(self.all))
        self.show("mine")
        self.app.main.flash_title("Added %d font%s" % (len(new), "" if len(new) == 1 else "s") if new
                                  else "No new font families found in that file", 3)

    def close(self):
        FontPicker.current = None
        try:
            self.top.destroy()
        except Exception:
            pass
SB_CHOICES = [("none", "Nothing"), ("segment", "Segment name"), ("timer", "Fight timer"), ("dps", "Group DPS"),
              ("my_dps", "Your DPS"), ("damage", "Group damage"), ("deaths", "Deaths"), ("kills", "Kills")]


class DSlider(tk.Canvas):
    """Details!-style slider: a dark bar that fills up, with the value printed inside it."""

    def __init__(self, parent, lo, hi, res, value, on_change, live=True, length=180, bg=None, fmt_fn=None):
        super().__init__(parent, width=length, height=px(20), bg=bg or C["bg"], highlightthickness=0, bd=0,
                         cursor="sb_h_double_arrow")
        self.lo, self.hi, self.res = float(lo), float(hi), float(res)
        self.value = self._snap(value)
        self.on_change, self.live = on_change, live
        self.fmt_fn = fmt_fn or (lambda v: ("%d" % round(v)) if self.res >= 1 else ("%.1f" % v))
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Button-1>", self._drag)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", lambda e: self.on_change(self.value))
        self.bind("<MouseWheel>", self._wheel)

    def _snap(self, v):
        v = max(self.lo, min(self.hi, float(v)))
        return round(round((v - self.lo) / self.res) * self.res + self.lo, 6)

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        frac = (self.value - self.lo) / max(1e-9, self.hi - self.lo)
        self.create_rectangle(0, 0, w, h, fill=C["menu_bg"], outline=C["sep"])
        self.create_rectangle(1, 1, 1 + int((w - 2) * frac), h - 1, fill="#4b4654", width=0)
        self.create_rectangle(int((w - 2) * frac) - 1, 1, int((w - 2) * frac) + 2, h - 1, fill=C["gold"], width=0)
        self.create_text(w // 2, h // 2, text=self.fmt_fn(self.value), font=FONTS["uib"], fill=C["text"])

    def set_value(self, v, fire):
        v = self._snap(v)
        if v != self.value:
            self.value = v
            self.draw()
            if fire and self.live:
                self.on_change(v)

    def _drag(self, e):
        w = max(1, self.winfo_width())
        self.set_value(self.lo + (self.hi - self.lo) * min(1.0, max(0.0, e.x / w)), True)

    def _wheel(self, e):
        self.set_value(self.value + (self.res if e.delta > 0 else -self.res), True)
        if not self.live:
            self.on_change(self.value)
        return "break"


class OptionsWin(DarkWin):
    """Details!-style options panel: Scale on top, categories on the left, a page on the right."""

    PAGES = [("Display", "page_display"), ("Log File", "page_log"), ("Combat Log", "page_combat"),
             (None, None),
             ("Profiles", "page_profiles"), ("Skins", "page_skins"), ("Mids' Build", "page_mids"),
             (None, None),
             ("Bars: General", "page_bars"), ("Bars: Texts", "page_texts"), ("Themes", "page_themes"),
             ("Theme Editor", "page_editor"),
             (None, None),
             ("Title Bar", "page_title"), ("Window Body", "page_body"), ("Statusbar", "page_status"),
             ("Windows & Tabs", "page_windows"), ("Automation", "page_auto"), ("Tooltips", "page_tips"),
             (None, None),
             ("Rename Powers", "page_rename")]

    def __init__(self, app):
        super().__init__(app, APP_NAME + " Options", "opt_geometry",
                         "%dx%d+%d+%d" % (px(900), px(620), px(300), px(100)), min_size=(640, 420))
        self.right_buttons = [(G_CLOSE, lambda x, y: self.close(), "Close")]
        self.vars = {}
        self.page = app.cfg.get("opt_page") or "page_display"
        self.log_label = None
        self.pagef = None
        self.build()

    # ------------------------------------------------------------------ frame
    def build(self):
        for w in self.body.winfo_children():
            w.destroy()
        self.pagef = None
        top = tk.Frame(self.body, bg=C["title"])
        top.pack(side="top", fill="x")
        tk.Label(top, text="Scale:", bg=C["title"], fg=C["gold"], font=FONTS["head"]).pack(
            side="left", padx=(px(10), px(4)), pady=px(3))
        self._slider_widget(top, "ui_scale", 50, 200, 5, 100.0, length=px(170), bg=C["title"],
                            live=False).pack(side="left", pady=px(4))
        nav = tk.Frame(self.body, bg=C["menu_bg"], width=px(170))
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        self.nav_btns = {}
        tk.Frame(nav, bg=C["menu_bg"], height=px(6)).pack(fill="x")
        for label, page in self.PAGES:
            if label is None:
                tk.Frame(nav, bg=C["menu_bg"], height=px(10)).pack(fill="x")
                continue
            b = tk.Label(nav, text=label, anchor="w", font=FONTS["ui"], padx=px(10), pady=px(4), cursor="hand2",
                         bg=C["block_head"], fg=C["text"])
            b.pack(fill="x", padx=px(6), pady=px(1))
            b.bind("<Button-1>", lambda e, p=page: self.show_page(p))
            self.nav_btns[page] = b
        right = tk.Frame(self.body, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)
        self.sc = tk.Canvas(right, bg=C["bg"], highlightthickness=0, bd=0)
        self.sb = DScroll(right, self.sc)
        self.sb.pack(side="right", fill="y", padx=(0, px(2)), pady=(px(2), px(16)))
        self.sc.pack(side="left", fill="both", expand=True)
        self.sc.configure(yscrollcommand=self.sb.set, yscrollincrement=px(24))
        self.show_page(self.page if hasattr(self, self.page) else "page_display")
        tk.Misc.lift(self.grip)

    def show_page(self, page):
        self.page = page
        self.app.cfg["opt_page"] = page
        for p, b in self.nav_btns.items():
            on = p == page
            b.configure(bg=C["sel"] if on else C["block_head"], fg=C["gold"] if on else C["text"])
        self.sc.delete("all")
        if self.pagef is not None:
            self.pagef.destroy()
        f = self.pagef = tk.Frame(self.sc, bg=C["bg"])
        win = self.sc.create_window(0, 0, window=f, anchor="nw")
        f.bind("<Configure>", lambda e: self.sc.configure(scrollregion=self.sc.bbox("all")))
        self.sc.bind("<Configure>", lambda e: (self.sc.itemconfigure(win, width=e.width), self._relayout(e.width)))
        self.cols = [tk.Frame(f, bg=C["bg"]), tk.Frame(f, bg=C["bg"])]
        self.vars = {}
        self.log_label = None
        self._wide = None
        getattr(self, page)()
        f.update_idletasks()
        self._relayout()
        self.sc.yview_moveto(0)

        def wheel(e):
            self.sc.yview_scroll(-1 if e.delta > 0 else 1, "units")
            return "break"

        def bind_tree(w):
            w.bind("<MouseWheel>", wheel)
            for c in w.winfo_children():
                bind_tree(c)
        bind_tree(f)
        self.sc.bind("<MouseWheel>", wheel)

    def _relayout(self, width=None):
        """Two columns side by side when they fit, otherwise stacked."""
        c0, c1 = self.cols
        width = width or self.sc.winfo_width()
        need = c0.winfo_reqwidth() + c1.winfo_reqwidth() + px(60)
        wide = width >= need
        if wide == self._wide:
            return
        self._wide = wide
        c0.grid(row=0, column=0, sticky="nw", padx=(px(16), px(20)), pady=(0, px(8)))
        if wide:
            c1.grid(row=0, column=1, sticky="nw", padx=(0, px(16)), pady=(0, px(16)))
        else:
            c1.grid(row=1, column=0, sticky="nw", padx=(px(16), px(16)), pady=(0, px(16)))

    # ----------------------------------------------------------------- widgets
    def section(self, col, text):
        tk.Label(self.cols[col], text=text, bg=C["bg"], fg=C["gold"], font=FONTS["head_big"], anchor="w").pack(
            fill="x", pady=(px(14), px(4)))

    def note(self, col, text):
        tk.Label(self.cols[col], text=text, bg=C["bg"], fg=C["faint"], font=FONTS["small"], anchor="w",
                 justify="left", wraplength=px(330)).pack(fill="x", pady=(px(2), px(4)))

    def check(self, col, key, text, after=None):
        v = tk.BooleanVar(value=bool(self.app.cfg.get(key)))
        self.vars[key] = v

        def cmd():
            self.app.set_cfg(key, bool(v.get()))
            if after:
                after()
        tk.Checkbutton(self.cols[col], text=text, variable=v, bg=C["bg"], fg=C["text"], selectcolor=C["menu_bg"],
                       activebackground=C["bg"], activeforeground=C["text"], font=FONTS["ui"], anchor="w",
                       bd=0, highlightthickness=0, command=cmd).pack(fill="x", pady=px(1))

    def _slider_widget(self, parent, key, lo, hi, res, mult, length=None, bg=None, live=True):
        integer = res >= 1 and mult == 1.0

        def apply(val):
            val = val / mult if mult != 1.0 else val
            if integer:
                val = int(round(val))
            if val != self.app.cfg.get(key):
                self.app.set_cfg(key, val)
        fmt_fn = None
        if mult == 100.0:
            fmt_fn = lambda v: "%d%%" % round(v)
        return DSlider(parent, lo, hi, res, float(self.app.cfg.get(key, lo)) * mult, apply, live=live,
                       length=length or px(190), bg=bg, fmt_fn=fmt_fn)

    def slider(self, col, key, text, lo, hi, res=1, mult=1.0, live=True):
        row = tk.Frame(self.cols[col], bg=C["bg"])
        row.pack(fill="x", pady=px(1))
        tk.Label(row, text=text, bg=C["bg"], fg=C["text"], font=FONTS["ui"], width=20, anchor="w").pack(side="left")
        self._slider_widget(row, key, lo, hi, res, mult, live=live).pack(side="left", pady=px(2))

    def dropdown(self, col, key, text, choices, getter=None, setter=None):
        row = tk.Frame(self.cols[col], bg=C["bg"])
        row.pack(fill="x", pady=px(3))
        tk.Label(row, text=text, bg=C["bg"], fg=C["text"], font=FONTS["ui"], width=20, anchor="w").pack(side="left")
        get = getter or (lambda: self.app.cfg.get(key))
        cur = dict(choices).get(get(), str(get()))
        btn = tk.Label(row, text=cur + "   ▾", bg=C["block_head"], fg=C["text"], font=FONTS["uib"],
                       padx=px(8), pady=px(2), cursor="hand2", anchor="w", width=20)
        btn.pack(side="left")

        def pick(val, lab):
            btn.configure(text=lab + "   ▾")
            if setter:
                setter(val)
            else:
                self.app.set_cfg(key, val)

        def open_menu(e):
            items = [{"label": lab, "check": get() == val, "cmd": lambda v=val, l=lab: pick(v, l)}
                     for val, lab in choices]
            DMenu(self.app, e.x_root, e.y_root, items)
        btn.bind("<Button-1>", open_menu)

    def color(self, col, key, text):
        row = tk.Frame(self.cols[col], bg=C["bg"])
        row.pack(fill="x", pady=px(3))
        sw = tk.Label(row, bg=self.app.cfg.get(key) or "#888888", width=3, relief="solid", bd=1, cursor="hand2")
        sw.pack(side="left", padx=(0, px(8)))
        lab = tk.Label(row, text=text, bg=C["bg"], fg=C["text"], font=FONTS["ui"], anchor="w", cursor="hand2")
        lab.pack(side="left")

        def choose(e=None):
            from tkinter import colorchooser
            res = colorchooser.askcolor(color=self.app.cfg.get(key), parent=self.top, title=text)
            if res and res[1]:
                sw.configure(bg=res[1])
                self.app.set_cfg(key, res[1])
        sw.bind("<Button-1>", choose)
        lab.bind("<Button-1>", choose)

    def button(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd, bg=C["block_head"], fg=C["text"], activebackground=C["sel"],
                      activeforeground=C["text"], relief="flat", bd=0, font=FONTS["ui"], padx=px(10), pady=px(3),
                      cursor="hand2")
        return b

    # ------------------------------------------------------------------ pages
    def page_display(self):
        a = self.app
        self.section(0, "General")
        self.dropdown(0, "num_format", "Number format",
                      [("short", "12.3K  (short)"), ("full", "12,345  (full)"), ("plain", "12345  (plain)")])
        self.slider(0, "update_interval", "Update interval (sec)", 0.1, 2.0, 0.1)
        self.slider(0, "wheel_speed", "Mouse wheel speed", 1, 5)
        self.dropdown(0, "time_measure", "Time measure",
                      [("effective", "Effective (whole fight)"), ("active", "Active (only while attacking)")])
        self.check(0, "realtime_dps", "Show real-time DPS (last 5 sec) while fighting")
        self.section(0, "Segments")
        self.slider(0, "max_segments", "Segments to keep", 5, 100)
        self.slider(0, "combat_timeout", "End fight after idle (sec)", 3, 60)
        self.check(0, "erase_trash", "Auto-erase short trash fights")
        self.slider(0, "trash_seconds", "...shorter than (sec)", 1, 30)

        self.section(1, "Overall Data")
        self.dropdown(1, "overall_clear", "Clear overall data",
                      [("manual", "Only when I reset"), ("zone", "On zone change"),
                       ("login", "On login / character switch")])
        self.section(1, "Pets")
        self.check(1, "show_pet_type", "Show pet type on bars")
        self.check(1, "tier_order", "Order pets by tier (Tier 3 first)")
        self.dropdown(1, None, "Grouping", [(tuple(sorted(k)), lab) for lab, k in GROUPINGS],
                      getter=lambda: tuple(sorted(a.collapsed)), setter=lambda k: a.set_grouping(list(k)))
        self.section(1, "Your Self")
        self.check(1, "self_color_on", "Use a different bar color for you")
        self.color(1, "self_color", "Your bar color")

    def page_log(self):
        a = self.app
        self.section(0, "Log File")
        self.log_label = tk.Label(self.cols[0], text="", bg=C["bg"], fg=C["dim"], font=FONTS["small"], anchor="w",
                                  justify="left", wraplength=px(560))
        self.log_label.pack(fill="x")
        row = tk.Frame(self.cols[0], bg=C["bg"])
        row.pack(fill="x", pady=px(6))
        self.button(row, "Use Today's Log", lambda: (a.set_log_auto(True), self.update_log_label())).pack(side="left")
        self.button(row, "Choose Log File…", lambda: (a.browse_log(), self.update_log_label())).pack(
            side="left", padx=px(6))
        self.button(row, "Logs Folder…", lambda: (a.browse_logs_dir(), self.update_log_label())).pack(side="left")
        self.check(0, "load_history", "Load earlier fights from today's log on start")
        self.note(0, "The game must have 'Log Chat' turned on (Options → Windows → Chat), and pet combat "
                     "channels added to a chat tab, for pet damage to show up.")
        self.update_log_label()

    def page_combat(self):
        self.section(0, "Death Recap")
        self.slider(0, "recap_window", "Recap length (sec)", 5, 30)
        self.slider(0, "recap_events", "Events to show", 10, 100)
        self.slider(0, "recap_min_heal", "Hide heals smaller than", 0, 500, 10)
        self.check(0, "recap_reverse", "Newest events first")
        self.check(0, "recap_show_misses", "Show attacks that missed you")
        self.section(1, "Parser")
        self.check(1, "dot_separate", "Show damage-over-time as its own line")
        self.check(1, "merge_crits", "Merge critical hits into normal hits")
        self.note(1, "Changing the damage-over-time option re-reads today's log.")

    def page_bars(self):
        self.section(0, "Bars")
        self.slider(0, "row_height", "Bar height", 14, 40)
        self.slider(0, "row_spacing", "Spacing", 0, 8)
        self.dropdown(0, "grow_up", "Bar growth direction", [(False, "Top to bottom"), (True, "Bottom to top")])
        self.dropdown(0, "bar_texture", "Texture",
                      BAR_STYLES)
        self.check(0, "show_icons", "Show icons")
        self.check(0, "row_border", "Thin border around bars")
        self.check(0, "total_bar", "Show a Total bar at the top")
        self.check(0, "aligned_cols", "Aligned text columns")
        self.section(1, "Colors")
        self.dropdown(1, "bar_color_mode", "Bar colors",
                      [("pet", "Each pet its own color"), ("tier", "By henchman tier"), ("single", "One color")])
        self.color(1, "bar_single_color", "Single bar color")
        self.color(1, "bar_bg_color", "Bar background")
        self.color(1, "self_color", "Your bar color (Display → Your Self)")

    def page_themes(self):
        a = self.app
        self.section(0, "Themes")
        self.note(0, "Click a theme to apply it. Want your own? Open the Theme Editor to change every color "
                     "and save it as a new theme.")
        eb = tk.Frame(self.cols[0], bg=C["bg"])
        eb.pack(fill="x", pady=px(4))
        self.button(eb, "Edit current theme", lambda: self._edit_load(a.cfg.get("theme", "minimal"))).pack(side="left")
        grid = tk.Frame(self.cols[0], bg=C["bg"])
        grid.pack(fill="x", pady=px(4))
        for i, (key, t) in enumerate([(k, v) for k, v in THEMES.items() if not k.startswith("__")]):
            on = a.cfg.get("theme", "minimal") == key
            cw, ch = px(250), px(96)
            card = tk.Canvas(grid, width=cw, height=ch, bg=t["C"].get("bg", BASE_C["bg"]), highlightthickness=2,
                             highlightbackground=C["gold"] if on else C["sep"], cursor="hand2", bd=0)
            card.grid(row=i // 2, column=i % 2, padx=px(5), pady=px(5))
            self._draw_theme_card(card, t, cw, ch, on)
            card.bind("<Button-1>", lambda e, k=key: a.root.after(10, lambda: a.set_theme(k)))
        self.section(1, "Bar Style")
        self.dropdown(1, "bar_texture", "Bar style", BAR_STYLES)
        self.check(1, "row_border", "Thin border around bars")
        self.slider(1, "row_spacing", "Spacing", 0, 8)
        self.note(1, "Picking a theme also sets its matching bar style; change it here any time.")

    # ---------------------------------------------------------------- theme editor
    THEME_FIELDS = [
        ("Window", [("title", "Title bar"), ("bg", "Window background"), ("border", "Window border"),
                    ("bar_bg", "Bar background"), ("row_alt", "Alternate rows"), ("sel", "Selected row"),
                    ("sep", "Separators / lines")]),
        ("Text & Accents", [("text", "Main text"), ("dim", "Secondary text"), ("faint", "Faint text"),
                            ("gold", "Accent color"), ("icon", "Icons"), ("icon_hover", "Icon hover"),
                            ("menu_head", "Menu headers")]),
        ("Menus & Panels", [("menu_bg", "Menu background"), ("menu_hover", "Menu hover"), ("block", "Panels"),
                            ("block_head", "Panel headers")]),
    ]

    def _edit_load(self, key):
        self.edit = theme_copy(THEMES.get(key) or THEMES["minimal"])
        self.edit_key = key
        self.show_page("page_editor")

    def _swatch(self, parent, text, get, set_, small=False):
        row = tk.Frame(parent, bg=C["bg"])
        sw = tk.Label(row, bg=get(), width=2 if small else 3, relief="solid", bd=1, cursor="hand2")
        sw.pack(side="left", padx=(0, px(6) if text else px(2)))
        lab = None
        if text:
            lab = tk.Label(row, text=text, bg=C["bg"], fg=C["text"], font=FONTS["ui"], anchor="w", cursor="hand2")
            lab.pack(side="left")

        def choose(e=None):
            from tkinter import colorchooser
            res = colorchooser.askcolor(color=get(), parent=self.top, title=text or "Color")
            if res and res[1]:
                set_(res[1].lower())
                sw.configure(bg=res[1])
                self._draw_preview()
        sw.bind("<Button-1>", choose)
        if lab is not None:
            lab.bind("<Button-1>", choose)
        return row

    def _draw_preview(self):
        cv = getattr(self, "_preview", None)
        if cv is None or not cv.winfo_exists():
            return
        cv.delete("all")
        cv.configure(bg=self.edit["C"]["bg"])
        self._draw_theme_card(cv, self.edit, int(cv.cget("width")), int(cv.cget("height")), False)

    def page_editor(self):
        a = self.app
        if getattr(self, "edit", None) is None:
            self._edit_load_quiet(a.cfg.get("theme", "minimal"))
        e = self.edit
        c0 = self.cols[0]
        self.section(0, "Theme Editor")
        self.note(0, "Start from any theme, change any color, then Apply to try it or Save it as your own.")
        self.dropdown(0, None, "Start from",
                      [(k, t["label"]) for k, t in THEMES.items() if not k.startswith("__")],
                      getter=lambda: self.edit_key, setter=self._edit_load)
        row = tk.Frame(c0, bg=C["bg"])
        row.pack(fill="x", pady=px(4))
        tk.Label(row, text="Theme name", bg=C["bg"], fg=C["text"], font=FONTS["ui"], width=20, anchor="w").pack(
            side="left")
        self._name = tk.Entry(row, bg=C["menu_bg"], fg=C["text"], insertbackground=C["text"], relief="flat",
                              font=FONTS["ui"], width=24)
        self._name.insert(0, e["label"] if self.edit_key.startswith("custom:") else "My " + e["label"].split(" \u2014")[0])
        self._name.pack(side="left")
        self._preview = tk.Canvas(c0, width=px(300), height=px(96), bg=e["C"]["bg"], highlightthickness=1,
                                  highlightbackground=C["sep"], bd=0)
        self._preview.pack(anchor="w", pady=px(6))
        self._draw_preview()
        btns = tk.Frame(c0, bg=C["bg"])
        btns.pack(fill="x", pady=px(2))
        self.button(btns, "Apply (try it)", self._edit_apply).pack(side="left")
        self.button(btns, "Save as theme", self._edit_save).pack(side="left", padx=px(6))
        if self.edit_key.startswith("custom:"):
            self.button(btns, "Delete", self._edit_delete).pack(side="left")
        btns2 = tk.Frame(c0, bg=C["bg"])
        btns2.pack(fill="x", pady=px(4))
        self.button(btns2, "Export (copy)", self._edit_export).pack(side="left")
        self.button(btns2, "Import (paste)", self._edit_import).pack(side="left", padx=px(6))

        self.section(0, "Bars")
        self.dropdown(0, None, "Bar style", BAR_STYLES, getter=lambda: e["texture"],
                      setter=lambda v: (e.__setitem__("texture", v), self._draw_preview()))
        for text, get, set_ in (
                ("Your bar", lambda: e["player"], lambda v: e.__setitem__("player", v)),
                ("Tier 3 (strongest)", lambda: e["tiers"][3], lambda v: e["tiers"].__setitem__(3, v)),
                ("Tier 2", lambda: e["tiers"][2], lambda v: e["tiers"].__setitem__(2, v)),
                ("Tier 1", lambda: e["tiers"][1], lambda v: e["tiers"].__setitem__(1, v)),
                ("Enemies", lambda: e["C"]["enemy"], lambda v: e["C"].__setitem__("enemy", v))):
            self._swatch(c0, text, get, set_).pack(fill="x", pady=px(2))
        self.section(0, "Pet Colors")
        grid = tk.Frame(c0, bg=C["bg"])
        grid.pack(anchor="w")
        for i in range(12):
            w = self._swatch(grid, "", lambda i=i: e["pets"][i], lambda v, i=i: e["pets"].__setitem__(i, v), True)
            w.grid(row=i // 6, column=i % 6, padx=px(2), pady=px(2))

        for title, fields in self.THEME_FIELDS:
            self.section(1, title)
            for key, text in fields:
                self._swatch(self.cols[1], text, lambda k=key: e["C"][k],
                             lambda v, k=key: e["C"].__setitem__(k, v)).pack(fill="x", pady=px(2))

    def _edit_load_quiet(self, key):
        self.edit = theme_copy(THEMES.get(key) or THEMES["minimal"])
        self.edit_key = key

    def _edit_apply(self):
        a = self.app
        t = theme_copy(self.edit)
        t["label"] = self._name.get().strip() or "Custom (unsaved)"
        a.cfg.setdefault("custom_themes", {})["__editing"] = theme_serialize(t)
        THEMES["__editing"] = t
        a.root.after(10, lambda: a.set_theme("__editing"))

    def _edit_save(self):
        import re
        a = self.app
        name = self._name.get().strip()
        if not name:
            a.main.flash_title("Give your theme a name first", 2.5)
            return
        key = "custom:" + (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "theme")
        t = theme_copy(self.edit)
        t["label"] = name
        self.edit["label"] = name
        store = a.cfg.setdefault("custom_themes", {})
        store[key] = theme_serialize(t)
        store.pop("__editing", None)
        THEMES.pop("__editing", None)
        THEMES[key] = t
        self.edit_key = key
        a.root.after(10, lambda: a.set_theme(key))

    def _edit_delete(self):
        a = self.app
        key = self.edit_key
        a.cfg.setdefault("custom_themes", {}).pop(key, None)
        THEMES.pop(key, None)
        self._edit_load_quiet("minimal")
        if a.cfg.get("theme") == key:
            a.root.after(10, lambda: a.set_theme("minimal"))
        else:
            a.save_cfg()
            self.show_page("page_editor")

    def _edit_export(self):
        a = self.app
        t = theme_serialize(self.edit)
        t["label"] = self._name.get().strip() or t["label"]
        a.root.clipboard_clear()
        a.root.clipboard_append("HEROMETER-THEME " + json.dumps(t, separators=(",", ":")))
        a.main.flash_title("Theme copied to the clipboard", 2.5)

    def _edit_import(self):
        a = self.app
        try:
            raw = a.root.clipboard_get().strip()
            if raw.startswith("HEROMETER-THEME"):
                raw = raw[len("HEROMETER-THEME"):].strip()
            t = theme_copy(json.loads(raw))
        except Exception:
            a.main.flash_title("Clipboard doesn't hold a Hero Meter theme", 3)
            return
        self.edit = t
        self.edit_key = "__import"
        self.show_page("page_editor")
        self._name.delete(0, "end")
        self._name.insert(0, t["label"])
        a.main.flash_title("Theme imported \u2014 Save it to keep it", 3)

    def _draw_theme_card(self, cv, t, w, h, on):
        tc = dict(BASE_C)
        tc.update(t["C"])
        th = px(20)
        cv.create_rectangle(0, 0, w, th, fill=tc["title"], width=0)
        cv.create_text(px(8), th // 2, text=t["label"], font=FONTS["uib"], fill=tc["text"], anchor="w")
        if on:
            cv.create_text(w - px(8), th // 2, text="\u2714", font=FONTS["uib"], fill=tc["gold"], anchor="e")
        rh = px(20)
        y = th + px(4)
        for name, color, frac in (("You", t["player"], 1.0), ("Lich", t["tiers"][3], 0.78),
                                  ("Zombie \u00d73", t["pets"][0], 0.55)):
            cv.create_rectangle(px(4), y, w - px(4), y + rh, fill=tc["bar_bg"], width=0)
            bw = int((w - px(8)) * frac)
            lines = bar_lines(color, rh, t["texture"])
            if t["texture"] == "outline":
                cv.create_rectangle(px(4), y, px(4) + bw - 1, y + rh - 1, fill=lines[0], outline=color)
            else:
                for gy, col in enumerate(lines):
                    cv.create_line(px(4), y + gy, px(4) + bw, y + gy, fill=col)
            cv.create_text(px(9), y + rh // 2 + 1, text=name, font=FONTS["small"], fill="#000000", anchor="w")
            cv.create_text(px(8), y + rh // 2, text=name, font=FONTS["small"], fill="#ffffff", anchor="w")
            y += rh + px(2)

    def page_texts(self):
        self.section(0, "Text")
        row = tk.Frame(self.cols[0], bg=C["bg"])
        row.pack(fill="x", pady=px(3))
        tk.Label(row, text="Font", bg=C["bg"], fg=C["text"], font=FONTS["ui"], width=20, anchor="w").pack(side="left")
        cur = self.app.cfg.get("row_font", "Oswald")
        fb = tk.Label(row, text=cur + "   \u25be", bg=C["block_head"], fg=C["text"], font=(cur, -px(15)),
                      padx=px(8), pady=px(2), cursor="hand2", anchor="w", width=18)
        fb.pack(side="left")
        fb.bind("<Button-1>", lambda e: FontPicker(self.app, e.x_root, e.y_root,
                                                    on_pick=lambda f: fb.configure(text=f + "   \u25be",
                                                                                   font=(f, -px(15)))))
        self.slider(0, "font_size", "Text size", 9, 26)
        self.dropdown(0, "text_style", "Text effect", [("shadow", "Shadow"), ("outline", "Outline"), ("none", "None")])
        self.check(0, "show_rank", "Show rank numbers")
        self.check(0, "show_pet_type", "Show pet type after the name")
        self.section(1, "Right Text")
        self.check(1, "rt_total", "Show total")
        self.check(1, "rt_ps", "Show per second")
        self.check(1, "rt_pct", "Show percent")
        self.dropdown(1, "bracket", "Bracket", [("(", "( )"), ("[", "[ ]"), ("none", "none")])

    def page_title(self):
        self.section(0, "Title Bar")
        self.slider(0, "title_height", "Height", 16, 36)
        self.slider(0, "title_font_size", "Text size", 9, 24)
        self.check(0, "title_bottom", "Title bar at the bottom")
        self.check(0, "autohide_buttons", "Hide buttons until mouse-over")
        self.section(1, "Buttons")
        self.check(1, "btn_segments", "Segments")
        self.check(1, "btn_report", "Report")
        self.check(1, "btn_reset", "Reset")
        self.check(1, "btn_min", "Minimize")
        self.note(1, "Settings and Close are always shown.")

    def page_body(self):
        self.section(0, "Window")
        self.slider(0, "alpha", "Opacity (%)", 20, 100, 1, 100.0)
        self.color(0, "body_bg", "Background color")
        self.check(0, "border_on", "Window border")
        self.color(0, "border_color", "Border color")
        self.check(0, "topmost", "Always on top (also above City of Heroes)")
        self.check(0, "no_focus", "Clicking the meter doesn't take focus from the game")
        self.check(0, "auto_dpi", "Match each monitor's Windows scaling automatically")
        self.section(1, "Click-Through")
        self.check(1, "click_through", "Click-through (clicks go to the game)")
        self.check(1, "click_through_combat", "Click-through only in combat")
        self.note(1, "Hold Ctrl to click the meter while click-through is on.")

    def page_status(self):
        self.section(0, "Statusbar")
        self.check(0, "statusbar", "Show statusbar")
        self.dropdown(0, "sb_left", "Left", SB_CHOICES)
        self.dropdown(0, "sb_center", "Center", SB_CHOICES)
        self.dropdown(0, "sb_right", "Right", SB_CHOICES)

    def _entry(self, parent, text="", width=22):
        e = tk.Entry(parent, bg=C["menu_bg"], fg=C["text"], insertbackground=C["text"], relief="flat",
                     font=FONTS["ui"], width=width)
        e.insert(0, text)
        return e

    def page_profiles(self):
        a = self.app
        c = a.cfg
        active = c.get("active_profile", "Default")
        self.section(0, "Profiles")
        self.note(0, "A profile holds every look & behavior setting plus your window layout. "
                     "Changes save to the active profile automatically.")
        box = tk.Frame(self.cols[0], bg=C["bg"])
        box.pack(fill="x", pady=px(4))
        for n in a.profile_names():
            on = n == active
            row = tk.Frame(box, bg=C["sel"] if on else C["block"])
            row.pack(fill="x", pady=px(1))
            tk.Label(row, text=("\u2714  " if on else "     ") + n, bg=row["bg"], fg=C["gold"] if on else C["text"],
                     font=FONTS["uib"], anchor="w", width=22).pack(side="left", padx=px(6), pady=px(3))
            if not on:
                self.button(row, "Load", lambda n=n: a.root.after(10, lambda: a.apply_profile(n))).pack(
                    side="left", padx=px(2))
                self.button(row, "Delete", lambda n=n: (a.delete_profile(n), self.show_page("page_profiles"))).pack(
                    side="left", padx=px(2))
            self.button(row, "Export", lambda n=n: a.export_profile(n)).pack(side="right", padx=px(2))
        self.section(0, "New Profile")
        row = tk.Frame(self.cols[0], bg=C["bg"])
        row.pack(fill="x", pady=px(3))
        tk.Label(row, text="Name", bg=C["bg"], fg=C["text"], font=FONTS["ui"]).pack(side="left", padx=(0, px(8)))
        ent = self._entry(row)
        ent.pack(side="left")
        row2 = tk.Frame(self.cols[0], bg=C["bg"])
        row2.pack(fill="x", pady=px(3))

        def new(blank):
            if not ent.get().strip():
                a.main.flash_title("Type a name for the profile first", 2.5)
                return
            a.root.after(10, lambda: a.save_profile_as(ent.get(), blank))
        self.button(row2, "Copy of current", lambda: new(False)).pack(side="left")
        self.button(row2, "Start from defaults", lambda: new(True)).pack(side="left", padx=px(6))
        self.section(0, "Share")
        row3 = tk.Frame(self.cols[0], bg=C["bg"])
        row3.pack(fill="x", pady=px(3))
        self.button(row3, "Import (paste)", lambda: (a.import_profile(), self.show_page("page_profiles"))).pack(
            side="left")
        self.button(row3, "Import from file\u2026",
                    lambda: (a.import_profile(True), self.show_page("page_profiles"))).pack(side="left", padx=px(6))
        self.button(row3, "Export active to file\u2026", lambda: a.export_profile(active, True)).pack(side="left")

        self.section(1, "Per Character")
        self.check(1, "auto_profile", "Switch profiles automatically when I log in")
        me = a.parser.player
        if me and me != "You":
            choices = [("", "(none \u2014 keep the current profile)")] + [(n, n) for n in a.profile_names()]

            def set_mine(v):
                if v:
                    c["char_profiles"][me] = v
                else:
                    c["char_profiles"].pop(me, None)
                a.save_cfg()
                self.show_page("page_profiles")
            self.dropdown(1, None, "Profile for " + truncate(FONTS["ui"], me, px(110)), choices,
                          getter=lambda: c["char_profiles"].get(me, ""), setter=set_mine)
        else:
            self.note(1, "Log in on a character (with Log Chat on) to give it its own profile.")
        if c.get("char_profiles"):
            self.note(1, "Assigned characters:")
            for ch, pn in sorted(c["char_profiles"].items()):
                row = tk.Frame(self.cols[1], bg=C["bg"])
                row.pack(fill="x", pady=px(1))
                tk.Label(row, text="%s  \u2192  %s" % (ch, pn), bg=C["bg"], fg=C["text"], font=FONTS["ui"],
                         anchor="w").pack(side="left")
                x = tk.Label(row, text="  \u2715", bg=C["bg"], fg=C["dim"], font=FONTS["ui"], cursor="hand2")
                x.pack(side="left")
                x.bind("<Button-1>", lambda e, ch=ch: (c["char_profiles"].pop(ch, None), a.save_cfg(),
                                                       self.show_page("page_profiles")))
        self.note(1, "\nGlobal (shared by all profiles): log file, renamed powers, pet types, "
                     "your custom themes and skins.")

    def page_skins(self):
        a = self.app
        self.section(0, "Skins")
        self.note(0, "A skin is the meter's shape: bar size, fonts, text style, title bar and statusbar. "
                     "Colors come from your theme.")
        grid = tk.Frame(self.cols[0], bg=C["bg"])
        grid.pack(fill="x", pady=px(4))
        cur = a.cfg.get("skin")
        for i, (key, sk) in enumerate(a.all_skins().items()):
            on = key == cur
            cw, ch = px(250), px(110)
            card = tk.Canvas(grid, width=cw, height=ch, bg=a.cfg["body_bg"], highlightthickness=2,
                             highlightbackground=C["gold"] if on else C["sep"], cursor="hand2", bd=0)
            card.grid(row=i // 2, column=i % 2, padx=px(5), pady=px(5))
            self._draw_skin_card(card, sk, cw, ch, on)
            card.bind("<Button-1>", lambda e, k=key: a.root.after(10, lambda: a.apply_skin(k)))
            if key.startswith("custom:"):
                card.bind("<Button-3>", lambda e, k=key: DMenu(a, e.x_root, e.y_root, [
                    {"label": "Delete this skin", "color": C["red"],
                     "cmd": lambda: (a.delete_skin(k), self.show_page("page_skins"))}]))
        self.section(1, "Your Own Skin")
        self.note(1, "Tweak sizes and fonts on the Bars, Texts and Title Bar pages, then save the look here.")
        row = tk.Frame(self.cols[1], bg=C["bg"])
        row.pack(fill="x", pady=px(3))
        ent = self._entry(row, width=20)
        ent.pack(side="left")

        def save():
            if a.save_skin_as(ent.get()):
                a.main.flash_title("Skin saved", 2)
                self.show_page("page_skins")
            else:
                a.main.flash_title("Type a name for the skin first", 2.5)
        self.button(row, "Save current look", save).pack(side="left", padx=px(6))
        self.note(1, "Right-click one of your skins to delete it.")

    def _draw_skin_card(self, cv, sk, w, h, on):
        c = self.app.cfg
        th = max(px(14), px(sk["title_height"] * 0.8))
        rh = max(px(10), px(sk["row_height"] * 0.8))
        fam = sk["row_font"] if sk["row_font"] in getattr(self.app, "_fams", ()) else "Segoe UI Semibold"
        f = (fam, -max(8, px(sk["font_size"] * 0.8)))
        tf = (fam, -max(8, px(sk["title_font_size"] * 0.8)))
        ty = h - th if sk["title_bottom"] else 0
        cv.create_rectangle(0, ty, w, ty + th, fill=C["title"], width=0)
        cv.create_text(px(6), ty + th // 2, text=sk["label"], font=tf, fill=C["text"], anchor="w")
        if on:
            cv.create_text(w - px(6), ty + th // 2, text="\u2714", font=tf, fill=C["gold"], anchor="e")
        top = 0 if sk["title_bottom"] else th
        sb = px(12) if sk["statusbar"] else 0
        y = top + px(2)
        rows = [("You", PLAYER_COLOR, 1.0, "52.1K"), ("Lich", TIER_COLORS.get(3, "#a0a0a0"), 0.72, "37.6K"),
                ("Zombie \u00d73", PET_COLORS[0], 0.45, "23.4K"), ("Grave Knight", PET_COLORS[1], 0.3, "15.7K")]
        if sk["total_bar"]:
            rows.insert(0, ("Total", "#6b6874", 1.0, "128.8K"))
        avail = h - th - sb - px(4)
        n = max(1, min(len(rows), avail // (rh + sk["row_spacing"])))
        order = rows[:n]
        for i, (name, color, frac, val) in enumerate(order):
            yy = (top + avail - (i + 1) * (rh + sk["row_spacing"])) if sk["grow_up"] else y
            cv.create_rectangle(0, yy, w, yy + rh, fill=c["bar_bg_color"], width=0)
            x0 = rh if sk["show_icons"] else 0
            if sk["show_icons"]:
                cv.create_rectangle(0, yy, rh, yy + rh, fill=shade(color, 0.42), width=0)
            bw = int((w - x0) * frac)
            for gy, col in enumerate(bar_lines(color, rh, c["bar_texture"])):
                cv.create_line(x0, yy + gy, x0 + bw, yy + gy, fill=col)
            if sk["row_border"]:
                cv.create_rectangle(0, yy, w - 1, yy + rh - 1, outline="#000000")
            label = ("%d. %s" % (i + 1, name)) if sk["show_rank"] and name != "Total" else name
            for (tx, ty2, txt, anc) in ((x0 + px(4), yy + rh // 2, label, "w"), (w - px(4), yy + rh // 2, val, "e")):
                if sk["text_style"] == "outline":
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        cv.create_text(tx + dx, ty2 + dy, text=txt, font=f, fill="#000000", anchor=anc)
                elif sk["text_style"] == "shadow":
                    cv.create_text(tx + 1, ty2 + 1, text=txt, font=f, fill="#000000", anchor=anc)
                cv.create_text(tx, ty2, text=txt, font=f, fill="#ffffff", anchor=anc)
            y += rh + sk["row_spacing"]
        if sb:
            sy = (h - th - sb) if sk["title_bottom"] else h - sb
            cv.create_rectangle(0, sy, w, sy + sb, fill=C["title"], width=0)
            cv.create_text(w // 2, sy + sb // 2, text="#12  1:24", font=(fam, -max(7, px(9))), fill=C["dim"])

    def page_mids(self):
        a = self.app
        c = a.cfg
        self.section(0, "Mids' Reloaded")
        exe = mids.mids_exe()
        self.note(0, ("Found Mids Reborn: " + exe) if exe else "Mids Reborn wasn't found (you can still link .mbd files).")
        builds = mids.find_builds()
        self.note(0, "%d saved build%s found in: %s" % (len(builds), "" if len(builds) == 1 else "s",
                                                        "; ".join(mids.build_dirs()[:2])))
        row = tk.Frame(self.cols[0], bg=C["bg"])
        row.pack(fill="x", pady=px(4))
        self.button(row, "Open build window", a.open_build).pack(side="left")
        self.check(0, "auto_build", "Match builds to characters by file name automatically")
        self.note(0, "Name a build file like \u201cMindguard - Tanker (...).mbd\u201d and it links itself.")
        self.section(1, "Linked Builds")
        if c.get("char_builds"):
            for ch, path in sorted(c["char_builds"].items()):
                r = tk.Frame(self.cols[1], bg=C["bg"])
                r.pack(fill="x", pady=px(1))
                tk.Label(r, text="%s  \u2192  %s" % (ch, os.path.basename(path)), bg=C["bg"], fg=C["text"],
                         font=FONTS["ui"], anchor="w").pack(side="left")
                x = tk.Label(r, text="  \u2715", bg=C["bg"], fg=C["dim"], font=FONTS["ui"], cursor="hand2")
                x.pack(side="left")
                x.bind("<Button-1>", lambda e, ch=ch: (c["char_builds"].pop(ch, None), a.save_cfg(),
                                                       self.show_page("page_mids")))
        else:
            self.note(1, "No builds linked by hand yet.")
        self.note(1, "\nThe build window shows:\n"
                     "\u2022 Value Ranking \u2014 which powers earn their slots\n"
                     "\u2022 Planned vs Actual \u2014 every power in the build vs the log\n"
                     "\u2022 Procs \u2014 whether slotted procs actually fire\n"
                     "\u2022 Not in Build \u2014 things you used that the plan doesn't have")

    def page_windows(self):
        a = self.app
        self.section(0, "Meter Windows")
        self.note(0, "You have %d meter window%s open. Each window (and each tab) shows its own "
                     "mode and segment." % (len(a.meters), "" if len(a.meters) == 1 else "s"))
        row = tk.Frame(self.cols[0], bg=C["bg"])
        row.pack(fill="x", pady=px(4))
        self.button(row, "Open a new window", lambda: (a.new_meter(a.main), self.show_page("page_windows"))).pack(
            side="left")
        self.section(0, "Snapping")
        self.check(0, "snap_windows", "Snap windows together when dragged close")
        self.note(0, "Snapped windows move together when you drag one of them.\n"
                     "Hold Alt while dragging to pull one window away.")
        self.section(1, "Tabs")
        self.check(1, "tabs_always", "Always show the tab bar")
        self.note(1, "Right-click a title \u2192 New tab / New window.\n"
                     "Click a tab to switch, click + to add one.\n"
                     "Right-click a tab to change what it shows.\n"
                     "Middle-click a tab to close it.\n"
                     "Closing the first (main) window closes them all.")

    def page_auto(self):
        self.section(0, "Combat")
        self.check(0, "ooc_fade", "Fade out when not in combat")
        self.slider(0, "ooc_alpha", "Out-of-combat opacity (%)", 0, 100, 1, 100.0)
        self.slider(0, "combat_alpha", "In-combat opacity (%)", 10, 100, 1, 100.0)
        self.check(0, "auto_current", "Switch to the current fight when a new one starts")
        self.section(1, "Mouse")
        self.check(1, "hover_fade", "Fade until mouse-over")
        self.slider(1, "hover_alpha", "Faded opacity (%)", 0, 100, 1, 100.0)
        self.note(1, "Hovering the meter always brings it back to full opacity.")

    def page_tips(self):
        self.section(0, "Tooltips")
        self.check(0, "tip_enabled", "Show tooltips")
        self.slider(0, "tip_font_size", "Text size", 9, 22)
        self.slider(0, "tip_lines", "Lines (hold Shift for all)", 3, 30)
        self.dropdown(0, "tip_side", "Position", [("cursor", "Next to the mouse"), ("window", "Beside the meter")])

    def page_rename(self):
        a = self.app
        self.section(0, "Rename / Merge Powers")
        self.note(0, "Give a power a new name, or merge two powers by giving them the same name "
                     "(e.g. 'Refracted Searing Beam' → 'Searing Beam').")
        box = tk.Frame(self.cols[0], bg=C["bg"])
        box.pack(fill="x", pady=px(4))
        rules = dict(a.cfg.get("renames") or {})

        def entry(parent, w=26):
            return tk.Entry(parent, bg=C["menu_bg"], fg=C["text"], insertbackground=C["text"], relief="flat",
                            font=FONTS["ui"], width=w)

        def save(new_rules):
            a.cfg["renames"] = new_rules
            a.save_cfg()
            self.show_page("page_rename")

        hdr = tk.Frame(box, bg=C["title"])
        hdr.pack(fill="x")
        for t, w in (("Power name in the log", 28), ("Show as", 28), ("", 4)):
            tk.Label(hdr, text=t, bg=C["title"], fg=C["gold"], font=FONTS["uib"], width=w, anchor="w").pack(
                side="left", padx=px(4))
        for i, (src, dst) in enumerate(sorted(rules.items())):
            r = tk.Frame(box, bg=C["row_alt"] if i % 2 else C["bg"])
            r.pack(fill="x")
            tk.Label(r, text=src, bg=r["bg"], fg=C["text"], font=FONTS["ui"], width=28, anchor="w").pack(
                side="left", padx=px(4))
            tk.Label(r, text=dst, bg=r["bg"], fg=C["text"], font=FONTS["ui"], width=28, anchor="w").pack(
                side="left", padx=px(4))
            x = tk.Label(r, text="✕", bg=r["bg"], fg=C["red"], font=FONTS["uib"], cursor="hand2")
            x.pack(side="left", padx=px(6))
            x.bind("<Button-1>", lambda e, s=src: save({k: v for k, v in rules.items() if k != s}))
        add = tk.Frame(self.cols[0], bg=C["bg"])
        add.pack(fill="x", pady=px(8))
        e1, e2 = entry(add), entry(add)
        e1.pack(side="left", padx=(0, px(6)))
        e2.pack(side="left", padx=(0, px(6)))

        def do_add():
            s, d = e1.get().strip(), e2.get().strip()
            if s and d and s != d:
                new = dict(rules)
                new[s] = d
                save(new)
        self.button(add, "Add", do_add).pack(side="left")
        row = tk.Frame(self.cols[0], bg=C["bg"])
        row.pack(fill="x", pady=px(6))

        def auto_refracted():
            names = set()
            for seg in [a.parser.overall] + list(a.parser.segments):
                for act in seg.actors.values():
                    names.update(act.powers.keys())
                    names.update(act.heal_powers.keys())
            new = dict(rules)
            for n in names:
                if n.startswith("Refracted "):
                    new[n] = n[len("Refracted "):]
            save(new)
        self.button(row, "Auto-merge 'Refracted' powers", auto_refracted).pack(side="left")
        self.button(row, "Apply & re-read log", lambda: (a.apply_cfg_all(), a.reparse())).pack(side="left",
                                                                                               padx=px(6))

    # ------------------------------------------------------------------ misc
    def update_log_label(self):
        if self.log_label is None or not self.log_label.winfo_exists():
            return
        a = self.app
        mode = "Automatic (today's log)" if a.cfg["log_auto"] else "Manual"
        self.log_label.configure(text="%s\n%s" % (mode, a.log_path or "No log file found"))

    def lift(self):
        self.update_log_label()
        super().lift()


# --------------------------------------------------------------------------
# Application controller
# --------------------------------------------------------------------------
class App:
    def __init__(self):
        global S
        win_dpi_aware()
        font_ok = win_load_font(res_path("fonts", "Oswald.ttf"))
        self.root = tk.Tk()
        self.root.withdraw()
        self.cfg = dict(DEFAULTS)
        self.load_cfg()
        load_custom_themes(self.cfg.get("custom_themes"))
        apply_theme_palette(self.cfg.get("theme", "minimal"))
        self._primary_dpi = max(1.0, self.root.winfo_fpixels("1i") / 96.0)
        self._dpi = self.initial_dpi()
        S = self.effective_scale()
        Fmt.abbreviate = self.cfg["abbreviate"]
        self._user_fams = load_user_fonts(self.root)
        fams = set(tkfont.families(self.root))
        row_fam = "Oswald" if (font_ok and "Oswald" in fams) else "Segoe UI Semibold"
        icon_fam = "Segoe Fluent Icons" if "Segoe Fluent Icons" in fams else "Segoe MDL2 Assets"
        FONTS["row"] = tkfont.Font(self.root, family=row_fam, size=-px(self.cfg["font_size"]))
        FONTS["title"] = tkfont.Font(self.root, family=row_fam, size=-px(14))
        FONTS["title_small"] = tkfont.Font(self.root, family=row_fam, size=-px(12))
        FONTS["big"] = tkfont.Font(self.root, family=row_fam, size=-px(24))
        FONTS["head_big"] = tkfont.Font(self.root, family=row_fam, size=-px(18))
        FONTS["head"] = tkfont.Font(self.root, family=row_fam, size=-px(13))
        FONTS["ui"] = tkfont.Font(self.root, family="Segoe UI", size=-px(13))
        FONTS["uib"] = tkfont.Font(self.root, family="Segoe UI Semibold", size=-px(13))
        FONTS["small"] = tkfont.Font(self.root, family="Segoe UI", size=-px(12))
        FONTS["tiny"] = tkfont.Font(self.root, family="Segoe UI Semibold", size=-px(10))
        FONTS["icon"] = tkfont.Font(self.root, family=icon_fam, size=-px(13))
        FONTS["icon_s"] = tkfont.Font(self.root, family=icon_fam, size=-px(11))
        FONTS["icon_big"] = tkfont.Font(self.root, family=icon_fam, size=-px(34))
        FONTS["tip"] = tkfont.Font(self.root, family="Segoe UI", size=-px(13))
        self._fams = fams
        self._oswald_ok = bool(font_ok and "Oswald" in fams)

        self.parser = cp.Parser(self.cfg["combat_timeout"], self.cfg["max_segments"], self.cfg["recap_window"])
        self.parser.typer.known.update(self.cfg.get("pet_types") or {})
        self.apply_cfg_all()
        self.collapsed = set(self.cfg.get("collapsed") or [])
        self.nodes, self.parents, self.ranks = {}, {}, {}
        self.seg_choice = "current"
        self.tail = None
        self.log_path = None
        self.tip = Tip(self)
        self.breakdown = None
        self.recap = None
        self.options = None
        self.build_win = None
        self.main = MainWindow(self)
        self.cur = self.main
        self.meters = [self.main]
        self.bd_src = self.main
        self.root.deiconify()
        self.root.update_idletasks()
        win_appwindow(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self._ver = -1
        self._last_draw = 0.0
        self._last_bd = 0.0
        self._last_day_check = 0.0
        self.choose_initial_log()
        self.root.after(200, self.poll)
        self.root.after(400, lambda: set_noactivate(self.root, self.cfg["no_focus"]))
        self.root.after(500, self.keep_on_top)
        self.root.after(600, self.install_fg_hook)
        self.root.after(1500, self.watch_monitor)
        self.root.after(300, self.auto_loop)
        self.root.after(250, self.restore_views)
        if not self.cfg.get("profiles"):
            self.cfg["profiles"] = {}
            self.cfg["active_profile"] = "Default"
        elif self.cfg.get("active_profile") not in self.cfg["profiles"]:
            self.cfg["active_profile"] = self.profile_names()[0]
        self.logged_out = False
        self._menu_since = None
        self.root.after(1200, self.watch_login)
        self.root.after(5000, self.check_updates)

    # --- multiple meter windows ---------------------------------------------
    @property
    def seg_choice(self):
        c = getattr(self, "cur", None)
        return c.seg_choice if c is not None else getattr(self, "_seg", "current")

    @seg_choice.setter
    def seg_choice(self, v):
        c = getattr(self, "cur", None)
        if c is not None:
            c.seg_choice = v
        else:
            self._seg = v

    def use(self, win):
        """Make 'win' the window whose mode/segment the shared drawing code reads."""
        self.cur = win
        self.cfg["mode"] = win.mode

    def restore_views(self):
        for v in (self.cfg.get("views") or [])[1:]:
            try:
                self._add_meter(v)
            except Exception:
                pass
        self.use(self.main)
        self.redraw(force=True)

    def _add_meter(self, view):
        m = MainWindow(self, view)
        self.meters.append(m)
        m.top.update_idletasks()
        set_noactivate(m.top, self.cfg["no_focus"])
        return m

    def new_meter(self, src=None):
        src = src or self.main
        pick = next((x for x in ("heal", "taken", "damage", "dps", "kills") if x not in src.tabs), "damage")
        L, T, R, B = src.rect()
        w, h = R - L, B - T
        ML, MT, MR, MB = monitor_area((L + R) // 2, (T + B) // 2, self.root)
        if R + w <= MR:
            x, y = R, T
        elif B + h <= MB:
            x, y = L, B
        elif L - w >= ML:
            x, y = L - w, T
        else:
            x, y = L + px(30), T + px(30)
        m = self._add_meter({"tabs": [pick], "tab": 0, "geom": "%dx%d+%d+%d" % (w, h, x, y)})
        self.use(m)
        self.redraw(force=True)
        self.save_views()
        m.flash_title("Right-click the title to pick what it shows", 3)
        return m

    def snap_group(self, win):
        tol = px(3)
        live = [m for m in self.meters if m.top.state() == "normal"]
        group, todo = [win], [win]
        while todo:
            a = todo.pop()
            ra = a.rect()
            for m in live:
                if m not in group and touching(ra, m.rect(), tol):
                    group.append(m)
                    todo.append(m)
        return group

    def save_views(self):
        try:
            self.cfg["views"] = [m.view_dict() for m in self.meters]
        except Exception:
            pass
        self.save_cfg()

    # --- config ----------------------------------------------------------
    def load_cfg(self):
        path = CONFIG_PATH
        if not os.path.isfile(path):
            for old in OLD_CONFIG_PATHS:     # first run after a rename: bring the old settings along
                if os.path.isfile(old):
                    path = old
                    break
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for k, v in data.items():
                if k in DEFAULTS:
                    self.cfg[k] = v
        except Exception:
            pass

    def save_cfg(self):
        if getattr(self, "main", None) is not None:
            self.cfg["mode"] = self.main.mode
        if not getattr(self, "_applying", False):
            profs = self.cfg.setdefault("profiles", {})
            profs[self.cfg.get("active_profile") or "Default"] = profile_snapshot(self.cfg)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
                json.dump(self.cfg, fh, indent=2)
        except Exception:
            pass

    def apply_cfg_all(self):
        """Push every setting into the parser / fonts / colors."""
        c = self.cfg
        Fmt.mode = c["num_format"] if c.get("abbreviate", True) or c["num_format"] != "short" else "full"
        COLOR_OPTS.update(mode=c["bar_color_mode"], single=c["bar_single_color"], self_on=bool(c["self_color_on"]),
                          self=c["self_color"], typer=self.parser.typer)
        p = self.parser
        p.combat_timeout = float(c["combat_timeout"])
        p.max_segments = int(c["max_segments"])
        p.recap_window = float(c["recap_window"])
        p.overall_clear = c["overall_clear"]
        p.trash_seconds = int(c["trash_seconds"]) if c["erase_trash"] else 0
        p.renames = dict(c.get("renames") or {})
        p.dot_separate = bool(c["dot_separate"])
        fam = c["row_font"]
        if fam == "Oswald" and not getattr(self, "_oswald_ok", False):
            fam = "Segoe UI Semibold"
        if fam not in getattr(self, "_fams", {fam}):
            fam = "Segoe UI Semibold"
        if "row" in FONTS:
            FONTS["row"].configure(family=fam, size=-px(c["font_size"]))
            FONTS["title"].configure(family=fam)
            FONTS["title_small"].configure(family=fam)
        FONT_BASE["title"] = int(c["title_font_size"])
        FONT_BASE["tip"] = int(c["tip_font_size"])
        if "title" in FONTS:
            FONTS["title"].configure(size=-px(FONT_BASE["title"]))
            FONTS["tip"].configure(size=-px(FONT_BASE["tip"]))
        _GRAD.clear()

    def set_cfg(self, key, value):
        self.cfg[key] = value
        self.apply_cfg_all()
        if key == "alpha":
            for w in self.windows():
                w.apply_alpha()
        elif key == "topmost":
            for w in self.windows():
                w.top.attributes("-topmost", bool(value))
        elif key == "no_focus":
            for m in self.meters:
                set_noactivate(m.top, bool(value))
        elif key in ("ui_scale", "auto_dpi"):
            if key == "auto_dpi" and value:
                t = self.main.top
                self._dpi = monitor_scale(t.winfo_rootx() + 20, t.winfo_rooty() + 20) or self._dpi
            self.rescale_all()
        elif key in ("title_height", "title_font_size"):
            for m in self.meters:
                m.rescale()
        elif key in ("btn_segments", "btn_report", "btn_reset", "btn_min", "autohide_buttons"):
            for m in self.meters:
                m.build_buttons()
                m.draw_title()
        elif key in ("title_bottom", "statusbar", "border_on", "border_color", "body_bg", "tabs_always"):
            for m in self.meters:
                m.apply_layout()
        elif key == "dot_separate":
            self.reparse()
        self.save_cfg()
        self.redraw(force=True, breakdown=True)

    def set_theme(self, name):
        if name not in THEMES:
            return
        old = apply_theme_palette(name)
        t = THEMES[name]
        c = self.cfg
        c["theme"] = name
        c["body_bg"], c["border_color"], c["bar_bg_color"] = C["bg"], C["border"], C["bar_bg"]
        c["bar_texture"] = t["texture"]
        if not c["self_color_on"]:
            c["self_color"] = PLAYER_COLOR
        mapping = {}
        for k, v in old.items():
            if k in C and v.lower() != C[k].lower():
                mapping.setdefault(v.lower(), C[k])
        for w in self.windows():
            try:
                recolor(w.top, mapping)
                w.draw_title()
            except Exception:
                pass
        self.apply_cfg_all()
        for m in self.meters:
            m.apply_layout()
        self.save_cfg()
        if self.options is not None:
            self.options.build()
        if self.recap is not None and self.recap.top.state() != "withdrawn":
            self.recap.draw()
        self.redraw(force=True, breakdown=True)
        self.main.flash_title("Theme: " + t["label"], 2)

    def reparse(self):
        """Re-read the current log from the start (after parser options changed)."""
        if self.log_path:
            seg = self.seg_choice
            self.open_log(self.log_path)
            self.seg_choice = seg if seg in ("current", "overall") else "current"
            if self.main:
                self.main.flash_title("Re-reading log\u2026")

    # --- automation: hover, fading, click-through, auto segment -----------------
    def current_alpha(self, hovering):
        c = self.cfg
        a = float(c["alpha"])
        if hovering:
            return a
        in_combat = self.parser.current is not None
        if in_combat:
            a *= float(c["combat_alpha"])
        elif c["ooc_fade"]:
            a *= float(c["ooc_alpha"])
        if c["hover_fade"]:
            a = min(a, float(c["alpha"]) * float(c["hover_alpha"]))
        return max(0.01, min(1.0, a))

    def auto_loop(self):
        try:
            in_combat = self.parser.current is not None
            want = bool(self.cfg["click_through"] or (self.cfg["click_through_combat"] and in_combat))
            if want and key_down(0x11):       # hold Ctrl to use the meter
                want = False
            for m in list(self.meters):
                t = m.top
                if t.state() != "normal":
                    continue
                mx, my = t.winfo_pointerxy()
                x, y = t.winfo_rootx(), t.winfo_rooty()
                hov = x <= mx < x + t.winfo_width() and y <= my < y + t.winfo_height()
                if hov != getattr(m, "_hovering", None):
                    m._hovering = hov
                    m.draw_title()
                a = self.current_alpha(hov)
                if abs(a - getattr(m, "_alpha_now", -1.0)) > 0.005:
                    m._alpha_now = a
                    t.attributes("-alpha", a)
                if want != getattr(m, "_ct", False):
                    m._ct = want
                    set_clickthrough(t, want)
            n = self.parser.seg_counter
            if n != getattr(self, "_seg_seen", n) and self.cfg["auto_current"]:
                for m in self.meters:
                    if m.seg_choice not in ("current", "overall"):
                        self.set_segment("current", m)
            self._seg_seen = n
        except Exception:
            pass
        self._health_tick = getattr(self, "_health_tick", 0) + 1
        if self._health_tick % 600 == 300:
            self.load_my_chars()
        if self._health_tick % 30 == 1:
            try:
                self.check_log_health()
            except Exception:
                pass
        self.root.after(100, self.auto_loop)

    def status_value(self, key, seg):
        if seg is None or key == "none":
            return ""
        dur = seg.duration()
        player = seg.actors.get(self.parser.player)
        if key == "segment":
            return "Overall" if seg.is_overall else "#%d %s" % (seg.number, seg.name)
        if key == "timer":
            return mmss(dur)
        if key == "dps":
            return "DPS " + fps(seg.total_damage / dur)
        if key == "my_dps":
            return "You " + fps((player.damage if player else 0) / dur)
        if key == "damage":
            return fmt(seg.total_damage)
        if key == "deaths":
            return "\u2620 %d" % len(seg.deaths)
        if key == "kills":
            return "Kills %d" % sum(a.kill_count for a in seg.actors.values())
        return ""

    # --- staying above the game ---------------------------------------------
    def keep_on_top(self):
        """The game window is itself 'always on top', so when it is the active window it can
        jump above us. We only re-raise when it actually covers one of our windows (no
        needless re-ordering = no flashing)."""
        try:
            tops = [w.top for w in self.windows()]
            if self.tip.top is not None:
                tops.append(self.tip.top)
            if DMenu.current is not None:
                tops.append(DMenu.current.top)
            if FontPicker.current is not None:
                tops.append(FontPicker.current.top)
            self._hwnds = [hwnd_of(t) for t in tops if t.winfo_exists() and t.state() == "normal"]
            self.raise_over_game()
        except Exception:
            pass
        self.root.after(50, self.keep_on_top)

    def raise_over_game(self):
        try:
            if not self.cfg["topmost"] or not game_is_active():
                return
            for h in list(getattr(self, "_hwnds", [])):
                if h and covered_by_game(h):
                    force_topmost_hwnd(h)
        except Exception:
            pass

    def install_fg_hook(self):
        """React the instant the game becomes the active window (instead of up to 200 ms later)."""
        try:
            proc_t = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_long,
                                        ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong)
            self._fg_proc = proc_t(lambda *a: self.raise_over_game())
            u = _u32()
            u.SetWinEventHook.restype = ctypes.c_void_p
            u.SetWinEventHook.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, proc_t,
                                          ctypes.c_ulong, ctypes.c_ulong, ctypes.c_uint]
            # EVENT_SYSTEM_FOREGROUND, WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS
            self._fg_hook = u.SetWinEventHook(0x0003, 0x0003, None, self._fg_proc, 0, 0, 0x0002)
        except Exception:
            self._fg_hook = None

    # --- scaling -------------------------------------------------------------
    def initial_dpi(self):
        import re
        m = re.search(r"\+(-?\d+)\+(-?\d+)", self.cfg.get("geometry") or "")
        if m:
            d = monitor_scale(int(m.group(1)) + 20, int(m.group(2)) + 20)
            if d:
                return d
        return self._primary_dpi

    def effective_scale(self):
        base = self._dpi if self.cfg["auto_dpi"] else self._primary_dpi
        return max(0.5, base * float(self.cfg["ui_scale"]))

    def rescale_all(self):
        global S
        new = self.effective_scale()
        if abs(new - S) < 0.005:
            return
        S = new
        _GRAD.clear()
        for k, base in FONT_BASE.items():
            if k in FONTS:
                FONTS[k].configure(size=-px(base))
        FONTS["row"].configure(size=-px(self.cfg["font_size"]))
        for w in self.windows():
            try:
                w.rescale()
            except Exception:
                pass
        self.redraw(force=True, breakdown=True)

    def check_monitor(self):
        """Meter moved to a monitor with different Windows scaling: keep the same look/size."""
        if not self.cfg["auto_dpi"]:
            return
        t = self.main.top
        d = monitor_scale(t.winfo_rootx() + t.winfo_width() // 2, t.winfo_rooty() + t.winfo_height() // 2)
        if not d or abs(d - self._dpi) < 0.01:
            return
        ratio = d / self._dpi
        self._dpi = d
        w, h = int(t.winfo_width() * ratio), int(t.winfo_height() * ratio)
        t.geometry("%dx%d" % (w, h))
        self.rescale_all()
        self.main.save_geom()

    def watch_monitor(self):
        try:
            if not getattr(self.main, "_drag", None):
                self.check_monitor()
        except Exception:
            pass
        self.root.after(500, self.watch_monitor)

    def toggle(self, key):
        self.set_cfg(key, not self.cfg[key])
        if self.options:
            v = self.options.vars.get(key)
            if v is not None:
                v.set(self.cfg[key])

    def windows(self):
        return list(getattr(self, "meters", [self.main])) + \
            [w for w in (self.breakdown, self.recap, self.options, self.build_win) if w is not None]

    # --- log handling ------------------------------------------------------
    def logs_dir(self):
        d = self.cfg.get("logs_dir")
        if d and os.path.isdir(d):
            return d
        root = self.game_root()
        found = cp.find_logs_dirs([root]) if root else []
        return found[0] if found else None

    def game_root(self, rescan=False):
        """Homecoming install folder: remembered > running game > next to the exe > usual folders."""
        g = self.cfg.get("game_dir")
        if g and os.path.isdir(os.path.join(g, "accounts")) and not rescan:
            return g
        hints = [game_process_dir(), app_dir(), os.getcwd()]
        if rescan or not getattr(self, "_scanned", False):
            self._scanned = True
            hints += common_game_dirs()
        for h in hints:
            r = game_root_of(h) if h else None
            if r:
                if r != self.cfg.get("game_dir"):
                    self.cfg["game_dir"] = r
                    self.save_cfg()
                return r
        return None

    def browse_game_dir(self):
        d = filedialog.askdirectory(parent=self.root, title="Where is City of Heroes (Homecoming) installed?",
                                    initialdir=self.cfg.get("game_dir") or "C:\\")
        if not d:
            return
        r = game_root_of(d)
        if not r:
            self.main.flash_title("No 'accounts' folder there \u2014 pick the Homecoming folder", 4)
            return
        self.cfg["game_dir"] = r
        self.cfg["logs_dir"] = ""
        self.save_cfg()
        self.choose_initial_log()
        self.main.flash_title("Found it!" if self.log_path else "Found the game \u2014 now turn on Log Chat", 3)

    def choose_initial_log(self):
        path = None
        if not self.cfg["log_auto"] and self.cfg["log_path"] and os.path.isfile(self.cfg["log_path"]):
            path = self.cfg["log_path"]
        else:
            path = cp.todays_log(self.logs_dir())
        self.open_log(path)

    def load_my_chars(self):
        """Character names on this account, from the game's accounts/<name>/playerslot.txt."""
        names = set()
        try:
            acct_dir = os.path.dirname(self.log_path or self.logs_dir() or "")
            if acct_dir and os.path.basename(acct_dir).lower() == "logs":
                acct_dir = os.path.dirname(acct_dir)
            path = os.path.join(acct_dir, "playerslot.txt")
            self._slot_path = path
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    parts = line.split('" "')
                    if len(parts) >= 3:
                        names.add(parts[2].strip().strip('"'))
        except Exception:
            pass
        if names:
            self.parser.my_chars = names
        return names

    def open_log(self, path, reset=True):
        if reset:
            self.parser.reset()
        self.log_path = path
        self.load_my_chars()
        self.log_path = path
        self.tail = cp.LogTail(path) if path else None
        if self.tail and not self.cfg["load_history"]:
            # skip old fights, but still learn the character name
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        if "respec to " in line and "You have granted" in line:
                            m = cp.TS_RE.match(line.rstrip())
                            if m:
                                self.parser.feed(line.rstrip())
                        if "Welcome to City of Heroes" in line or "Now entering" in line:
                            m = cp.TS_RE.match(line.rstrip())
                            if m:
                                nm = cp.R_NAME.match(m.group(2))
                                if nm:
                                    self.parser.player = nm.group(1).strip()
                self.tail.offset = os.path.getsize(path)
            except OSError:
                pass
        self.redraw(force=True)

    def set_log_auto(self, on):
        self.cfg["log_auto"] = bool(on)
        self.save_cfg()
        if on:
            path = cp.todays_log(self.logs_dir())
            if path != self.log_path:
                self.open_log(path)
        if self.options:
            self.options.update_log_label()

    def browse_log(self):
        init = os.path.dirname(self.log_path) if self.log_path else (self.logs_dir() or app_dir())
        path = filedialog.askopenfilename(parent=self.root, title="Choose a City of Heroes chat log",
                                          initialdir=init, filetypes=[("Chat logs", "chatlog*.txt"),
                                                                      ("Text files", "*.txt"), ("All", "*.*")])
        if path:
            self.cfg["log_auto"] = False
            self.cfg["log_path"] = path
            self.save_cfg()
            self.open_log(path)
        if self.options:
            self.options.update_log_label()

    def browse_logs_dir(self):
        d = filedialog.askdirectory(parent=self.root, title="Choose your Homecoming Logs folder",
                                    initialdir=self.logs_dir() or self.cfg.get("game_dir") or app_dir())
        if d:
            self.cfg["logs_dir"] = d
            self.save_cfg()
            if self.cfg["log_auto"]:
                self.open_log(cp.todays_log(d))
        if self.options:
            self.options.update_log_label()

    def status_message(self, seg):
        if not self.log_path:
            if not self.game_root():
                return ("City of Heroes wasn't found.\n\n"
                        "Start the game and the meter finds it by itself \u2014\n"
                        "or click here to choose your Homecoming folder.")
            return ("Found City of Heroes, but no chat logs yet.\n\n"
                    "In the game: Menu \u2192 Options \u2192 Windows \u2192 Chat \u2192 Log Chat\n"
                    "(or type  /logchat  in the chat box).")
        if getattr(self, "_at_select", False) and self.parser.current is None:
            return ("At character select\u2026\n\n"
                    "The meter switches over as soon as\nyour next character logs in.")
        if self.log_warning():
            return ("\u26a0  Your chat log isn't updating.\n\n"
                    "Enable Chat Log for this character in the game:\n"
                    "Menu \u2192 Options \u2192 Windows \u2192 Chat \u2192 Log Chat\n"
                    "(or type  /logchat  in the chat box)\n\n"
                    "Click here to enable it for you.")
        name = os.path.basename(self.log_path)
        if self.tail and not self.tail.done:
            return "Reading %s…" % name
        if self.cfg["mode"] == "deaths":
            return "No deaths in this segment.\n\nRight-click → 'Recap Last Moments' to capture one manually."
        if seg is None:
            return "Waiting for combat…\n%s" % name
        return "No %s data in this segment." % MODE_LABEL[self.cfg["mode"]].lower()

    # --- segments / modes -----------------------------------------------
    def get_segment(self):
        p = self.parser
        c = self.seg_choice
        if c == "overall":
            return p.overall
        if c == "current":
            if p.current is not None:
                return p.current
            last = p.segments[-1] if p.segments else None
            sw = getattr(self, "_switch_ts", 0)
            if last is not None and sw and last.last <= sw:
                return None
            return last
        for s in p.segments:
            if s.number == c:
                return s
        self.seg_choice = "current"
        return self.get_segment()

    def set_segment(self, choice, win=None):
        win = win or self.cur
        win.seg_choice = choice
        win.scroll = 0
        self.use(win)
        self.redraw(force=True, breakdown=True)

    def set_mode(self, mode, win=None):
        win = win or self.cur
        win.tabs[win.tab] = mode
        win.mode = mode
        win.scroll = 0
        win.drill = None
        self.use(win)
        self.save_views()
        self.redraw(force=True)

    def reset_data(self):
        self.parser.reset()
        for m in self.meters:
            m.seg_choice = "current"
        self.main.flash_title("Data reset")
        self.redraw(force=True, breakdown=True)

    # --- grouping ----------------------------------------------------------
    def group_click(self, key, shift):
        node = self.nodes.get(key)
        if node is None:
            return
        if not shift and node["children"] and key in self.collapsed:
            self.collapsed.discard(key)
            msg = "Expanded " + node["name"]
        else:
            parent = self.parents.get(key)
            if parent is None:
                return
            self.collapsed.add(parent)
            msg = "Grouped: " + self.nodes[parent]["name"]
        self.cfg["collapsed"] = sorted(self.collapsed)
        self.save_cfg()
        self.cur.flash_title(msg)
        self.redraw(force=True)

    def set_grouping(self, keys):
        self.collapsed = set(keys)
        self.cfg["collapsed"] = sorted(self.collapsed)
        self.save_cfg()
        self.redraw(force=True)

    def grouping_items(self):
        items = [{"header": True, "label": "GROUPING"}]
        for label, keys in GROUPINGS:
            items.append({"label": label, "check": set(keys) == self.collapsed,
                          "cmd": lambda k=keys: self.set_grouping(k)})
        return items

    # --- opening windows -------------------------------------------------
    def open_breakdown(self, row):
        mode = self.cfg["mode"]
        if mode == "deaths":
            self.open_recap(row.key)
            return
        self.bd_src = self.cur
        if self.breakdown is None:
            self.breakdown = Breakdown(self)
        self.breakdown.open(mode, row.key)

    def open_recap(self, idx):
        if self.recap is None:
            self.recap = RecapWin(self)
        self.recap.show(idx)

    # --- about / diagnostics / updates ---------------------------------------
    def open_url(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def about_menu(self, x, y):
        gh = "https://github.com/" + REPO
        items = [{"header": True, "label": "%s  v%s" % (APP_NAME.upper(), VERSION)},
                 {"label": "A Details!-style damage meter for City of Heroes", "disabled": True},
                 {"label": "Free & open source \u2014 GNU GPL v3", "disabled": True},
                 {"sep": True},
                 {"label": "Project page / downloads", "cmd": lambda: self.open_url(gh)},
                 {"label": "Report a bug or suggest a feature", "cmd": lambda: self.open_url(gh + "/issues")},
                 {"label": "Copy diagnostics (paste into a bug report)", "cmd": self.copy_diagnostics},
                 {"label": "Open my settings folder", "cmd": lambda: os.startfile(DATA_DIR)},
                 {"sep": True},
                 {"label": "Check for updates now", "cmd": lambda: self.check_updates(force=True)},
                 {"label": "Check for updates at startup", "check": bool(self.cfg.get("check_updates", True)),
                  "cmd": lambda: self.toggle("check_updates")}]
        DMenu(self, x, y, items, min_width=300)

    def diagnostics(self):
        import platform
        import re as _re

        def mask(t):
            return _re.sub(r"(?i)(accounts[\\/])[^\\/]+", r"\1<account>", str(t or ""))
        builds = mids.find_builds()
        lines = ["%s %s (%s)" % (APP_NAME, VERSION, "exe" if FROZEN else "source"),
                 "Windows: %s" % platform.platform(),
                 "Scale: S=%.2f  dpi=%.2f  ui=%.2f  auto_dpi=%s" % (S, getattr(self, "_dpi", 0), self.cfg["ui_scale"],
                                                                 self.cfg["auto_dpi"]),
                 "Settings: %s" % ("portable" if DATA_DIR == app_dir() else "AppData"),
                 "Game folder: %s" % (self.cfg.get("game_dir") or "not found"),
                 "Game running: %s" % bool(find_game_window()[0]),
                 "Log: %s" % mask(self.log_path),
                 "Log warning: %s   logged out: %s" % (self.log_warning(), getattr(self, "logged_out", False)),
                 "Mids: %s   builds found: %d" % ("yes" if mids.mids_exe() else "no", len(builds)),
                 "Theme: %s  Skin: %s  Profile: %s  Windows: %d" % (self.cfg.get("theme"), self.cfg.get("skin"),
                                                                    self.cfg.get("active_profile"), len(self.meters))]
        try:
            with open(ERROR_LOG, "r", encoding="utf-8", errors="replace") as fh:
                tail = fh.read()[-3000:]
            if tail.strip():
                lines += ["", "Recent errors:", mask(tail)]
        except OSError:
            lines.append("No errors logged.")
        return "\n".join(lines)

    def copy_diagnostics(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.diagnostics())
        self.main.flash_title("Diagnostics copied \u2014 paste them in your bug report", 3)

    def check_updates(self, force=False):
        if not force and (not self.cfg.get("check_updates", True)
                          or time.time() - float(self.cfg.get("last_update_check") or 0) < 6 * 3600):
            return
        import threading

        def work():
            res = None
            try:
                import urllib.request
                req = urllib.request.Request("https://api.github.com/repos/%s/releases/latest" % REPO,
                                             headers={"User-Agent": "HeroMeter/" + VERSION,
                                                      "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=6) as r:
                    data = json.loads(r.read().decode("utf-8"))
                tag = str(data.get("tag_name") or "")
                res = (tag, data.get("html_url") or "https://github.com/%s/releases" % REPO)
            except Exception:
                res = None
            self.root.after(0, lambda: self._update_result(res, force))
        threading.Thread(target=work, daemon=True).start()

    def _update_result(self, res, force):
        self.cfg["last_update_check"] = time.time()
        self.save_cfg()

        def vt(t):
            import re as _re
            return tuple(int(x) for x in _re.findall(r"\d+", t or "")[:3]) or (0,)
        if res and vt(res[0]) > vt(VERSION):
            self.update_info = res
            self.main.flash_title("\u2b06 Update %s available \u2014 see the \u2699 menu" % res[0], 6)
        elif force:
            self.main.flash_title("You're up to date (v%s)" % VERSION if res else "Couldn't reach GitHub", 3)

    def build_char(self):
        p = self.parser.player
        return p if p and p != "You" else getattr(self, "_name_before", "You")

    def open_build(self):
        if self.build_win is None:
            self.build_win = BuildWin(self)
        self.build_win.load()
        self.build_win.lift()

    def open_options(self):
        if self.options is None:
            self.options = OptionsWin(self)
        self.options.lift()

    def manual_recap(self):
        now = self.parser.last_line_ts or time.time()
        d = self.parser.record_death(self.parser.player, now, "manual")
        if d is not None:
            self.open_recap(len(self.parser.deaths) - 1)

    def show_tip(self, row, x, y):
        if not self.cfg["tip_enabled"]:
            return
        nlines = 999 if key_down(0x10) else int(self.cfg["tip_lines"])
        if row.kind == "header":
            if row.key == "@warn":
                self.tip.show(x, y, "Chat log isn't updating", row.color,
                              [("Click", "show how to fix it", 0, C["gold"])], row.key)
            else:
                self.tip.show(x, y, row.name, row.color, [("Click / right-click", "go back", 0, row.color)],
                              row.key)
            return
        drill = getattr(self.cur, "drill", None)
        if drill and row.kind == "power":
            self.show_power_tip(drill, row, x, y)
            return
        seg = self.get_segment()
        mode = self.cfg["mode"]
        if mode == "deaths" or seg is None:
            if mode == "deaths":
                d = self.parser.deaths[row.key] if 0 <= row.key < len(self.parser.deaths) else None
                if d:
                    lines = [("Killed by", d.killer or "-", 0, C["red"]),
                             ("Killing blow", d.killing_power or "-", 0, C["red"]),
                             ("Click", "open death recap", 0, C["red"])]
                    self.tip.show(x, y, row.name, row.color, lines, row.key)
            return
        bd = build_breakdown(self, seg, mode, row.key)
        if bd is None or not bd.tabs:
            self.tip.hide()
            return
        label, kind, data = bd.tabs[0]
        lines = []
        if kind == "stats":
            items = sorted(data, key=lambda it: -(it[2].rolls if bd.preset in ("accuracy", "avoid") else it[2].total))
            total = sum(it[2].total for it in items) or 1.0
            top = (items[0][2].total if items else 1) or 1
            for k, name, s, color in items[:nlines]:
                if bd.preset in ("accuracy", "avoid"):
                    p = (100.0 * (s.roll_hits if bd.preset == "accuracy" else s.roll_miss) / s.rolls) if s.rolls else 0
                    lines.append((name, "%.1f%% of %d" % (p, s.rolls), p / 100.0, color))
                else:
                    lines.append((name, "%s (%.1f%%)" % (fmt(s.total), 100 * s.total / total), s.total / top, color))
        else:
            items = sorted(data, key=lambda it: -it[1])
            total = sum(v for _n, v, _c in items) or 1.0
            top = (items[0][1] if items else 1) or 1
            for n, v, c in items[:nlines]:
                lines.append((n, "%s (%.1f%%)" % (fmt(v) if v != int(v) or v > 999 else "%d" % v, 100 * v / total),
                              v / top, c))
        title = row.name
        if row.kind == "group":
            node = self.nodes.get(row.key)
            if node:
                title = "%s  \u2014  %s" % (row.name, ", ".join(node["members"]))
        if row.kind == "pet":
            info = self.parser.typer.get(row.key)
            if info:
                title = "%s  —  %s" % (row.key, pettypes.describe(info))
        self.tip.show(x, y, title, row.color, lines, row.key)

    def show_power_tip(self, drill, row, x, y):
        bd = build_breakdown(self, self.get_segment(), drill[0], drill[1])
        if bd is None or not bd.tabs:
            return
        _l, kind, data = bd.tabs[0]
        if kind != "stats":
            self.tip.show(x, y, row.name, row.color, [("Amount", row.right, 0, row.color)], row.key)
            return
        s = None
        for k, _n, st, _c in data:
            if k == row.key:
                s = st
                break
        if s is None:
            return
        total = sum(it[2].total for it in data) or 1.0
        cnt = s.count
        lines = [("Total", fmt(s.total), s.total / total, row.color),
                 ("Share", "%.1f%%" % (100.0 * s.total / total), s.total / total, row.color),
                 (bd.per, fps(s.total / bd.dur), 0, row.color),
                 ("Hits", str(cnt), 0, row.color),
                 ("Average", fmt(s.total / cnt) if cnt else "-", 0, row.color),
                 ("Biggest", fmt(_smax(s)) if cnt else "-", 0, row.color)]
        if s.crit_count:
            lines.append(("Critical hits", "%d" % s.crit_count, 0, C["gold"]))
        if s.n_tick:
            lines.append(("Damage over time", "%s (%d ticks)" % (fmt(s.tick_total), s.n_tick), 0, row.color))
        if s.rolls:
            lines.append(("Accuracy", "%.1f%% of %d" % (100.0 * s.roll_hits / s.rolls, s.rolls), 0, row.color))
        lines.append(("Click", "full breakdown", 0, C["dim"]))
        self.tip.show(x, y, row.name, row.color, lines[:max(3, nlines_default(self))], row.key)

    def open_breakdown_at(self, mode, key, sel):
        self.bd_src = self.cur
        if self.breakdown is None:
            self.breakdown = Breakdown(self)
        self.breakdown.open(mode, key)
        self.breakdown.tab = 0
        self.breakdown.sel = sel
        self.breakdown.draw_table()
        self.breakdown.draw_detail()

    # --- chat log health -------------------------------------------------------
    def log_warning(self):
        return bool(getattr(self, "_log_warn", False))

    # --- logout / character select detection --------------------------------
    def _menu_title(self, title):
        """In the game world the window title is the zone name; at login / character select
        (or with the game closed) it isn't."""
        import re
        t = (title or "").strip()
        if not t:
            return True
        if t in getattr(self.parser, "zones", ()):
            return False
        return bool(re.search(r"city of (heroes|villains)|homecoming|login|select|loading|server", t, re.I))

    def _log_title(self, title, menu):
        try:
            p = os.path.join(DATA_DIR, "hero_meter_titles.log")
            if not os.path.isfile(p) or os.path.getsize(p) < 60000:
                with open(p, "a", encoding="utf-8") as fh:
                    fh.write("%s  %-40r  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), title,
                                                  "MENU/LOGGED OUT" if menu else "in game"))
        except Exception:
            pass

    # --- profiles --------------------------------------------------------------
    def profile_names(self):
        return sorted(self.cfg.get("profiles") or {}, key=lambda n: (n != "Default", n.lower()))

    def save_profile_as(self, name, blank=False):
        name = name.strip()
        if not name:
            return False
        self.save_views()
        snap = profile_snapshot(dict(DEFAULTS)) if blank else profile_snapshot(self.cfg)
        if blank:
            snap["geometry"] = self.cfg.get("geometry", "")
            snap["views"] = [self.main.view_dict()]
        self.cfg["profiles"][name] = snap
        self.apply_profile(name)
        return True

    def delete_profile(self, name):
        if name == self.cfg.get("active_profile") or name not in self.cfg["profiles"]:
            return
        del self.cfg["profiles"][name]
        for ch in [c for c, p in self.cfg["char_profiles"].items() if p == name]:
            del self.cfg["char_profiles"][ch]
        self.save_cfg()

    def apply_profile(self, name, flash=True):
        import copy
        profs = self.cfg.get("profiles") or {}
        if name not in profs:
            return
        self.save_views()                     # keep the profile we're leaving up to date
        self._applying = True
        try:
            for k, v in profs[name].items():
                if k in DEFAULTS and k not in GLOBAL_KEYS:
                    self.cfg[k] = copy.deepcopy(v)
            self.cfg["active_profile"] = name
            # windows: rebuild the layout this profile saved
            for m in self.meters[1:]:
                try:
                    m.top.destroy()
                except Exception:
                    pass
            self.meters = [self.main]
            self.bd_src = self.main
            views = self.cfg.get("views") or []
            v0 = views[0] if views else {}
            m = self.main
            m.tabs = [x for x in (v0.get("tabs") or []) if x in MODE_LABEL] or \
                [self.cfg["mode"] if self.cfg["mode"] in MODE_LABEL else "damage"]
            m.tab = max(0, min(int(v0.get("tab", 0)), len(m.tabs) - 1))
            m.mode = m.tabs[m.tab]
            m.drill, m.scroll = None, 0
            if self.cfg.get("geometry"):
                m.top.geometry(self.cfg["geometry"])
            for v in views[1:]:
                try:
                    self._add_meter(v)
                except Exception:
                    pass
            self.use(m)
            self.reapply_all()
        finally:
            self._applying = False
        self.save_views()
        if flash:
            self.main.flash_title("Profile: " + name, 2)

    def reapply_all(self):
        """Push every look/behavior setting to every window (after a profile or skin change)."""
        old = apply_theme_palette(self.cfg.get("theme", "minimal"))
        mapping = {}
        for k, v in old.items():
            if k in C and v.lower() != C[k].lower():
                mapping.setdefault(v.lower(), C[k])
        Fmt.abbreviate = self.cfg["abbreviate"]
        self.collapsed = set(self.cfg.get("collapsed") or [])
        self.apply_cfg_all()
        self.rescale_all()
        for w in self.windows():
            try:
                if mapping:
                    recolor(w.top, mapping)
                w.top.attributes("-topmost", bool(self.cfg["topmost"]))
                w.apply_alpha()
            except Exception:
                pass
        for m in self.meters:
            m.rescale()
            m.build_buttons()
            m.apply_layout()
            m.draw_title()
            set_noactivate(m.top, self.cfg["no_focus"])
        if self.options is not None:
            self.options.build()
        if self.recap is not None and self.recap.top.state() != "withdrawn":
            self.recap.draw()
        self.redraw(force=True, breakdown=True)

    def profile_for_character(self, name):
        if not self.cfg.get("auto_profile") or not name or name == "You":
            return
        prof = (self.cfg.get("char_profiles") or {}).get(name)
        if prof and prof in self.cfg["profiles"] and prof != self.cfg.get("active_profile"):
            self.root.after(50, lambda: self.apply_profile(prof))

    def export_profile(self, name, to_file=False):
        data = {"hero_meter_profile": name, "settings": (self.cfg["profiles"] or {}).get(name)}
        text = json.dumps(data, indent=1 if to_file else None, separators=None if to_file else (",", ":"))
        if to_file:
            path = filedialog.asksaveasfilename(parent=self.options.top if self.options else self.root,
                                                title="Export profile", initialfile=name + ".heromp",
                                                defaultextension=".heromp",
                                                filetypes=[("Hero Meter profile", "*.heromp"), ("All", "*.*")])
            if not path:
                return
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.main.flash_title("Profile saved to file", 2.5)
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append("HEROMETER-PROFILE " + text)
            self.main.flash_title("Profile copied to the clipboard", 2.5)

    def import_profile(self, from_file=False):
        try:
            if from_file:
                path = filedialog.askopenfilename(parent=self.options.top if self.options else self.root,
                                                  title="Import profile",
                                                  filetypes=[("Hero Meter profile", "*.heromp"), ("All", "*.*")])
                if not path:
                    return None
                raw = open(path, "r", encoding="utf-8").read()
            else:
                raw = self.root.clipboard_get()
            raw = raw.strip()
            if raw.startswith("HEROMETER-PROFILE"):
                raw = raw[len("HEROMETER-PROFILE"):].strip()
            data = json.loads(raw)
            settings = {k: v for k, v in data["settings"].items() if k in DEFAULTS and k not in GLOBAL_KEYS}
            base = str(data.get("hero_meter_profile") or "Imported").strip() or "Imported"
        except Exception:
            self.main.flash_title("That isn't a Hero Meter profile", 3)
            return None
        name, n = base, 2
        while name in self.cfg["profiles"]:
            name, n = "%s (%d)" % (base, n), n + 1
        self.cfg["profiles"][name] = settings
        self.save_cfg()
        self.main.flash_title("Imported profile: " + name, 3)
        return name

    # --- skins -----------------------------------------------------------------
    def all_skins(self):
        d = dict(SKINS)
        for k, v in (self.cfg.get("custom_skins") or {}).items():
            d["custom:" + k] = dict(v, label=k)
        return d

    def apply_skin(self, key):
        sk = self.all_skins().get(key)
        if sk is None:
            return
        for k in SKIN_KEYS:
            if k in sk:
                self.cfg[k] = sk[k]
        self.cfg["skin"] = key
        self.reapply_all()
        self.save_cfg()
        self.main.flash_title("Skin: " + sk["label"], 2)

    def save_skin_as(self, name):
        name = name.strip()
        if not name:
            return False
        self.cfg.setdefault("custom_skins", {})[name] = {k: self.cfg[k] for k in SKIN_KEYS}
        self.cfg["skin"] = "custom:" + name
        self.save_cfg()
        return True

    def delete_skin(self, key):
        if key.startswith("custom:"):
            self.cfg.get("custom_skins", {}).pop(key[7:], None)
            if self.cfg.get("skin") == key:
                self.cfg["skin"] = ""
            self.save_cfg()

    def character_unknown(self, msg, warn=False, select=False):
        """We no longer know who's playing: show 'You' and hide the old character's last fight."""
        p = self.parser
        self._name_before = p.player if p.player != "You" else getattr(self, "_name_before", "You")
        self._switch_ts = p.last_line_ts or 0
        self._force_warn = warn
        self._at_select = select
        if select:
            self._log_warn = False
        if p.current is not None:
            p._close_current()          # the old character's fight is over
            self._switch_ts = max(self._switch_ts, p.segments[-1].last if p.segments else 0)
        if p.player != "You":
            p.player = "You"
        p.version += 1
        self.main.flash_title(msg, 4)
        self.redraw(force=True)

    def watch_login(self):
        try:
            now = time.time()
            if not self.log_path and now - getattr(self, "_last_seek", 0) > 5:
                self._last_seek = now
                if game_process_dir():
                    self.choose_initial_log()
            hwnd, title = find_game_window()
            menu = not hwnd
            if (hwnd, title) != getattr(self, "_last_title", None):
                if hwnd and getattr(self, "_last_title", None) and getattr(self, "_at_select", False):
                    self._at_select = False                 # left character select
                    self._login_wall = now
                    self._need_welcome = True
                    self._logins_at_enter = getattr(self.parser, "login_count", 0)
                    self.redraw(force=True)
                self._last_title = (hwnd, title)
                self._log_title(title if hwnd else "<game not running>", menu)
            p = self.parser
            if getattr(self, "_need_welcome", False) and now - getattr(self, "_login_wall", now) > 6:
                self._need_welcome = False
                if not getattr(p, "last_login_welcome", False) or \
                        getattr(p, "login_count", 0) == getattr(self, "_logins_at_enter", -1):
                    # logged in, but this character's chat log is off
                    self._force_warn = True
                    self._log_size = os.path.getsize(self.log_path) if self.log_path and \
                        os.path.isfile(self.log_path) else -1
                    self.check_log_health()
                    self.main.flash_title("This character isn't logging chat", 3)
            # The game rewrites accounts/<name>/playerslot.txt when the character select
            # screen loads - the one reliable 'you left your character' signal.
            sp = getattr(self, "_slot_path", None)
            if sp:
                try:
                    mt = os.path.getmtime(sp)
                except OSError:
                    mt = None
                seen = getattr(self, "_slot_mtime", None)
                if mt is not None and seen is not None and mt != seen and hwnd:
                    self.load_my_chars()
                    self.character_unknown("Character select \u2014 waiting for your next character", select=True)
                self._slot_mtime = mt
            if menu:
                if self._menu_since is None:
                    self._menu_since = now
                if not self.logged_out and now - self._menu_since >= 4:
                    self.logged_out = True
                    self._name_before = p.player
                    self._out_ts = self._menu_since
                    self._back_ts = None
                    self.character_unknown("Logged out \u2014 waiting for your next character")
            else:
                self._menu_since = None
                if self.logged_out:
                    self.logged_out = False
                    self._back_ts = now
                    self._logins_at_back = getattr(p, "login_count", 0)
            # back in the world quickly with no 'Welcome' line: it was just a loading screen
            back = getattr(self, "_back_ts", None)
            if back and now - back > 15:
                self._back_ts = None
                if (p.player == "You" and getattr(p, "login_count", 0) == self._logins_at_back
                        and back - self._out_ts < 30 and getattr(self, "_name_before", "You") != "You"):
                    p.player = self._name_before
                    p.version += 1
        except Exception:
            pass
        self.root.after(1000, self.watch_login)

    def check_log_health(self):
        """Warn when the game is running but the chat log has stopped growing
        (typically a character that doesn't have 'Log Chat' turned on)."""
        now = time.time()
        hwnd, title = find_game_window()
        warn = False
        if hwnd and not getattr(self, "logged_out", False):
            size = -1
            if self.log_path and os.path.isfile(self.log_path):
                size = os.path.getsize(self.log_path)
            if size != getattr(self, "_log_size", None):
                if hasattr(self, "_log_size"):
                    self._force_warn = False
                first = not hasattr(self, "_log_size")
                self._log_size = size
                self._log_grow_ts = now
                if first and size >= 0:
                    self._log_grow_ts = os.path.getmtime(self.log_path)   # real time of the last log line
                self._title_at_grow = title
            quiet = now - getattr(self, "_log_grow_ts", now)
            changed = title != getattr(self, "_title_at_grow", title)
            if now < getattr(self, "_warn_snooze", 0):
                warn = False
            else:
                warn = ((self.log_path is None) or (quiet > 30 and changed) or quiet > 180
                        or bool(getattr(self, "_force_warn", False)))
        if warn != self.log_warning():
            self._log_warn = warn
            self.redraw(force=True)

    def chatlog_menu(self, x, y):
        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append("/logchat")
            self.main.flash_title("Copied /logchat")

        def dismiss():
            self._warn_snooze = time.time() + 600
            self._log_warn = False
            self.redraw(force=True)
        items = [{"header": True, "label": "CHAT LOG ISN'T UPDATING"},
                 {"label": "Copy /logchat  (then paste it in the game's chat)", "color": C["gold"], "cmd": copy},
                 {"label": "Type /logchat into the game for me", "cmd": self.enable_chat_log},
                 {"sep": True},
                 {"label": "Or in the game:  Menu \u2192 Options \u2192 Windows \u2192 Chat", "disabled": True},
                 {"label": "and turn on  'Log Chat'", "disabled": True},
                 {"label": "(/logchat switches logging on AND off \u2014 use it once)", "disabled": True},
                 {"sep": True},
                 {"label": "Dismiss for 10 minutes", "cmd": dismiss}]
        DMenu(self, x, y, items, min_width=330)

    def enable_chat_log(self):
        hwnd, _t = find_game_window()
        if not hwnd:
            self.main.flash_title("City of Heroes isn't running", 2.5)
            return
        before = os.path.getsize(self.log_path) if self.log_path and os.path.isfile(self.log_path) else -1
        send_chat_command(hwnd, "/logchat")
        self.parser.player = "You"          # the new character's name is picked up again from the log
        self._warn_snooze = time.time() + 20
        self._log_warn = False
        self.redraw(force=True)

        def verify():
            path = cp.todays_log(self.logs_dir()) if self.cfg["log_auto"] else self.log_path
            if path and path != self.log_path:
                self.open_log(path, reset=False)
            size = os.path.getsize(self.log_path) if self.log_path and os.path.isfile(self.log_path) else -1
            if size != before:
                self.main.flash_title("\u2714 Chat log is on", 3)
            else:
                self.main.flash_title("No new log lines yet \u2014 do something in game", 4)
        self.root.after(6000, verify)

    # --- report ------------------------------------------------------------
    def report(self, n, oneline, win=None):
        if win is not None:
            self.use(win)
        seg = self.get_segment()
        rows = build_rows(self, seg)[:n]
        seg_label = "Overall" if self.seg_choice == "overall" else ("%s" % seg.name if seg else "-")
        head = "Hero Meter: %s for %s [%s]" % (MODE_LABEL[self.cfg["mode"]], seg_label,
                                             mmss(seg.duration() if seg else 0))
        if oneline:
            text = head + ": " + "  ".join("%d.%s %s" % (i + 1, r.name, r.short) for i, r in enumerate(rows))
            text = text[:250]
        else:
            text = "\n".join([head] + ["%d. %s  %s" % (i + 1, r.name, r.right) for i, r in enumerate(rows)])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        self.cur.flash_title("Copied to clipboard!")

    # --- main loop -------------------------------------------------------
    def _bd_view(self):
        src = getattr(self, "bd_src", None)
        self.use(src if src in self.meters else self.main)

    def redraw(self, force=False, breakdown=False):
        prev = self.cur if self.cur in self.meters else self.main
        for m in list(self.meters):
            m.refresh()
        self._last_draw = time.time()
        self._ver = self.parser.version
        if self.breakdown is not None and (breakdown or force) and self.breakdown.top.state() != "withdrawn":
            self._bd_view()
            self.breakdown.refresh()
            self._last_bd = time.time()
        self.use(prev)

    def poll(self):
        backlog = False
        try:
            now = time.time()
            if self.tail is not None:
                lines = self.tail.read_new()
                if lines:
                    self._lines_wall = now
                    if getattr(self, "_at_select", False) and self.parser.current is not None:
                        self._at_select = False
                for line in lines:
                    self.parser.feed(line)
                backlog = not self.tail.done
            lc = getattr(self.parser, "login_count", 0)
            if lc != getattr(self, "_logins_seen", 0):
                # a login line named the character: start the 'current' view fresh
                self._logins_seen = lc
                self._switch_ts = self.parser.last_line_ts or 0
                self._force_warn = False
                self._at_select = False
                self._login_wall = now
                self._need_welcome = not getattr(self.parser, "last_login_welcome", True)
                if not self.tail or self.tail.done:
                    self.profile_for_character(self.parser.player)
            if not backlog:
                self.parser.tick(now)
            # day rollover for automatic mode
            if self.cfg["log_auto"] and now - self._last_day_check > 10:
                self._last_day_check = now
                path = cp.todays_log(self.logs_dir())
                if path and path != self.log_path:
                    self.open_log(path, reset=False)
            if self.parser.typer.changed:
                self.parser.typer.changed = False
                self.cfg["pet_types"] = self.parser.typer.known
                self.save_cfg()
                self._ver = -1
            changed = self.parser.version != self._ver
            if ((changed and now - self._last_draw >= float(self.cfg["update_interval"]))
                    or now - self._last_draw > 1.0):
                live = self.parser.current is not None
                prev = self.cur if self.cur in self.meters else self.main
                for m in list(self.meters):
                    if changed or live:
                        m.refresh()
                    else:
                        m.update_title()
                self.use(prev)
                self._ver = self.parser.version
                self._last_draw = now
            if (self.breakdown is not None and changed and now - self._last_bd > 1.0
                    and self.breakdown.top.state() != "withdrawn"):
                prev = self.cur
                self._bd_view()
                self.breakdown.refresh()
                self.use(prev)
                self._last_bd = now
            bw = self.build_win
            if bw is not None and changed and now - getattr(self, "_last_build", 0) > 2.0 \
                    and bw.top.state() != "withdrawn":
                self._last_build = now
                bw.refresh()
            if self.recap is not None and changed and self.recap.top.state() != "withdrawn":
                # keep the recap pointing at the newest death when it was already showing it
                pass
        except Exception as ex:  # keep running whatever happens
            try:
                with open(ERROR_LOG, "a", encoding="utf-8") as fh:
                    import traceback
                    fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")
            except Exception:
                pass
        self.root.after(60 if backlog else max(50, min(300, int(float(self.cfg["update_interval"]) * 500))),
                        self.poll)

    def quit(self):
        for w in self.windows():
            try:
                w.save_geom()
            except Exception:
                pass
        self.save_views()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    App().run()


if __name__ == "__main__":
    main()
