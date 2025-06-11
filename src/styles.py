from PySide6.QtGui import QColor

STYLE_SHEET = """
/* === GLOBÁLNÍ NASTAVENÍ === */
QWidget {
    background-color: #242933;
    color: #E5E9F0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

/* ZMĚNA: Přidáno pravidlo pro focus, aby se nekreslil ošklivý rámeček */
QWidget:focus {
    outline: none;
}

/* === LEVÝ SIDEBAR === */
QFrame#sidebar {
    background-color: #2E3440;
    border-right: 1px solid #4C566A;
}

/* === HLAVNÍ OBSAH === */
QWidget#mainContent {
    background-color: #242933;
    border: none;
}

/* === TLAČÍTKA === */
QPushButton {
    background-color: #4C566A;
    color: #ECEFF4;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5E81AC;
}
QPushButton:pressed {
    background-color: #81A1C1;
}

/* === VSTUPNÍ POLE A COMBOBOX === */
QLineEdit, QComboBox {
    background-color: #3B4252;
    border: 1px solid #4C566A;
    padding: 6px;
    border-radius: 5px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #88C0D0;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

/* === KARTA LOKACE (LocationSectionWidget) === */
QFrame#locationCard {
    background-color: #2E3440;
    border-radius: 8px;
    border: 1px solid #434C5E;
    margin: 0px 0px 8px 0px;
}

/* Hlavička karty */
#locationCard > QWidget {
    background-color: #3B4252;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    border-bottom-left-radius: 7px;
    border-bottom-right-radius: 7px;
}
/* Hlavička karty, když je rozbalená */
#locationCard > QWidget[expanded="true"] {
    background-color: #434C5E;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    border-bottom: 1px solid #4C566A;
}

/* ZMĚNA: Ujistíme se, že QLabel v hlavičce nemá žádné pozadí ani ohraničení */
#locationCard QLabel {
    background-color: transparent;
    border: none; /* Toto explicitně odstraní nechtěné čáry */
}

#locationCard #location_name_label {
    font-weight: bold;
    font-size: 12pt;
    color: #ECEFF4;
}
#locationCard QLabel#locationIcon {
    border-image: url(assets/icons/map.svg);
    background-color: transparent;
    border: none;
}

/* === TABULKA BOSSŮ === */
QTableWidget {
    background-color: #2E3440;
    border: none;
    gridline-color: #434C5E;
    border-bottom-left-radius: 7px;
    border-bottom-right-radius: 7px;
}

/* Hlavička tabulky */
QHeaderView::section {
    background-color: #3B4252;
    color: #D8DEE9;
    padding: 5px;
    /* UPRAVENO: Přidáme spodní linku, která opticky oddělí hlavičku od prvního řádku. */
    border: none;
    border-bottom: 1px solid #434C5E; /* PŘIDANÁ LINKA */
    font-weight: bold;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #434C5E;
}

/* === VLASTNÍ WIDGETY V TABULCE === */

/* === SCROLLBAR === */
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    border: none;
    background: #2E3440;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #4C566A;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* === SCROLL AREA A JEJÍ OBSAH === */
QScrollArea#mainBossScrollArea {
    border: none;
    background-color: transparent;
}

QWidget#locationsContainer {
    background-color: transparent;
}

/* === TLAČÍTKO PRO ROZBALENÍ KARTY === */
QPushButton#expandButton {
    background-color: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}
QPushButton#expandButton:hover {
    background-color: #4C566A;
    border-radius: 4px;
}

/* === VYLEPŠENÝ CHECKBOX === */
/* Cílíme POUZE na checkboxy uvnitř našich karet */
#locationCard QCheckBox {
    spacing: 0px; /* Žádné místo mezi indikátorem a textem (text nemáme) */
    background-color: transparent; /* KLÍČOVÁ ZMĚNA: zprůhledníme pozadí kontejneru */
    border: none;                  /* Pro jistotu odstraníme i okraj */
}

/* Pro konzistenci přidáme i hover efekt, stejně jako u šipky */
#locationCard QCheckBox:hover {
    background-color: #4C566A;
    border-radius: 4px;
}

/* Styly pro samotný obrázek (indikátor) zůstávají stejné */
#locationCard QCheckBox::indicator {
    width: 20px;  /* Můžete si pohrát s velikostí obrázku */
    height: 20px;
}
#locationCard QCheckBox::indicator:unchecked {
    image: url(assets/icons/square.svg); /* Vidím, že používáš square, což je super! */
}
#locationCard QCheckBox::indicator:checked {
    image: url(assets/icons/check-square.svg);
}
/* QCheckBox::indicator:disabled {} - Ponecháno pro případné budoucí úpravy, pokud by bylo potřeba */
/* === STYLY PRO SIDEBAR === */

/* Oprava pozadí pro všechny QLabel v sidebaru, aby nebyly tmavé */
QFrame#sidebar QLabel {
    background-color: transparent;
}

/* Styl pro nové nadpisy s ikonou */
QLabel#sidebarHeader {
    font-size: 13pt;
    font-weight: bold;
    color: #ECEFF4;
}

/* Styl pro zobrazení cesty k souboru */
QLabel#filePathLabel {
    background-color: #242933; /* Tmavší pozadí */
    border: 1px solid #434C5E;
    border-radius: 5px;
    padding: 8px;
    font-size: 9pt;
    color: #8899A6; /* Šedivější text */
}

/* Styl pro nové "Browse" tlačítko */
QPushButton#browseButton {
    background-color: #3B4252;
    text-align: center;
}
QPushButton#browseButton:hover {
    background-color: #4C566A;
}
/* === PATIČKA (FOOTER) === */
QFrame#footer {
    background-color: #2E3440;
    border-top: 1px solid #4C566A;
}

#footer QLabel {
    background-color: transparent;
    font-size: 9pt;
    color: #D8DEE9;
}

/* === UPRAVENÉ STYLY PRO NADPISY FÁZÍ HRY === */

/* Obecný styl, který platí pro VŠECHNY nadpisy fází */
QLabel#gamePhaseHeader {
    font-size: 10pt;
    font-weight: bold;
    text-transform: uppercase;
    padding-top: 15px;
    padding-bottom: 8px;
    margin: 0px 5px 10px 5px;
    border-bottom: 1px solid #434C5E;
}

/* Specifická pravidla pro barvy na základě vlastnosti 'phase' */
QLabel#gamePhaseHeader[phase="early"] {
    color: rgb(78, 122, 81); /* Zelená */
}
QLabel#gamePhaseHeader[phase="mid"] {
    color: rgb(183, 178, 87); /* Žlutá */
}
QLabel#gamePhaseHeader[phase="late"] {
    color: rgb(110, 23, 23); /* Red */
}
/* --- ADDED RULE --- */
QLabel#gamePhaseHeader[phase="dlc"] {
    color: rgb(136, 99, 187); /* A nice purple for DLC */
}
/* --- END ADDED RULE --- */
/* === NOVÝ STYL PRO VERZI V PATIČCE === */
#footer QLabel#versionLabel {
    color: #616E88; /* Tlumená, méně výrazná barva */
    font-weight: bold;
}

/* === STYL PRO INFORMAČNÍ TLAČÍTKA === */
QPushButton#infoButton {
    background-color: #434C5E; /* Tmavší, decentní pozadí */
    color: #D8DEE9;            /* Světlý text */
    border: 1px solid #4C566A; /* Jemný okraj */
    padding: 5px 12px;         /* Menší padding než hlavní tlačítka */
    font-weight: normal;       /* Normální tloušťka písma */
    text-align: left;          /* Zarovná ikonu a text doleva uvnitř tlačítka */
    max-width: 220px;          /* Omezí šířku, aby se neroztahovalo */
    border-radius: 5px;
}
QPushButton#infoButton:hover {
    background-color: #5E81AC; /* Zvýraznění při najetí myší */
    color: #ECEFF4;
    border-color: #6a8ab1;
}

/* === STYL PRO ODDĚLOVACÍ LINKU === */
QFrame#separatorLine {
    border: 1px solid #434C5E;
}

/* Styl pro GroupBoxy v panelech nastavení */
QGroupBox {
    font-weight: bold;
    color: #ECEFF4;
    border: 1px solid #434C5E;
    border-radius: 5px;
    margin-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px 5px 5px;
    background-color: #2E3440; /* Barva pozadí panelu */
}
/* === STYLY PRO PATIČKU (OBNOVENO) === */
QFrame#footer {
    background-color: #2E3440;
    border-top: 1px solid #4C566A;
}
#footer QLabel {
    background-color: transparent;
    font-size: 9pt;
    color: #D8DEE9;
}
QLabel#monitoringStatus {
    font-weight: bold;
}
QLabel#monitoringStatus[active="false"] {
    color: #EBCB8B; /* Žlutá pro neaktivní */
}
QLabel#monitoringStatus[active="true"] {
    color: #A3BE8C; /* Zelená pro aktivní */
}
#footer QLabel#versionLabel {
    color: #616E88;
    font-weight: bold;
}
"""

def apply_app_styles(app_widget):
    app_widget.setStyleSheet(STYLE_SHEET)

# Define colors for tree items (can be imported by gui.py)
DEFEATED_TEXT_COLOR = QColor("#98C379")  # Greenish
NOT_DEFEATED_TEXT_COLOR = QColor("#E06C75") # Reddish
LOCATION_TEXT_COLOR = QColor("#D8DEE9") # Default light text
BOSS_NAME_TEXT_COLOR = QColor("#D8DEE9")

LOCATION_ITEM_BG_COLOR = QColor("#3B4252") # Slightly lighter than tree background
BOSS_ITEM_BG_COLOR = QColor("#2E3440") # Same as tree background or slightly different