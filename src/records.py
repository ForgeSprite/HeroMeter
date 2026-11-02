"""records.py - personal records for each character, kept in sets you can rename or start fresh.

store = {character: {"active": 0, "sets": [{"name", "created", "build", "rec": {key: record}}]}}
record = {"value": float, "date": "YYYY-MM-DD", "zone": str, "detail": str}
"""
import time

# (key, label, in the light list too)
RECORDS = [
    ("hit", "Biggest hit", True),
    ("dps", "Best fight DPS", True),
    ("damage", "Most damage in one fight", True),
    ("team_dps", "Best DPS with your pets", False),
    ("kills", "Most kills in one fight", False),
    ("hps", "Best healing per second", False),
    ("survive", "Longest fight survived", False),
]
LABEL = {k: lab for k, lab, _l in RECORDS}
SHORT = {"hit": "biggest hit", "dps": "best DPS", "damage": "most damage", "team_dps": "best DPS with pets",
         "kills": "most kills", "hps": "best HPS", "survive": "longest fight survived"}


def shown(mode):
    return [k for k, _lab, light in RECORDS if mode != "light" or light]


def fmt(key, v):
    if key in ("dps", "team_dps", "hps"):
        return "%.1f" % v
    if key == "kills":
        return "%d" % v
    if key == "survive":
        v = int(v)
        return "%d:%02d" % (v // 60, v % 60)
    if v >= 100000:
        return "%.1fK" % (v / 1000.0)
    return "{:,}".format(int(round(v)))


def _biggest(actor):
    best, power, crit = 0.0, "", False
    for name, s in actor.powers.items():
        cands = [(getattr(s, "nmax", 0.0) or 0.0, False), (getattr(s, "tmax", 0.0) or 0.0, False)]
        for flair, f in (getattr(s, "flairs", None) or {}).items():
            cands.append((f[3], "CRIT" in flair.upper()))
        for v, c in cands:
            if v > best:
                best, power, crit = v, name, c
    return best, power, crit


def measure(seg, player, min_fight=20.0):
    """Record candidates from one finished fight -> {key: (value, detail)}."""
    out = {}
    a = seg.actors.get(player)
    if a is None:
        return out
    dur = max(1.0, seg.duration())
    hit, power, crit = _biggest(a)
    if hit > 0:
        out["hit"] = (hit, power + (" (critical)" if crit else ""))
    if a.damage > 0:
        top = max(a.powers.items(), key=lambda kv: kv[1].total)[0] if a.powers else ""
        out["damage"] = (a.damage, "%d s fight%s" % (dur, (", mostly " + top) if top else ""))
        if dur >= min_fight:
            out["dps"] = (a.damage / dur, "%d s fight" % dur)
    pets = [x for x in seg.actors.values() if x.kind == "pet"]
    if pets and dur >= min_fight:
        team = a.damage + sum(x.damage for x in pets)
        if team > 0:
            out["team_dps"] = (team / dur, "%d s fight, %d pet%s" % (dur, len(pets), "" if len(pets) == 1 else "s"))
    kills = sum(x.kill_count for x in seg.actors.values())
    if kills:
        out["kills"] = (kills, "%d s fight" % dur)
    if a.heal > 0 and dur >= min_fight:
        out["hps"] = (a.heal / dur, "%d s fight" % dur)
    died = any(getattr(d, "victim", None) == player for d in (getattr(seg, "deaths", None) or []))
    if a.taken > 0 and not died:
        out["survive"] = (dur, "took %s damage" % fmt("hit", a.taken))
    return out


def active_set(store, char, build=None, by_build=False):
    """The record set new results go into (made on first use)."""
    c = store.setdefault(char, {"active": 0, "sets": []})
    sets = c["sets"]
    if by_build and build:
        for i, st in enumerate(sets):
            if st.get("build") == build:
                c["active"] = i
                return st
        sets.append({"name": "%s - %s" % (char, build), "created": time.strftime("%Y-%m-%d"), "build": build,
                     "rec": {}})
        c["active"] = len(sets) - 1
        return sets[-1]
    if not sets:
        sets.append({"name": char, "created": time.strftime("%Y-%m-%d"), "build": None, "rec": {}})
        c["active"] = 0
    return sets[min(c.get("active", 0), len(sets) - 1)]


def update(store, char, results, zone="", build=None, by_build=False, mode="full"):
    """Add one fight's results. -> [(key, new value, old value or None)] for every record it beat."""
    st = active_set(store, char, build, by_build)
    rec = st["rec"]
    beaten = []
    for key in shown(mode):
        if key not in results:
            continue
        v, detail = results[key]
        old = rec.get(key)
        if old is None or v > old["value"] + 1e-9:
            rec[key] = {"value": float(v), "date": time.strftime("%Y-%m-%d"), "zone": zone or "",
                        "detail": detail}
            beaten.append((key, v, old["value"] if old else None))
    return beaten


def start_fresh(store, char, name=None):
    c = store.setdefault(char, {"active": 0, "sets": []})
    c["sets"].append({"name": name or "%s (%s)" % (char, time.strftime("%b %d, %Y")),
                      "created": time.strftime("%Y-%m-%d"), "build": None, "rec": {}})
    c["active"] = len(c["sets"]) - 1
    return c["sets"][-1]
