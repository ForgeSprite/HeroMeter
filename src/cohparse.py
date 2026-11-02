"""
cohparse.py - City of Heroes (Homecoming) chat-log combat parser.

Reads chatlog lines, splits combat into segments and keeps per-actor stats
(you + your pets), enemy stats, and death recaps.
"""
import collections
import datetime as dt
import glob
import os
import re

import pettypes

# --------------------------------------------------------------------------
# Line patterns
# --------------------------------------------------------------------------
NUM = r"([\d,]+(?:\.\d+)?)"
TS_RE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (.*?)\s*$")
PET_RE = re.compile(r"^([^\[\]:]{1,40}):  (.*)$")

R_DMG = re.compile(r"^You hit (.+?) with your (.+?) for " + NUM +
                   r" points? of (?:unresistable )?(.+?) damage( over time)?\.?(?: \(([^)]+)\))?\.?$")
R_HIT = re.compile(r"^HIT (.+?)! Your (.+?) power (?:had a ([\d.]+)% chance to hit, you rolled a [\d.]+|is autohit"
                   r"|was forced to hit by streakbreaker)")
R_MISS = re.compile(r"^MISSED (.+?)!+ Your (.+?) power had a ([\d.]+)% chance to hit, you rolled a [\d.]+")
R_TAKEN = re.compile(r"^(.+?) hits you with their (.+?) for " + NUM +
                     r" points? of (?:unresistable )?(.+?) damage( over time)?\.?(?: \(([^)]+)\))?\.?$")
R_EHIT = re.compile(r"^(.+?) HITS you! (.+?) power (?:had a ([\d.]+)% chance to hit and rolled a [\d.]+|is autohit)")
R_EMISS = re.compile(r"^(.+?) MISSES! (.+?) power had a ([\d.]+)% chance to hit, but rolled a [\d.]+")
R_HEAL = re.compile(r"^You heal (.+?) with (.+?) for " + NUM + r" health points?")
R_SELFHEAL = re.compile(r"^You are healed by your (.+?) for " + NUM + r" health points?")
R_HEALED = re.compile(r"^(.+?) heals you with their (.+?) for " + NUM + r" health points?")
R_ABS_OUT = re.compile(r"^You grant (.+?) " + NUM + r" points? of absorption(?: over time)? with (.+?)\.?$")
R_ABS_IN = re.compile(r"^(.+?) grants you " + NUM + r" points? of absorption(?: over time)? with their (.+?)\.?$")
R_PROTECT = re.compile(r"^Your henchmen protect you from " + NUM + r" damage")
R_KILL = re.compile(r"^You have defeated (.+?)\.?$")
R_XP = re.compile(r"^You gain " + NUM + r" experience")
R_ZONE = re.compile(r"^Entering (.+?)\.$")
R_SEEN = re.compile(r"Your (.+?) (?:power is autohit|has made you|has |is recharged)|You activated the (.+?) power"
                    r"|with your (.+?) (?:for [\d.]|granting)|^(.+?) is recharged")
R_MEZ = re.compile(r"^(.+?) (Holds|Stuns|Sleeps|Deep Sleeps|Terrifies|Terrorizes|Confuses|Immobilizes) you with their (.+?)\.?$")
R_YOU_MEZ = re.compile(r"^You are (held|stunned|asleep|terrified|confused)!$")
R_DEFEATS = re.compile(r"^(.+?) has defeated (.+?)\.?$")
R_ACTIVATE = re.compile(r"^You activated the (.+?) power\.?$")
R_NAME = re.compile(r"^(?:Welcome to City of Heroes|Now entering .+?), (.+?)!$")
R_DEATH = re.compile(r"(brink of death|You have been defeated|You were defeated|You are defeated|"
                     r"have been resurrected|resurrects you|revives you|You have been revived|"
                     r"Rise of the Phoenix|Return to Hospital)", re.I)


