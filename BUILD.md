# Building H4Launcher

H4Launcher is packaged with [PyInstaller](https://pyinstaller.org/).
PyInstaller **cannot cross-compile** - a build produced on macOS only
runs on macOS, a build produced on Windows only runs on Windows, and
so on. So there are two ways to get all three platforms:

## Option A - build locally on each OS

Run this on a Windows machine, a Mac, and a Linux machine (or VMs):

```bash
pip install -r requirements.txt
pip install -r requirements-build.txt
python build.py
```

Output appears in `dist/`:

| OS      | Raw output                          | Packaged                                                        |
|---------|--------------------------------------|-------------------------------------------------------------------|
| Windows | `dist/H4Launcher/H4Launcher.exe`    | `dist/H4Launcher-0.1.0-windows-x64.zip`                          |
| macOS   | `dist/H4Launcher.app`               | `dist/H4Launcher-0.1.0-macos.zip`, `dist/H4Launcher-0.1.0-macos.dmg` (dmg only if `hdiutil` is present, which it is on every real Mac) |
| Linux   | `dist/H4Launcher/H4Launcher`        | `dist/H4Launcher-0.1.0-linux-x64.tar.gz`                          |

## Option B - build all three at once with GitHub Actions

Push a version tag and CI builds all three for you:

```bash
git tag v0.1.0
git push origin v0.1.0
```

`.github/workflows/build.yml` runs `build.py` on
`windows-latest`, `macos-latest`, and `ubuntu-latest`, and uploads
each result as a workflow artifact. You can also trigger it manually
from the **Actions** tab ("Run workflow") without pushing a tag.

## Known gotchas

- **Linux Tk**: some Linux distros / Python builds don't ship Tk by
  default. If `python build.py` fails with a Tk-related import
  error, install it first: `sudo apt install python3-tk` (Debian/
  Ubuntu) or the equivalent for your distro. The CI workflow already
  does this for you.
- **macOS Gatekeeper**: an unsigned `.app` will show an "unidentified
  developer" warning on other people's Macs. That's expected without
  an Apple Developer certificate - right-click → Open bypasses it.
  Proper code signing/notarization is a separate step not covered
  here.
- **App icon**: the spec file looks for `assets/icon.ico` (Windows)
  and `assets/icon.icns` (macOS) and uses them automatically if
  present, but the project doesn't ship these yet - builds work fine
  without them, they'll just use the default PyInstaller icon.
- **Antivirus false positives**: PyInstaller-built exes are commonly
  (and incorrectly) flagged by some Windows antivirus engines. This
  is a known PyInstaller/AV issue, not a sign anything's wrong with
  the build.