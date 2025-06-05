# PROJECT KICKOFF: Elden Ring Boss Tracker – "The Tarnished's Chronicle"

**Datum Kickoffu:** 29. května 2025
**Verze Dokumentu:** 1.1
**Motto Projektu:** Každý poražený boss je kapitolou tvé legendy. Zaznamenej je všechny!

---

## Část 1: ÚVOD A PŘEDSTAVENÍ APLIKACE

### Představení Aplikace ("The Tarnished's Chronicle"):

"The Tarnished's Chronicle" je desktopová aplikace pro Windows navržená pro fanoušky hry Elden Ring, kteří chtějí detailně sledovat svůj postup hrou, zejména co se týče poražených bossů. Aplikace nebude pouhým statickým seznamem; jejím cílem je nabídnout **interaktivní a vizuálně poutavý zážitek**, který hráče vtáhne a motivuje k prozkoumávání Lands Between a překonávání jejích výzev. Uživatelé budou moci sledovat svůj pokrok v reálném čase (nebo téměř v reálném čase) díky monitorování save souboru, vidět, které bossy v jednotlivých oblastech již porazili, odemykat achievementy za dosažené milníky a prozkoumávat detaily o jednotlivých protivnících. Celé rozhraní bude navrženo s důrazem na **"gamifikaci" a uživatelskou přívětivost**, aby používání aplikace bylo zábavné a uspokojující.

### Cíl Projektu:

Vytvořit robustní a uživatelsky přívětivou desktopovou aplikaci, která:

- **Automaticky monitoruje save file** hry Elden Ring.
- **Přesně detekuje a parsuje** status poražených bossů.
- **Zobrazuje postup hráče** v interaktivním a gamifikovaném uživatelském rozhraní.
- Nabízí **detailní informace o bossech** a sleduje achievementy.
- Poskytuje **"téměř real-time" aktualizace** na základě změn v save souboru.

### Klíčové Funkce (Rozšířené):

- **Automatické monitorování save filu Elden Ringu** (ER0000.sl2 a potenciálně .co2 pro Seamless Coop).
- **Parsování relevantních částí save filu** pro získání statusu jednotlivých bossů.
- **Gamifikované Uživatelské Rozhraní (GUI):**
  - **Rozbalovací Sekce Podle Mapy:** Bossy seskupené podle herních oblastí (Limgrave, Caelid, atd.) s checkboxy a vizuálními progress indikátory pro každou oblast.
  - **Panel s Achievementy:** Za poražení všech bossů v oblasti, specifických skupin bossů, nebo dosažení jiných milníků. Zobrazení s progress bary a odměnami (např. hvězdičky, virtuální trofeje).
  - **Detail Bossu při Kliknutí:** Dialogové okno s detailními informacemi o bossovi (popis, příběhové pozadí, známé slabiny, odměny za poražení, placeholder pro obrázek/artwork).
- **Možnost výběru/správy herních profilů** (postav).
- **Ukládání a načítání** zjištěných statusů bossů a achievementů per profil lokálně.
- **Distribuce jako .exe instalační soubor.**

---

## Část 2: TECHNICKÉ SPECIFIKACE A ZDROJE

### Hlavní Technologie:

- **Jazyk:** Python
- **GUI:** PySide6 (preferováno kvůli LGPL licenci) nebo PyQt6
- **Monitorování Souborů:** watchdog
- **Parsování Binárních Dat:** Modul struct, potenciálně Kaitai Struct
- **Ukládání Dat Aplikace:** JSON soubory

### Zdroje Informací:

