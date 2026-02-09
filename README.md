# EMPRESS YAPYAP Dual Launcher (Linux)

A Tkinter GUI launcher that starts **two YAPYAP instances** on Linux using **one Steam account** for local multiplayer testing.

Both instances are forced to load **BepInEx from your Gale profile** (Keso or Gale mod manager).
No BepInEx installation is required inside the Steam game directory.

## What this does

- Launches two YAPYAP instances (Host and Client)
- Uses separate Proton prefixes to avoid prefix locking
- Injects Doorstop and BepInEx from the Gale profile for both instances
- Prevents Unity from launching UnityCrashHandler instead of the game
- Optionally creates a Doorstop DLL symlink if required by Proton

## Requirements

- Linux
- Steam
- YAPYAP installed via Steam
- Proton installed (Proton 10, Proton Experimental, or similar)
- Gale Mod Manager or an existing Gale profile containing BepInEx
- Python 3 with Tkinter (included on most distributions)

## BepInEx location

This launcher targets the Gale profile preloader DLL:

~/.local/share/com.kesomannen.gale/yapyap/profiles/Default/BepInEx/core/BepInEx.Preloader.dll

Mods and configs are loaded from:

~/.local/share/com.kesomannen.gale/yapyap/profiles/Default/BepInEx/plugins
~/.local/share/com.kesomannen.gale/yapyap/profiles/Default/BepInEx/config

If you use a different Gale profile, select the correct BepInEx.Preloader.dll for that profile.

## Usage

1. Launch the application
2. Confirm Steam root is detected or browse to it manually
3. Select a Proton version
4. Confirm the game executable is YAPYAP.exe
5. Confirm the BepInEx DLL points to your Gale profile
6. Click EXECUTE LAUNCH
7. In the first window select Host
8. In the second window select Client

## Notes

- Steam Overlay may interfere with multi instance launching
- Windowed mode is recommended for testing
- Both instances share the same BepInEx profile and mods

## Folder expectations

### Steam root paths checked

- ~/.local/share/Steam
- ~/.steam/steam

### Game directory

$STEAM_ROOT/steamapps/common/YAPYAP

### Proton directory

$STEAM_ROOT/steamapps/common/Proton*/proton

## Running from source

python3 launcher.py

## Building a standalone binary

### Arch, CachyOS, Manjaro

sudo pacman -S python-pipx
pipx ensurepath
pipx install pyinstaller

pyinstaller --onefile --noconsole --name yapyap-dual-launcher launcher.py

Output binary:
dist/yapyap-dual-launcher

### Ubuntu, Debian, Fedora

sudo apt install pipx
pipx ensurepath
pipx install pyinstaller
pyinstaller --onefile --noconsole --name yapyap-dual-launcher launcher.py

## AppImage distribution

1. Build the binary with PyInstaller
2. Place it in AppDir/usr/bin/
3. Add a .desktop file in AppDir/usr/share/applications/
4. Add an application icon
5. Run appimagetool AppDir

## License

MIT