# Pseudo pets: invisible stand-ins some powers drop (Rain of Fire, Caltrops, Burn patches, Chain
# Induction's jumps, Judgement powers...). The log shows their damage as if a pet did it, often under a
# different name than the power you clicked. Their damage is yours, so it's credited to you under the
# power's name. Anything named exactly like a power you activated counts too (see Parser.pseudo_pet).
# (pattern on the pet name, power to credit it to, power you must have used first or None)
PSEUDO_PETS = [
    (r"^Chain Induction Jump", "Chain Induction", None),
    (r"^(Ion|Cryonic|Mighty|Pyronic|Void|Vorpal)\b.*Judgement", None, None),   # keeps "<kind> Judgement"
    (r"^Lightning ?Rod", "Lightning Rod", None),
    (r"^Irradiated.*Ground", "Irradiated Ground", None),
    (r"^Burn\b", "Burn", None),
    (r"^Rain ?of ?Arrows|RainofArrows", "Rain of Arrows", None),
    (r"^Savage Leap", "Savage Leap", None),
    (r"^Meteor\b", "Meteor", None),
    (r"^Caltrops\b", "Caltrops", None),
    (r"^Bonfire\b", "Bonfire", None),
    (r"^Liquid Nitrogen\b", "Liquid Nitrogen", None),
    (r"^Poison Gas Arrow\b", "Poison Gas Arrow", None),
    (r"^Fire$", "Oil Slick Arrow", "Oil Slick Arrow"),
]
PSEUDO_RES = [(re.compile(p), m, need) for p, m, need in PSEUDO_PETS]
_RE_OWN_DMG = re.compile(r"^(You hit .+? with your ).+?( for [\d,.]+ points? of )")
_RE_OWN_HIT = re.compile(r"^((?:HIT|MISSED) .+?!+ Your ).+?( power )")
_RE_OWN_HEAL = re.compile(r"^(You heal .+? with ).+?( for [\d,.]+ health)")
_RE_OWN_ABS = re.compile(r"^(You grant .+? [\d,.]+ points? of absorption(?: over time)? with ).+?(\.?)$")
R_EAUTO = re.compile(r"^(.+?) HITS you! (.+?) power was autohit\.?$")


def num(s):
    return float(s.replace(",", ""))


# --------------------------------------------------------------------------
# Stats containers
# --------------------------------------------------------------------------
class Stat:
    """Amount + hit statistics for one power (or one source/target bucket)."""
    __slots__ = ("total", "n_direct", "direct_total", "n_norm", "norm_total", "nmin", "nmax",
                 "n_tick", "tick_total", "tmax", "flairs", "rolls", "roll_hits", "roll_miss",
                 "chance_sum", "chance_n", "dtypes", "targets", "sources")

    def __init__(self):
        self.total = 0.0
        self.n_direct = 0
        self.direct_total = 0.0
        self.n_norm = 0
        self.norm_total = 0.0
        self.nmin = None
        self.nmax = 0.0
        self.n_tick = 0
        self.tick_total = 0.0
        self.tmax = 0.0
        self.flairs = {}            # flair -> [count, total, min, max]
        self.rolls = 0
        self.roll_hits = 0
        self.roll_miss = 0
        self.chance_sum = 0.0
        self.chance_n = 0
        self.dtypes = {}            # damage type -> total
        self.targets = {}           # target -> total
        self.sources = {}           # source -> total (used by "taken by ability")

    @property
    def count(self):
        return self.n_direct + self.n_tick

    def add(self, amount, dot=False, flair=None, dtype=None, target=None, source=None):
        self.total += amount
        if dot:
            self.n_tick += 1
            self.tick_total += amount
            if amount > self.tmax:
                self.tmax = amount
        else:
            self.n_direct += 1
            self.direct_total += amount
            if flair:
                f = self.flairs.get(flair)
                if f is None:
                    self.flairs[flair] = [1, amount, amount, amount]
                else:
                    f[0] += 1
                    f[1] += amount
                    f[2] = min(f[2], amount)
                    f[3] = max(f[3], amount)
            else:
                self.n_norm += 1
                self.norm_total += amount
                self.nmin = amount if self.nmin is None else min(self.nmin, amount)
                self.nmax = max(self.nmax, amount)
        if dtype:
            self.dtypes[dtype] = self.dtypes.get(dtype, 0.0) + amount
        if target:
            self.targets[target] = self.targets.get(target, 0.0) + amount
        if source:
            self.sources[source] = self.sources.get(source, 0.0) + amount

    def add_roll(self, hit, chance=None):
        self.rolls += 1
        if hit:
            self.roll_hits += 1
        else:
            self.roll_miss += 1
        if chance is not None:
            self.chance_sum += chance
            self.chance_n += 1

    def merge(self, o):
        self.total += o.total
        self.n_direct += o.n_direct
        self.direct_total += o.direct_total
        self.n_norm += o.n_norm
        self.norm_total += o.norm_total
        if o.nmin is not None:
            self.nmin = o.nmin if self.nmin is None else min(self.nmin, o.nmin)
        self.nmax = max(self.nmax, o.nmax)
        self.n_tick += o.n_tick
        self.tick_total += o.tick_total
        self.tmax = max(self.tmax, o.tmax)
        for k, v in o.flairs.items():
            f = self.flairs.get(k)
            if f is None:
                self.flairs[k] = list(v)
            else:
                f[0] += v[0]; f[1] += v[1]; f[2] = min(f[2], v[2]); f[3] = max(f[3], v[3])
        self.rolls += o.rolls
        self.roll_hits += o.roll_hits
        self.roll_miss += o.roll_miss
        self.chance_sum += o.chance_sum
        self.chance_n += o.chance_n
        for d_self, d_o in ((self.dtypes, o.dtypes), (self.targets, o.targets), (self.sources, o.sources)):
            for k, v in d_o.items():
                d_self[k] = d_self.get(k, 0.0) + v

    @property
    def crit_count(self):
        f = self.flairs.get("CRITICAL")
        return f[0] if f else 0

    @property
    def top_dtype(self):
        if not self.dtypes:
            return None
        return max(self.dtypes.items(), key=lambda kv: kv[1])[0]


