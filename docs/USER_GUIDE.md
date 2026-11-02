# Hero Meter user guide

This guide covers everything in Hero Meter: setting it up, reading the meter, every page in Options with its default, the bigger features, and fixes for common problems.

You can open it from the meter at any time. Click **⚙** and choose **User Guide**, or click **User Guide** at the top right of the Options window to jump straight to the section for the page you're on.

## Contents

- [Getting started](#getting-started)
- [Using the meter](#using-the-meter)
- [Options reference](#options-reference)
  - Meter: [General](#general), [Fights and segments](#fights-and-segments), [Pets](#pets), [Alerts](#alerts), [Records](#records)
  - Look: [Skin and layout](#skin-and-layout), [Window themes](#window-themes), [Bar themes](#bar-themes), [Bars](#bars), [Bar text](#bar-text), [Title bar](#title-bar), [Statusbar](#statusbar), [Tooltips](#tooltips)
  - Windows: [Windows and tabs](#windows-and-tabs), [Opacity and fading](#opacity-and-fading), [Profiles](#profiles)
  - Data: [Log files](#log-files), [Death recap and breakdown](#death-recap-and-breakdown), [Builds](#builds), [Rename powers](#rename-powers)
  - Editors: [Window theme editor](#window-theme-editor), [Bar theme editor](#bar-theme-editor)
- [Features in depth](#features-in-depth)
- [Troubleshooting and FAQ](#troubleshooting-and-faq)
- [Privacy](#privacy)

---

## Getting started

### Install

1. Download `HeroMeter.exe` from the [latest release](https://github.com/ForgeSprite/HeroMeter/releases/latest).
2. Put it anywhere you like and double-click it. There is no installer.
3. If Windows shows "Windows protected your PC", click **More info** and then **Run anyway**. New programs without a paid signing certificate always get this warning. Each release page lists the file's SHA-256 checksum if you want to check your download.

### Turn on chat logging in the game

Hero Meter reads the chat log the game writes to disk, so logging has to be on for every character you want to track.

- In the game, open **Menu → Options → Windows → Chat** and turn on **Log Chat**.
- Or type `/logchat` once in the chat box.

If you log in on a character that doesn't have logging on, the meter tells you within a few seconds and gives you the command to paste.

### Add the pet channels (pet users only)

The game only writes a chat channel to the log if that channel is in one of your chat tabs. Pet damage uses its own channels, which aren't in any tab by default. This matters for Masterminds and pet classes, and also for powers that do their damage through an invisible pet, such as Rain of Fire, Caltrops, Burn, Ice Storm and Blizzard.

1. Right-click a tab on your chat window (Combat is a good choice) and choose **Edit Tab**.
2. Add these channels: Pet Combat, Pet Damage Inflicted, Pet Damage Received, Pet Hit Rolls, Pet Healing Delivered and Pet Healing Received.
3. Do this once on each character that uses pets.

Hero Meter warns you if it sees you use a pet power but no pet lines turn up in the log.

### Finding the game

The meter looks for Homecoming on its own. If the game is running it asks the game where it's installed. If not, it checks the usual install folders on each drive. If it still can't find it, click the meter and point it at your Homecoming folder. It only asks once.

---

## Using the meter

### The window

The title bar shows the current mode and fight. It has buttons for Segments, Report, Reset, Minimize, Settings (⚙) and Close. You can hide the first four on the [Title bar](#title-bar) page.

Drag the title bar to move the window. Drag the bottom-right corner to resize it.

### Modes

Right-click the title, or right-click an empty part of the meter, to choose what it shows. There are fifteen modes:

| Group | Modes |
|---|---|
| Damage | Damage Done, DPS, Damage Taken, Enemy Damage Taken, Damage Taken by Ability, Bodyguard Protection, Kills |
| Healing | Healing Done, HPS, Healing Taken, Absorbs Granted |
| Other | Accuracy, Avoidance, Deaths, Experience |

The same menu lets you add a tab, open a new window, show example bars and open a manual death recap.

### Segments and Overall

Each fight becomes its own segment. A fight ends when nothing happens for a few seconds (10 by default). Click the Segments button to pick a fight, the current fight, or Overall, which is everything since the last reset. The Reset button clears all fights and Overall.

### Looking closer

- Click a bar to see that character's or pet's powers. Right-click to go back.
- Shift+click a bar to open the full breakdown: every power with hits, average, biggest hit, accuracy, damage types and targets, plus a DPS-over-time graph.
- Right-click a pet group (such as a tier) to open or close it.
- Hover a bar for a tooltip. Hold Shift to see every line instead of the first few.

### Reports

The Report button copies the numbers to your clipboard. Pick a one-line top 5 or top 10 to paste into game chat, or a full multi-line report.

### The ⚙ menu

Clicking ⚙ gives you quick access to Options, the build window, the log file choice, pet display and grouping, profiles, Always on top, the User Guide and About Hero Meter. About Hero Meter has the update check switch and **Copy diagnostics** for bug reports.

---

## Options reference

Open Options from **⚙ → Options…**. Pages are grouped into Meter, Look, Windows and Data. The search box at the top of the list finds any setting by name and highlights it on the page.

Two controls sit at the top of every page:

- **Scale** makes the whole Hero Meter interface bigger or smaller (default 100%).
- **Show example bars in the meter** fills the meter with sample numbers while Options is open, so you can try a look without starting a fight. It turns itself off when you close Options.

Most changes apply right away. The defaults below are what a fresh install uses. Sizes on the Look pages come from your skin and layout preset, so those are listed with their range instead.

### General

| Setting | Default | What it does |
|---|---|---|
| Number format | 12.3K (short) | How numbers are written: short (12.3K), full (12,345) or plain (12345). |
| Update interval (sec) | 0.3 | How often the bars redraw, from 0.1 to 2 seconds. Higher uses a little less CPU. |
| Mouse wheel speed | 1 | How many rows one wheel notch scrolls. |
| Time measure | Effective (whole fight) | Effective divides by the whole fight. Active only counts the time each character was attacking, which is kinder to support characters who join late. |
| Show real-time DPS (last 5 sec) while fighting | Off | Shows your DPS over the last five seconds during a fight instead of the fight average. |

### Fights and segments

| Setting | Default | What it does |
|---|---|---|
| End fight after idle (sec) | 10 | Seconds of quiet before a fight is closed and saved as a segment. |
| Switch to the current fight when a new one starts | On | Jumps the meter to the new fight. Turn it off to keep looking at an old one. |
| Auto-erase short trash fights | Off | Throws away fights shorter than the next setting. |
| ...shorter than (sec) | 5 | The cut-off for trash fights. |
| Fights to keep | 30 | Older fights are dropped once you pass this number. Overall is not affected. |
| Clear overall data | Only when I reset | Can also clear Overall on every zone change, or on login and character switch. |

### Pets

| Setting | Default | What it does |
|---|---|---|
| Show pet type on bars | On | Adds the pet's type after its name, which helps when you've renamed your pets. |
| Order pets by tier (Tier 3 first) | On | Sorts pets by tier instead of by damage. |
| Grouping | Group pets by tier | Show every pet, group pets by tier, group all pets together, or merge everything (you and your pets as one bar). |

Right-click a bar in the meter to switch grouping quickly.

### Alerts

A short message pops up just above the meter when something needs your attention. Alerts only react to what's happening now, never to old lines read when the meter starts. See [How alerts work](#how-alerts-work) for more.

| Setting | Default | What it does |
|---|---|---|
| When you're held, stunned, slept, terrified or confused | On | The pop-up names the effect, the enemy and the power. |
| Also when you're immobilized | Off | Immobilize happens a lot, so it starts off. |
| When one of your pets is defeated | On | |
| When one of your pets is held, stunned or slept | Off | |
| When pet or pseudo-pet damage isn't reaching the chat log | On | Fires when you use a pet power but no pet lines appear. See [Add the pet channels](#add-the-pet-channels-pet-users-only). |
| Play a sound with each alert | Off | |

**Show a test alert** shows an example so you can see how it looks in your skin.

### Records

Hero Meter keeps your best numbers for each character, from fights it saw live. See [How records work](#how-records-work).

| Setting | Default | What it does |
|---|---|---|
| Records to keep | Full list | The full list has seven records. Light keeps three: biggest hit, best fight DPS and most damage in one fight. |
| Pop up when you set a new record | On | |
| Keep separate records for each linked build | Off | Uses a separate record set for each build you link on the [Builds](#builds) page. |
| Min. fight length (sec) | 20 | A fight has to last this long to count for the per-second records, so one lucky crit can't set them. |

Below the settings, pick a **Character** and a **Record set** to see its records. **Rename** changes the set's name. **Start fresh** keeps the current set (you can still pick it to look back) and starts a new one, for example after a respec.

### Skin and layout

A skin is the shape and style of every Hero Meter window: frames, title bars, tabs, menus and fonts.

- City of Heroes (the default) copies the game's own windows, with the oval title tab, the beveled border, the see-through body and the game's own fonts.
- Details! is the flat, square look of the WoW addon.

Colors come from window themes and bar themes, which work with every skin.

**Layout presets** change sizes and fonts only: Default, Compact, Minimalist, Classic Details, Large & Bold and Bottom HUD. Click one to apply it. **Save current layout** stores your own sizes as a new preset.

### Window themes

Window themes are the colors of the windows. Every theme works with every skin. The built-in themes are City of Heroes, Details! Dark, Paragon Blue, Arachnos Red, Praetorian Steel, Rikti Green, Midnight Purple, Ember, Frost and Synthwave.

| Setting | Default | What it does |
|---|---|---|
| Match the game's window color | On | Uses your character's own window color from the game. Picking a theme switches this off. |
| Pick it from a game window | | Click this, then click the border of any game window to take its exact color. |
| Read it automatically | | Reads the color again from the game's window borders. |
| Edit current window theme | | Opens the [Window theme editor](#window-theme-editor). |

See [Matching the game's color](#matching-the-games-color) for how this works.

### Bar themes

Bar themes only color the bars: you, each pet tier, other pets and enemies. The built-in themes are Minimalistic (Details), which is the default, plus Hero, Villain, Praetorian, Rikti, Shadow, Phoenix, Frost and Neon.

Click a theme to use it. **Edit current bar theme** opens the [Bar theme editor](#bar-theme-editor). Bar shape, height, spacing and borders are on the [Bars](#bars) page.

### Bars

| Setting | Default | What it does |
|---|---|---|
| Bar height | from your skin (14 to 40) | Height of each row. |
| Spacing | from your skin (0 to 8) | Gap between rows. |
| Bar growth direction | Top to bottom | Bottom to top is handy when the meter sits low on the screen. |
| Bar shape | City of Heroes (rounded gloss) | Also Glossy, Smooth, Flat, Dark, Raised edges, Inset, Glass, Split two-tone and Outline (neon). |
| Show icons | On | Class and pet icons at the start of each bar. |
| Thin border around bars | Off | |
| Show a Total bar at the top | Off | Adds a bar with the group total. |
| Aligned text columns | Off | Lines up the numbers on the right into columns. |
| Bar colors | Each pet its own color | Also by henchman tier, or one color for every bar. |
| Single bar color | light blue | Used when Bar colors is set to one color. |
| Bar background | from the theme | The empty part of each row. |
| Use a different bar color for you | Off | Makes your own bar stand out. |
| Your bar color | | The color for your bar when the setting above is on. |

### Bar text

| Setting | Default | What it does |
|---|---|---|
| Font | from your skin | Any font on your PC. You can also add your own `.ttf` file. |
| Text size | from your skin (9 to 26) | |
| Text effect | from your skin | Shadow, Outline or None. |
| Show rank numbers | On | The 1, 2, 3 in front of each name. |
| Show pet type after the name | On | Same as the setting on the Pets page. |
| Show total | On | The total on the right side of each bar. |
| Show per second | On | DPS or HPS on the right side. |
| Show percent | On | Share of the group total. |
| Bracket | ( ) | What goes around the per second and percent numbers: ( ), [ ] or nothing. |

### Title bar

| Setting | Default | What it does |
|---|---|---|
| Height | from your skin (16 to 36) | |
| Text size | from your skin (9 to 24) | |
| Title bar at the bottom | Off | Moves the title bar under the bars. |
| Hide buttons until mouse-over | Off | |
| Segments, Report, Reset, Minimize | On | Show or hide each button. Settings and Close are always shown. |

### Statusbar

An optional strip under the bars.

| Setting | Default | What it does |
|---|---|---|
| Show statusbar | Off | |
| Left | Segment name | Each slot can show nothing, the segment name, the fight timer, group DPS, your DPS, group damage, deaths or kills. |
| Center | Fight timer | |
| Right | Group DPS | |

### Tooltips

| Setting | Default | What it does |
|---|---|---|
| Show tooltips | On | Hovering a bar shows its top powers. |
| Text size | 13 | |
| Lines (hold Shift for all) | 10 | How many lines show before you hold Shift. |
| Position | Next to the mouse | Or beside the meter. |

### Windows and tabs

Each window, and each tab, shows its own mode and segment.

- **Open a new window** adds another meter window. You can also right-click a title and choose New window.
- **Snap windows together when dragged close** (default on). Snapped windows move together when you drag one of them. Hold Alt while dragging to pull one window away.
- **Always show the tab bar** (default off). Without it the tab bar only appears once a window has two or more tabs.

Working with tabs:

- Right-click a title and choose New tab, or click **+** on the tab bar.
- Click a tab to switch to it.
- Right-click a tab to change what it shows.
- Middle-click a tab to close it.
- Closing the first (main) window closes them all.

### Opacity and fading

| Setting | Default | What it does |
|---|---|---|
| Opacity (%) | 100 | How see-through the whole window is, from 20 to 100. |
| Always on top (also above City of Heroes) | On | |
| Clicking the meter doesn't take focus from the game | On | Your keys keep going to the game after you click the meter. |
| Match each monitor's Windows scaling automatically | On | Keeps the meter the right size when you move it between monitors with different scaling. |
| Fade out when not in combat | Off | |
| Out-of-combat opacity (%) | 40 | Used while faded. |
| In-combat opacity (%) | 100 | |
| Fade until mouse-over | Off | Keeps the meter faded until you hover it. |
| Faded opacity (%) | 35 | |
| Click-through (clicks go to the game) | Off | Clicks pass through the meter to the game. Hold Ctrl to click the meter while this is on. |
| Click-through only in combat | Off | |

Hovering the meter always brings it back to full opacity.

The **Details! skin window** settings (background color, window border and border color) are only used by the Details! skin. Colors for every skin come from window themes.

### Profiles

A profile holds every look and behavior setting plus your window layout. Changes save to the active profile on their own.

- **New profile**: give it a name, then choose **Copy of current** or **Start from defaults**.
- **Share**: export the active profile to a file or the clipboard, and import one from a file or by pasting.
- **Switch profiles automatically when I log in** (default on). Pick a profile for the character you're on, and the meter switches to it whenever that character logs in.

Some things are shared by all profiles: the log file, renamed powers, pet types, and your own themes and skins.

### Log files

| Setting | Default | What it does |
|---|---|---|
| Log file | Automatic (today's log) | **Use Today's Log** follows the newest log on its own. **Choose Log File…** reads one file you pick. **Logs Folder…** sets where the logs are. |
| Load earlier fights from today's log on start | On | When the meter opens, it reads the fights you already had today. |

**Logging pets** repeats the pet channel steps from [Getting started](#add-the-pet-channels-pet-users-only).

**Log clean-up** keeps the game's logs folder from growing forever. See [Log clean-up](#log-clean-up) for how it keeps your logs safe.

| Setting | Default | What it does |
|---|---|---|
| Clean up old chat logs automatically | On | |
| Keep logs unzipped for | 1 week | 3 days, 1 week, 2 weeks, 1 month or 3 months. |
| Delete zipped logs after | 6 months | 1 month, 3 months, 6 months, 1 year, 2 years or Never. |

The page shows how many logs and zipped months you have and how much space they use. **Clean up now** runs it straight away, and **Open logs folder** opens the folder in Explorer.

### Death recap and breakdown

| Setting | Default | What it does |
|---|---|---|
| Recap length (sec) | 12 | How far back the death recap looks. |
| Events to show | 40 | |
| Hide heals smaller than | 0 | Hides tiny heals and regeneration ticks. |
| Newest events first | Off | |
| Show attacks that missed you | On | |
| Show damage-over-time as its own line | Off | Splits DoT ticks from the hit that applied them. Changing this re-reads today's log. |
| Merge critical hits into normal hits | Off | |
| Show the DPS-over-time graph | On | The graph at the top of the breakdown window. |

### Builds

Compare a planned build from Mids Reborn (`.mbd`) or CoH Sidekick (`.skif`) with what you actually do in game. See [Comparing your build](#comparing-your-build).

- **Open build window** opens the comparison for your current character.
- **Match builds to characters by file name automatically** (default on). Name a build file like `Mindguard - Tanker (...).mbd` or `Mindguard - anything.skif` and it links itself to the character Mindguard.
- **Linked builds** lists each character and its build. Click ✕ to unlink one.

### Rename powers

Give a power a new name, or merge two powers by giving them the same name (for example `Refracted Searing Beam` → `Searing Beam`).

Type the power name as it appears in the log, type the name to show, and click **Add**. **Auto-merge 'Refracted' powers** does this for every Refracted power at once. Click **Apply & re-read log** to see the change.

### Window theme editor

Open it from **Window themes → Edit current window theme**. Pick a theme in **Start from**, change any color, then click **Apply (try it)** or **Save as theme** to keep it under a new name.

- Window border is the frame color in every skin. With "Match the game's window color" on, the game's color is used instead.
- Window, Text & accents and Menus & panels hold the rest of the colors. Window, text and panel colors are used by the Details! skin. Accents and menus are used by both skins.

### Bar theme editor

Open it from **Bar themes → Edit current bar theme**. Pick a theme in **Start from**, change any color, then **Apply (try it)** or **Save as theme**.

You can set colors for your bar, each pet tier, enemies and each pet type. **Export (copy)** puts the theme on your clipboard to share, and **Import (paste)** adds one a friend sent you. The preview uses your current skin and bar shape.

---

## Features in depth

### Matching the game's color

With **Match the game's window color** on, the meter reads your character's window color when you log in. It looks at the borders of the game's own windows, only while City of Heroes is the window in front, and keeps nothing but the color.

If it picks the wrong color (for example because a bright zone is behind a window), use **Pick it from a game window** and click a window border yourself. The picked color is used right away, and the automatic reader keeps running for your other characters.

Each character gets its own color. Choosing a window theme by hand turns matching off.

### Skins and themes

Three separate things decide how the meter looks, and you can mix them freely:

- The skin sets the shape: frames, title bar, tabs, menus and fonts.
- The window theme sets the window colors.
- The bar theme sets the bar colors, and the bar shape is picked on the Bars page.

Layout presets change sizes and fonts on top of all that. Once you like the result, save it in a [profile](#profiles).

### How alerts work

Alerts read the same chat log as the meter, so they show up as soon as the game writes the line. The pop-up names what happened, who did it and with what power, and uses the look of your skin. Click it to close it early.

The log doesn't say how long an effect lasts, so alerts don't show timers.

The pet logging alert is different. It appears when you use a pet power such as a summon, Rain of Fire or Caltrops, but no pet lines show up after it. That almost always means the pet channels aren't in a chat tab yet.

### How records work

Records only come from fights the meter saw live, not from old logs it reads when it starts. The full list holds:

- Biggest hit
- Best fight DPS
- Most damage in one fight
- Best DPS with your pets
- Most kills in one fight
- Best healing per second
- Longest fight survived

Each record shows the fight length, date and zone. Records are kept for each character, in record sets. Use **Start fresh** after a respec so your new build starts from zero, and rename the set to say which build it's for. If you link builds, **Keep separate records for each linked build** does this for you.

### Comparing your build

Link a build on the [Builds](#builds) page, or name the file after your character so it links itself. The build window has four tabs:

- Value ranking shows which powers do the work and which have a lot of slots for very little output.
- Planned vs actual lists every power in the build, what's slotted in it, and whether the log shows you using it.
- Procs shows whether your slotted procs fire, and how often.
- Not in build lists powers you used that aren't in the build. This usually means a respec, or the wrong build is linked.

You can compare against Overall or against the segment shown in the main window.

Some things never print a line in the chat log. Passive powers like Health and Stamina don't, and neither do some procs (debuffs and Build Up chances). For those, "not seen" doesn't mean anything is wrong.

Power and enhancement names come from your own Mids Reborn install when you have one.

### Log clean-up

The game writes one chat log for every day you play and never deletes them. Over a few years this can reach hundreds of megabytes. Clean-up runs in the background:

1. Logs older than the keep time (1 week by default) are zipped into one archive per month. Zipping makes them about 90% smaller and nothing is lost.
2. Before an original log is removed, its zipped copy is checked for the right size and checksum. If the check fails, the original stays.
3. Zipped archives older than the delete time (6 months by default) are removed. Set this to **Never** to keep them forever.

A few rules keep this safe:

- Today's log and the log the meter is reading are never touched.
- A newly made archive is never deleted in its first two weeks, even if the logs inside it are old. This gives you time to change the setting after you first turn it on.
- A small notice appears when clean-up zips or deletes anything. Click it to open the Log files page.

To open an old log, double-click the monthly zip in Explorer.

### Death recap

When you die, the recap shows the last few seconds hit by hit: who hit you, with what, how much each enemy did and how long you lasted. **Recap Last Moments (manual)** in the right-click menu opens one at any time, even if you didn't die.

---

## Troubleshooting and FAQ

### The meter is empty

Check that Log Chat is on for this character (`/logchat`). Then check that the meter is reading today's log: the file name is shown in the ⚙ menu, and **Use today's log automatically** should be ticked.

### My pets or Rain of Fire don't show up

The pet channels aren't in a chat tab. Follow [Add the pet channels](#add-the-pet-channels-pet-users-only). The game only starts logging them from that point, so earlier fights stay without pet damage.

### Can Hero Meter add the pet channels for me?

No. Doing it would mean typing into the game or replacing your chat settings file, and both would get in the way of how you set up your chat. It's a one-time change per character.

### The window color is wrong

Use **Pick it from a game window** on the [Window themes](#window-themes) page and click a game window border.

### The meter covers the game and I can't click through it

Turn on click-through on the [Opacity and fading](#opacity-and-fading) page. Hold Ctrl when you want to click the meter.

### Numbers look different from another parser

Check **Time measure** on the [General](#general) page. Effective and Active time give different DPS for the same fight.

### I changed a lot and want the old look back

Make a new profile with **Start from defaults**, or switch back to a profile you saved.

### Where are my settings?

In `%APPDATA%\Hero Meter`. To keep everything next to the exe instead (for example on a USB stick), put an empty file named `portable.txt` beside `HeroMeter.exe`.

### How do I report a bug?

Go to **⚙ → About Hero Meter → Copy diagnostics** and paste the result into a [new issue](https://github.com/ForgeSprite/HeroMeter/issues/new), along with what happened. Account names are blanked out of the diagnostics.

### How do updates work?

Hero Meter checks GitHub for a newer version and shows **Update available** in the ⚙ menu when there is one. You can turn the check off under **⚙ → About Hero Meter**.

---

## Privacy

Hero Meter only reads files on your own PC: your chat logs, your account's character list, the game's fonts and your Mids or Sidekick builds.

The only files it changes are old chat logs, when log clean-up zips or removes them, and its own settings.

To match your window color it looks at the game window, only while City of Heroes is in front, and keeps nothing but the color it found.

Nothing is uploaded. The only thing it does online is check GitHub for a newer version, and you can turn that off.
