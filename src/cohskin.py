"""City of Heroes look for Hero Meter.

- coh_palette(): every window color, derived from the character's in-game window (border) color
- detect_border_color(): reads that color straight off the screen. CoH draws each window edge
  as the exact border color with a bevel of darker copies of the same color right beside it
  (x0.77, x0.59, x0.47, x0.38). Nothing in the 3D world looks like that, so the brightest
  line that has such a bevel is the border color.
- round_window(): rounded window corners (Windows region)
"""
import ctypes


# ------------------------------------------------------------------ colors
def _hex(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))


def _mix(base, tint, t):
    return _hex(*(base[i] + (tint[i] - base[i]) * t for i in range(3)))


def pct_to_rgb(p):
    return tuple(int(round(max(0, min(100, v)) * 2.55)) for v in p)


def rgb_to_pct(c):
    return tuple(int(round(v / 2.55)) for v in c)


PRESETS = [("Hero blue", (20, 60, 100)), ("Villain red", (100, 20, 20)), ("Praetorian gray", (60, 60, 64)),
           ("Ice", (80, 94, 100)), ("Emerald", (48, 100, 58)), ("Royal purple", (48, 0, 100)),
           ("Gold", (100, 80, 20)), ("Steel", (40, 40, 40))]


COH_KEY = "#010203"          # keyed see-through color for CoH windows (the frame is drawn behind)


def rrect_insets(h, r):
    """Per pixel row, how far a rounded rectangle of height h and corner radius r is pulled in."""
    import math
    out = []
    for y in range(h):
        d = None
        if y < r:
            d = r - y - 0.5
        elif y >= h - r:
            d = y - (h - r) + 0.5
        out.append(0 if d is None else int(round(r - math.sqrt(max(0.0, r * r - d * d)))))
    return out


def coh_palette(rgb):
    """All window colors for the CoH skin from the border color (0-255 RGB)."""
    t = tuple(rgb)
    lum = (0.3 * t[0] + 0.59 * t[1] + 0.11 * t[2]) / 255.0
    black = (10, 10, 13)
    grey = (150, 150, 155)
    hi = tuple(min(255, v * 1.25 + 30) for v in t)          # hover glow
    return {
        "border": _hex(*t),                                  # the bright bevel line
        "title": COH_KEY,                                    # see-through: the game frame shows
        "bg": COH_KEY,
        "bar_bg": _mix((6, 6, 8), t, 0.08),
        "row_alt": _mix(black, t, 0.14),
        "sel": _mix(black, t, 0.42),
        "sep": _mix(black, t, 0.38),
        "block": _mix(black, t, 0.10),
        "block_head": _mix((20, 20, 24), t, 0.24),
        "menu_bg": _mix(black, t, 0.13),
        "menu_hover": _mix((24, 24, 28), t, 0.40),
        "menu_head": "#ffb21f",
        "text": "#ffffff",
        "dim": _mix(grey, t, 0.30),
        "faint": _mix((95, 95, 100), t, 0.30),
        "icon": "#eceef2",
        "icon_hover": _hex(*hi),
        "gold": "#ffb21f",                                  # CoH's orange section headers
        "coh_glow": _hex(*hi),
        "coh_lum": "%.3f" % lum,
    }


# ------------------------------------------------------------------ detection
RATIOS = (0.77, 0.59, 0.47, 0.38)


