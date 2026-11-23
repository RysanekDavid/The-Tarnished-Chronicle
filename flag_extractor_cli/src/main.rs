// flag_extractor_cli/src/main.rs

use clap::{Parser, Subcommand};
use er_save_lib::SaveApi;
use serde::Serialize;
use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[clap(author, version, about = "Elden Ring Save Utility CLI", long_about = None)]
struct Cli {
    #[clap(subcommand)]
    command: Commands,
}

// --- ZMĚNA: Přidán nový příkaz GetFullStatus a staré jsou odstraněny ---
#[derive(Subcommand, Debug)]
enum Commands {
    /// Lists all characters in a save file with their core stats.
    ListCharacters {
        #[clap(short, long, value_parser)]
        save_file_path: PathBuf,
    },
    /// Gets all relevant gameplay stats and event flags for a character in one go.
    GetFullStatus {
        #[clap(short, long, value_parser)]
        save_file_path: PathBuf,
        #[clap(short, long, value_parser = clap::value_parser!(u32))]
        slot_index: u32,
        /// A comma-separated list of all boss event IDs to check.
        #[clap(long, value_parser, use_value_delimiter = true, value_delimiter = ',')]
        event_ids: Vec<u32>,
    },
    /// Finds the event flag ID that changed from false to true between two save files.
    FindDiff {
        #[clap(long)]
        before_save: PathBuf,
        #[clap(long)]
        after_save: PathBuf,
        #[clap(long)]
        slot_index: u32,
        /// The starting ID for the event flag search range.
        #[clap(long, default_value_t = 100000000)]
        start_id: u32,
        /// The ending ID for the event flag search range.
        #[clap(long, default_value_t = 2600000000)]
        end_id: u32,
    },
}

// Struktury pro JSON výstup
#[derive(Serialize, Debug)]
struct CharacterInfo {
    slot_index: u32,
    character_name: String,
    character_level: u32,
    death_count: u32,
    seconds_played: u32,
}

#[derive(Serialize, Debug)]
struct StatsInfo {
    deaths: u32,
    seconds_played: u32,
}

#[derive(Serialize, Debug)]
struct FullStatus {
    stats: StatsInfo,
    boss_statuses: HashMap<String, bool>,
}

fn handle_list_characters(save_file_path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    // Listing never reads param data, so skip the regulation decrypt.
    let save_api = SaveApi::from_path_no_regulation(save_file_path)?;
    let mut characters_info: Vec<CharacterInfo> = Vec::new();

    // Get active character flags from ProfileSummary
    let active_chars = save_api.active_characters();

    for (slot_idx, &is_active) in active_chars.iter().enumerate() {
        // Skip inactive slots to avoid duplicates
        if !is_active {
            continue;
        }

        let character_name_str = save_api.character_name(slot_idx);
        if !character_name_str.is_empty() {
            characters_info.push(CharacterInfo {
                slot_index: slot_idx as u32,
                character_name: character_name_str,
                character_level: save_api.level(slot_idx),
                death_count: save_api.deaths(slot_idx),
                seconds_played: save_api.seconds_played(slot_idx),
            });
        }
    }

    println!("{}", serde_json::to_string_pretty(&characters_info)?);
    Ok(())
}

// --- ZDE JE NOVÁ VÝKONNÁ FUNKCE ---
fn handle_get_full_status(
    save_file_path: &PathBuf,
    slot_index: u32,
    event_ids: Vec<u32>,
) -> Result<(), Box<dyn std::error::Error>> {
    if slot_index >= 10 {
        eprintln!("Error: Slot index {} is out of bounds (0-9).", slot_index);
        std::process::exit(1);
    }

    // Fast read-only parse: only the requested slot + no regulation decrypt.
    let save_api = SaveApi::from_path_fast(save_file_path, slot_index as usize)?;

    // 1. Získání statistik
    let stats = StatsInfo {
        deaths: save_api.deaths(slot_index as usize),
        seconds_played: save_api.seconds_played(slot_index as usize),
    };

    // 2. Získání stavů bossů
    let mut boss_statuses = HashMap::new();
    for id in event_ids {
        let flag_state = save_api.get_event_flag(id, slot_index as usize)?;
        boss_statuses.insert(id.to_string(), flag_state);
    }

    // 3. Sestavení finálního JSONu
    let full_status = FullStatus {
        stats,
        boss_statuses,
    };

    println!("{}", serde_json::to_string(&full_status)?);
    Ok(())
}

fn handle_find_diff(
    before_save: &PathBuf,
    after_save: &PathBuf,
    slot_index: u32,
    start_id: u32,
    end_id: u32,
) -> Result<(), Box<dyn std::error::Error>> {
    let before_api = SaveApi::from_path(before_save)?;
    let after_api = SaveApi::from_path(after_save)?;

    println!(
        "Porovnávám event flagy v rozsahu od {} do {}...",
        start_id, end_id
    );
    let mut found_ids: Vec<u32> = Vec::new();

    for id in start_id..=end_id {
        // Zpracujeme výsledek, abychom ignorovali chyby (např. neexistující ID)
        if let (Ok(before_state), Ok(after_state)) = (
            before_api.get_event_flag(id, slot_index as usize),
            after_api.get_event_flag(id, slot_index as usize),
        ) {
            if !before_state && after_state {
                found_ids.push(id);
            }
        }
        // Pokud get_event_flag vrátí chybu, jednoduše pokračujeme na další ID
    }

    if !found_ids.is_empty() {
        println!("ÚSPĚCH: Nalezena následující ID se změnou z false na true:");
        for id in found_ids {
            println!("- {}", id);
        }
    } else {
        println!("CHYBA: V daném rozsahu nebylo nalezeno žádné ID se změnou z false na true.");
    }

    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.command {
        Commands::ListCharacters { save_file_path } => handle_list_characters(&save_file_path),
        Commands::GetFullStatus {
            save_file_path,
            slot_index,
            event_ids,
        } => handle_get_full_status(&save_file_path, slot_index, event_ids),
        Commands::FindDiff {
            before_save,
            after_save,
            slot_index,
            start_id,
            end_id,
        } => handle_find_diff(&before_save, &after_save, slot_index, start_id, end_id),
    }
}
