"""Hover help for Options: one or two plain sentences per setting.

Keys are settings names. Keys starting with "@" match a label or button by its text
(a trailing "*" matches any text that starts with it). The default is added by the app.
"""

HELP = {
    # --- General
    "num_format": "How numbers are written on the bars. Short is easiest to read at a glance.",
    "update_interval": "How often the bars redraw, in seconds. Higher uses a little less CPU.",
    "wheel_speed": "How many rows one notch of the mouse wheel scrolls.",
    "time_measure": "How DPS is worked out. Effective divides damage by the whole fight. Active only counts "
                    "the time each character was attacking, which is fairer to someone who joined late.",
    "realtime_dps": "During a fight, show DPS over the last 5 seconds instead of the fight's average. "
                    "Good for seeing bursts.",
    # --- Fights
    "combat_timeout": "How many quiet seconds end a fight. The fight is then saved as its own segment.",
    "auto_current": "Jump to the new fight as soon as it starts. Turn off to keep looking at an older one.",
    "erase_trash": "Throw away very short fights, like one stray mob, so the fight list stays tidy.",
    "trash_seconds": "Fights shorter than this are thrown away when Auto-erase is on.",
    "max_segments": "How many fights the list keeps. Older ones drop off. Overall isn't affected.",
    "overall_clear": "When Overall starts again from zero. By default only when you press Reset.",
    # --- Pets
    "show_pet_type": "Add the pet's type after its name, such as Zombie. Handy when you rename your pets.",
    "tier_order": "List pets by tier, strongest first, instead of by how much they did.",
    "@Grouping": "Show every pet on its own bar, group them by tier, put all pets on one bar, or add your "
                 "pets into your own bar.",
    # --- Alerts
    "alert_mez": "A pop-up above the meter when you're held, stunned, slept, terrified or confused, "
                 "with who did it and with what. Only when it lands: attempts your mez protection "
                 "stops don't count.",
    "alert_immob": "Also warn when you're immobilized. It happens a lot in some fights, so it starts off.",
    "alert_taunt": "A pop-up when an enemy taunts you and it lands.",
    "alert_pet_dead": "A pop-up when one of your pets is defeated, and by what.",
    "alert_pet_mez": "A pop-up when one of your pets is held, stunned or slept.",
    "alert_pet_log": "Warns once a day if you use pet powers but no pet damage reaches the chat log. "
                     "That means the Pet channels aren't in a chat tab yet.",
    "alert_sound": "Play the Windows alert sound with each pop-up.",
    "@Show a test alert": "Shows an example alert, so you can see how it looks with your skin.",
    # --- Records
    "records_mode": "Full keeps seven records. Light keeps three: biggest hit, best fight DPS and most "
                    "damage in one fight.",
    "records_popup": "A pop-up when you beat one of your records.",
    "records_by_build": "Keep a separate set of records for each build you link on the Builds page.",
    "records_min_fight": "A fight has to last this long to count for the per-second records, so one lucky "
                         "crit can't set them.",
    "@Character": "Which character's records to show.",
    "@Record set": "Pick a set to look at. Older sets are kept when you Start fresh.",
    "@Rename": "Rename this record set, for example after the build it belongs to.",
    "@Start fresh": "Keeps this set to look back at and starts a new one from zero. Use it after a respec.",
    # --- Skin and layout
    "@Save current layout": "Saves your current sizes and fonts as a layout preset you can pick again later.",
    # --- Window themes
    "match_game_color": "Use your character's own window color from the game. Each character gets its own. "
                        "Picking a theme here turns this off.",
    "@Pick it from a game window": "Click this, then click the border of any game window to use its exact color.",
    "@Read it automatically": "Read the color again from the game's window borders. The game has to be in front.",
    "@Edit current window theme": "Change any window color and save it as your own theme.",
    "@Edit current bar theme": "Change any bar color, save it as your own theme, or share it.",
    # --- Bars
    "row_height": "Height of each bar.",
    "row_spacing": "Gap between bars.",
    "grow_up": "Where the first bar is. Bottom to top suits a meter that sits low on the screen.",
    "bar_texture": "The look of each bar: glossy, flat, glass and more.",
    "show_icons": "Class and pet icons at the start of each bar.",
    "row_border": "A thin outline around each bar.",
    "total_bar": "An extra bar at the top with the total of all bars.",
    "aligned_cols": "Line up the numbers on the right into neat columns.",
    "bar_color_mode": "Color each pet its own way, color pets by tier, or use one color for every bar.",
    "bar_single_color": "The color used when Bar colors is set to one color.",
    "bar_bg_color": "The color of the empty part of each bar.",
    "self_color_on": "Give your own bar a different color so it stands out.",
    "self_color": "The color of your own bar, when the setting above is on.",
    # --- Bar text
    "@Font": "The font on the bars. Pick any font on your PC, or add your own .ttf file.",
    "font_size": "Size of the text on the bars.",
    "text_style": "A shadow or outline behind the text makes it easier to read over bright bars.",
    "show_rank": "The 1, 2, 3 in front of each name.",
    "rt_total": "The total, such as 12.3K, on the right of each bar.",
    "rt_ps": "Per second (DPS or HPS) on the right of each bar.",
    "rt_pct": "Each bar's share of all bars, in percent.",
    "bracket": "What goes around the per second and percent numbers.",
    # --- Title bar
    "title_height": "Height of the title bar.",
    "title_font_size": "Size of the title text.",
    "title_bottom": "Put the title bar under the bars instead of above them.",
    "autohide_buttons": "Only show the title bar buttons while the mouse is over the meter.",
    "btn_segments": "The button for picking a fight or Overall.",
    "btn_report": "The button that copies the numbers, ready to paste in game chat.",
    "btn_reset": "The button that clears all fights and Overall.",
    "btn_min": "The button that minimizes Hero Meter to the taskbar.",
    # --- Statusbar
    "statusbar": "A thin strip under the bars with up to three extra numbers.",
    "sb_left": "What the left side of the statusbar shows. Totals add up every bar on the meter.",
    "sb_center": "What the middle of the statusbar shows.",
    "sb_right": "What the right side of the statusbar shows. Totals add up every bar on the meter.",
    # --- Tooltips
    "tip_enabled": "Hovering a bar shows its top powers.",
    "tip_font_size": "Size of the tooltip text.",
    "tip_lines": "How many lines a tooltip shows. Hold Shift while hovering to see all of them.",
    "tip_side": "Show tooltips next to the mouse, or beside the meter.",
    # --- Windows and tabs
    "@Open a new window": "Opens another meter window. Each window can show its own mode and fight.",
    "snap_windows": "Windows dragged close together stick and move as one. Hold Alt while dragging to pull one away.",
    "tabs_always": "Show the tab bar even when a window has only one tab.",
    # --- Opacity and fading
    "alpha": "How see-through the meter is. Lower lets more of the game show through.",
    "topmost": "Keep the meter above other windows, including the game.",
    "no_focus": "Clicking the meter leaves the game active, so your keys keep going to the game.",
    "hide_unfocused": "Minimize the meter to the taskbar while another program is focused, and bring it back "
                      "when you click into the game. It stays visible while you use Hero Meter's own windows.",
    "auto_dpi": "Keeps the meter the same size when you move it to a monitor with different Windows scaling.",
    "ooc_fade": "Fade the meter out when you're not fighting.",
    "ooc_alpha": "How visible the meter is while faded out of combat.",
    "combat_alpha": "How visible the meter is during a fight.",
    "hover_fade": "Keep the meter faded until you move the mouse over it.",
    "hover_alpha": "How visible the meter is until you hover it.",
    "click_through": "Clicks go through the meter to the game. Hold Ctrl when you want to click the meter.",
    "click_through_combat": "Only let clicks through during a fight.",
    "body_bg": "Window background color. Only used by the Details! skin.",
    "border_on": "A border around the window. Only used by the Details! skin.",
    "border_color": "Border color. Only used by the Details! skin.",
    # --- Profiles
    "auto_profile": "When a character logs in, switch to the profile you picked for them below.",
    "@Profile for*": "The profile to use when this character logs in.",
    "@Copy of current": "Make the new profile from your current setup.",
    "@Start from defaults": "Make the new profile with every setting at its default.",
    "@Export": "Copy this profile to the clipboard so you can share it.",
    "@Import (paste)": "Add something a friend shared, from your clipboard.",
    "@Import from file…": "Add a profile from a file.",
    "@Export active to file…": "Save the active profile to a file.",
    # --- Log files
    "@Use Today's Log": "Follow the newest chat log on its own. This is the default.",
    "@Choose Log File…": "Read one log file you pick, for example an older day.",
    "@Logs Folder…": "Tell Hero Meter where your Logs folder is, if it can't find it.",
    "load_history": "When the meter opens, read the fights you already had today.",
    "log_cleanup": "Zip chat logs once they're old and delete very old zips. Today's log is never touched, "
                   "and a new zip is never deleted in its first two weeks.",
    "log_keep_days": "Logs newer than this stay as they are. Older ones are zipped, one zip per month.",
    "log_delete_days": "Zips older than this are deleted. Choose Never to keep them all.",
    "@Clean up now": "Run the log clean-up right away instead of waiting for it.",
    "@Open logs folder": "Open the game's Logs folder in Explorer.",
    # --- Death recap and breakdown
    "recap_window": "How many seconds before a death the recap covers.",
    "recap_events": "The most hits and heals one recap shows.",
    "recap_min_heal": "Hide heals smaller than this, like regeneration ticks, to keep the recap short.",
    "recap_reverse": "Put the killing blow at the top instead of the bottom.",
    "recap_show_misses": "Also list attacks that missed you.",
    "dot_separate": "Show damage-over-time ticks as their own line, apart from the hit that started them. "
                    "Changing this reads today's log again.",
    "merge_crits": "In the breakdown, count critical hits together with normal hits instead of listing them separately.",
    "bd_graph": "The DPS-over-time graph at the top of the breakdown window.",
    # --- Builds
    "@Open build window": "Compare your linked build with what you actually do in game.",
    "auto_build": "Link a build to a character when the file name starts with that character's name.",
    # --- Rename powers
    "@Auto-merge 'Refracted' powers": "Show every Refracted power under its normal name, so the two "
                                      "count as one power.",
    "@Apply & re-read log": "Use your renames and read today's log again to show them.",
    "@Add": "Add this rename to the list.",
    # --- Theme editors
    "@Start from": "Pick a theme to start from. Nothing changes until you Apply or Save.",
    "@Theme name": "The name your saved theme gets.",
    "@Apply (try it)": "Use these colors now without saving them.",
    "@Save as theme": "Keep these colors as your own theme under the name above.",
    "@Export (copy)": "Copy this theme to the clipboard to share it.",
    # --- Top of every page
    "@Scale:": "Makes everything in Hero Meter bigger or smaller.",
    "@Show example bars in the meter": "Fill the meter with sample numbers while Options is open, so you can "
                                       "try a look without a fight.",
}
