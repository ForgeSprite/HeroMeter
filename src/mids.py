"""Mids' Reloaded / Mids Reborn integration for Hero Meter.

- finds your saved builds (.mbd, Mids Reborn's JSON format)
- reads enhancement names from Mids' own database (EnhDB.mhd)
- compares the planned build with what the chat log shows you actually doing
"""
import json
import os
import re

APPDATA = os.environ.get("APPDATA", "")
MIDS_DIR = os.path.join(APPDATA, "LoadedCamel", "MidsReborn")

# powers that aren't worth judging (travel, inherent fluff, temp powers, incarnates)
SKIP_PREFIX = ("Incarnate.", "Temporary_Powers.")
SKIP_INHERENT = {"fast mode", "speed phase", "double jump", "gauntlet", "prestige power slide", "rest", "sprint",
                 "brawl", "swift", "hurdle", "jump", "inherent", "fury", "domination", "scourge", "defiance",
                 "containment", "vigilance", "critical hit", "assassination", "bodyguard", "supremacy",
                 "conditioning"}
# things that show up in the log but never belong to a build
LOG_IGNORE = {"sprint", "brawl", "rest", "prestige power slide", "prestige power dash", "prestige power surge",
              "prestige power rush", "prestige power quick", "ninja run", "beast run", "athletic run",
              "steam jump", "afterburner", "fold space", "temporal selection", "jump pack", "assemble the team",
              "vengeance", "inspiration", "enhancement", "health", "stamina", "swift", "hurdle", "fast mode"}


def norm(name):
    """'Titan Sweep (Fast)' / 'Titan_Sweep' -> 'titansweep'."""
    name = re.sub(r"\(.*?\)", "", name or "")
    name = name.replace("_", " ")
    return re.sub(r"[^a-z0-9]", "", name.lower())


def nice(full):
    """'Tanker_Melee.Titan_Weapons.Defensive_Sweep' -> 'Defensive Sweep'."""
    last = (full or "").split(".")[-1]
    return last.replace("_", " ").strip()


def set_label(full):
    parts = (full or "").split(".")
    if len(parts) < 2:
        return ""
    s = parts[1].replace("_", " ")
    s = re.sub(r"\s+(TankBrute|Tank Brute|Scrapper|Brute|Tanker|Blaster|Defender|Corruptor|Controller|Dominator|"
               r"Mastermind|Sentinel|Stalker)$", "", s)
    return s