- **Seznam Bossů a ID Flagů:** Uživatelský spreadsheet bossů (již poskytnut); komunitní zdroje (Google Spreadsheet 1Nn-d4_mzEtGUSQXscCkQ41AhtqO_wF2Aw3yoTBdW9lk, Hexinton's Cheat Engine Table, soarqin/EROverlay, SoulsModding Wiki, Elden Ring Compass, ClayAmore/ER-Save-Lib).
- **Detaily Bossů (Popis, Slabiny, Odměny, Obrázky):** Herní wikiny (Fextralife, IGN, atd.), komunitní databáze. Tyto informace nebudou parsovány ze save filu, ale budou součástí dat aplikace.

---

## Část 3: ŘÍZENÍ PROJEKTU A DOKUMENTACE

### Sledování Postupu:

- Tento dokument slouží jako hlavní TO-DO list. Každý úkol bude po dokončení označen jako splněný (např. zaškrtnutím `[x]`).
- Postup bude pravidelně revidován.

### Správa Změn (CHANGELOG.md):

- Všechny významné změny v kódu, funkcionalitě, nebo struktuře projektu musí být zaznamenány v souboru `CHANGELOG.md` v kořenovém adresáři projektu.
- **Formát Záznamu v CHANGELOG.md:**

  ```markdown
  ## [Verze Aplikace] - RRRR-MM-DD

  ### Added (Přidáno)

  - Popis nové funkce nebo vylepšení.

  ### Changed (Změněno)

  - Popis změny v existující funkcionalitě.

  ### Fixed (Opraveno)

  - Popis opravy chyby.

  ### Removed (Odebráno)

  - Popis odebrané funkce.
  ```

- Zodpovědnost za udržování `CHANGELOG.md` leží na každém, kdo provádí změny.

---

## FÁZE 1: ANALÝZA A VÝZKUM (Nejvyšší priorita, největší nejistota) 🔬

- [ ] **1.1. Zmapování Formátu Save Souboru ER0000.sl2 (a .co2):**
  - [ ] 1.1.1. Shromáždit a analyzovat save fily.
  - [ ] 1.1.2. Prozkoumat základní strukturu (hex editory).
  - [ ] 1.1.3. Analyzovat implementaci MD5 checksumů.
  - [ ] 1.1.4. Zvážit podporu pro .co2 save fily.
- [ ] **1.2. Identifikace a Způsob Uložení Flagů Poražených Bossů:**
  - [ ] 1.2.1. Analyzovat komunitní zdroje pro ID event flagů bossů.
  - [ ] 1.2.2. Porozumět mechanismu uložení event flagů (bitová pole, výpočty).
  - [ ] 1.2.3. Provádět cílené diffování save filů pro ověření.
- [ ] **1.3. Analýza Existujících Nástrojů (zejména ClayAmore/ER-Save-Lib):**
  - [ ] 1.3.1. Prostudovat zdrojový kód ER-Save-Lib.
  - [ ] 1.3.2. Zhodnotit přenositelnost logiky do Pythonu.
  - [ ] 1.3.3. Prozkoumat další relevantní parsery/editory.
- [ ] **1.4. Sběr Dat pro Gamifikaci a Detaily Bossů:**
  - [ ] 1.4.1. Pro každého bosse ze spreadsheetu shromáždit:
    - Krátký popis / příběhové pozadí.
    - Známé slabiny (typy poškození, status efekty).
    - Odměny za poražení (runy, klíčové itemy).
    - Herní oblast, ve které se nachází.
    - Připravit placeholder nebo identifikátor pro budoucí obrázek.
  - [ ] 1.4.2. Navrhnout strukturu a podmínky pro achievementy (např. "Vládce Limgrave: Poraž všechny hlavní bossy v Limgrave", "Lovec Draků: Poraž X draků").
  - [ ] 1.4.3. Zdroje: Herní wikiny, databáze, vlastní znalost hry.
- [ ] **1.5. Finalizace Volby Technologií a Knihoven:**
  - [ ] 1.5.1. Python.
  - [ ] 1.5.2. Parsování: `struct`, zvážit `Kaitai Struct`.
  - [ ] 1.5.3. Monitorování: `watchdog` + debouncing.
  - [ ] 1.5.4. GUI: PySide6 / PyQt6.

---

## FÁZE 2: NÁVRH SYSTÉMU ⚙️

- [ ] **2.1. Návrh Architektury Aplikace:**
  - [ ] 2.1.1. Moduly: `FileMonitor`, `SaveParser`, `DataManager`, `UserInterface` (GUI).
  - [ ] 2.1.2. Tok dat.
  - [ ] 2.1.3. Využití vláken (QThread).
  - [ ] 2.1.4. Komunikace mezi vlákny (signály a sloty).
  - [ ] 2.1.5. Systém logování.
  - [ ] 2.1.6. Zpracování chyb.
- [ ] **2.2. Návrh Datových Struktur (Rozšířený):**
  - [ ] 2.2.1. Objekt/třída **`Boss`**:
    - `name` (str)
    - `internal_id` (str/int - Event Flag ID)
    - `is_defeated` (bool)
    - `description` (str)
    - `weaknesses` (list/str)
    - `rewards` (list/str)
    - `area` (str - název herní oblasti)
    - `image_placeholder_id` (str - pro budoucí načtení obrázku)
  - [ ] 2.2.2. Objekt/třída **`GameArea`**:
    - `name` (str)
    - `list_of_boss_ids` (list `internal_id` bossů v této oblasti)
    - `completion_progress` (float - 0.0 až 1.0)
    - `achievement_status_area` (např. počet hvězdiček)
  - [ ] 2.2.3. Objekt/třída **`Achievement`**:
    - `id` (str)
    - `name` (str)
    - `description` (str)
    - `icon_placeholder_id` (str)
    - `conditions_to_unlock` (definice pravidel)
    - `current_progress` (int/float)
    - `max_progress` (int/float)
    - `is_unlocked` (bool)
  - [ ] 2.2.4. Objekt/třída **`Profile`**:
    - `profile_index` (int)
    - `profile_name` (str, volitelné)
    - `boss_statuses` (dict: `internal_id_bosse` -> `is_defeated`)
    - `area_progress` (dict: `area_name` -> `GameArea` object/status)
    - `unlocked_achievements` (list `Achievement` id nebo `Achievement` objects)
  - [ ] 2.2.5. Struktura lokálního úložiště (JSON): Musí reflektovat nové datové struktury, ukládat i postup v achievementsech a oblastech.
- [ ] **2.3. Návrh Uživatelského Rozhraní (GUI) (Rozšířený):**
  - [ ] 2.3.1. Vytvořit wireframy/mockupy pro všechny nové a upravené pohledy.
  - [ ] 2.3.2. **Hlavní okno:**
    - [ ] Navigační panel (např. záložky nebo boční menu) pro přepínání mezi "Postupem Bossů" a "Achievementy".
    - [ ] Prvek pro nastavení/zobrazení cesty k ER0000.sl2.
    - [ ] Dropdown/seznam pro výběr herního profilu.
    - [ ] **Pohled "Postup Bossů":**
      - [ ] Rozbalovací sekce pro každou `GameArea` (Limgrave, Liurnia, atd.).
      - [ ] V každé sekci seznam bossů s checkboxem (nebo jiným indikátorem poražení).
      - [ ] Progress bar pro každou `GameArea` ukazující procento poražených bossů.
    - [ ] **Pohled "Achievementy":**
      - [ ] Seznam achievementů, každý s ikonou (placeholder), názvem, popisem, progress barem a indikací splnění (např. hvězdičky, barva).
    - [ ] Stavový řádek.
  - [ ] 2.3.3. **Dialog "Detail Bossu":**
    - [ ] Zobrazí se po kliknutí na jméno bosse.
    - [ ] Obsahuje: Jméno, velký placeholder pro obrázek, popis, slabiny, odměny.
  - [ ] 2.3.4. Návrh datového modelu (podtřída `QAbstractTableModel` nebo `QAbstractListModel`) pro `QTableView`/`QListView` používané pro zobrazení bossů a achievementů.
  - [ ] 2.3.5. Zvážit vizuální styl a témování pro dosažení "fun to use" pocitu (ikony, barvy, fonty).

---

## FÁZE 3: VÝVOJ 👨‍💻

- [ ] **3.1. Implementace FileMonitor Modulu:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)
- [ ] **3.2. Implementace SaveParser Modulu:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)
- [ ] **3.3. Implementace DataManager Modulu (Rozšířený):**
  - [ ] 3.3.1. Načtení definice bossů **VČETNĚ jejich detailů** (popis, slabiny, odměny, oblast) a definic achievementů z externích souborů.
  - [ ] 3.3.2. Správa rozšířených datových struktur (`GameArea`, `Achievement`, `Profile` s novými poli).
  - [ ] 3.3.3. Výpočet postupu v oblastech a achievementsech na základě statusů bossů.
  - [ ] 3.3.4. Implementace ukládání/načítání rozšířených dat do/z lokálního JSON souboru.
  - [ ] 3.3.5. API pro GUI k získání všech potřebných dat pro nové pohledy.
