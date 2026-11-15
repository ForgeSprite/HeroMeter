"""Alert sounds: the Windows default, a few built-in tones (made here, so there's nothing to license or
ship), or your own sound file (.wav, .ogg or .mp3), made ready once when you pick it."""
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


MAX_SECS = 2.0          # alerts stay short, so one never runs into the next
FADE_SECS = 0.08        # a quick fade where a long sound is cut, so it doesn't end in a click
SILENCE = 0.01          # about -40 dB: quieter than this at the start is trimmed off
FORMATS = (".wav", ".ogg", ".mp3")


def import_custom(src, folder):
    """Turn any .wav / .ogg / .mp3 into a short, ready-to-play .wav in the settings folder.

    The silence at the start is trimmed and anything past MAX_SECS fades out and is cut. The original file
    is never changed. Returns (path, info) where info has "secs" (the sound's own length) and "trimmed"
    (True when it was cut to MAX_SECS). Raises ValueError with a short reason if it can't be used."""
    import numpy as np
    ext = os.path.splitext(src)[1].lower()
    if ext not in FORMATS:
        raise ValueError("Please pick a .wav, .ogg or .mp3 file")
    try:
        import soundfile as sf
        data, rate = sf.read(src, dtype="float32", always_2d=True)
    except ImportError:
        if ext != ".wav":
            raise ValueError("Please pick a .wav file")
        data, rate = _read_wav(src)
    except Exception:
        raise ValueError("Couldn't read that sound file")
    if data.shape[1] > 2:                                    # surround sound: mix it down
        data = data.mean(axis=1, keepdims=True)
    loud = np.nonzero(np.abs(data).max(axis=1) > SILENCE)[0]
    if not len(loud):
        raise ValueError("That sound is silent")
    start = max(0, int(loud[0]) - int(rate * 0.005))         # keep 5 ms so the attack isn't clipped
    data = data[start:]
    secs = len(data) / float(rate)
    cap = int(rate * MAX_SECS)
    trimmed = len(data) > cap
    if trimmed:
        data = data[:cap].copy()
        nf = min(cap, int(rate * FADE_SECS))
        data[-nf:] *= np.linspace(1.0, 0.0, nf, dtype="float32")[:, None]
    os.makedirs(folder, exist_ok=True)
    stop()                                                   # Windows can't replace a file it's playing
    dest = os.path.join(folder, "alert sound.wav")
    pcm = (np.clip(data, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(dest, "wb") as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(int(rate))
        w.writeframes(pcm.tobytes())
    return dest, {"secs": secs, "trimmed": trimmed}


def _read_wav(src):
    """Plain 16-bit .wav without the sound library (only used if it's missing)."""
    import numpy as np
    with wave.open(src, "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError("Couldn't read that sound file")
        ch, rate = w.getnchannels(), w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return (raw.reshape(-1, ch).astype("float32") / 32768.0), rate


def stop():
    try:
        import winsound
        winsound.PlaySound(None, 0)
    except Exception:
        pass


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
