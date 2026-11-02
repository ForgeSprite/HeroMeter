**This is a beta.** Thanks for helping test Hero Meter before the full release!

### How to try it

1. Download **`HeroMeter.exe`** below.
2. Put it anywhere and double-click it. There's no installer.
3. In the game, turn on **Log Chat** for each character you test with:
   `Menu → Options → Windows → Chat → Log Chat` (or type `/logchat` once).

If Windows says **"Windows protected your PC"**, click **More info → Run anyway**. New programs without a paid
signing certificate always get that warning. This file was built by GitHub from the code in this repo, and its
SHA-256 checksum is in `SHA256.txt` below.

### New in beta.4

- **Alerts**: a pop-up above the meter when you're held, stunned, slept, terrified or confused, or a pet is
  defeated. Immobilize, pet mez and sound are optional (**Options → Alerts**).
- **Personal records** for each character, with a pop-up when you beat one (**Options → Records**).
- **DPS over time** graph in the Breakdown window.
- **Proc fire rates** in Mids' Build → Procs.
- **CoH Sidekick builds** (`.skif`) work just like Mids builds.
- **Chat log clean-up**: old logs are zipped after a week and the zips deleted after six months (both
  changeable, or set to Never). Nothing is deleted in the first two weeks.
- Build powers show their in-game names, so more of them match your log.

### New in beta.3

- **Pseudo pets count as your damage.** Rain of Fire, Caltrops, Burn, Chain Induction, Lightning Rod, the
  Judgement powers and other powers that drop an invisible stand-in are now credited to you under the
  power's name, instead of showing up as a separate pet.
- **Streakbreaker hits** now count toward accuracy, for you and your pets.
- **"Unresistable" damage** is listed under its real damage type.
- The version number now shows which beta you're on (**⚙ → About Hero Meter**).

### New in beta.2

- **City of Heroes skin**, now the default. Every Hero Meter window looks like a window from the game:
  the same sloped title tab, beveled border and see-through body, measured from the game's own windows.
- **Matches your in-game window color.** When you log in, the meter reads the color of your game's windows
  (power tray first) and uses it for its border. You can turn this off under **⚙ → Window Themes**.
  For an exact pick, use **Pick it from a game window** there and click the border of any game window.
- **Skins, Window Themes and Bar Themes**: pick the window style (City of Heroes or Details!), the window
  colors and the bar colors separately. Every theme works with every skin, and each has an editor.
- **The game's fonts**, read from your own install (nothing is bundled). Until the meter can find your game,
  it uses a close Windows look-alike and switches over by itself.
- **Game-style menus**: see-through, with radio dots, light-cyan items and fading dividers.
- **Mouse-over glow**: the border brightens and the title tab firms up while your mouse is over a window.
- **Procs collapse into one "Procs" row**, like pets do. Left-click it to see each proc, right-click to go
  back. A pet's procs go into that pet's own Procs row.
- **Multiple monitors**: the meter resizes itself when you move it to a screen with different scaling.

### Things worth testing

- Does it find your game by itself? (Try it with the game closed and with it running.)
- Log into a few characters with different window colors. Does the meter's frame follow?
- Switch characters, or log out to character select and back in. Does the name follow you?
- Mastermind? Check that your pets show the right type and tier.
- Open a second window, snap them together, add tabs.
- If you use Mids Reborn, link a build: **⚙ → Mids' Build**.
- Close it. It should close quietly with no error box.

The full list of changes is in [CHANGELOG.md](https://github.com/ForgeSprite/HeroMeter/blob/main/CHANGELOG.md).

### Found a problem?

Go to **⚙ → About Hero Meter → Copy diagnostics**, then paste it into a
[new issue](https://github.com/ForgeSprite/HeroMeter/issues/new) along with what happened.
Account names are blanked out automatically.