def detect_border_color(img):
    """(r, g, b) of the CoH window border color in a screenshot (PIL image), or None."""
    import numpy as np
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    score = {}
    for arr in (a, np.ascontiguousarray(a.transpose(1, 0, 2))):
        h, w, _ = arr.shape
        if h < 8 or w < 60:
            continue
        eq = (np.abs(arr[:, 1:] - arr[:, :-1]).max(axis=2) <= 4)
        pad = np.zeros((h, w + 1), np.int8)
        pad[:, 1:w] = eq
        d = np.diff(pad.ravel())
        st = np.flatnonzero(d == 1) + 1
        en = np.flatnonzero(d == -1) + 1
        n = min(len(st), len(en))
        st, en = st[:n], en[:n]
        L = en - st + 1
        keep = L >= max(40, w // 30)
        st, L = st[keep], L[keep]
        rows = st // (w + 1)
        cols = st % (w + 1) - 1
        mid = np.clip(cols + L // 2, 0, w - 1)
        col = arr[rows, mid]
        mC = col.max(axis=1)
        bevel = np.zeros(len(rows), bool)
        for dy in (-2, -1, 1, 2):
            rr = np.clip(rows + dy, 0, h - 1)
            nb = arr[rr, mid]
            mN = nb.max(axis=1)
            r = mN / np.maximum(mC, 1)
            dev = np.abs(nb - col * r[:, None]).max(axis=1)
            bevel |= (r >= 0.3) & (r <= 0.9) & (dev <= np.maximum(4, 0.06 * mN)) & (mN >= 20)
        sel = (mC >= 60) & bevel
        for c, ln in zip(map(tuple, col[sel]), L[sel]):
            k = (int(c[0]) // 3, int(c[1]) // 3, int(c[2]) // 3)
            s = score.get(k)
            if s is None:
                score[k] = [int(ln), tuple(int(v) for v in c)]
            else:
                s[0] += int(ln)
    if not score:
        return None
    items = sorted(score.values(), key=lambda x: -x[0])
    top = items[0][0]
    if top < max(200, a.shape[1] // 6):          # not enough window edges on screen to be sure
        return None
    strong = [c for t, c in items if t >= 0.3 * top]
    return max(strong, key=lambda c: max(c))


def capture(rect, exclude=()):
    """Screenshot of rect=(l, t, r, b) with our own windows (exclude) blacked out."""
    from PIL import ImageGrab, ImageDraw
    img = ImageGrab.grab(bbox=rect, all_screens=True).convert("RGB")
    if exclude:
        dr = ImageDraw.Draw(img)
        for (l, t, r, b) in exclude:
            dr.rectangle([l - rect[0] - 2, t - rect[1] - 2, r - rect[0] + 2, b - rect[1] + 2], fill=(0, 0, 0))
    return img


# ------------------------------------------------------------------ window shape
def round_window(hwnd, w, h, radius):
    """Clip a window to a rounded rectangle (radius 0 = square again)."""
    try:
        g, u = ctypes.windll.gdi32, ctypes.windll.user32
        u.SetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
        if radius <= 0:
            u.SetWindowRgn(hwnd, None, True)
            return
        g.CreateRoundRectRgn.restype = ctypes.c_void_p
        rgn = g.CreateRoundRectRgn(0, 0, int(w) + 1, int(h) + 1, int(radius) * 2, int(radius) * 2)
        u.SetWindowRgn(hwnd, rgn, True)          # Windows owns the region afterwards
    except Exception:
        pass


def pill_insets(h):
    """Per-row left/right inset that turns an h-pixel-tall bar into a pill (round ends)."""
    import math
    r = h / 2.0
    out = []
    for y in range(h):
        dy = abs(y + 0.5 - r)
        out.append(int(round(r - math.sqrt(max(0.0, r * r - dy * dy)))))
    return out



def detect_window_color(img, min_regions=2):
    """The game's window color, read carefully: it must show up on at least two separate windows
    (a single highlighted button can't fool it), and borders near the bottom of the screen, where
    everyone's power tray sits, count extra. Returns (r, g, b) or None when it isn't sure."""
    import numpy as np
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    H0, W0 = a.shape[:2]
    gx, gy = max(1, W0 // 8), max(1, H0 // 8)
    score = {}
    for flip, arr in ((False, a), (True, np.ascontiguousarray(a.transpose(1, 0, 2)))):
        h, w, _ = arr.shape
        if h < 8 or w < 60:
            continue
        eq = (np.abs(arr[:, 1:] - arr[:, :-1]).max(axis=2) <= 4)
        pad = np.zeros((h, w + 1), np.int8)
        pad[:, 1:w] = eq
        d = np.diff(pad.ravel())
        st = np.flatnonzero(d == 1) + 1
        en = np.flatnonzero(d == -1) + 1
        n = min(len(st), len(en))
        st, en = st[:n], en[:n]
        L = en - st + 1
        keep = L >= max(40, w // 30)
        st, L = st[keep], L[keep]
        rows = st // (w + 1)
        cols = st % (w + 1) - 1
        mid = np.clip(cols + L // 2, 0, w - 1)
        col = arr[rows, mid]
        mC = col.max(axis=1)
        bevel = np.zeros(len(rows), bool)
        for dy in (-2, -1, 1, 2):
            rr = np.clip(rows + dy, 0, h - 1)
            nb = arr[rr, mid]
            mN = nb.max(axis=1)
            r = mN / np.maximum(mC, 1)
            dev = np.abs(nb - col * r[:, None]).max(axis=1)
            bevel |= (r >= 0.3) & (r <= 0.9) & (dev <= np.maximum(4, 0.06 * mN)) & (mN >= 20)
        sel = (mC >= 60) & bevel
        for c, ln, rw, cl in zip(map(tuple, col[sel]), L[sel], rows[sel], mid[sel]):
            x, y = (int(rw), int(cl)) if flip else (int(cl), int(rw))
            key = (int(c[0]) // 3, int(c[1]) // 3, int(c[2]) // 3)
            wgt = int(ln) * (1.5 if y > H0 * 0.62 else 1.0)          # the power tray lives down here
            s = score.get(key)
            if s is None:
                s = score[key] = [0.0, tuple(int(v) for v in c), set()]
            s[0] += wgt
            s[2].add((x // gx, y // gy))
    if not score:
        return None

    def separate(cells):
        cells = list(cells)
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                if max(abs(cells[i][0] - cells[j][0]), abs(cells[i][1] - cells[j][1])) >= 2:
                    return True
        return False
    ok = [s for s in score.values() if len(s[2]) >= min_regions and separate(s[2])]

    q = (a // 3).astype(np.int32)                                      # how many pixels of each color there are, in one pass
    counts = np.bincount((q[:, :, 0] * 7396 + q[:, :, 1] * 86 + q[:, :, 2]).ravel(), minlength=86 ** 3)

    def thin(s):                                    # a border line, not a big flat window body
        r, g, b = (v // 3 for v in s[1])
        n = sum(int(counts[(r + i) * 7396 + (g + j) * 86 + b + k])
                for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)
                if 0 <= r + i <= 85 and 0 <= g + j <= 85 and 0 <= b + k <= 85)
        return n <= 8 * s[0]
    ok = [s for s in ok if thin(s)]
    if not ok:
        return None
    ok.sort(key=lambda s: -s[0])
    top = ok[0][0]
    if top < max(200, W0 // 6):
        return None
    strong = [s[1] for s in ok if s[0] >= 0.3 * top]
    best = max(strong, key=lambda c: max(c))       # the bright line of the bevel is the real color

    def same_hue_brighter(c):                       # a brighter shade of the confirmed color
        m = max(best)
        if max(c) <= m or max(c) > m * 1.12:
            return False
        k = max(c) / float(m)
        return max(abs(c[i] - best[i] * k) for i in range(3)) <= max(4, 0.03 * max(c))
    extra = [s[1] for s in score.values() if s[0] >= 0.1 * top and same_hue_brighter(s[1])]
    return max(extra, key=lambda c: max(c)) if extra else best


def pick_color_at(img, x, y, radius=6):
    """The window color from a spot the player clicked on a game window's border.

    The click gives the color's tint; the brightest straight line of that same tint anywhere on
    screen (the top edge of the game's windows) gives its full strength. Returns (r, g, b) or None."""
    import numpy as np
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    H, W = a.shape[:2]
    x0, x1, y0, y1 = max(0, x - radius), min(W, x + radius + 1), max(0, y - radius), min(H, y + radius + 1)
    patch = a[y0:y1, x0:x1].reshape(-1, 3)
    if not len(patch):
        return None
    m = patch.max(axis=1)
    seed = a[min(H - 1, max(0, y)), min(W - 1, max(0, x))]
    if int(seed.max()) < 40:                  # clicked just off the line: use the brightest spot nearby
        seed = patch[int(m.argmax())]
    sm = int(seed.max())
    if sm < 25:
        return None
    tint = seed / float(sm)

    def same_tint(cols):
        cm = cols.max(axis=1).astype(float)
        return (np.abs(cols - tint[None, :] * cm[:, None]).max(axis=1) <= np.maximum(6, 0.05 * cm))

    best, best_len = None, 0
    minrun = max(20, W // 120)
    for arr in (a, np.ascontiguousarray(a.transpose(1, 0, 2))):
        h, w, _ = arr.shape
        eq = (np.abs(arr[:, 1:] - arr[:, :-1]).max(axis=2) <= 3)
        pad = np.zeros((h, w + 1), np.int8)
        pad[:, 1:w] = eq
        d = np.diff(pad.ravel())
        st = np.flatnonzero(d == 1) + 1
        en = np.flatnonzero(d == -1) + 1
        n = min(len(st), len(en))
        st, en = st[:n], en[:n]
        L = en - st + 1
        keep = L >= minrun
        st, L = st[keep], L[keep]
        if not len(st):
            continue
        rows = st // (w + 1)
        mid = np.clip(st % (w + 1) - 1 + L // 2, 0, w - 1)
        cols = arr[rows, mid]
        cm = cols.max(axis=1)
        ok = same_tint(cols) & (cm >= sm) & (cm <= min(255, sm * 3.2))
        for c, ln in zip(cols[ok], L[ok]):
            if best is None or int(c.max()) > int(best.max()) + 2 or (abs(int(c.max()) - int(best.max())) <= 2 and ln > best_len):
                best, best_len = c, int(ln)
    if best is None:
        best = seed
    return tuple(int(v) for v in best)