def _get(d, k):
    s = d.get(k)
    if s is None:
        s = d[k] = Stat()
    return s


class Actor:
    """A friendly combatant: the player or one of the player's pets."""

    def __init__(self, name, kind):
        self.name = name
        self.kind = kind                # 'player' or 'pet'
        self.damage = 0.0
        self.powers = {}                # power -> Stat (damage done)
        self.taken = 0.0
        self.taken_by = {}              # (source, power) -> Stat
        self.heal = 0.0
        self.heal_powers = {}           # power -> Stat (heals done)
        self.healed = 0.0
        self.healed_by = {}             # (source, power) -> Stat
        self.absorb = 0.0
        self.absorb_powers = {}         # power -> Stat (absorbs granted)
        self.absorbed = 0.0
        self.protect = 0.0
        self.protect_n = 0
        self.kills = {}                 # enemy -> count
        self.xp = 0.0
        self.rolls = 0
        self.roll_hits = 0
        self.chance_sum = 0.0
        self.chance_n = 0
        self.def_rolls = 0              # enemy attack rolls against this actor
        self.def_miss = 0
        self.active = 0.0               # seconds this actor was actually fighting
        self._last_act = None
        self.recent = collections.deque(maxlen=600)    # (ts, damage) for real-time DPS
        self.activations = {}           # power -> times activated (player only)
        self.timeline = {}              # time bucket -> damage (for the DPS graph)
        self.tl_step = 1                # seconds per bucket
        self.seen = {}                  # power -> times the log mentioned it (toggles, autohits, buffs)

    def touch(self, ts):
        """Track 'active time': gaps of up to 3s between actions count as fighting."""
        last = self._last_act
        if last is None or ts - last > 3.0:
            self.active += 1.0
        elif ts > last:
            self.active += ts - last
        self._last_act = ts

    @property
    def kill_count(self):
        return sum(self.kills.values())

    def merge_from(self, o, prefix=""):
        for k, v in getattr(o, "seen", {}).items():
            self.seen[k] = self.seen.get(k, 0) + v
        for k, v in o.activations.items():
            self.activations[k] = self.activations.get(k, 0) + v
        self.damage += o.damage
        self.taken += o.taken
        self.heal += o.heal
        self.healed += o.healed
        self.absorb += o.absorb
        self.absorbed += o.absorbed
        self.protect += o.protect
        self.protect_n += o.protect_n
        self.xp += o.xp
        tl = getattr(o, "timeline", None)
        if tl:
            self.tl_step = getattr(o, "tl_step", 1)
            for k, v in tl.items():
                self.timeline[k] = self.timeline.get(k, 0.0) + v
        self.rolls += o.rolls
        self.roll_hits += o.roll_hits
        self.chance_sum += o.chance_sum
        self.chance_n += o.chance_n
        self.def_rolls += o.def_rolls
        self.def_miss += o.def_miss
        self.active = max(self.active, o.active)
        self.recent.extend(o.recent)
        for k, v in o.activations.items():
            self.activations[prefix + k] = self.activations.get(prefix + k, 0) + v
        for k, v in o.kills.items():
            self.kills[k] = self.kills.get(k, 0) + v
        for mine, theirs in ((self.powers, o.powers), (self.heal_powers, o.heal_powers),
                             (self.absorb_powers, o.absorb_powers)):
            for k, s in theirs.items():
                _get(mine, prefix + k).merge(s)
        for mine, theirs in ((self.taken_by, o.taken_by), (self.healed_by, o.healed_by)):
            for k, s in theirs.items():
                _get(mine, k).merge(s)


