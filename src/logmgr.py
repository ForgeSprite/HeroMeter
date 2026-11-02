"""logmgr.py - keeps the game's chat logs from piling up.

City of Heroes writes one chat log per day and never removes any. This zips logs older than a chosen
number of days into one archive per month (Logs/Archive/chatlogs YYYY-MM.zip, about 90% smaller), and
deletes archives once they're older than a second, longer limit. It only ever touches files named
'chatlog YYYY-MM-DD.txt' and 'chatlogs YYYY-MM.zip' inside the folders it's given, never today's or
yesterday's log, and never the log the meter is reading.
"""
import calendar
import datetime as dt
import os
import re
import zipfile
import json
import zlib

LOG_RE = re.compile(r"^chatlog (\d{4})-(\d{2})-(\d{2})\.txt$", re.I)
ARCH_RE = re.compile(r"^chatlogs (\d{4})-(\d{2})\.zip$", re.I)
ARCHIVE = "Archive"
MANIFEST = "herometer_archive.json"     # zip name -> date Hero Meter first created it
GRACE_DAYS = 14                         # a zip is never deleted in its first two weeks


def _manifest(ad):
    try:
        with open(os.path.join(ad, MANIFEST), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_manifest(ad, man):
    try:
        with open(os.path.join(ad, MANIFEST), "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1)
    except OSError:
        pass


def _crc(path):
    c = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            c = zlib.crc32(b, c)
    return c & 0xFFFFFFFF


def stats(dirs):
    """-> dict: logs (count), log_bytes, archives (count), archive_bytes, oldest (date or None)"""
    out = {"logs": 0, "log_bytes": 0, "archives": 0, "archive_bytes": 0, "oldest": None}
    for d in dirs:
        try:
            for fn in os.listdir(d):
                m = LOG_RE.match(fn)
                if m:
                    out["logs"] += 1
                    out["log_bytes"] += os.path.getsize(os.path.join(d, fn))
                    day = dt.date(*map(int, m.groups()))
                    if out["oldest"] is None or day < out["oldest"]:
                        out["oldest"] = day
            ad = os.path.join(d, ARCHIVE)
            if os.path.isdir(ad):
                for fn in os.listdir(ad):
                    m = ARCH_RE.match(fn)
                    if m:
                        out["archives"] += 1
                        out["archive_bytes"] += os.path.getsize(os.path.join(ad, fn))
                        day = dt.date(int(m.group(1)), int(m.group(2)), 1)
                        if out["oldest"] is None or day < out["oldest"]:
                            out["oldest"] = day
        except OSError:
            continue
    return out


def run(dirs, keep_days=7, delete_days=180, active=None, today=None):
    """Zip logs older than keep_days, delete archives older than delete_days (0 = never).
    -> dict: zipped, saved (bytes), deleted, errors"""
    today = today or dt.date.today()
    keep_days = max(2, int(keep_days))
    res = {"zipped": 0, "saved": 0, "deleted": 0, "errors": 0}
    act = os.path.normcase(os.path.abspath(active)) if active else None
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        ad = os.path.join(d, ARCHIVE)
        man = _manifest(ad)
        for fn in names:
            m = LOG_RE.match(fn)
            if not m:
                continue
            try:
                day = dt.date(*map(int, m.groups()))
            except ValueError:
                continue
            if (today - day).days <= keep_days:
                continue
            path = os.path.join(d, fn)
            if act and os.path.normcase(os.path.abspath(path)) == act:
                continue
            try:
                size = os.path.getsize(path)
                crc = _crc(path)
                os.makedirs(ad, exist_ok=True)
                zname = "chatlogs %04d-%02d.zip" % (day.year, day.month)
                zpath = os.path.join(ad, zname)
                man.setdefault(zname, today.isoformat())
                with zipfile.ZipFile(zpath, "a", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
                    if fn not in z.namelist():
                        z.write(path, fn)
                with zipfile.ZipFile(zpath) as z:
                    info = z.getinfo(fn)
                    ok = info.file_size == size and (info.CRC & 0xFFFFFFFF) == crc
                    packed = info.compress_size
                if ok:                      # only remove the original once it's safely in the archive
                    os.remove(path)
                    res["zipped"] += 1
                    res["saved"] += max(0, size - packed)
                else:
                    res["errors"] += 1
            except Exception:
                res["errors"] += 1
        if man:
            _save_manifest(ad, man)
        if delete_days and int(delete_days) > 0 and os.path.isdir(ad):
            try:
                for fn in os.listdir(ad):
                    m = ARCH_RE.match(fn)
                    if not m:
                        continue
                    y, mo = int(m.group(1)), int(m.group(2))
                    last = dt.date(y, mo, calendar.monthrange(y, mo)[1])
                    try:                # only zips Hero Meter made, and never in their first two weeks
                        made = dt.date.fromisoformat(man[fn])
                    except Exception:
                        continue
                    if (today - made).days < GRACE_DAYS:
                        continue
                    if (today - last).days > int(delete_days):
                        try:
                            os.remove(os.path.join(ad, fn))
                            res["deleted"] += 1
                        except OSError:
                            res["errors"] += 1
            except OSError:
                res["errors"] += 1
    return res
