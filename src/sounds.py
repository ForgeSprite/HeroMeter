"""Alert sounds: the Windows default, a few built-in tones (made here, so there's nothing to license or
ship), or your own .wav file."""
import math
import os
import struct
import tempfile
import wave

RATE = 22050

# key -> label, in the order shown in Options
CHOICES = [
    ("default", "Windows alert"),
    ("chime", "Chime"),
    ("ping", "Ping"),
    ("alarm", "Alarm"),
    ("soft", "Soft tone"),
    ("power", "Power down"),
    ("custom", "Your own sound"),
]
LABEL = dict(CHOICES)


def _tone(parts, volume=0.5):
    """parts: [(freq_hz or (f0, f1) for a slide, seconds, attack_s, decay_rate)] -> 16-bit samples."""
    out = []
    for freq, secs, attack, decay in parts:
        n = int(RATE * secs)
        phase = 0.0
        for i in range(n):
            t = i / RATE
            f = freq if not isinstance(freq, tuple) else freq[0] + (freq[1] - freq[0]) * (i / max(1, n - 1))
            phase += 2 * math.pi * f / RATE
            env = min(1.0, t / attack) if attack else 1.0
            env *= math.exp(-decay * t)
            env *= min(1.0, (n - i) / (RATE * 0.01))            # no click at the end
            s = math.sin(phase) * 0.8 + math.sin(2 * phase) * 0.2  # a touch of brightness
            out.append(int(max(-1.0, min(1.0, s * env * volume)) * 32767))
    return out


SHAPES = {
    "chime": lambda: _tone([(880, 0.16, 0.005, 9), (1318.5, 0.32, 0.005, 7)], 0.45),
    "ping": lambda: _tone([(1568, 0.22, 0.002, 16)], 0.45),
    "alarm": lambda: _tone([(740, 0.11, 0.004, 2), (988, 0.11, 0.004, 2)] * 3, 0.4),
    "soft": lambda: _tone([(523.25, 0.35, 0.04, 6)], 0.4),
    "power": lambda: _tone([((900, 300), 0.35, 0.005, 3)], 0.4),
}


def builtin_path(key):
    """A .wav for a built-in tone, made once and kept in the temp folder."""
    folder = os.path.join(tempfile.gettempdir(), "HeroMeter sounds")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s.wav" % key)
    if not os.path.isfile(path):
        samples = SHAPES[key]()
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(struct.pack("<%dh" % len(samples), *samples))
    return path


def play(key, custom_file=None):
    """Play an alert sound without waiting for it to finish. Never raises."""
    try:
        import winsound
        if key == "custom" and custom_file and os.path.isfile(custom_file):
            winsound.PlaySound(custom_file, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        elif key in SHAPES:
            winsound.PlaySound(builtin_path(key), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        else:
            winsound.MessageBeep(0x30)
    except Exception:
        pass
