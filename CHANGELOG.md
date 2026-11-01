# Changelog

All notable changes to Hero Meter are listed here, newest first.

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
