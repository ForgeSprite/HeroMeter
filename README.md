# Hero Meter

**A Details!-style damage meter for City of Heroes (Homecoming).**
Live damage, healing, deaths and pet stats in a small window that sits on top of the game,
built by reading your chat log as you play.

> Free and open source (GPL v3). One file, no installer.

<!-- screenshots go here: docs/screenshots/*.png -->

---

## Download & run

1. Grab **`HeroMeter.exe`** from the [latest release](../../releases/latest).
2. Put it anywhere (Desktop, Downloads, a tools folder...) and double-click it.
3. Turn on **Log Chat** in the game for each character:
   `Menu → Options → Windows → Chat → Log Chat` (or type `/logchat` once).

That's it. Hero Meter finds your Homecoming install by itself: from the running game,
from the usual install folders on every drive, or you point it there once.

**"Windows protected your PC"?** New programs without a paid code-signing certificate show this.
Click **More info → Run anyway**. Every release is built automatically by GitHub from the source in
this repository, and its SHA-256 checksum is attached to the release so you can verify the file.

---

## Features

**The meter**
- 15 modes: Damage Done, DPS, Damage Taken, Enemy Damage Taken, Damage Taken by Ability,
  Bodyguard Protection, Kills, Healing Done, HPS, Healing Taken, Absorbs, Accuracy, Avoidance,
  Deaths, Experience
- Segments per fight plus Overall; click any bar to drill into its powers, Shift+click for the full breakdown
- **Death recap**, MOBA-style: the last seconds before you died, hit by hit
- **Mastermind pets**: recognizes pet types and tiers; group them by tier, all together, or show each one
- Stays on top of the game (even fullscreen-windowed), optional click-through and fading

**Your way**
- **Multiple windows** that snap together (hold Alt to pull one away), each with its own **tabs**
- **9 themes** (Hero, Villain, Praetorian, Rikti, ...) plus a **Theme Editor** to make, save and share your own
- **Skins** (Compact, Minimalist, Classic, Large, Bottom HUD...) and any font on your PC, or add your own `.ttf`
- **Profiles**: save, load, export and import whole setups, and switch automatically **per character**

**Smart about characters**
- Knows which character you're on, switches at character select, and warns you
  (with a one-click fix) when a character doesn't have Log Chat turned on

**Mids' Reloaded integration**
- Links your Mids Reborn builds (`.mbd`) to your characters (automatically by file name)
- **Planned vs Actual**: every power in the build next to what the log shows you really doing
- **Value Ranking**: which powers earn their slots, and which ones are idle
- **Procs**: are your slotted procs actually firing?
- **Not in Build**: powers you use that the build doesn't have (respec drift, or the wrong build)

---

## Privacy

Hero Meter only **reads** files on your PC: your game chat log, your account's character list,
and (if you have it) your Mids Reborn builds. Nothing is uploaded.
The only network request is an optional check for a newer version on GitHub (turn it off under
`⚙ → About Hero Meter`).

Settings are saved in `%APPDATA%\Hero Meter`. Want everything next to the exe instead (USB stick, etc.)?
Create an empty file called `portable.txt` beside `HeroMeter.exe`.

## Reporting bugs

`⚙ → About Hero Meter → Copy diagnostics`, then paste it into a
[new issue](../../issues/new) with what happened. Account names are masked automatically.

---

## Building from source

Needs Windows, Python 3.10+ and PyInstaller.

```powershell
pip install pyinstaller
./build.ps1              # -> dist\HeroMeter.exe
# or run it straight from source:
python src/meter.py
```

Releases: bump `VERSION` in `src/meter.py`, add a line to `CHANGELOG.md`, then
`git tag v2.0.1; git push --tags`. GitHub Actions builds the exe and publishes the release.

## Credits

- Inspired by **Details! Damage Meter** for World of Warcraft
- **Oswald** font by Vernon Adams et al., SIL Open Font License (`src/fonts/OFL.txt`)
- Build data and enhancement names read from **Mids Reborn** when it's installed

## License

GNU General Public License v3.0. See [`LICENSE`](LICENSE).
You can use, share and change Hero Meter freely; shared modified versions must stay open source under the same license.

*Hero Meter is a fan-made tool and is not affiliated with or endorsed by Homecoming Servers or NCSoft.
City of Heroes is a trademark of NCSoft Corporation.*
