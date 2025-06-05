# PROJECT KICKOFF: Elden Ring Boss Tracker – "The Tarnished's Chronicle"

**Kickoff Date:** May 29, 2025
**Document Version:** 1.1
**Project Motto:** Every defeated boss is a chapter in your legend. Record them all!

---

## Part 1: INTRODUCTION AND APPLICATION OVERVIEW

### Application Overview ("The Tarnished's Chronicle"):

"The Tarnished's Chronicle" is a desktop application for Windows designed for Elden Ring fans who want to meticulously track their game progress, especially concerning defeated bosses. This application won't just be a static list; its goal is to offer an **interactive and visually engaging experience** that immerses players and motivates them to explore the Lands Between and overcome its challenges. Users will be able to track their progress in real-time (or near real-time) by monitoring their save file, see which bosses they've already defeated in each area, unlock achievements for reaching milestones, and explore detailed information about individual adversaries. The entire interface will be designed with an emphasis on **"gamification" and user-friendliness**, making the application enjoyable and satisfying to use.

### Project Goal:

To create a robust and user-friendly desktop application that:

- **Automatically monitors the Elden Ring save file.**
- **Accurately detects and parses** the status of defeated bosses.
- **Displays player progress** in an interactive and gamified user interface.
- Offers **detailed information about bosses** and tracks achievements.
- Provides **"near real-time" updates** based on changes in the save file.

### Key Features (Extended):

- **Automatic monitoring of the Elden Ring save file** (ER0000.sl2 and potentially .co2 for Seamless Coop).
- **Parsing of relevant parts of the save file** to obtain the status of individual bosses.
- **Gamified User Interface (GUI):**
  - **Expandable Sections by Map Area:** Bosses grouped by in-game regions (Limgrave, Caelid, etc.) with checkboxes and visual progress indicators for each area.
  - **Achievements Panel:** For defeating all bosses in an area, specific groups of bosses, or reaching other milestones. Displayed with progress bars and rewards (e.g., stars, virtual trophies).
  - **Boss Detail on Click:** A dialog window with detailed information about the boss (description, lore background, known weaknesses, rewards for defeat, placeholder for image/artwork).
- **Option to select/manage game profiles** (characters).
- **Local storage and loading** of detected boss statuses and achievements per profile.
- **Distribution as an .exe installer.**

---

## Part 2: TECHNICAL SPECIFICATIONS AND RESOURCES

### Main Technologies:

- **Language:** Python
- **GUI:** PySide6 (preferred due to LGPL license) or PyQt6
- **File Monitoring:** watchdog
- **Binary Data Parsing:** `struct` module, potentially Kaitai Struct
- **Application Data Storage:** JSON files

### Information Sources:

- **Boss List and ID Flags:** User-provided boss spreadsheet (already provided); community resources (Google Spreadsheet 1Nn-d4_mzEtGUSQXscCkQ41AhtqO_wF2Aw3yoTBdW9lk, Hexinton's Cheat Engine Table, soarqin/EROverlay, SoulsModding Wiki, Elden Ring Compass, ClayAmore/ER-Save-Lib).
- **Boss Details (Description, Weaknesses, Rewards, Images):** Game wikis (Fextralife, IGN, etc.), community databases. This information will not be parsed from the save file but will be part of the application's data.

---

## Part 3: PROJECT MANAGEMENT AND DOCUMENTATION

### Progress Tracking:

- This document serves as the main TO-DO list. Each task will be marked as completed (e.g., by checking `[x]`) once finished.
- Progress will be reviewed regularly.

### Change Management (CHANGELOG.md):

- All significant changes in code, functionality, or project structure must be recorded in the `CHANGELOG.md` file in the project's root directory.
- **CHANGELOG.md Entry Format:**

  ```markdown
  ## [Application Version] - YYYY-MM-DD

  ### Added

  - Description of new feature or enhancement.

  ### Changed

  - Description of a change to existing functionality.

  ### Fixed

  - Description of a bug fix.

  ### Removed

  - Description of a removed feature.
  ```

- Responsibility for maintaining `CHANGELOG.md` lies with anyone making changes.

---

## PHASE 1: ANALYSIS AND RESEARCH (Highest Priority, Most Uncertainty) 🔬

- [ ] **1.1. Mapping the ER0000.sl2 Save File Format (and .co2):**
  - [ ] 1.1.1. Gather and analyze save files.
  - [ ] 1.1.2. Explore basic structure (hex editors).
  - [ ] 1.1.3. Analyze MD5 checksum implementation.
  - [ ] 1.1.4. Consider support for .co2 save files.
- [ ] **1.2. Identification and Storage Method for Defeated Boss Flags:**
  - [ ] 1.2.1. Analyze community resources for boss event flag IDs.
  - [ ] 1.2.2. Understand the mechanism of event flag storage (bit fields, calculations).
  - [ ] 1.2.3. Perform targeted save file diffing for verification.
- [ ] **1.3. Analysis of Existing Tools (especially ClayAmore/ER-Save-Lib):**
  - [ ] 1.3.1. Study the source code of ER-Save-Lib.
  - [ ] 1.3.2. Evaluate the portability of logic to Python.
  - [ ] 1.3.3. Explore other relevant parsers/editors.
- [ ] **1.4. Data Collection for Gamification and Boss Details:**
  - [ ] 1.4.1. For each boss from the spreadsheet, collect:
    - Short description / lore background.
    - Known weaknesses (damage types, status effects).
    - Rewards for defeat (runes, key items).
    - In-game area where it is located.
    - Prepare a placeholder or identifier for future image.
  - [ ] 1.4.2. Design the structure and conditions for achievements (e.g., "Lord of Limgrave: Defeat all main bosses in Limgrave", "Dragon Hunter: Defeat X dragons").
  - [ ] 1.4.3. Sources: Game wikis, databases, personal game knowledge.
- [ ] **1.5. Finalizing Technology and Library Choices:**
  - [ ] 1.5.1. Python.
  - [ ] 1.5.2. Parsing: `struct`, consider `Kaitai Struct`.
  - [ ] 1.5.3. Monitoring: `watchdog` + debouncing.
  - [ ] 1.5.4. GUI: PySide6 / PyQt6.

---

## PHASE 2: SYSTEM DESIGN ⚙️

- [ ] **2.1. Application Architecture Design:**
  - [ ] 2.1.1. Modules: `FileMonitor`, `SaveParser`, `DataManager`, `UserInterface` (GUI).
  - [ ] 2.1.2. Data flow.
  - [ ] 2.1.3. Use of threads (QThread).
  - [ ] 2.1.4. Inter-thread communication (signals and slots).
  - [ ] 2.1.5. Logging system.
  - [ ] 2.1.6. Error handling.
- [ ] **2.2. Data Structures Design (Extended):**
  - [ ] 2.2.1. `Boss` object/class:
    - `name` (str)
    - `internal_id` (str/int - Event Flag ID)
    - `is_defeated` (bool)
    - `description` (str)
    - `weaknesses` (list/str)
    - `rewards` (list/str)
    - `area` (str - name of in-game area)
    - `image_placeholder_id` (str - for future image loading)
  - [ ] 2.2.2. `GameArea` object/class:
    - `name` (str)
    - `list_of_boss_ids` (list of `internal_id`s of bosses in this area)
    - `completion_progress` (float - 0.0 to 1.0)
    - `achievement_status_area` (e.g., number of stars)
  - [ ] 2.2.3. `Achievement` object/class:
    - `id` (str)
    - `name` (str)
    - `description` (str)
    - `icon_placeholder_id` (str)
    - `conditions_to_unlock` (rule definitions)
    - `current_progress` (int/float)
    - `max_progress` (int/float)
    - `is_unlocked` (bool)
  - [ ] 2.2.4. `Profile` object/class:
    - `profile_index` (int)
    - `profile_name` (str, optional)
    - `boss_statuses` (dict: `boss_internal_id` -> `is_defeated`)
    - `area_progress` (dict: `area_name` -> `GameArea` object/status)
    - `unlocked_achievements` (list of `Achievement` ids or `Achievement` objects)
  - [ ] 2.2.5. Local storage structure (JSON): Must reflect new data structures, storing progress in achievements and areas as well.
- [ ] **2.3. User Interface (GUI) Design (Extended):**
  - [ ] 2.3.1. Create wireframes/mockups for all new and modified views.
  - [ ] 2.3.2. **Main Window:**
    - [ ] Navigation panel (e.g., tabs or side menu) for switching between "Boss Progress" and "Achievements".
    - [ ] Element for setting/displaying the path to ER0000.sl2.
    - [ ] Dropdown/list for selecting game profile.
    - [ ] **"Boss Progress" View:**
      - [ ] Expandable sections for each `GameArea` (Limgrave, Liurnia, etc.).
      - [ ] In each section, a list of bosses with a checkbox (or other defeat indicator).
      - [ ] Progress bar for each `GameArea` showing the percentage of defeated bosses.
    - [ ] **"Achievements" View:**
      - [ ] List of achievements, each with an icon (placeholder), name, description, progress bar, and completion indicator (e.g., stars, color).
    - [ ] Status bar.
  - [ ] 2.3.3. **"Boss Detail" Dialog:**
    - [ ] Appears when clicking on a boss's name.
    - [ ] Contains: Name, large image placeholder, description, weaknesses, rewards.
  - [ ] 2.3.4. Design of a data model (subclass of `QAbstractTableModel` or `QAbstractListModel`) for `QTableView`/`QListView` used for displaying bosses and achievements.
  - [ ] 2.3.5. Consider visual style and theming to achieve a "fun to use" feel (icons, colors, fonts).

---

## PHASE 3: DEVELOPMENT 👨‍💻

- [ ] **3.1. Implement FileMonitor Module:**
  - (Tasks remain the same as in the previous document version)
- [ ] **3.2. Implement SaveParser Module:**
  - (Tasks remain the same as in the previous document version)
- [ ] **3.3. Implement DataManager Module (Extended):**
  - [ ] 3.3.1. Load boss definitions **INCLUDING their details** (description, weaknesses, rewards, area) and achievement definitions from external files.
  - [ ] 3.3.2. Manage extended data structures (`GameArea`, `Achievement`, `Profile` with new fields).
  - [ ] 3.3.3. Calculate progress in areas and achievements based on boss statuses.
  - [ ] 3.3.4. Implement saving/loading extended data to/from a local JSON file.
  - [ ] 3.3.5. API for GUI to retrieve all necessary data for new views.
- [ ] **3.4. Implement UserInterface (GUI) Module (Extended):**
  - [ ] 3.4.1. Create the main window with navigation elements and new views ("Boss Progress" with expandable sections and progress bars, "Achievements" with progress bars and stars).
  - [ ] 3.4.2. Implement the "Boss Detail" dialog.
  - [ ] 3.4.3. Implement custom models for `QTableView`/`QListView` to display bosses in areas and the achievement list.
  - [ ] 3.4.4. Connect the GUI with DataManager for displaying and dynamically updating all gamified elements.
  - [ ] 3.4.5. Apply visual style for a "fun to use" experience.
- [ ] **3.5. Module Integration:**
  - (Task remains the same as in the previous document version)

---

## PHASE 4: TESTING 🧪

- [ ] **4.1. Unit Tests:**
  - (Extend as needed for new data structures and logic)
- [ ] **4.2. Integration Tests:**
  - (Task remains the same as in the previous document version)
- [ ] **4.3. User Acceptance Testing (UAT) (Extended):**
  - [ ] 4.3.1. Testing with real save files.
  - [ ] 4.3.2. Verification of correct boss detection and associated progress in areas and achievements.
  - [ ] 4.3.3. Testing all new GUI elements (expandable sections, dialogs, progress bars, achievement panel).
  - [ ] 4.3.4. Assessment of overall usability, clarity, and "fun" of the interface.
- [ ] **4.4. Performance Testing:**
  - (Task remains the same as in the previous document version)
- [ ] **4.5. Compatibility Testing:**
  - (Task remains the same as in the previous document version)

---

## PHASE 5: DEPLOYMENT AND PACKAGING 📦

- [ ] **5.1. Preparation for Packaging:**
  - (Tasks remain the same as in the previous document version)
- [ ] **5.2. .exe File Creation:**
  - (Tasks remain the same as in the previous document version)
- [ ] **5.3. Installer Creation:**
  - (Tasks remain the same as in the previous document version)
- [ ] **5.4. Documentation Preparation:**
  - (Tasks remain the same as in the previous document version)

---

## PHASE 6: MAINTENANCE AND FUTURE DEVELOPMENT 🛠️

- [ ] **6.1. Maintenance Plan:**
  - (Tasks remain the same as in the previous document version)
- [ ] **6.2. List of Possible Future Enhancements (Backlog) (Extended):**
  - [ ] Support for .co2 save files.
  - [ ] Implementation of actual boss images and achievement icons (instead of placeholders).
  - [ ] More advanced player statistics (if parseable from save or derivable).
  - [ ] Option to share progress / achievements.
  - [ ] Themed application skins.
  - [ ] Adding sound effects for gamification.
