# Changelog

All notable changes to Hero Meter are listed here, newest first.

## v2.0.0-beta.4

### New
- **DPS over time graph** in the Breakdown window: damage per second across the fight (smoothed over
  5 seconds), with the peak and the average marked. It's drawn from per-second totals the meter already
  keeps, only when the window refreshes, so it's light on low-end PCs. It can be turned off under
  **Options → Alerts**.
- **Alerts**: a short message pops up above the meter when you're held, stunned, slept, terrified or
  confused (with who did it and with what), or when one of your pets is defeated. Immobilize alerts, pet
  mez alerts and a sound can be turned on under **Options → Alerts**. Only new events trigger alerts, never old log lines.
  Alerts follow the skin: a see-through game-menu panel in the City of Heroes skin, a flat banner in Details!.
- **Chat log clean-up** (Options → Log File). The game never removes its daily chat logs, so they pile up
  (hundreds of MB over time). Logs older than a week are zipped into one archive per month (about 90% smaller,
  nothing lost), and archives older than six months are deleted (never a zip in its first two weeks, so
  nothing disappears the first time it runs). Both ages can be changed, deleting can be set
  to Never, and today's log and the one being read are never touched. It runs in the background at most once
  a day, and there's a Clean up now button.
- **Personal records** (Options → Records): each character's biggest hit, best fight DPS, most damage, best
  DPS with pets, most kills, best HPS and longest fight survived, from live fights only (or a light list of the
  first three). A pop-up announces a new record. Record sets can be renamed or started fresh after a respec,
  and can optionally follow the linked build.
- **Copy diagnostics** lists pets the meter couldn't place, to help track down unusual pseudo pets.
- **CoH Sidekick builds** work like Mids builds: link a `.skif` file (or name it `CharacterName - anything.skif`)
  and Mids' Build shows Value Ranking, Planned vs Actual, Procs and Not in Build for it.
- **Proc fire rate** in Mids' Build → Procs: how often each proc fired, as a share of the hits (or uses) of
  the powers it's slotted in, or per minute for procs in passives and toggles.

### Fixed
- Shields granted by pseudo pets are credited to you, like their damage and heals.
- Enemy attacks logged as "was autohit" now count in your avoidance numbers (teammates' buffs, which use the
  same wording, are left out).
- Build powers now show their in-game names (Grave Knight, Barrier Reef, Whirling Smash...) instead of the
  internal names in the build file, so they match what the chat log says.

## v2.0.0-beta.3

### Fixed
- **Pseudo pets count as your damage.** Powers that drop an invisible stand-in to do their damage (Rain of
  Fire, Caltrops, Burn, Chain Induction, Lightning Rod, the Judgement powers and others) are now credited to
  you under the power's name, instead of showing up as a separate pet.
- Hits forced by the streakbreaker now count toward accuracy, for you and your pets.
- "Unresistable" damage is listed under its real damage type.

## v2.0.0-beta.2

### New
- **City of Heroes skin** (now the default). Every window, including Options, Breakdown, Recap and Mids'
  Build, gets the game's window look: a title tab with the game's long sloped corners, the beveled border
  in your window color, and a see-through body. Shapes, shades and opacity were measured from the game's
  own windows.
- **Skins, Window Themes and Bar Themes.** A **skin** is the shape and style of the windows (City of Heroes
  or Details!). **Window Themes** are the window colors, and **Bar Themes** color the bars. Every theme works
  with every skin, and both kinds of theme have their own editor.
- **Match the game's window color** (on by default). At login the meter reads the color of your in-game
  windows from their borders on screen (only while the game is the window in front) and uses it for its
  border, without any typing or `/wdw_save`. It only accepts a color it finds on at least two windows and
  sees twice in a row, skips big window bodies, the area under the mouse and Hero Meter's own windows, and
  keeps the last good color for each character, so a character you've played before switches instantly. With it off, the window
  theme's color is used (the default City of Heroes theme is the game's stock blue).
- **Pick it from a game window**: an eyedropper with a magnifier. Click the border of any game window to
  take its exact color for the character you're on.
- **The game's own fonts** (Montreal and Paragon City), read from each player's install. Nothing is bundled.
  Until the game can be found, a close Windows look-alike is used, and the meter switches over by itself.
- **Game-style menus**: see-through panels with radio dots, light-cyan items, white headings and fading
  dividers.
- **Mouse-over glow**: the border brightens and the title tab becomes more solid while the mouse is over
  a window.
- **CoH bars**: rounded, outlined bars with a sheen that follows each color's brightness, and a dim
  highlight on hover.
- **Procs collapse into one "Procs" row**, like pets. Left-click to open it, right-click to go back.
  A pet's procs collapse into that pet's own Procs row. Works in the meter and the Breakdown window.
- Bar Shape is its own dropdown, separate from bar colors.
- Hover tooltips get rounded corners with a matching edge in the CoH skin.
- Your own row always shows (at zero) when your pets have done damage and you haven't, so you can always
  get back to "You + Pets".
- Errors are written to `error_log.txt`, and the window-color reader keeps a short `color_log.txt`, both
  next to your settings, to make bug reports easier.
- **Show example bars** fills the meter with sample numbers while Options is open, to try looks without a
  fight.

### Fixed
- Moving the meter to a monitor with different scaling now resizes the fonts, border and frame together.
- Smooth, readable title text and title-bar icons at every size.
- Faster resizing and menu highlighting.
- The resize grip is easier to grab.
- Tooltips no longer stay on screen after the mouse leaves the meter.
- Clicking a bar to see its powers no longer leaves the window blank.
- Changing a theme, skin or preset updates the windows in place: no flashing, and Options keeps your
  scroll position instead of jumping to the top.
- Close always shuts Hero Meter down completely.
- Row spacing defaults to 3.

## v2.0.0-beta.1

First public beta of 2.0.0:

- Runs from anywhere: finds the Homecoming install by itself (running game, usual folders on every drive,
  or pick it once); settings live in `%APPDATA%\Hero Meter` (or next to the exe with `portable.txt`)
- Multiple snapping windows with tabs
- Themes, Theme Editor with save/share, skins, any font (plus your own `.ttf`/`.otf`)
- Profiles with export/import and automatic per-character switching
- Character select / logout detection, and a quick fix when a character isn't logging chat
- Mids' Reloaded integration: build linking, Planned vs Actual, Value Ranking, Procs, Not in Build
- Update check, About menu, Copy diagnostics for bug reports
- Hero Medallion app icon; fixed an error box that could appear on close
