# Contributing to Hero Meter

Thanks for wanting to help! Bug reports, ideas and code are all welcome.

## Found a bug?

Open a [bug report](../../issues/new?template=bug_report.yml). The most useful thing you can include is the
output of **⚙ → About Hero Meter → Copy diagnostics** (account names are blanked out). If Hero Meter froze,
attach `freeze-log.txt` from its settings folder too.

## Have an idea?

Open a [feature idea](../../issues/new?template=feature_request.yml) first, before writing any code. That way we
can agree it fits Hero Meter before you spend time on it, and nobody builds something that gets turned down.

## Sending code

1. **Talk first.** Open or comment on an issue so we've agreed on the idea.
2. **One change per pull request.** Small pull requests are easier to review and easier to undo.
3. **Keep the defaults safe.** New behavior that changes how the meter acts starts **off**, unless we agree
   otherwise.
4. **Match the rest of the app.** A new setting needs:
   - a hover note in `src/options_help.py`
   - a line in `docs/USER_GUIDE.md`
   - a fresh Options search index: run `python src/_make_index.py` if you have it, or just mention it in the
     pull request and it'll be regenerated.
5. **Test it in game** and say what you tried in the pull request.

Every pull request is reviewed before it's merged, and changes may be asked for.

## Running it from source

You'll need Windows and Python 3.10 or newer.

```powershell
pip install numpy pillow
python src/meter.py          # run it
pip install pyinstaller
./build.ps1                  # build dist\HeroMeter.exe
```

## A few house rules

- **Hero Meter only reads.** It reads your chat log and files on your own PC. It doesn't upload anything, and it
  doesn't change other programs' settings. Please keep it that way.
- **No personal data in commits:** no chat logs, settings files, account or character names.
- **Plain, friendly wording** in anything players see.

## License

Hero Meter is licensed under the [GNU GPL v3](LICENSE). By sending a pull request, you agree that your
contribution is shared under the same license. You'll be credited in the changelog and release notes.
