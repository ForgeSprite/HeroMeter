"""Draws City of Heroes style window frames (title tab, sloped corners, beveled border) with Pillow.

Everything is drawn 4x larger and scaled down, so edges and corners come out smooth like the game's.
Shapes, shades and see-through amounts were measured from the game's own windows at 4K (scale 1.0).
The result is an RGBA image: the body and tab are partly transparent, like the game's windows.
"""
from PIL import Image, ImageDraw

SS = 4                                   # supersampling factor
CORNER_STRETCH = 1.2

# The bordered box's corner, measured row by row at 4K: how far the edge is pulled in at each row.
CORNER = [22, 22, 20, 17, 15, 14, 13, 12, 10, 10, 9, 8, 7, 7, 6, 5, 5, 4, 3, 3, 3, 2, 2, 2, 2, 1, 1, 0]
# The title tab's corner: one long gentle slope over the tab's whole height.
def _arc(r):
    import math
    return [int(round(r - math.sqrt(max(0.0, r * r - (r - i - 0.5) ** 2)))) for i in range(int(r))]


# The title tab is a tall rounded box whose lower half is hidden behind the window's border.
# Its corners are ovals (measured fit at 4K: 59 px wide, 75 px tall), so the part that shows above the
# border is one smooth sweep that is still curving when it slips behind the border.
TAB_RX, TAB_RY = 59.0, 75.0


def _oval_corner(rx, ry, n=96):
    """Points (pull-in, depth) along a quarter oval, traced finely so it leaves the flat top smoothly."""
    import math
    pts = []
    for k in range(n + 1):
        a = (math.pi / 2) * k / n                  # 0 = top of the curve, pi/2 = where it runs straight down
        pts.append((rx * (1 - math.sin(a)), ry * (1 - math.cos(a))))
    return pts


TAB_CORNER = _oval_corner(TAB_RX, TAB_RY)
TAB_H = 46                                               # tab height above the border, 4K pixels
# Border shades as a fraction of the window color, outside -> inside (6px), measured.
TOP_BEVEL = [1.0, 0.95, 0.77, 0.59, 0.47, 0.38]
BOTTOM_BEVEL = [0.985, 0.8, 0.62, 0.49, 0.39, 0.3]
SIDE_BEVEL = [0.475, 0.487, 0.535, 0.583, 0.556, 0.5]
INNER = [(0.48, (97, 93, 118)), (1.0, (93, 46, 106)), (1.0, (27, 8, 30))]   # tinted lines inside the border
TAB_FILL = (84, 94, 102)
BODY_ALPHA = 0.80                                        # how solid the black body is (game default look)
TAB_ALPHA = 0.62                                         # the game's title tab is see-through...
TAB_ALPHA_HOVER = 0.86                                   # ...and firms up while the mouse is over the window


