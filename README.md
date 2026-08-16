# H4Launcher

A lightweight custom Minecraft Java Edition launcher written in Python.

H4Launcher is designed to provide a simple desktop launcher for Minecraft Java
Edition with support for vanilla installations, Forge, offline profiles,
custom Java configurations, and a verbose launch console.

## Features

- Minecraft Java Edition launcher
- Vanilla support
- Forge support
- Offline profiles
- Microsoft account authentication
- Minecraft versions:
  - 1.8.9
  - 1.12.2
  - 1.16.5
- Automatic Minecraft directory management
- Custom Java executable
- Custom JVM arguments
- Configurable RAM allocation
- Forge mods folder access
- Multiple UI color themes
- Verbose Minecraft launch console
- Background downloading and launching
- Cross-platform design for:
  - Windows
  - Linux
  - macOS

## Requirements

- Python 3.10.6
- Java
- Internet connection for downloading Minecraft/Forge files

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/H4Launcher.git
cd H4Launcher
````

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it.

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run H4Launcher:

```bash
python main.py
```

## Minecraft Directory

H4Launcher currently stores Minecraft data inside the project directory:

```text
H4Launcher/
└── .minecraft/
```

The directory is created automatically when the launcher starts.

The launcher stores:

* Minecraft versions
* Libraries
* Assets
* Mods
* Logs
* Other Minecraft runtime files

The `.minecraft` directory is ignored by Git and will not be uploaded to
GitHub.

## Configuration

Launcher settings are stored locally in:

```text
.h4launcher/config.json
```

Settings include:

* RAM allocation
* Java executable
* JVM arguments
* Offline username
* Selected Minecraft version
* Selected loader
* UI theme

Local configuration files are ignored by Git.

## Forge

When Forge is selected, H4Launcher provides access to the local mods folder.

```text
.minecraft/
└── mods/
```

Place compatible `.jar` mods inside the directory.

Always make sure a mod matches the Minecraft and Forge version you are using.

## Offline Mode

H4Launcher supports local offline profiles.

Offline mode does not authenticate with Microsoft and should only be used with
Minecraft installations you are legally entitled to use.

## Development

The project is intentionally separated into several modules:

```text
core/
    Authentication and launcher logic

ui/
    CustomTkinter interface

utils/
    Configuration and local data management
```

The application is designed to keep UI code separate from Minecraft launcher
logic.

## Roadmap

Planned improvements include:

* Per-instance Minecraft installations
* Better Forge version management
* Installed mod management
* Mod enable/disable controls
* Minecraft profile management
* Java version detection
* Download progress improvements
* Launcher update system
* Crash log viewer
* Better Microsoft authentication handling
* More Minecraft versions
* Launcher packaging for Windows, Linux, and macOS

## Disclaimer

H4Launcher is an independent third-party project and is not affiliated with,
endorsed by, or sponsored by Mojang Studios or Microsoft.

Minecraft is a property of Mojang Studios.

Users are responsible for complying with the applicable Minecraft and Microsoft
terms and licenses.

## License

H4Launcher is released under the MIT License.

See [LICENSE](LICENSE) for details.