- [ ] **3.4. Implementace UserInterface (GUI) Modulu (Rozšířený):**
  - [ ] 3.4.1. Vytvořit hlavní okno s navigačními prvky a novými pohledy ("Postup Bossů" s rozbalovacími sekcemi a progress bary, "Achievementy" s progress bary a hvězdičkami).
  - [ ] 3.4.2. Implementovat dialog "Detail Bossu".
  - [ ] 3.4.3. Implementovat vlastní modely pro `QTableView`/`QListView` pro zobrazení bossů v oblastech a seznamu achievementů.
  - [ ] 3.4.4. Propojit GUI s DataManager pro zobrazení a dynamickou aktualizaci všech gamifikovaných prvků.
  - [ ] 3.4.5. Aplikovat vizuální styl pro "fun to use" zážitek.
- [ ] **3.5. Integrace Modulů:**
  - (Úkol zůstává stejný jako v předchozí verzi dokumentu)

---

## FÁZE 4: TESTOVÁNÍ 🧪

- [ ] **4.1. Jednotkové Testy:**
  - (Rozšířit dle potřeby pro nové datové struktury a logiku)
- [ ] **4.2. Integrační Testy:**
  - (Úkol zůstává stejný jako v předchozí verzi dokumentu)
- [ ] **4.3. Uživatelské Testování (UAT) (Rozšířené):**
  - [ ] 4.3.1. Testování s reálnými save fily.
  - [ ] 4.3.2. Ověření správnosti detekce bossů a navázaného postupu v oblastech a achievementsech.
  - [ ] 4.3.3. Testování všech nových GUI prvků (rozbalovací sekce, dialogy, progress bary, achievement panel).
  - [ ] 4.3.4. Posouzení celkové použitelnosti, přehlednosti a "zábavnosti" rozhraní.