def sh(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shape(x0, y0, x1, y1, s, prof=CORNER, top=True, bottom=True):
    """Clockwise outline of a box with the game's sloped corners. s = pixels per 4K-pixel."""
    if prof and isinstance(prof[0], tuple):          # already (pull-in, depth) points
        p = [(dx * s, dy * s) for dx, dy in prof]
    else:
        p = [(c * s, i * s) for i, c in enumerate(prof)]
    pts = []
    if top:
        pts += [(x0 + dx, y0 + dy) for dx, dy in reversed(p)]
        pts += [(x1 - dx, y0 + dy) for dx, dy in p]
    else:
        pts += [(x0, y0), (x1, y0)]
    if bottom:
        pts += [(x1 - dx, y1 - dy) for dx, dy in reversed(p)]
        pts += [(x0 + dx, y1 - dy) for dx, dy in p]
    else:
        pts += [(x1, y1), (x0, y1)]
    return pts


def _rings(size, pts, rings, fill):
    """RGBA: fill a shape, then lay rings inward from its edge, evenly all the way round.
    rings = [(thickness, (r, g, b, a)), ...] outside -> inside."""
    img = Image.new("RGBA", size, fill)
    d = ImageDraw.Draw(img)
    depth = sum(t for t, _c in rings)
    closed = pts + [pts[0]]
    for t, col in reversed(rings):
        d.line(closed, fill=col, width=max(1, int(round(2 * depth))), joint="curve")
        depth -= t
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def border_px(scale):
    return (len(SIDE_BEVEL) + len(INNER)) * scale


def metrics(scale, tab=True):
    """Screen pixels: (top of the border from the window top, border thickness incl. inner lines)."""
    return (int(round(TAB_H * scale)) if tab else 0), int(round(border_px(scale)))


def render(w, h, color, scale=1.0, tab=True, glow=False, body_alpha=BODY_ALPHA, tab_alpha=None):
    """Full window frame as RGBA (transparent outside, see-through body/tab) and the body rectangle."""
    S = scale * SS
    W, H = w * SS, h * SS
    bc = sh(color, 1.18) if glow else tuple(color[:3])
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top = int(round(TAB_H * S)) if tab else 0
    ba = int(255 * body_alpha)
    if tab:
        if tab_alpha is None:
            tab_alpha = TAB_ALPHA_HOVER if glow else TAB_ALPHA
        # measured: the game's tab is ~36% of the window color's brightness (a hint of gray keeps
        # very dark window colors from turning the tab black)
        tc = sh(mix(sh(bc, 0.36), (40, 44, 48), 0.15), 1.12 if glow else 1.0)
        ta = int(255 * tab_alpha)
        # the tab runs down behind the border, straight down its sides
        pts = shape(0, 0, W - 1, top + max(TAB_RY - TAB_H, len(CORNER) * CORNER_STRETCH) * S + 4 * S,
                    S, TAB_CORNER, True, False)
        t = _rings((W, H), pts, [(1 * S, (12, 12, 16, ta)), (1 * S, sh(tc, 0.85) + (ta,)),
                                 (1 * S, sh(tc, 1.2) + (ta,))], tc + (ta,))
        # the tab's lower half is hidden behind the window, so cut it away inside the border
        box_mask = Image.new("L", (W, H), 255)
        ImageDraw.Draw(box_mask).polygon(shape(0, top, W - 1, H - 1, S * CORNER_STRETCH), fill=0)
        from PIL import ImageChops
        t.putalpha(ImageChops.multiply(t.split()[3], box_mask))
        out = Image.alpha_composite(out, t)
    box = shape(0, top, W - 1, H - 1, S * CORNER_STRETCH)

    def ring_set(bevel):
        r = [(1 * S, sh(bc, f) + (255,)) for f in bevel]
        side_last = sh(bc, SIDE_BEVEL[-1])
        for k, (f, tint) in enumerate(INNER):
            c = mix(side_last, tint, f) if k == 0 else tint
            r.append((1 * S, c + (255 if k < 2 else 200,)))
        return r
    body = (4, 4, 5, ba)
    side = _rings((W, H), box, ring_set(SIDE_BEVEL), body)
    topi = _rings((W, H), box, ring_set(TOP_BEVEL), body)
    boti = _rings((W, H), box, ring_set(BOTTOM_BEVEL), body)
    # bright top and bottom edges, fading out along the corner slopes into the medium sides
    span = len(CORNER) * S * CORNER_STRETCH
    ft = Image.new("L", (W, H), 0)
    fb = Image.new("L", (W, H), 0)
    dt, db = ImageDraw.Draw(ft), ImageDraw.Draw(fb)
    for y in range(int(span)):
        v = int(255 * (1 - y / span) ** 1.5)
        dt.line((0, top + y, W, top + y), fill=v)
        db.line((0, H - 1 - y, W, H - 1 - y), fill=v)
    side = Image.composite(topi, side, ft)
    side = Image.composite(boti, side, fb)
    out = Image.alpha_composite(out, side)
    out = out.resize((w, h), Image.LANCZOS)
    b = border_px(scale)
    inner = (int(round(b)), int(round(top / SS + b)), int(round(w - b)), int(round(h - b)))
    return out, inner


def close_button(size, hot=False):
    """The game's close button: a dim mauve-gray disc, light rim, darker x, centered (RGBA size x size)."""
    W = size * SS
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = W / 2.0
    r = W / 2.0 - SS * 0.5
    d.ellipse((c - r, c - r, c + r, c + r), fill=(124, 126, 132, 255) if not hot else (190, 150, 156, 255))
    d.ellipse((c - r, c - r + r * 0.18, c + r, c + r), fill=(75, 73, 79, 255))
    r2 = r * 0.8
    d.ellipse((c - r2, c - r2, c + r2, c + r2), fill=(150, 64, 74, 255) if hot else (106, 80, 88, 255))
    r3 = r * 0.55
    d.ellipse((c - r3, c - r3 - r * 0.15, c + r3, c + r3 - r * 0.15),
              fill=(178, 96, 106, 255) if hot else (116, 104, 116, 255))
    a = r * 0.36
    wd = max(1, int(r * 0.26))
    col = (70, 30, 38, 255) if hot else (64, 46, 54, 255)
    d.line((c - a, c - a, c + a, c + a), fill=col, width=wd)
    d.line((c - a, c + a, c + a, c - a), fill=col, width=wd)
    return img.resize((size, size), Image.LANCZOS)


def premultiply_img(img):
    """RGBA -> an image holding premultiplied BGRA (what a layered window wants)."""
    from PIL import ImageChops
    r, g, b, a = img.split()
    r, g, b = (ImageChops.multiply(c, a) for c in (r, g, b))
    return Image.merge("RGBA", (b, g, r, a))


def premultiply(img):
    """RGBA -> premultiplied BGRA bytes + size, ready for a layered window."""
    return (premultiply_img(img).tobytes(), img.size)


_REF = {}


def _margins(scale, tab):
    import math
    mx = int(math.ceil(max(TAB_RX if tab else 0, CORNER[0] * CORNER_STRETCH) * scale)) + 4
    top = TAB_H * scale if tab else 0
    span = len(CORNER) * CORNER_STRETCH * scale
    mt = int(math.ceil(top + max((TAB_RY - TAB_H) * scale if tab else 0, span))) + 6
    mb = int(math.ceil(span)) + 6
    return mx, mt, mb


_REF_RGBA = {}


def render_fast_rgba(w, h, color, scale=1.0, tab=True, glow=False, body_alpha=BODY_ALPHA):
    """Same picture as render() (plain RGBA), built from a small cached frame with its straight
    middle pieces stretched, so it takes milliseconds instead of a tenth of a second."""
    mx, mt, mb = _margins(scale, tab)
    rw, rh = 2 * mx + 8, mt + mb + 8
    if w < rw or h < rh:
        return render(w, h, color, scale, tab=tab, glow=glow, body_alpha=body_alpha)[0]
    key = (tuple(color[:3]), round(scale, 4), tab, glow, round(body_alpha, 3))
    ref = _REF_RGBA.get(key)
    if ref is None:
        ref = render(rw, rh, color, scale, tab=tab, glow=glow, body_alpha=body_alpha)[0]
        if len(_REF_RGBA) > 40:
            _REF_RGBA.clear()
        _REF_RGBA[key] = ref
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs = [(0, mx, 0, mx), (mx, rw - mx, mx, w - mx), (rw - mx, rw, w - mx, w)]
    ys = [(0, mt, 0, mt), (mt, rh - mb, mt, h - mb), (rh - mb, rh, h - mb, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            piece = ref.crop((sx0, sy0, sx1, sy1))
            if (dx1 - dx0, dy1 - dy0) != piece.size:
                piece = piece.resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.paste(piece, (dx0, dy0))
    return out


def render_fast(w, h, color, scale=1.0, tab=True, glow=False, body_alpha=BODY_ALPHA):
    """Same picture as render(), premultiplied and ready to show, but in milliseconds.

    Only the corners and the tab's ends curve; everything between them is identical along its length.
    So one small frame is drawn once (and kept), and its straight middle pieces are stretched to size."""
    mx, mt, mb = _margins(scale, tab)
    rw, rh = 2 * mx + 8, mt + mb + 8
    if w < rw or h < rh:
        img, _ = render(w, h, color, scale, tab=tab, glow=glow, body_alpha=body_alpha)
        return premultiply(img)
    key = (tuple(color[:3]), round(scale, 4), tab, glow, round(body_alpha, 3))
    ref = _REF.get(key)
    if ref is None:
        img, _ = render(rw, rh, color, scale, tab=tab, glow=glow, body_alpha=body_alpha)
        ref = premultiply_img(img)
        if len(_REF) > 16:
            _REF.clear()
        _REF[key] = ref
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs = [(0, mx, 0, mx), (mx, rw - mx, mx, w - mx), (rw - mx, rw, w - mx, w)]
    ys = [(0, mt, 0, mt), (mt, rh - mb, mt, h - mb), (rh - mb, rh, h - mb, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            piece = ref.crop((sx0, sy0, sx1, sy1))
            if (dx1 - dx0, dy1 - dy0) != piece.size:
                piece = piece.resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.paste(piece, (dx0, dy0))
    return (out.tobytes(), (w, h))


def update_layered(hwnd, pm, x, y, alpha=255):
    """Show premultiplied pixels (from premultiply) on a WS_EX_LAYERED window at screen (x, y)."""
    import ctypes
    from ctypes import wintypes as wt
    data, (w, h) = pm
    u, g = ctypes.windll.user32, ctypes.windll.gdi32
    vp = ctypes.c_void_p

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                    ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                    ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                    ("biClrImportant", wt.DWORD)]

    class BLEND(ctypes.Structure):
        _fields_ = [("op", ctypes.c_ubyte), ("flags", ctypes.c_ubyte), ("alpha", ctypes.c_ubyte),
                    ("fmt", ctypes.c_ubyte)]
    u.GetDC.restype = vp
    u.GetDC.argtypes = [vp]
    u.ReleaseDC.argtypes = [vp, vp]
    g.CreateCompatibleDC.restype = vp
    g.CreateCompatibleDC.argtypes = [vp]
    g.CreateDIBSection.restype = vp
    g.CreateDIBSection.argtypes = [vp, vp, ctypes.c_uint, ctypes.POINTER(vp), vp, wt.DWORD]
    g.SelectObject.restype = vp
    g.SelectObject.argtypes = [vp, vp]
    g.DeleteObject.argtypes = [vp]
    g.DeleteDC.argtypes = [vp]
    u.UpdateLayeredWindow.argtypes = [vp, vp, vp, vp, vp, vp, wt.DWORD, vp, wt.DWORD]
    bih = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    sdc = u.GetDC(None)
    mdc = g.CreateCompatibleDC(sdc)
    bits = vp()
    hbmp = g.CreateDIBSection(sdc, ctypes.byref(bih), 0, ctypes.byref(bits), None, 0)
    ok = False
    try:
        ctypes.memmove(bits, data, len(data))
        old = g.SelectObject(mdc, hbmp)
        pt, src, sz = wt.POINT(int(x), int(y)), wt.POINT(0, 0), wt.SIZE(w, h)
        bl = BLEND(0, 0, max(0, min(255, int(alpha))), 1)
        ok = bool(u.UpdateLayeredWindow(vp(hwnd), sdc, ctypes.byref(pt), ctypes.byref(sz), mdc, ctypes.byref(src),
                                        0, ctypes.byref(bl), 2))
        g.SelectObject(mdc, old)
    finally:
        g.DeleteObject(hbmp)
        g.DeleteDC(mdc)
        u.ReleaseDC(None, sdc)
    return ok


# ------------------------------------------------------------------ menus (the game's Menu window)
MENU_TEXT = (138, 236, 255)          # the game's light cyan menu text
MENU_WHITE = (255, 255, 255)


def _font(path, size):
    """The game's font, or the closest Windows look-alike (Bahnschrift SemiBold) until it can be read."""
    from PIL import ImageFont
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        f = ImageFont.truetype(r"C:\Windows\Fonts\bahnschrift.ttf", size)
        try:
            f.set_variation_by_name("SemiBold")
        except Exception:
            pass
        return f
    except Exception:
        pass
    for f in (r"C:\Windows\Fonts\seguisb.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _otext(d, xy, text, font, fill, anchor="lm", ow=1):
    x, y = xy
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx or dy:
                d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255), anchor=anchor)
    d.text((x, y), text, font=font, fill=tuple(fill[:3]) + (255,), anchor=anchor)


def radio(size, on):
    """The game's round radio dot: lit (on) or dark (off)."""
    W = size * SS
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, r = W / 2.0, W / 2.0 - SS * 0.5
    d.ellipse((c - r, c - r, c + r, c + r), fill=(8, 8, 10, 255))
    r2 = r * 0.8
    d.ellipse((c - r2, c - r2, c + r2, c + r2), fill=(150, 160, 170, 255) if on else (46, 50, 54, 255))
    r3 = r * 0.6
    d.ellipse((c - r3, c - r3 - r * 0.12, c + r3, c + r3 - r * 0.12),
              fill=(215, 225, 235, 255) if on else (72, 78, 84, 255))
    r4 = r * 0.22
    d.ellipse((c - r4 - r * 0.2, c - r4 - r * 0.38, c + r4 - r * 0.2, c + r4 - r * 0.38),
              fill=(250, 252, 255, 255) if on else (110, 116, 122, 255))
    return img.resize((size, size), Image.LANCZOS)


class MenuLook:
    """Sizes for a CoH-style menu at a given scale (1.0 = the game at 4K)."""
    def __init__(self, scale, font_path):
        self.sc = sc = scale
        self.ih = max(16, int(round(46 * sc)))          # item height
        self.hh = max(16, int(round(50 * sc)))          # header height
        self.sep = max(8, int(round(26 * sc)))          # separator height
        self.pad = max(6, int(round(16 * sc)))
        self.dot = max(10, int(round(24 * sc)))
        self.tx = self.pad + self.dot + max(6, int(round(12 * sc)))
        self.font = _font(font_path, max(10, int(round(29 * sc))))
        self.small = _font(font_path, max(9, int(round(23 * sc))))
        self.head = _font(font_path, max(10, int(round(31 * sc))))
        self.radius = max(6, int(round(22 * sc)))
        self.ow = max(1, int(round(1.3 * sc)))


def menu_size(items, look, min_w):
    w = min_w
    h = look.pad
    for it in items:
        if it.get("sep"):
            h += look.sep
            continue
        if it.get("header"):
            w = max(w, int(look.head.getlength(it["label"])) + 2 * look.pad + 20)
            h += look.hh
            continue
        lw = look.tx + int(look.font.getlength(it.get("label", ""))) + look.pad * 2
        if it.get("right"):
            lw += int(look.small.getlength(it["right"])) + look.pad * 2
        w = max(w, lw)
        h += look.ih
    return w, h + look.pad


def menu_hot(base, items, look, w, slot, alpha=0.78):
    """The menu with one row lit, built from the plain menu (fast: only that row is redrawn)."""
    y0, y1, i = slot
    it = items[i]
    img = base.copy()
    band = Image.new("RGBA", (w - 2 * look.pad, (y1 - y0) - 4), (255, 255, 255, 26))
    img.alpha_composite(band, (look.pad, y0 + 2))
    d = ImageDraw.Draw(img)
    _otext(d, (look.tx, y0 + (y1 - y0) // 2), it.get("label", ""), look.font, MENU_WHITE, "lm", look.ow)
    return img


def render_menu(items, look, w, h, hover=-1, alpha=0.78):
    """The whole menu as an RGBA image + the clickable rows [(y0, y1, index)]."""
    S = SS
    panel = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    r = look.radius * S
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), r, fill=(150, 156, 162, 235))            # thin light rim
    d.rounded_rectangle((1.6 * S, 1.6 * S, w * S - 1 - 1.6 * S, h * S - 1 - 1.6 * S), r - 1.6 * S,
                        fill=(0, 0, 0, 255))
    d.rounded_rectangle((2.6 * S, 2.6 * S, w * S - 1 - 2.6 * S, h * S - 1 - 2.6 * S), r - 2.6 * S,
                        fill=(6, 6, 8, int(255 * alpha)))
    img = panel.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    slots = []
    y = look.pad
    dots = {}
    for i, it in enumerate(items):
        if it.get("sep"):
            cy = y + look.sep // 2
            x0, x1 = int(w * 0.36), int(w * 0.64)
            for x in range(x0, x1):
                t = abs((x - x0) / max(1, (x1 - x0)) * 2 - 1)
                a = int(230 * (1 - t ** 2))
                d.line((x, cy, x, cy + max(1, int(look.sc * 2)) - 1), fill=(255, 255, 255, a))
            y += look.sep
            continue
        if it.get("header"):
            lab = it["label"].title() if it["label"].isupper() else it["label"]
            _otext(d, (w // 2, y + look.hh // 2), lab, look.head, MENU_WHITE, "mm", look.ow)
            y += look.hh
            continue
        ih = look.ih
        hot = i == hover and not it.get("disabled")
        if hot:
            band = Image.new("RGBA", (w - 2 * look.pad, ih - 4), (255, 255, 255, 26))
            img.alpha_composite(band, (look.pad, y + 2))
        if "check" in it:
            on = bool(it.get("check"))
            k = (look.dot, on)
            if k not in dots:
                dots[k] = radio(look.dot, on)
            img.alpha_composite(dots[k], (look.pad, y + (ih - look.dot) // 2))
        if it.get("disabled"):
            col = (110, 116, 122)
        elif it.get("color"):
            hx = it["color"].lstrip("#")
            col = tuple(int(hx[j:j + 2], 16) for j in (0, 2, 4))
        else:
            col = MENU_TEXT
        if hot:
            col = MENU_WHITE
        _otext(d, (look.tx, y + ih // 2), it.get("label", ""), look.font, col, "lm", look.ow)
        if it.get("right"):
            _otext(d, (w - look.pad - 4, y + ih // 2), it["right"], look.small, (170, 176, 182), "rm", look.ow)
        slots.append((y, y + ih, i))
        y += ih
    return img, slots



_PREVIEWS = {}


def preview(w, h, color, bar_colors, font_path=None, scale=0.4, check=False, title="City of Heroes"):
    """A small picture of a CoH window (frame, title, three bars) for the Skins/Themes pages (cached)."""
    key = (w, h, tuple(color[:3]), tuple(tuple(c) for c in bar_colors), font_path, round(scale, 3), check, title)
    img = _PREVIEWS.get(key)
    if img is None:
        img = _preview(w, h, color, bar_colors, font_path, scale, check, title)
        if len(_PREVIEWS) > 120:
            _PREVIEWS.clear()
        _PREVIEWS[key] = img
    return img


def _preview(w, h, color, bar_colors, font_path, scale, check, title):
    frame = render_fast_rgba(w, h, color, scale, tab=True)
    b = border_px(scale)
    top = int(round(TAB_H * scale))
    x0, y0, x1, y1 = int(round(b)), int(round(top + b)), int(round(w - b)), int(round(h - b))
    img = Image.new("RGBA", (w, h), (10, 10, 12, 255))
    img.alpha_composite(frame)
    d = ImageDraw.Draw(img)
    th = int(round(TAB_H * scale))
    ft = _font(font_path, max(13, int(round(40 * scale))))
    d.text((int(30 * scale) + 4, th // 2), title, font=ft, fill=(168, 172, 176, 255), anchor="lm",
           stroke_width=1, stroke_fill=(14, 14, 18, 255))
    if check:
        d.text((x1 - 6, th // 2), "\u2714", font=_font(r"C:\Windows\Fonts\seguisym.ttf", max(9, int(28 * scale))),
               fill=(255, 178, 31, 255), anchor="rm")
    bh = max(8, int((y1 - y0 - 12) / 3.4))
    y = y0 + 4
    for col, frac in zip(bar_colors, (0.95, 0.7, 0.45)):
        bx0, bx1 = x0 + 4, x1 - 4
        rad = max(2, bh // 4)
        d.rounded_rectangle((bx0, y, bx1, y + bh), rad, fill=(0, 0, 0, 255))
        d.rounded_rectangle((bx0 + 1, y + 1, bx1 - 1, y + bh - 1), rad - 1, fill=(70, 74, 80, 255))
        ih = bh - 3
        lum = (0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2]) / 255.0
        k = 0.10 + 0.34 * lum
        fill_w = int((bx1 - bx0 - 4) * frac)
        bar = Image.new("RGBA", (bx1 - bx0 - 3, ih), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bar)
        for yy in range(ih):
            t = yy / max(1, ih - 1)
            if t <= 0.12:
                wm, f = k, 1.06
            elif t < 0.5:
                wm, f = k * 0.6 * (0.5 - t) / 0.38, 1.02
            else:
                wm, f = 0.0, 0.94 - 0.42 * (t - 0.5)
            g = 1.25 - 0.35 * t if t < 0.5 else 0.95 - 0.35 * (t - 0.5)
            bd.line((0, yy, bar.width, yy), fill=tuple(int(min(255, 58 * g)) for _ in range(3)) + (255,))
            bd.line((0, yy, fill_w, yy), fill=tuple(int(min(255, c * f * (1 - wm) + 255 * wm)) for c in col) + (255,))
        m = Image.new("L", bar.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, bar.width - 1, ih - 1), max(1, rad - 1), fill=255)
        img.paste(bar, (bx0 + 2, y + 2), m)
        y += bh + max(2, int(6 * scale))
    return img
