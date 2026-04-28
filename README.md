# 🏰 The Tarnished's Chronicle

<div align="center">

🏰⚔️

**The ultimate boss tracking companion for Elden Ring**

[![Latest Release](https://img.shields.io/github/v/release/RysanekDavid/The-Tarnished-Chronicle?style=for-the-badge)](https://github.com/RysanekDavid/The-Tarnished-Chronicle/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/RysanekDavid/The-Tarnished-Chronicle/total?style=for-the-badge)](https://github.com/RysanekDavid/The-Tarnished-Chronicle/releases)
[![License](https://img.shields.io/github/license/RysanekDavid/The-Tarnished-Chronicle?style=for-the-badge&v=1)](LICENSE)

</div>

---

## 📖 About

**The Tarnished's Chronicle** is a comprehensive desktop application for Windows designed for Elden Ring enthusiasts who want to meticulously track their journey through the Lands Between. This isn't just a static checklist – it's an interactive, visually appealing companion that monitors your progress in real-time and motivates you to explore every corner of the game world.

Main site of the project: [NexusMods](https://www.nexusmods.com/eldenring/mods/8650?tab=description)

### ✨ Key Features

- **🎯 Real-time Boss Tracking** - Automatically detects defeated bosses by monitoring your save file
- **📍 Location-based Organization** - Bosses organized by game areas with progression indicators
- **⚔️ Comprehensive Coverage** - Includes both base game and Shadow of the Erdtree DLC bosses
- **📊 Detailed Statistics** - Track deaths, playtime, and completion percentages
- **🎮 Live Overlay** - In-game overlay showing your current progress
- **📹 OBS Integration** - Export stats to text files for streaming setups
- **🔄 Auto-Updates** - Automatic update notifications and installation
- **🔗 Seamless Coop Support** - Compatible with both Vanilla (.sl2) and Seamless Coop Mod (.co2) save files

---

## 🚀 Quick Start

### Installation

1. **Download** the latest `ER_Boss_Checklist_Setup.exe` from [Releases](https://github.com/RysanekDavid/The-Tarnished-Chronicle/releases/latest) or from [NexusMods](https://www.nexusmods.com/eldenring/mods/8650?tab=description)
2. **Run** the installer and follow the setup wizard
3. **Launch** The Tarnished's Chronicle from your desktop or start menu

### First Setup

1. **Select Save File** - Browse to your Elden Ring save file:
   - **Vanilla Elden Ring**: `ER0000.sl2` (Default location: `%APPDATA%\EldenRing\[Steam_ID]\ER0000.sl2`)
   - **Seamless Coop Mod**: `ER0000.co2` (Same location)
2. **Choose Character** - Select which character slot you want to track
3. **Start Playing** - The app will automatically monitor your progress!

---

## 📋 Features Deep Dive

### 🎯 Boss Tracking

- **Automatic Detection**: Monitors your save file for newly defeated bosses
- **Manual Marking**: Click checkboxes to manually mark bosses as defeated
- **Detailed Info**: Click boss names to see stats, death count, and kill timestamps
- **Search Function**: Quickly find specific bosses or locations

### 📊 Statistics

- **Boss Counter**: Track defeated bosses vs. total available
- **Death Tracking**: Monitor deaths per boss and overall
- **Playtime**: Real-time and total playtime tracking
- **Progress Percentage**: Visual completion indicators

### 🎮 Live Overlay

- **Customizable Display**: Show/hide different stats (bosses, deaths, time, last boss killed)
- **Color Customization**: Choose your preferred text color
- **Font Size Options**: Adjust overlay text size (10-30pt)
- **Always on Top**: Overlay stays visible while gaming

### 📹 OBS Integration

- **Text File Export**: Exports stats to `.txt` files for OBS text sources
- **Customizable Formats**: Define your own text formats for each stat
- **Real-time Updates**: Files update automatically as you play
- **Stream-Ready**: Perfect for livestreaming your Elden Ring runs

### 🔄 Content Filtering

- **Base Game/DLC**: Filter to show only base game or DLC content
- **Hide Defeated**: Option to hide already completed bosses
- **Location Search**: Find bosses by location or name

---

## 🔧 Configuration

### Overlay Settings

- **Toggle Overlay**: Enable/disable the in-game overlay
- **Display Options**: Choose which information to show
  - Boss counter
  - Death counter
  - Playtime (with/without seconds)
  - Last boss killed
- **Appearance**: Customize text color and font size

### OBS Integration Setup

1. **Enable OBS Output** - Toggle the OBS file generation
2. **Set Output Folder** - Choose where to save the text files
3. **Configure Files**:
   - `bosses.txt` - Boss counter (e.g., "Bosses: 45/238")
   - `deaths.txt` - Death counter (e.g., "Deaths: 127")
   - `time.txt` - Playtime (e.g., "Time: 25:30:15")
   - `last_boss.txt` - Last defeated boss (e.g., "Last Kill: Margit (14:23:45)")
4. **Custom Formats** - Define your own text templates using placeholders

### Advanced Features

- **Death Counter Reset**: Reset OBS death counter without affecting actual stats
- **Character Switching**: Switch between different character saves
- **Auto-Updates**: Automatically check for and install new versions

---

## 🎮 Supported Games

- **Elden Ring** (Base Game) ✅
- **Elden Ring: Shadow of the Erdtree** (DLC) ✅

---

## 💻 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB available space
- **Additional**: Active Elden Ring installation

---

## 🐛 Troubleshooting

### Common Issues

**App doesn't detect save file:**

- Ensure Elden Ring is installed and has been launched at least once
- Verify the save file path in Windows Explorer
- Try running the app as administrator

**Overlay not showing:**

- Check if overlay is enabled in settings
- Ensure the game is running in windowed or borderless mode
- Try toggling the overlay on/off

**OBS files not updating:**

- Verify the output folder path is correct
- Check that OBS file generation is enabled
- Ensure the files aren't being used by another application

**Performance issues:**

- Close unnecessary applications
- Reduce overlay refresh rate if experiencing frame drops
- Consider disabling real-time monitoring if on older hardware

### Getting Help

If you encounter issues not covered here:

1. Check [existing issues](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues)
2. Create a [new issue](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues/new) with:
   - Detailed description of the problem
   - Your system specifications
   - Steps to reproduce the issue
   - Any error messages

---

## 🔄 Updates & Changelog

The application includes automatic update checking. You'll be notified when new versions are available with detailed changelogs and the option to download and install updates automatically.

### Recent Updates

- **v1.0.1** - UI improvements, better settings panel management, scrollable OBS panel
- **v1.0.0** - Initial release with core functionality

### 🔮 Planned Features (Future Updates)

If the application gains community traction and success, planned features include:

- **👥 Friends Comparison** - Compare your boss completion stats with friends
- **⏱️ Speedrun Tracking** - Time tracking for speedrun attempts and personal bests
- **📊 Advanced Statistics** - Detailed analytics of your gameplay patterns and progress
- **🏆 Community Leaderboards** - Compare completion times and achievements globally
- **📈 Progress Visualization** - Charts and graphs showing your improvement over time
- **🎯 Challenge Modes** - Special tracking modes for no-death runs, SL1 runs, etc.
- **💾 Cloud Sync** - Backup and sync your progress across multiple devices
- **🎮 Multiple Character Comparison** - Side-by-side stats for all your characters

_These features will be prioritized based on community feedback and application usage._

---

## 🤝 Feedback & Bug Reports

**feedback and bug reports are highly welcomed!**

### 🐛 Bug Reports

Found a bug? Please report it:

1. **Check [existing issues](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues)** to avoid duplicates
2. **Create a [new issue](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues/new)** with:
   - Detailed description of the problem
   - Steps to reproduce the issue
   - Your system specifications
   - Screenshots if applicable

### 💡 Feature Requests

Have an idea for a new feature? I'd love to hear it! Create a [feature request issue](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues/new) and describe your idea.

### 🙏 Community Support

Your feedback helps make the application better for everyone. Thank you for contributing to the community!

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FromSoftware** - For creating the masterpiece that is Elden Ring
- **Community Contributors** - For feedback, bug reports, and suggestions
- **Beta Testers** - For helping refine the user experience

---

<div align="center">

**Made with ❤️ for the Elden Ring community**

[🔗 Download Latest Release](https://github.com/RysanekDavid/The-Tarnished-Chronicle/releases/latest) |
[🐛 Report Bug](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues) |
[💡 Request Feature](https://github.com/RysanekDavid/The-Tarnished-Chronicle/issues)

</div>
