import os
import struct
import argparse
import sys

# Add the project root to sys.path to allow imports from src
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from src.process_event_flags import load_event_flag_map

# Constants based on ER-Save-Lib and provided information
FLAG_DIVISOR = 1000
# BLOCK_SIZE_FROM_RUST = 125 # This is number of u32 entries, so 125 * 4 = 500 bytes
# The rust code: mapped_offset_value * 125. This seems to be an index into a u32 array.
# Let's re-verify the calculation:
# base_byte_offset_for_block = mapped_offset_value * 125 (konstanta BLOCK_SIZE)
# This seems to imply that mapped_offset_value is an index into blocks of 125 u32s,
# so each block is 125 * 4 = 500 bytes.
# However, the user's initial description states:
# mapped_offset_value = event_flag_map.get(&block_id).
# base_byte_offset_for_block = mapped_offset_value * 125 (konstanta BLOCK_SIZE).
# This suggests BLOCK_SIZE is indeed 125, and it's used to multiply an offset value.
# If mapped_offset_value is a direct byte offset multiplier, then BLOCK_SIZE = 125 is correct.
# If mapped_offset_value is an index into some other structure, this needs clarification.
# The ER-Save-Lib code (event_flags.rs) has:
# letफल_offset = फल_map.get(&block_id).ok_or(Error::MalformedSaveFile)? * 0x7D; (0x7D is 125)
# This `फल_offset` is then used as `(फल_offset + फल_idx / 8) as usize`. This strongly suggests
# `फल_offset` is already a byte offset for the start of the block of 8000 flags (1000 bytes).
# So, `mapped_offset_value * 125` should be the direct byte offset.
# Let's stick to the user's provided algorithm for now.
BLOCK_MULTIPLIER = 125 # As per user's algorithm: mapped_offset_value * 125

# Save file structure constants from ER-Save-Lib
SAVE_FILE_HEADER_SIZE = 0x310
USER_DATA_SLOT_SIZE = 0x280090
EVENT_FLAGS_OFFSET_IN_SLOT = 0x10 # Offset of event_flags from the start of UserDataX
MAX_EVENT_FLAGS_SIZE = 0x1BF99F # Max size of the event_flags byte array