class Enemy:
    def __init__(self, name):
        self.name = name
        self.received = 0.0             # damage we did to it
        self.received_by = {}           # (actor, power) -> Stat
        self.dealt = 0.0                # damage it did to us
        self.dealt_by = {}              # power -> Stat (targets = victims)
        self.kills = 0


class Death:
    def __init__(self, victim, ts, trigger_ts, trigger_text, events, window):
        self.victim = victim
        self.ts = ts                    # time of the killing blow
        self.trigger_ts = trigger_ts
        self.trigger_text = trigger_text
        self.events = events            # list of dicts, oldest first
        self.window = window
        self.killer = None
        self.killing_power = None
        self.killing_amount = 0.0
        self.killing_type = None
        for e in reversed(events):
            if e["kind"] == "dmg":
                self.killer = e["src"]
                self.killing_power = e["power"]
                self.killing_amount = e["amount"]
                self.killing_type = e["dtype"]
                e["killing_blow"] = True
                break
        self.manual = trigger_text == "manual"


class Segment:
    def __init__(self, start, number=0, is_overall=False):
        self.number = number
        self.is_overall = is_overall
        self.start = start
        self.last = start
        self.closed = False
        self.actors = {}                # name -> Actor
        self.enemies = {}               # name -> Enemy
        self.deaths = []
        self.xp = 0.0
        self._duration = 0.0            # used by the overall segment

    # duration in seconds (never zero so per-second math works)
    def duration(self, now=None):
        if self.is_overall:
            return max(1.0, self._duration)
        end = self.last
        return max(1.0, end - self.start)

    def actor(self, name, kind):
        a = self.actors.get(name)
        if a is None:
            a = self.actors[name] = Actor(name, kind)
        elif kind == "player":
            a.kind = "player"
        return a

    def enemy(self, name):
        e = self.enemies.get(name)
        if e is None:
            e = self.enemies[name] = Enemy(name)
        return e

    @property
    def name(self):
        if self.is_overall:
            return "Overall Data"
        if self.enemies:
            best = max(self.enemies.values(), key=lambda e: (e.received, e.dealt))
            if best.received > 0 or best.dealt > 0:
                return best.name
        return "Trash"

    @property
    def total_damage(self):
        return sum(a.damage for a in self.actors.values())


