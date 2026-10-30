"""
pettypes.py - works out what kind of pet each named pet is.

City of Heroes logs only show a pet's name. When you use a Mastermind summon
power the log says "You activated the <power> power.", and the new pets start
showing up in the log right after. We match the two up, so every pet gets a
type ("Lich") and a tier (Tier 3 Henchman). What we learn is saved, so pets
keep their type across days and restarts.
"""

# summon power -> (pet type, tier, power set, pets per summon)
SUMMONS = {
    # Necromancy
    "Zombie Horde": ("Zombie", 1, "Necromancy", 3),
    "Grave Knight": ("Grave Knight", 2, "Necromancy", 2),
    "Lich": ("Lich", 3, "Necromancy", 1),
    # Demon Summoning
    "Summon Demonlings": ("Demonling", 1, "Demon Summoning", 3),
    "Summon Demons": ("Demon", 2, "Demon Summoning", 2),
    "Summon Demon Prince": ("Demon Prince", 3, "Demon Summoning", 1),
    # Robotics
    "Battle Drones": ("Battle Drone", 1, "Robotics", 3),
    "Protector Bots": ("Protector Bot", 2, "Robotics", 2),
    "Assault Bot": ("Assault Bot", 3, "Robotics", 1),
    # Mercenaries
    "Soldiers": ("Soldier", 1, "Mercenaries", 3),
    "Spec Ops": ("Spec Ops", 2, "Mercenaries", 2),
    "Commando": ("Commando", 3, "Mercenaries", 1),
    # Ninjas
    "Call Genin": ("Genin", 1, "Ninjas", 3),
    "Call Jounin": ("Jounin", 2, "Ninjas", 2),
    "Oni": ("Oni", 3, "Ninjas", 1),
    # Thugs
    "Call Thugs": ("Thug", 1, "Thugs", 3),
    "Call Enforcer": ("Enforcer", 2, "Thugs", 2),
    "Call Bruiser": ("Bruiser", 3, "Thugs", 1),
    # Beast Mastery
    "Call Wolves": ("Wolf", 1, "Beast Mastery", 3),
    "Call Lions": ("Lion", 2, "Beast Mastery", 2),
    "Call Dire Wolf": ("Dire Wolf", 3, "Beast Mastery", 1),
    # common temporary / non-henchman pets
    "Dark Servant": ("Dark Servant", 0, "Pet", 1),
    "Soul Extraction": ("Soul Spirit", 0, "Pet", 6),
    "Gang War": ("Gang War Thug", 0, "Pet", 5),
    "Summon Spiderlings": ("Spiderling", 0, "Pet", 3),
    "Phantom Army": ("Phantasm Decoy", 0, "Pet", 3),
    "Phantasm": ("Phantasm", 0, "Pet", 1),
    "Animate Stone": ("Animated Stone", 0, "Pet", 1),
    "Fire Imps": ("Fire Imp", 0, "Pet", 3),
    "Singularity": ("Singularity", 0, "Pet", 1),
    "Voltaic Sentinel": ("Voltaic Sentinel", 0, "Pet", 1),
    "Gun Drone": ("Gun Drone", 0, "Pet", 1),
}

# Signature powers: a pet using one of these is that type, even if we never saw
# it being summoned (e.g. it was out before the log started).
SIGNATURE = {
    "Zombie Vomit": "Zombie Horde", "Projectile Vomit": "Zombie Horde", "Zombie Brawl": "Zombie Horde",
    "Hack": "Grave Knight", "Disembowel": "Grave Knight", "Slash": "Grave Knight",
    "Ghastly Blast": "Soul Extraction",
    "Tenebrous Tentacles": "Lich", "Torrent": "Lich", "Petrifying Gaze": "Lich",
}

TIER_LABEL = {1: "Tier 1 Henchman", 2: "Tier 2 Henchman", 3: "Tier 3 Henchman", 0: "Pet"}


def describe(info):
    """'Lich  \u2022  Tier 3 Henchman' style text for a pet-type entry."""
    if not info:
        return "Pet"
    ptype, tier, pset = info[0], info[1], info[2]
    if tier:
        return "%s  \u2022  %s  (%s)" % (ptype, TIER_LABEL[tier], pset)
    return "%s  \u2022  Pet" % ptype


class PetTyper:
    WINDOW = 25.0           # seconds after a summon in which new pets are linked to it

    def __init__(self, known=None):
        self.known = dict(known or {})      # name -> [type, tier, set]
        self.pending = []                   # [summon power, ts, slots left]
        self.seen = set()
        self.confirmed = set()           # types proven by a signature power
        self.changed = False

    def on_activate(self, power, ts):
        if power in SUMMONS:
            self.pending.append([power, ts, SUMMONS[power][3]])
            self.pending = [p for p in self.pending if ts - p[1] <= self.WINDOW]

    def on_pet_line(self, name, body, ts):
        if name not in self.seen:
            self.seen.add(name)
            if name not in self.confirmed:
                self._first_seen(name, ts)
        if name not in self.confirmed:
            for sig, summon in SIGNATURE.items():
                if (" your %s " % sig) in body:
                    self._set(name, summon)
                    self.confirmed.add(name)
                    break

    def _first_seen(self, name, ts):
        live = [p for p in self.pending if 0 <= ts - p[1] <= self.WINDOW and p[2] > 0]
        if not live:
            return
        # newest summon that still has room, otherwise the oldest with room
        p = live[-1]
        p[2] -= 1
        self._set(name, p[0])

    def _set(self, name, summon):
        t = SUMMONS[summon]
        val = [t[0], t[1], t[2]]
        if self.known.get(name) != val:
            self.known[name] = val
            self.changed = True

    def get(self, name):
        return self.known.get(name)