def get_event_flag_byte_offset(character_index: int,
                               event_id: int,
                               event_flag_map: dict[int, int]) -> tuple[int | None, int | None]:
    """
    Calculates the byte offset within the event_flags array and the bit index.
    Returns (None, None) if calculation fails (e.g., block_id not in map).
    """
    if not isinstance(event_id, int) or event_id < 0:
        print(f"Error: event_id must be a non-negative integer. Received: {event_id}")
        return None, None

    block_id = event_id // FLAG_DIVISOR
    index_in_block = event_id % FLAG_DIVISOR

    mapped_offset_value = event_flag_map.get(block_id)
    if mapped_offset_value is None:
        print(f"DEBUG: block_id {block_id} (derived from event_id {event_id}) not found in event_flag_map.")
        return None, None

    # base_byte_offset_for_block is the offset for the specific group of 1000 flags (125 bytes)
    # This seems to be the direct offset for the block of 1000 flags (which occupy 1000/8 = 125 bytes).
    base_byte_offset_for_block = mapped_offset_value * BLOCK_MULTIPLIER
    print(f"DEBUG: event_id={event_id}, block_id={block_id}, index_in_block={index_in_block}, mapped_offset_value={mapped_offset_value}, base_byte_offset_for_block={base_byte_offset_for_block}")
    
    # final_byte_offset_in_event_flags_array is the specific byte within that block
    final_byte_offset = base_byte_offset_for_block + (index_in_block // 8)
    
    bit_index_in_byte = 7 - (index_in_block % 8) # MSB is bit 7, LSB is bit 0
    print(f"DEBUG: final_byte_offset={final_byte_offset}, bit_index_in_byte={bit_index_in_byte}")

    if final_byte_offset >= MAX_EVENT_FLAGS_SIZE :
        print(f"Error: Calculated final_byte_offset ({final_byte_offset}) is out of bounds for event_flags array (max size: {MAX_EVENT_FLAGS_SIZE}).")
        print(f"  event_id: {event_id}, block_id: {block_id}, index_in_block: {index_in_block}, mapped_offset_value: {mapped_offset_value}")
        return None, None
        
    return final_byte_offset, bit_index_in_byte

def is_event_flag_set(save_file_path: str,
                        character_index: int,
                        event_id: int,
                        event_flag_map: dict[int, int]) -> bool | None:
    """
    Checks if a specific event flag is set in the Elden Ring save file.

    Args:
        save_file_path: Path to the ER0000.sl2 save file.
        character_index: The character slot index (0-9).
        event_id: The event ID to check.
        event_flag_map: The loaded map from eventflag_bst.txt.

    Returns:
        True if the flag is set, False if not set, None if an error occurs.
    """
    if not (0 <= character_index <= 9):
        print("Error: character_index must be between 0 and 9.")
        return None

    final_byte_offset_in_event_flags, bit_index_in_byte = get_event_flag_byte_offset(
        character_index, event_id, event_flag_map
    )

    if final_byte_offset_in_event_flags is None or bit_index_in_byte is None:
        return None # Error occurred in offset calculation

    # Calculate the absolute offset in the save file
    offset_of_character_slot_start = SAVE_FILE_HEADER_SIZE + (character_index * USER_DATA_SLOT_SIZE)
    offset_of_event_flags_block_start = offset_of_character_slot_start + EVENT_FLAGS_OFFSET_IN_SLOT
    absolute_byte_to_read_offset = offset_of_event_flags_block_start + final_byte_offset_in_event_flags

    try:
        with open(save_file_path, 'rb') as f:
            f.seek(absolute_byte_to_read_offset)
            event_flag_byte_data = f.read(1)
            if not event_flag_byte_data:
                print(f"Error: Could not read byte at offset {absolute_byte_to_read_offset}.")
                return None
            
            event_flag_byte = struct.unpack('B', event_flag_byte_data)[0]
            
            # Extract the bit
            is_set = ((event_flag_byte >> bit_index_in_byte) & 1) == 1
            return is_set
            
    except FileNotFoundError:
        print(f"Error: Save file not found at {save_file_path}")
        return None
    except IOError as e:
        print(f"Error reading save file: {e}")
        return None
    except struct.error as e:
        print(f"Error unpacking byte: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if an Elden Ring event flag is set.")
    parser.add_argument("save_file", help="Path to the ER0000.sl2 save file.")
    parser.add_argument("char_index", type=int, help="Character index (0-9).")
    parser.add_argument("event_id", type=int, help="The event ID to check.")
    parser.add_argument("--bst_file", help="Path to eventflag_bst.txt. Defaults to ../data/EventFlags/eventflag_bst.txt",
                        default=None)
    
    args = parser.parse_args()

    # Determine bst_file_path
    if args.bst_file:
        bst_file_path = args.bst_file
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        bst_file_path = os.path.join(project_root, "data", "EventFlags", "eventflag_bst.txt")

    if not os.path.exists(bst_file_path):
        print(f"Error: eventflag_bst.txt not found at {bst_file_path}. Please specify with --bst_file or place it correctly.")
    else:
        print(f"Loading event flag map from: {bst_file_path}")
        event_map = load_event_flag_map(bst_file_path)

        if not event_map:
            print("Failed to load event_flag_map. Exiting.")
        else:
            print(f"Successfully loaded {len(event_map)} entries from event_flag_map.")
            
            result = is_event_flag_set(args.save_file, args.char_index, args.event_id, event_map)

            if result is None:
                print(f"Could not determine status for event ID {args.event_id}.")
            elif result:
                print(f"Event ID {args.event_id} IS SET (Boss defeated / Event occurred).")
            else:
                print(f"Event ID {args.event_id} IS NOT SET (Boss not defeated / Event not occurred).")