# --------------------------------------------------------------------------
# The parser
# --------------------------------------------------------------------------
class Parser:
    def __init__(self, combat_timeout=10.0, max_segments=30, recap_window=12.0):
        self.combat_timeout = combat_timeout
        self.max_segments = max_segments
        self.recap_window = recap_window
        self.player = "You"
        self.typer = pettypes.PetTyper()
        self.my_powers = set()          # powers you've activated (to spot pseudo pets named after them)
        self.alerts = collections.deque(maxlen=60)   # (ts, kind, ...) for on-screen alerts
        self.just_closed = collections.deque(maxlen=30)   # fights that just ended (for personal records)
        self.zone = ""
        self._pet_seen = {}             # pet name -> last time it fought
        self._enemy_seen = {}           # enemy name -> last time you or a pet hit it
        self._foe_seen = {}             # name -> last time it damaged you or a pet
        self.unplaced = {}              # pet names that aren't henchmen or known pseudo pets -> lines seen
        self.my_chars = set()           # every character name on the account (playerslot.txt)
        self.renames = {}               # power name -> merged / renamed name
        self.dot_separate = False       # list damage-over-time ticks as "<power> (DoT)"
        self.overall_clear = "manual"   # manual | zone | login
        self.trash_seconds = 0          # drop fights shorter than this (0 = keep all)
        self.reset()
        self._ts_cache = {}

    def reset(self):
        self.segments = []              # closed + active segments, oldest first
        self.current = None             # active segment (or None)
        self.overall = Segment(0, is_overall=True)
        self.deaths = []
        self.seg_counter = 0
        self.incoming = collections.defaultdict(lambda: collections.deque(maxlen=400))
        self.version = 0                # bumped on every change (UI dirty flag)
        self.last_line_ts = None

    def pname(self, power, dot=False):
        p = self.renames.get(power, power)
        if dot and self.dot_separate:
            p += " (DoT)"
        return p

    def clear_overall(self):
        self.overall = Segment(0, is_overall=True)
        self.version += 1

    # -- time -------------------------------------------------------------
    def _epoch(self, s):
        v = self._ts_cache.get(s)
        if v is None:
            try:
                v = dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()
            except ValueError:
                v = 0.0
            if len(self._ts_cache) > 5000:
                self._ts_cache.clear()
            self._ts_cache[s] = v
        return v

    # -- segments ---------------------------------------------------------
    def _close_current(self):
        c = self.current
        if c is None:
            return
        c.closed = True
        trash = self.trash_seconds and c.duration() < self.trash_seconds
        if trash or (c.total_damage <= 0 and not any(a.taken > 0 for a in c.actors.values())):
            # nothing really happened (a stray miss or buff) - drop it
            if c in self.segments:
                self.segments.remove(c)
            self.current = None
            return
        self.overall._duration += c.duration()
        c.zone = self.zone
        self.just_closed.append(c)
        self.current = None
        self.version += 1

    def tick(self, now):
        """Close the active segment once combat has been idle long enough."""
        if self.current and now - self.current.last > self.combat_timeout:
            self._close_current()

    def _combat(self, ts):
        c = self.current
        if c is not None and ts - c.last > self.combat_timeout:
            self._close_current()
            c = None
        if c is None:
            self.seg_counter += 1
            c = Segment(ts, self.seg_counter)
            self.current = c
            self.segments.append(c)
            if len(self.segments) > self.max_segments:
                self.segments.pop(0)
        if ts > c.last:
            c.last = ts
        return c

    def _targets(self, ts, combat=True):
        """Segments an event applies to: active segment + overall."""
        if combat:
            seg = self._combat(ts)
        else:
            seg = self.current
        return (seg, self.overall) if seg is not None else (self.overall,)

    # -- feeding ----------------------------------------------------------
    def feed(self, raw):
        m = TS_RE.match(raw)
        if not m:
            return
        ts_s, body = m.groups()
        if not body or body[0] == "[":
            return
        ts = self._epoch(ts_s)
        self.last_line_ts = ts
        actor_name, kind = self.player, "player"
        pm = PET_RE.match(body)
        if pm:
            actor_name, body = pm.group(1).strip(), pm.group(2)
            kind = "pet"
            if actor_name == self.player:
                kind = "player"
            else:
                merged = self.pseudo_pet(actor_name)
                if merged:                      # a pseudo pet: its damage is yours, under the power's name
                    body = self._as_own(body, merged)
                    actor_name, kind = self.player, "player"
                else:
                    self.typer.on_pet_line(actor_name, body, ts)
                    self._pet_seen[actor_name] = ts
                    if actor_name not in self.typer.known and body.startswith("You hit "):
                        self.unplaced[actor_name] = self.unplaced.get(actor_name, 0) + 1
        try:
            if kind == "player" and ("our " in body or body.endswith(" is recharged.")):
                sm = R_SEEN.search(body)
                if sm:
                    pw = next(g for g in sm.groups() if g)
                    for seg in self._targets(ts, combat=False):
                        a = seg.actor(actor_name, kind)
                        a.seen[pw] = a.seen.get(pw, 0) + 1
            self._dispatch(ts, actor_name, kind, body)
        except Exception:
            pass  # never let one weird line break the meter

    def pseudo_pet(self, name):
        """The power a pseudo pet's damage belongs to, or None for a real pet."""
        if name in self.typer.known:
            return None
        for rx, merged, need in PSEUDO_RES:
            if rx.search(name) and (need is None or need in self.my_powers):
                return merged or name
        if name in self.my_powers:
            return name
        return None

    @staticmethod
    def _as_own(body, power):
        f = lambda m: m.group(1) + power + m.group(2)
        for rx in (_RE_OWN_DMG, _RE_OWN_HIT, _RE_OWN_HEAL, _RE_OWN_ABS):
            if rx.match(body):
                return rx.sub(f, body, 1)
        return body

    def _dispatch(self, ts, who, kind, body):
        c0 = body[0]
        # login notice that names the character: "You have granted a free GM respec to <Name>."
        if c0 == "<" and "respec to " in body:
            m = re.search(r"respec to (.+?)\.?\s*$", re.sub(r"<[^>]*>", "", body))
            if m and m.group(1).strip():
                self._login_as(m.group(1).strip())
            return
        # --- outgoing damage -------------------------------------------
        if c0 == "Y" and body.startswith("You hit "):
            m = R_DMG.match(body)
            if m:
                target, power, amt, dtype, dot, flair = m.groups()
                amt = num(amt)
                power = self.pname(power, bool(dot))
                for seg in self._targets(ts):
                    a = seg.actor(who, kind)
                    a.damage += amt
                    a.touch(ts)
                    a.recent.append((ts, amt))
                    _get(a.powers, power).add(amt, bool(dot), flair, dtype, target)
                    step = 5 if seg.is_overall else 1
                    b = int(ts) // step
                    a.timeline[b] = a.timeline.get(b, 0.0) + amt
                    a.tl_step = step
                    e = seg.enemy(target)
                    e.received += amt
                    _get(e.received_by, (who, power)).add(amt, bool(dot), flair, dtype)
                self._enemy_seen[target] = ts
                self.version += 1
                return
        if c0 == "H" and body.startswith("HIT "):
            m = R_HIT.match(body)
            if m:
                target, power, chance = m.groups()
                power = self.pname(power)
                if kind == "pet" or not self._is_friendly_name(target):
                    chance = float(chance) if chance else None
                    for seg in self._targets(ts):
                        a = seg.actor(who, kind)
                        _get(a.powers, power).add_roll(True, chance)
                        a.rolls += 1
                        a.roll_hits += 1
                        if chance is not None:
                            a.chance_sum += chance
                            a.chance_n += 1
                    self.version += 1
                return
        if c0 == "M" and body.startswith("MISSED "):
            m = R_MISS.match(body)
            if m:
                target, power, chance = m.groups()
                power = self.pname(power)
                chance = float(chance)
                for seg in self._targets(ts):
                    a = seg.actor(who, kind)
                    _get(a.powers, power).add_roll(False, chance)
                    a.rolls += 1
                    a.chance_sum += chance
                    a.chance_n += 1
                self.version += 1
                return
        # --- incoming damage --------------------------------------------
        if " hits you with their " in body:
            m = R_TAKEN.match(body)
            if m:
                src, power, amt, dtype, dot, flair = m.groups()
                amt = num(amt)
                self._foe_seen[src] = ts
                if self._learn_self(src) and kind == "player":
                    who = self.player
                for seg in self._targets(ts):
                    a = seg.actor(who, kind)
                    a.taken += amt
                    _get(a.taken_by, (src, power)).add(amt, bool(dot), flair, dtype)
                    e = seg.enemy(src)
                    e.dealt += amt
                    _get(e.dealt_by, power).add(amt, bool(dot), flair, dtype, who)
                self.incoming[who].append(dict(ts=ts, kind="dmg", src=src, power=power, amount=amt,
                                               dtype=dtype, dot=bool(dot), flair=flair))
                self.version += 1
                return
        if " HITS you! " in body:
            m = R_EHIT.match(body)
            if m:
                src, power, chance = m.groups()
                chance = float(chance) if chance else None
                for seg in self._targets(ts):
                    a = seg.actor(who, kind)
                    a.def_rolls += 1
                    _get(a.taken_by, (src, power)).add_roll(True, chance)
                self.version += 1
                return
        if " HITS you! " in body and body.endswith("was autohit."):
            m = R_EAUTO.match(body)
            if m:
                src, power = m.groups()
                # the same wording is used for teammates' buffs, so only count someone who has been
                # fighting you (or that you've been fighting) in the last two minutes
                seen = max(self._foe_seen.get(src, 0), self._enemy_seen.get(src, 0))
                if ts - seen < 120 and not self._is_friendly_name(src):
                    for seg in self._targets(ts):
                        a = seg.actor(who, kind)
                        a.def_rolls += 1
                        _get(a.taken_by, (src, power)).add_roll(True, None)
                    self.version += 1
                return
        if " MISSES! " in body:
            m = R_EMISS.match(body)
            if m:
                src, power, chance = m.groups()
                for seg in self._targets(ts):
                    a = seg.actor(who, kind)
                    a.def_rolls += 1
                    a.def_miss += 1
                    _get(a.taken_by, (src, power)).add_roll(False, float(chance))
                self.incoming[who].append(dict(ts=ts, kind="miss", src=src, power=power, amount=0.0,
                                               dtype=None, dot=False, flair=None))
                self.version += 1
                return
        # --- healing -----------------------------------------------------
        if body.startswith("You heal "):
            m = R_HEAL.match(body)
            if m:
                target, power, amt = m.groups()
                amt = num(amt)
                power = self.pname(power)
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.heal += amt
                    a.touch(ts)
                    _get(a.heal_powers, power).add(amt, target=target)
                self.version += 1
                return
        if body.startswith("You are healed by your "):
            m = R_SELFHEAL.match(body)
            if m:
                power, amt = m.groups()
                amt = num(amt)
                power = self.pname(power)
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.heal += amt
                    _get(a.heal_powers, power).add(amt, target=who)
                    a.healed += amt
                    _get(a.healed_by, (who, power)).add(amt)
                self.incoming[who].append(dict(ts=ts, kind="heal", src=who, power=power, amount=amt,
                                               dtype=None, dot=False, flair=None))
                self.version += 1
                return
        if " heals you with their " in body:
            m = R_HEALED.match(body)
            if m:
                src, power, amt = m.groups()
                amt = num(amt)
                self._learn_owner(who, kind, src)
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.healed += amt
                    _get(a.healed_by, (src, power)).add(amt)
                self.incoming[who].append(dict(ts=ts, kind="heal", src=src, power=power, amount=amt,
                                               dtype=None, dot=False, flair=None))
                self.version += 1
                return
        if body.startswith("You grant "):
            m = R_ABS_OUT.match(body)
            if m:
                target, amt, power = m.groups()
                amt = num(amt)
                self._learn_self(target)
                power = self.pname(power)
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.absorb += amt
                    _get(a.absorb_powers, power).add(amt, target=target)
                self.version += 1
                return
        if " grants you " in body and "absorption" in body:
            m = R_ABS_IN.match(body)
            if m:
                src, amt, power = m.groups()
                amt = num(amt)
                self._learn_owner(who, kind, src)
                for seg in self._targets(ts, combat=False):
                    seg.actor(who, kind).absorbed += amt
                self.incoming[who].append(dict(ts=ts, kind="absorb", src=src, power=power, amount=amt,
                                               dtype=None, dot=False, flair=None))
                self.version += 1
                return
        if body.startswith("Your henchmen protect you"):
            m = R_PROTECT.match(body)
            if m:
                amt = num(m.group(1))
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.protect += amt
                    a.protect_n += 1
                self.incoming[who].append(dict(ts=ts, kind="protect", src="Your henchmen", power="Bodyguard",
                                               amount=amt, dtype=None, dot=False, flair=None))
                self.version += 1
                return
        # --- misc --------------------------------------------------------
        if body.startswith("You have defeated "):
            m = R_KILL.match(body)
            if m:
                target = m.group(1)
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.kills[target] = a.kills.get(target, 0) + 1
                    seg.enemy(target).kills += 1
                self.version += 1
                return
        if body.startswith("You gain ") and kind == "player":
            m = R_XP.match(body)
            if m:
                amt = num(m.group(1))
                for seg in self._targets(ts, combat=False):
                    seg.actor(who, kind).xp += amt
                    seg.xp += amt
                self.version += 1
                return
        if kind == "player" and (body.startswith("Welcome to City of Heroes") or body.startswith("Now entering")):
            m = R_NAME.match(body)
            if m:
                login = body.startswith("Welcome")
                if login:
                    self._login_as(m.group(1).strip(), welcome=True)
                else:
                    self.player = m.group(1).strip()
                    if self.overall_clear == "zone":
                        self.clear_overall()
                    self.version += 1
                return
        if kind == "player" and body.startswith("Entering "):
            zm = R_ZONE.match(body)
            if zm:
                if not hasattr(self, "zones"):
                    self.zones = set()
                self.zones.add(zm.group(1).strip())
                self.zone = zm.group(1).strip()
            if zm and self.overall_clear == "zone":
                self.clear_overall()
            return
        if kind == "player" and body.startswith("You activated the "):
            m = R_ACTIVATE.match(body)
            if m:
                power = self.pname(m.group(1))
                self.my_powers.add(m.group(1))
                self.typer.on_activate(m.group(1), ts)
                for seg in self._targets(ts, combat=False):
                    a = seg.actor(who, kind)
                    a.activations[power] = a.activations.get(power, 0) + 1
                return
        # --- crowd control on you or a pet, and pets going down (for alerts) ---------
        if " you with their " in body:
            m = R_MEZ.match(body)
            if m:
                self.alerts.append((ts, "mez_pet" if kind == "pet" else "mez", who) + m.groups())
                return
        if kind == "player" and body.startswith("You are ") and body.endswith("!"):
            m = R_YOU_MEZ.match(body)
            if m:
                self.alerts.append((ts, "mez", who, "", m.group(1), ""))
                return
        if kind == "player" and " has defeated " in body:
            m = R_DEFEATS.match(body)
            if m:
                killer, victim = m.groups()
                seen = self._pet_seen.get(victim)
                foe = self._enemy_seen.get(victim)
                if seen is not None and ts - seen < 120 and (foe is None or ts - foe > 120):
                    self._pet_seen.pop(victim, None)
                    self.alerts.append((ts, "pet_dead", victim, killer))
                return
        if R_DEATH.search(body):
            self.record_death(who, ts, body)

    def _login_as(self, name, welcome=False):
        """A login line named the character (Welcome / free respec notice)."""
        self.last_login_welcome = welcome
        first = self.player != name or getattr(self, "_last_login_name", None) != name
        self.player = name
        self.login_count = getattr(self, "login_count", 0) + 1
        self._last_login_name = name
        if first and self.overall_clear in ("zone", "login"):
            self.clear_overall()
        self.version += 1

    def _learn_self(self, name):
        """One of the account's own characters showing up as '<Name> heals/grants/hits you' can
        only be the character you're playing (you can't be logged in on two at once)."""
        if name and name in self.my_chars and name != self.player:
            self.player = name
            self.version += 1
            return True
        return False

    def _learn_owner(self, who, kind, src):
        """When the character is unknown (chat logging switched on mid-session), a pet saying
        '<Name> grants you / heals you' tells us who its owner - the player - is."""
        if self._learn_self(src):
            return
        if (self.player == "You" and kind == "pet" and src and src != who and not src.startswith("Your")
                and src not in self.typer.known):
            self.player = src
            self.version += 1

    def _is_friendly_name(self, name):
        """True when an autohit buff 'HIT' line targets you or one of your pets."""
        if name == self.player:
            return True
        if self.current and name in self.current.actors:
            return True
        return name in self.overall.actors

    # -- deaths -----------------------------------------------------------
    def record_death(self, victim, trigger_ts, text, window=None):
        window = window or self.recap_window
        inc = list(self.incoming.get(victim, ()))
        death_ts = None
        for e in reversed(inc):
            if e["kind"] == "dmg" and e["ts"] <= trigger_ts and trigger_ts - e["ts"] <= 600:
                death_ts = e["ts"]
                break
        if death_ts is None:
            if text != "manual":
                return None
            death_ts = trigger_ts
        # avoid recording the same death twice (e.g. several resurrect messages)
        for d in self.deaths[-5:]:
            if d.victim == victim and abs(d.ts - death_ts) < 1 and not d.manual and text != "manual":
                return None
        events = [dict(e) for e in inc if death_ts - window <= e["ts"] <= death_ts]
        d = Death(victim, death_ts, trigger_ts, text, events, window)
        self.deaths.append(d)
        # attach to the segment that contains the death
        target_seg = None
        for seg in reversed(self.segments):
            if seg.start - 1 <= death_ts <= seg.last + self.combat_timeout:
                target_seg = seg
                break
        if target_seg is None:
            target_seg = self.current or (self.segments[-1] if self.segments else None)
        if target_seg is not None:
            target_seg.deaths.append(d)
        self.overall.deaths.append(d)
        self.version += 1
        return d