# ---------------------------------------------------------------------------------- settings / files
def mids_settings():
    try:
        with open(os.path.join(MIDS_DIR, "appSettings.json"), "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _find_key(d, key):
    if isinstance(d, dict):
        for k, v in d.items():
            if k == key and isinstance(v, str):
                return v
            r = _find_key(v, key)
            if r:
                return r
    return None


def mids_exe():
    for p in (os.path.join(MIDS_DIR, "MidsReborn.exe"),
              os.path.join(os.environ.get("ProgramFiles", ""), "MidsReborn", "MidsReborn.exe"),
              os.path.join(os.environ.get("ProgramFiles(x86)", ""), "MidsReborn", "MidsReborn.exe")):
        if p and os.path.isfile(p):
            return p
    return None


def build_dirs():
    st = mids_settings()
    home = os.path.expanduser("~")
    dirs = []
    for d in (_find_key(st, "BuildsPath"),
              os.path.join(home, "OneDrive", "Documents", "Hero & Villain Builds"),
              os.path.join(home, "Documents", "Hero & Villain Builds"),
              os.path.join(home, "Documents", "Mids Reborn"),
              os.path.join(home, "Downloads"),
              os.path.join(home, "Desktop")):
        if d and os.path.isdir(d) and os.path.normcase(os.path.abspath(d)) not in \
                [os.path.normcase(os.path.abspath(x)) for x in dirs]:
            dirs.append(d)
    return dirs


def find_builds():
    """[(path, mtime)] newest first; Downloads/Desktop copies of a file in the builds folder are dropped."""
    seen, out = set(), []
    for d in build_dirs():
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for fn in names:
            if not fn.lower().endswith(".mbd"):
                continue
            p = os.path.join(d, fn)
            key = fn.lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                out.append((p, os.path.getmtime(p)))
            except OSError:
                pass
    out.sort(key=lambda t: -t[1])
    return out


# ---------------------------------------------------------------------------------- enhancement names
_ENH = None


def _net_strings(b):
    out, i, n = [], 0, len(b)
    while i < n - 2:
        L = b[i]
        if 2 <= L < 0x80 and i + 1 + L <= n:
            try:
                t = b[i + 1:i + 1 + L].decode("utf-8")
                if t.isprintable() and any(c.isalpha() for c in t):
                    out.append(t)
                    i += 1 + L
                    continue
            except UnicodeDecodeError:
                pass
        i += 1
    return out


def enh_names():
    """uid -> (set name, piece name) from Mids' EnhDB.mhd (best effort)."""
    global _ENH
    if _ENH is not None:
        return _ENH
    _ENH = {}
    st = mids_settings()
    data = _find_key(st, "DataPath") or os.path.join(MIDS_DIR, "Databases", "Homecoming")
    try:
        with open(os.path.join(data, "EnhDB.mhd"), "rb") as fh:
            ss = _net_strings(fh.read())
    except Exception:
        return _ENH
    # each record ends with its Uid: ... Name, ShortName, [Description], Image.png, [SetUid, ...], Uid
    uidlike = lambda x: "_" in x and " " not in x and not x.lower().endswith(".png")
    for k, t in enumerate(ss):
        if not uidlike(t):
            continue
        j = None
        for back in range(1, 7):
            if k - back >= 0 and ss[k - back].lower().endswith(".png"):
                j = k - back
                break
        if j is None:
            continue
        i = j - 1
        while i > 0 and not uidlike(ss[i - 1]) and j - i < 4:
            i -= 1
        name = ss[i] if 0 <= i < j else ""
        sset = ss[j + 1].replace("_", " ") if j + 1 < k else ""
        _ENH[t] = (sset, name)
    return _ENH


def enh_label(uid):
    if not uid:
        return "(empty)"
    s, n = enh_names().get(uid, ("", ""))
    if s:
        return "%s: %s" % (s, n)
    if n:
        return n
    m = re.match(r"(?:Superior_)?(?:Attuned_)?(?:Crafted_)?(.+?)_([A-F])$", uid)
    if m:
        return "%s (%s)" % (m.group(1).replace("_", " "), m.group(2))
    return uid.replace("_", " ")


def enh_set(uid):
    s, _n = enh_names().get(uid or "", ("", ""))
    if s:
        return s
    m = re.match(r"(?:Superior_)?(?:Attuned_)?(?:Crafted_)?(.+?)_[A-F]$", uid or "")
    return m.group(1).replace("_", " ") if m else ""


def is_proc(uid):
    _s, n = enh_names().get(uid or "", ("", ""))
    n = n.lower()
    return (n.startswith("chance") or "proc" in n or n.startswith("+hit points") or n.startswith("+end")
            or "contagious" in n)


# ---------------------------------------------------------------------------------- builds
class PlannedPower:
    def __init__(self, level, full, slots):
        self.level = level
        self.full = full
        self.name = nice(full)
        self.key = norm(self.name)
        self.set = set_label(full)
        self.group = full.split(".")[0] if full else ""
        self.uids = [u for u in slots]
        self.slots = len(slots)

    @property
    def enh(self):
        return [enh_label(u) for u in self.uids if u]

    def sets(self):
        out = {}
        for u in self.uids:
            s = enh_set(u) if u else ""
            if s:
                out[s] = out.get(s, 0) + 1
        return out


class Build:
    def __init__(self, path):
        self.path = path
        with open(path, "r", encoding="utf-8-sig") as fh:
            d = json.load(fh)
        self.raw = d
        self.name = d.get("Name") or os.path.splitext(os.path.basename(path))[0]
        self.archetype = (d.get("Class") or "").replace("Class_", "").replace("_", " ")
        self.level = d.get("Level")
        self.sets = [set_label("x." + s.split(".")[-1]) for s in (d.get("PowerSets") or []) if s]
        self.powers = []
        for pe in d.get("PowerEntries") or []:
            full = pe.get("PowerName") or ""
            if not full:
                continue
            slots = []
            for se in pe.get("SlotEntries") or []:
                e = se.get("Enhancement") or {}
                slots.append(e.get("Uid") if e else None)
            self.powers.append(PlannedPower(int(pe.get("Level") or 0), full, slots))

    @property
    def title(self):
        return "%s — %s (%s)" % (self.name, self.archetype, " / ".join(self.sets[:2]))

    def judged(self):
        """Powers worth judging (no travel fluff, temp powers, incarnates or empty inherents)."""
        out = []
        for p in self.powers:
            if p.full.startswith(SKIP_PREFIX):
                continue
            if p.group == "Inherent" and (p.key in {norm(x) for x in SKIP_INHERENT} or not any(p.uids)):
                continue
            out.append(p)
        return out


def match_build(char, builds):
    """Best build file for a character name: filename 'Name - ...' or the build's own name."""
    if not char or char == "You":
        return None
    c = char.lower().strip()
    for p, _t in builds:
        base = os.path.basename(p).lower()
        if base.startswith(c + " - ") or base.startswith(c + " (") or os.path.splitext(base)[0] == c:
            return p
    for p, _t in builds:
        try:
            with open(p, "r", encoding="utf-8-sig") as fh:
                if (json.load(fh).get("Name") or "").lower().strip() == c:
                    return p
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------------- planned vs actual
class PowerResult:
    __slots__ = ("plan", "name", "level", "slots", "dmg", "heal", "absorb", "uses", "seen", "rolls", "hits",
                 "share", "verdict", "vcolor", "procs")

    def __init__(self, plan, name):
        self.plan, self.name = plan, name
        self.level = plan.level if plan else 0
        self.slots = plan.slots if plan else 0
        self.dmg = self.heal = self.absorb = 0.0
        self.uses = self.seen = self.rolls = self.hits = 0
        self.share = 0.0
        self.verdict, self.vcolor = "", ""
        self.procs = []

    @property
    def output(self):
        return self.dmg + self.heal + self.absorb

    @property
    def active(self):
        return self.output > 0 or self.uses > 0 or self.seen > 0


def _collect(actor):
    """norm(power) -> dict of totals from one actor (the player)."""
    agg = {}

    def slot(name):
        k = norm(name.split(":")[0]) if ":" in name else norm(name)
        d = agg.get(k)
        if d is None:
            d = agg[k] = {"name": re.sub(r"\s*\(.*?\)\s*", " ", name).strip(), "dmg": 0.0, "heal": 0.0,
                          "absorb": 0.0, "uses": 0, "seen": 0, "rolls": 0, "hits": 0, "n": 0, "proc": ":" in name,
                          "full": name}
        return d
    for n, s in actor.powers.items():
        d = slot(n)
        d["dmg"] += s.total
        d["n"] += s.count
        d["rolls"] += s.rolls
        d["hits"] += s.roll_hits
    for n, s in actor.heal_powers.items():
        d = slot(n)
        d["heal"] += s.total
        d["n"] += s.count
    for n, s in actor.absorb_powers.items():
        d = slot(n)
        d["absorb"] += s.total
        d["n"] += s.count
    for n, c in actor.activations.items():
        slot(n)["uses"] += c
    for n, c in getattr(actor, "seen", {}).items():
        slot(n)["seen"] += c
    return agg


def analyze(build, actor):
    """-> (results for planned powers, results for log powers not in the build, procs list, total output)"""
    agg = _collect(actor) if actor is not None else {}
    total = sum(d["dmg"] + d["heal"] + d["absorb"] for d in agg.values() if not d["proc"]) or 0.0
    planned, used_keys = [], set()
    for p in build.judged():
        r = PowerResult(p, p.name)
        d = agg.get(p.key)
        if d is not None:
            used_keys.add(p.key)
            r.dmg, r.heal, r.absorb = d["dmg"], d["heal"], d["absorb"]
            r.uses, r.seen, r.rolls, r.hits = d["uses"], d["seen"], d["rolls"], d["hits"]
        r.share = (100.0 * r.output / total) if total else 0.0
        planned.append(r)
    # procs slotted in the build, and whether they fired
    procs, by_proc = [], {}
    proc_logs = {k: d for k, d in agg.items() if d["proc"]}
    for r in planned:
        for u in r.plan.uids:
            if not u or not is_proc(u):
                continue
            label = enh_label(u)
            pr = by_proc.get(label)
            if pr is None:
                sname = enh_set(u)
                hit = proc_logs.get(norm(sname))
                pr = by_proc[label] = {"powers": [], "proc": label, "set": sname,
                                       "fires": max(hit["seen"], hit["n"], hit["rolls"]) if hit else 0,
                                       "output": (hit["dmg"] + hit["heal"] + hit["absorb"]) if hit else 0.0,
                                       "log": hit["full"] if hit else ""}
                procs.append(pr)
            pr["powers"].append(r.name)
            r.procs.append(pr)
    for pr in procs:
        pr["power"] = ", ".join(pr["powers"])
    # verdicts (value ranking)
    attacks = [r for r in planned if r.dmg > 0]
    best_per_slot = max([r.output / max(1, r.slots) for r in planned] or [0]) or 1.0
    for r in planned:
        per_slot = r.output / max(1, r.slots)
        if r.output > 0 and r.share >= 15:
            r.verdict, r.vcolor = "Top performer", "good"
        elif r.output > 0 and r.slots >= 4 and r.share < 3 and r.dmg > 0:
            r.verdict, r.vcolor = "Low return for %d slots" % r.slots, "bad"
        elif r.output > 0 and per_slot >= 0.5 * best_per_slot:
            r.verdict, r.vcolor = "Great value per slot", "good"
        elif r.output > 0:
            r.verdict, r.vcolor = "Pulling its weight", "ok"
        elif r.uses or r.seen:
            r.verdict, r.vcolor = "Used (buff / control / toggle)", "ok"
        elif r.slots >= 3:
            r.verdict, r.vcolor = "Not seen — %d slots idle?" % r.slots, "warn"
        else:
            r.verdict, r.vcolor = "Not seen (passive?)", "dim"
    _ = attacks
    # things done in the log that the build doesn't have
    extra = []
    plan_keys = {p.key for p in build.powers}
    for k, d in agg.items():
        if d["proc"] or k in plan_keys or k in used_keys or not k:
            continue
        if k in {norm(x) for x in LOG_IGNORE}:
            continue
        out = d["dmg"] + d["heal"] + d["absorb"]
        if out <= 0 and d["uses"] == 0:
            continue
        r = PowerResult(None, d["name"])
        r.dmg, r.heal, r.absorb, r.uses, r.seen = d["dmg"], d["heal"], d["absorb"], d["uses"], d["seen"]
        r.share = (100.0 * out / total) if total else 0.0
        extra.append(r)
    extra.sort(key=lambda r: -r.output)
    return planned, extra, procs, total
