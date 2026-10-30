# Hero Meter

A damage meter for City of Heroes (Homecoming), modeled on Details! from World of Warcraft.

It reads your chat log while you play and shows damage, healing, deaths and pet numbers in a small window on top of the game. It's one `.exe` with no installer. It's free, and the code is open source.

![Two Hero Meter windows snapped together](docs/screenshots/meter-windows.png)

---

## Getting started

1. Download **`HeroMeter.exe`** from the [latest release](../../releases/latest).
2. Put it wherever you like (Desktop, Downloads, a tools folder) and double-click it.
3. In the game, turn on chat logging for each character: **Menu → Options → Windows → Chat → Log Chat**. You can also type `/logchat` once in the chat box.

The meter looks for Homecoming on its own. If the game is running, it reads the install folder from the game itself. If not, it checks the usual install folders on each drive. If it still can't find it, click the meter and point it at your Homecoming folder. It only asks once.

**Windows says "Windows protected your PC"?** That's normal for a new program without a paid signing certificate. Click **More info**, then **Run anyway**. Every release is built by GitHub straight from the code in this repo, and the release page lists the file's SHA-256 checksum so you can check your download.

---

## What it does

### The meter

Fifteen modes: damage done, DPS, damage taken (by enemy or by ability), healing, HPS, healing taken, absorbs, bodyguard protection, kills, accuracy, avoidance, deaths and experience. Each fight is its own segment, plus an Overall total.

Click a bar to see that character's powers. Right-click to go back.

![Drilling into one character's powers](docs/screenshots/drilldown.png)

Shift+click a bar for the full breakdown: every power with hits, averages, the biggest hit, accuracy, damage types and targets.

![The breakdown window](docs/screenshots/breakdown.png)

### Masterminds

Hero Meter works out what each of your pets is, even after you rename them, and which tier it belongs to. You can show every pet on its own line, group them by tier, or lump them all together. Right-click a bar to switch.

![Every pet on its own line, with its type](docs/screenshots/pets.png)

### Death recap

When you die, the recap shows the last few seconds hit by hit: who killed you, with what, how much each enemy did and how long you lasted. It works much like the recap in a MOBA.

![Death recap](docs/screenshots/death-recap.png)

### Make it look how you want

- **Several windows**: open more meters, each showing its own mode and fight. Drag them near each other and they snap together and move as one. Hold Alt while dragging to pull one off.
- **Tabs**: give any window extra tabs so you can flip between modes.
- **Themes**: nine built-in color themes, including Hero, Villain, Praetorian and Rikti. The Theme Editor lets you change any color, save it as your own theme, and share it with friends by copy and paste.

![A few of the themes](docs/screenshots/themes.png)

- **Skins** change the shape of the meter: bar height, fonts, text style, title bar and status bar. You can pick any font on your PC or add your own `.ttf` file.

![The skins page](docs/screenshots/skins.png)

- **Profiles** save your whole setup, including window layout. You can export and import them, and give each character its own profile so the meter switches when you log in.

### It keeps up with your characters

Hero Meter knows which character you're on. When you go to character select, it goes back to "You" until the next character logs in. If that character doesn't have Log Chat turned on, the meter tells you within a few seconds and gives you the `/logchat` command to paste.

### Mids' Reloaded builds

If you plan builds in Mids Reborn, link a build to your character. Save the build as `CharacterName - anything.mbd` and it links itself. Then Hero Meter compares the plan with what you actually do in game:

- **Value Ranking**: which powers do the work, and which ones have a lot of slots for very little output.
- **Planned vs Actual**: every power in the build, what's slotted in it, and whether the log shows you using it.
- **Procs**: whether the procs you slotted are actually firing.
- **Not in Build**: powers you use that aren't in the build. This usually means a respec, or the wrong build is linked.

![Value Ranking for a linked build](docs/screenshots/mids-value.png)

![Which procs are firing](docs/screenshots/mids-procs.png)

The chat log can only show so much. Passive powers like Health and Stamina never print a line, and neither do some procs (debuffs, Build Up chances). For those, "not seen" doesn't mean anything is wrong.

---

## Privacy

Hero Meter only reads files on your own PC: your chat logs, your account's character list and, if you have Mids, your builds. Nothing gets uploaded. The one thing it does online is check GitHub for a newer version, and you can turn that off under **⚙ → About Hero Meter**.

Settings are saved in `%APPDATA%\Hero Meter`. To keep everything next to the exe instead (handy on a USB stick), put an empty file named `portable.txt` beside `HeroMeter.exe`.

## Found a bug?

Go to **⚙ → About Hero Meter → Copy diagnostics** and paste the result into a [new issue](../../issues/new), along with what happened. Account names are blanked out of the diagnostics automatically.

---

## Building it yourself

You'll need Windows, Python 3.10 or newer, and PyInstaller.

```powershell
pip install pyinstaller
./build.ps1            # makes dist\HeroMeter.exe
python src/meter.py    # or run it straight from the source
```

To release a new version: bump `VERSION` in `src/meter.py`, add a note to `CHANGELOG.md`, then push a tag (`git tag v2.0.1` and `git push --tags`). GitHub builds the exe and publishes the release.

## Credits

- Inspired by **Details! Damage Meter** for World of Warcraft.
- **Oswald** font by Vernon Adams and contributors, under the SIL Open Font License (see `src/fonts/OFL.txt`).
- Build data and enhancement names come from your own **Mids Reborn** install, when you have one.
- The screenshots use made-up demo characters.

## License

GNU General Public License v3.0 (see [`LICENSE`](LICENSE)). You can use, share and change Hero Meter. If you share a modified version, it has to stay open source under the same license.

*Hero Meter is a fan project. It isn't affiliated with or endorsed by Homecoming Servers or NCSoft. City of Heroes is a trademark of NCSoft Corporation.*
