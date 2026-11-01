"""Reads assets from the player's own City of Heroes install.

The game's fonts live inside 'fonts.pigg' (a simple archive: header, directory, name table,
zlib-packed files). Hero Meter never ships these fonts; it unpacks them once from the
player's own game files into its settings folder and loads them privately.
"""
import glob
import os
import struct
import zlib

# file in the archive -> font family name it registers
COH_FONTS = {
    "fonts/mont_demibold.ttf": "Montreal-DemiBold",     # main UI text
    "fonts/mont_bold.ttf": "Montreal-Bold",             # window titles, tabs
    "fonts/mont_hvbold.ttf": "Montreal-Heavy",
    "fonts/redcircl.ttf": "Paragon City",               # NCsoft's own CoH font
    "fonts/paragon city italic.ttf": "Paragon City",    # the orange section headers
}


def find_fonts_pigg(game_root):
    if not game_root:
        return None
    hits = glob.glob(os.path.join(game_root, "assets", "*", "fonts.pigg"))
    return max(hits, key=os.path.getmtime) if hits else None


def read_pigg(path, wanted=None):
    """{lower-case name: bytes} for the files in a .pigg (only 'wanted' names if given)."""
    with open(path, "rb") as fh:
        b = fh.read()
    marker, _u, _v, _hs, used, n = struct.unpack_from("<IHHHHI", b, 0)
    if marker != 0x123:
        raise ValueError("not a pigg archive")
    ents, off = [], 16
    for _ in range(n):
        _m, name_id, size, _ts, data_off = struct.unpack_from("<IIIII", b, off)
        packed, = struct.unpack_from("<I", b, off + used - 4)
        ents.append((name_id, size, data_off, packed))
        off += used
    _m, cnt, _tsize = struct.unpack_from("<III", b, off)
    o, names = off + 12, []
    for _ in range(cnt):
        ln, = struct.unpack_from("<I", b, o)
        names.append(b[o + 4:o + 4 + ln].rstrip(b"\0").decode("latin1"))
        o += 4 + ln
    out = {}
    for name_id, size, data_off, packed in ents:
        nm = names[name_id].lower() if name_id < len(names) else ""
        if wanted is not None and nm not in wanted:
            continue
        raw = b[data_off:data_off + (packed or size)]
        data = zlib.decompress(raw) if packed else raw
        if len(data) == size:
            out[nm] = data
    return out


def extract_coh_fonts(game_root, dest):
    """Unpack the CoH fonts into 'dest' (once). Returns the font file paths, or [] if unavailable."""
    os.makedirs(dest, exist_ok=True)
    targets = {nm: os.path.join(dest, "coh_" + os.path.basename(nm).replace(" ", "_")) for nm in COH_FONTS}
    if all(os.path.isfile(p) and os.path.getsize(p) > 1000 for p in targets.values()):
        return list(targets.values())          # already unpacked: instant
    pigg = find_fonts_pigg(game_root)
    if not pigg:
        return [p for p in targets.values() if os.path.isfile(p)]
    try:
        files = read_pigg(pigg, set(targets))
    except Exception:
        return []
    for nm, data in files.items():
        with open(targets[nm], "wb") as fh:
            fh.write(data)
    return [p for p in targets.values() if os.path.isfile(p)]
