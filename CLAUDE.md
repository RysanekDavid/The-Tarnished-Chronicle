# The Tarnished's Chronicle

## Stack

- Python 3.8+ desktop application using PySide6
- Rust save-file parser exposed through `flag_extractor_cli`
- PyInstaller and NSIS for Windows packaging
- `unittest` test suite

## Commands

| Task | Command |
|------|---------|
| Dev app | `python -m src.main` |
| Build Rust parser | `cargo build --release --manifest-path flag_extractor_cli/Cargo.toml` |
| Build app | `pyinstaller build.spec` |
| Build installer | `powershell -ExecutionPolicy Bypass -File build_installer.ps1` |
| Test | `python tests/run_all_tests.py` |
| Test (stdlib) | `python -m unittest discover tests` |
| Rust lint | `cargo clippy --manifest-path flag_extractor_cli/Cargo.toml --all-targets --all-features -- -D warnings` |
| Rust format | `cargo fmt --manifest-path flag_extractor_cli/Cargo.toml --check` |

## Architecture

- `src/main.py` creates the Qt application and main window.
- `src/ui/` contains widgets, dialogs, layouts, and overlay/OBS managers.
- `src/app_logic.py` coordinates UI actions, save selection, monitoring, and updates.
- `src/services/` contains save polling, Rust CLI integration, asset downloads, and update checks.
- `src/domain/` owns boss data, statistics, and timestamps.
- `src/config/` contains version, URL, monitoring, and display constants.
- `flag_extractor_cli/` is the Rust executable that parses `.sl2` and `.co2` saves.
- `er_save_lib_source/` is a vendored fork of ClayAmore/ER-Save-Lib (upstream commit `fbe5a4c`, no upstream license) with local fast-path and regulation-skip changes. Its `test/` sample saves are gitignored.
- `data/` and `assets/` contain boss metadata and bundled UI resources.
- `tests/` contains Python unit and integration tests.

## Conventions

- Keep UI code in `src/ui/`, orchestration in `src/app_logic.py`, and external operations in `src/services/`.
- Surface parse, network, and filesystem failures explicitly.
- Preserve support for both vanilla `.sl2` and Seamless Coop `.co2` saves.
- Keep save parsing off the GUI thread.
- Add or update tests for behavioral changes.

## Do NOT

- Do not edit generated `resources_rc.py`; regenerate it from `resources.qrc`.
- Do not commit build artifacts, installers, save files, or virtual environments.
- Do not make the core save-monitoring path depend on network access.
- Do not use `.unwrap()` in non-test Rust code or `any` in typed code.

## Stav projektu

### Hotové milníky
- v1.0.8: interaktivní overlay (F8/F9), výkon, filtry bossů.

### Rozpracované: v1.0.9 hotfix (větev `fix/v1.0.9`)
- #11: regulation blok (`USER_DATA011`) se přeskakuje podle velikosti BND4 entry, ne podle vnitřní hlavičky (1.17.x savy mají v hlavičce nesmyslnou velikost).
- Chybový dialog ukazuje skutečnou chybu z readeru místo „pirated/wrong folder“; prázdný save hlásí chybu.
- #13 / #8: řádky v `LocationSectionWidget` se párují s daty podle indexu (duplicitní jména bossů v Liurnii, Altus, Jagged Peak).
- F8 overlay respektuje „Hide Defeated Bosses“.
- Rust CLI a fork knihovny jsou nově v gitu (dřív gitignored).
- Manifest `update_test/latest.json` se mění až po vydání releasu.

### Na později (v1.0.10)
- Timestamps: od v1.0.1 se nenapojují do řádků (`char_timestamps` v `app_logic.py` se nepoužívá); klíč je event ID.
- #12: last boss v overlayi bez času.
- File dialog: `*.err` (Reforged), `*.cnv` (Convergence), All files.
- Logging do souboru + „Export diagnostics“ (Rust `diagnose` subcommand).
- `get_boss_name_by_id` vrací truthy „Unknown Boss“.

### Otevřená rozhodnutí / známé problémy
- B: staré testy v `tests/` (untracked) padají na mockách a `sys.exit` v updateru; nové regresní testy jsou v `tests/test_hide_defeated_regressions.py`.
- er-save-lib nemá upstream licenci; zvážit dotaz u ClayAmore.
- Vendorovaný fork neprojde `cargo clippy --manifest-path er_save_lib_source/Cargo.toml -- -D warnings` (5 errorů, ~54 warningů, `.unwrap()` v `regulation.rs`); lint gate je zatím jen CLI crate.
- `user_data_11.rs`: známá verze regulation, která selže při parsování, se při zápisu ztratí (appka saves nezapisuje).
- `user_data_10.rs`: neparsovatelný profile summary tiše spadne na „žádné postavy“ (exit 0, `[]`); appka pak ukáže jen „No Characters Found“.
- #11 ověřeno jen na syntetických savech (garbage `size` v hlavičce `USER_DATA011` dává identické `NeedSize` chyby); potvrdit u reportera na pre-release buildu.
- Reforged/Convergence bossové mají nezdokumentované event flagy.