- [ ] **4.4. Výkonnostní Testování:**
  - (Úkol zůstává stejný jako v předchozí verzi dokumentu)
- [ ] **4.5. Testování Kompatibility:**
  - (Úkol zůstává stejný jako v předchozí verzi dokumentu)

---

## FÁZE 5: NASAZENÍ A BALENÍ 📦

- [ ] **5.1. Příprava pro Balení:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)
- [ ] **5.2. Vytvoření .exe Souboru:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)
- [ ] **5.3. Vytvoření Instalátoru:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)
- [ ] **5.4. Příprava Dokumentace:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)

---

## FÁZE 6: ÚDRŽBA A BUDOUCÍ ROZVOJ 🛠️

- [ ] **6.1. Plán Údržby:**
  - (Úkoly zůstávají stejné jako v předchozí verzi dokumentu)
- [ ] **6.2. Seznam Možných Budoucích Vylepšení (Backlog) (Rozšířený):**
  - [ ] Podpora pro .co2 save fily.
  - [ ] Implementace skutečných obrázků bossů a ikon achievementů (místo placeholderů).
  - [ ] Pokročilejší statistiky hráče (pokud parsovatelné ze savu nebo odvoditelné).
  - [ ] Možnost sdílení postupu / achievementů.
  - [ ] Tematické vzhledy aplikace.
  - [ ] Přidání zvukových efektů pro gamifikaci.