# --------------------------------------------------------------------------
# Log file discovery + tailing
# --------------------------------------------------------------------------
def find_logs_dirs(hints):
    """Return candidate '<game>/accounts/<acct>/Logs' folders, newest first."""
    roots = []
    for h in hints:
        if not h:
            continue
        p = os.path.abspath(h)
        for _ in range(5):
            if os.path.isdir(os.path.join(p, "accounts")):
                roots.append(p)
                break
            parent = os.path.dirname(p)
            if parent == p:
                break
            p = parent
    roots.append(r"C:\Games\Homecoming")
    found = []
    for r in roots:
        for d in glob.glob(os.path.join(r, "accounts", "*", "Logs")):
            if os.path.isdir(d) and d not in found:
                found.append(d)
    found.sort(key=lambda d: os.path.getmtime(d), reverse=True)
    return found


def todays_log(logs_dir):
    """Today's chatlog, or the newest chatlog in the folder."""
    if not logs_dir or not os.path.isdir(logs_dir):
        return None
    today = os.path.join(logs_dir, "chatlog %s.txt" % dt.date.today().strftime("%Y-%m-%d"))
    if os.path.isfile(today):
        return today
    files = glob.glob(os.path.join(logs_dir, "chatlog*.txt"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


class LogTail:
    """Incrementally reads new complete lines from a growing text file."""

    def __init__(self, path):
        self.path = path
        self.offset = 0
        self.partial = b""

    def read_new(self, max_bytes=4 * 1024 * 1024):
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return []
        if size < self.offset:            # file was truncated / replaced
            self.offset, self.partial = 0, b""
        if size == self.offset:
            return []
        with open(self.path, "rb") as f:
            f.seek(self.offset)
            data = f.read(min(size - self.offset, max_bytes))
        self.offset += len(data)
        data = self.partial + data
        parts = data.split(b"\n")
        self.partial = parts.pop()
        return [p.decode("utf-8", "replace").rstrip("\r") for p in parts]

    @property
    def done(self):
        try:
            return os.path.getsize(self.path) <= self.offset
        except OSError:
            return True
