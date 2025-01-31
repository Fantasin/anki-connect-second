import re, csv

from typing import Dict, List, Any
from bs4 import BeautifulSoup

from anki_connect_api import find_note_info, find_notes_for_deck, update_note_fields, add_note
from settings import DECKS_PRIMARY_FIELDS, PATTERN_BASIC_CARD, PATTERN_REVERSE_CARD, PATTERN_FIELD_AUDIO, PATTERN_REVERSE_CARD_BACK, DECK_DATA_JSON_PATH, AUDIO_SOURCES, PATTERN_FIELD_AUDIO_FULL, ANKI_MODELS
from media_handler import get_audio_data_from_field, save_deck_data_to_json, load_data_from_json
from models import NoteOptions


#HELPER FUNCTIONS FOR DATA PARSING
def clean_note_fields(entry: Dict[str, any], front_field: str, back_field: str) -> Dict[str, Any]:

    front_value = entry.get("fields").get(front_field).get("value")
    upd_front = find_and_remove_html_from_field(front_value)

    back_value = entry.get("fields").get(back_field).get("value")
    upd_back = find_and_remove_html_from_field(back_value)

    note_id = entry.get("noteId")

    print(f"Cleaned Front: '{upd_front}', Cleaned Back: '{upd_back}'")

    return {front_field: upd_front, back_field: upd_back, "noteId": note_id}


def find_and_remove_html_from_field(field_value: str) -> str:
    html_tag_pattern = re.compile(r"<.*?>")

    if html_tag_pattern.search(field_value):
        return BeautifulSoup(field_value, "html.parser").get_text().replace("\xa0", "")
    else:
        return field_value


#PARSING FUNCTIONS

#TODO: add checks for empty data and for exceptions
def parse_data_from_deck(deck_name: str) -> List[Dict[str, Any]]:

    if deck_name not in DECKS_PRIMARY_FIELDS.keys():
        print(f"Deck {deck_name} is not in the decks constant...")
        return
 
    front_field, back_field = DECKS_PRIMARY_FIELDS[deck_name] #get primary fields to parse data from

    notes = find_notes_for_deck(deck_name)
    new_data = find_note_info(notes)

    return [clean_note_fields(entry, front_field, back_field) for entry in new_data] #return list of fields without html markup


#find note ids for cards and reverse cards for audio change
def prepare_change_audio_notes(json_path, deck_name):
    deck_data = load_data_from_json(json_path, deck_name)

    change_audio_list = []
    change_audio_entries = []

    audio_pattern = re.compile(PATTERN_FIELD_AUDIO_FULL)

    for index, entry in enumerate(deck_data.values()):
        if entry["Flag"] == "Change audio":
            change_audio_list.append(index)
            change_audio_list.append(index + 1)

    for index, entry in enumerate(deck_data.values()):
        if index in change_audio_list:
            entry["Flag"] = 'Change audio'
            new_text = re.sub(audio_pattern, "" , entry["Back"]).strip()
            entry["Back"] = new_text
            change_audio_entries.append({entry["noteId"]:entry["Back"]})

    return change_audio_entries


#TODO: fix a bug where if note_id doesnt exists it raises an exception. Skip entries like that
def parse_data_from_note(note_id: int, deck_name: str) -> Dict[str, Any]:

    if deck_name not in DECKS_PRIMARY_FIELDS.keys():
        print(f"Deck {deck_name} is not in the decks constant...")
        return

    front_field, back_field = DECKS_PRIMARY_FIELDS[deck_name] #get primary fields to parse data from

    field_data = find_note_info(note_id)

    if not field_data:
        print(f"Data was not found for {note_id}. Parsing not possible")
        return

    return clean_note_fields(field_data[0], front_field, back_field)

def find_patterns_for_deck(parsed_deck_data: List[Dict[str, Any]], deck_name: str) -> List[Dict[str, Any]]: 

    front_field_name, back_field_name = DECKS_PRIMARY_FIELDS[deck_name]

    card_pattern = re.compile(PATTERN_BASIC_CARD)
    reverse_card_pattern = re.compile(PATTERN_REVERSE_CARD)
    audio_pattern = re.compile(PATTERN_FIELD_AUDIO)

    #entries_for_audio_change = prepare_change_audio_notes(DECK_DATA_JSON_PATH, deck_name)

    for entry in parsed_deck_data:
        front = entry.get(front_field_name)
        back = entry.get(back_field_name)
        note_id = entry.get("noteId")
        entry["Flag"] = ""

        '''for audio_entry in entries_for_audio_change: 
            if note_id in audio_entry:
                print(f"Removing audio part for {audio_entry}")
                entry["Back"] = audio_entry[note_id]
                break'''

        if audio_pattern.search(entry.get(back_field_name)):
            print(f"Found audio match for {back}. Flagging as Skip")
            entry["Flag"] = "Skip"
            continue

        if card_pattern.search(entry.get(front_field_name)):
            print(f"Found Basic Card match for {front}. Flagging as Card")
            entry["Flag"] = "Card"
            continue

        if reverse_card_pattern.search(entry.get(front_field_name)):
            print(f"Found Reverse Card match for {front}. Flagging as Reverse Card")
            entry["Flag"] = "Reverse Card"
            continue

        print(f"Wasn't able to identify pattern for {entry}. Flagging as Unknown")
        entry["Flag"] = "Unknown"
        
    return parsed_deck_data


#TODO: get rid of this function, integrate functionality
def find_kanji_part(entry, back_field_name):

    match = re.match(PATTERN_REVERSE_CARD_BACK, entry[back_field_name])

    if match:
        return match.group(1).strip()
    
#TODO: Optimize, get rid of excessive loops, add more print statements
#TODO: get rid of hardcode
def find_card_pairs(flagged_deck_data: List[Dict[str, Any]]) -> List[tuple]:

    front_dict = {entry["noteId"]: entry for entry in flagged_deck_data if entry["Flag"] == "Card"}
    back_dict = {entry["noteId"]: entry for entry in flagged_deck_data if entry["Flag"] == "Reverse Card"}

    matched_pairs = []

    for back_id, back_entry in back_dict.items():

        kanji_part = find_kanji_part(back_entry, "Back")

        if kanji_part:
            print(f"Found {kanji_part} for {back_entry} with {back_id}")

            for front_id, front_entry in front_dict.items():

                if kanji_part == front_entry["Front"].strip():
                    print(f"Kanji match found: {front_id}:{front_entry["Front"]} <-> {back_id}:{back_entry["Back"]}")
                    matched_pairs.append((back_id, front_entry["Audio"]))

        else:
            for front_id, front_entry in front_dict.items():
                # Check if the Front field is a substring of the Back field
                if front_entry["Front"] in back_entry["Back"]:
                    print(f"Partial match found: {front_id}:{front_entry["Front"]} <-> {back_id}:{back_entry["Back"]}")
                    matched_pairs.append((back_id, front_entry["Audio"]))
    
    return matched_pairs


#TODO: add more verbose print statements
#TODO: add updateAnkiCard methods
#TODO: create mapping dict (id: entry) to use instead of a second loop after finding matched pairs
def add_audio_to_deck(deck_name):
    front_field_name, back_field_name = DECKS_PRIMARY_FIELDS[deck_name]
    data = parse_data_from_deck(deck_name)
    flagged_data = find_patterns_for_deck(data, deck_name)

    for entry in flagged_data:
        if entry["Flag"] == "Card":
            audio_part = get_audio_data_from_field(entry[front_field_name], AUDIO_SOURCES)

            if audio_part:
                entry[back_field_name] = f"{entry[back_field_name]} {audio_part}"
                entry["Audio"] = audio_part
                
                update_note_fields(entry["noteId"], {back_field_name: entry[back_field_name]})
                print(f"Update for Card was successful")

            else:
                print(f"Audio was not found for card: {entry[front_field_name]}. Removing it from cards to update")
                entry["Flag"] = "Not found"


    matched_pairs = find_card_pairs(flagged_data)

    for note_id, audio_data in matched_pairs:
        for entry in flagged_data:
            if entry["noteId"] == note_id:
                entry[back_field_name] = f"{entry[back_field_name]} {audio_data}"
                
                update_note_fields(entry["noteId"], {back_field_name: entry[back_field_name]})
                print(f"Update for Reverse Card was successful")
    
    #save_deck_data_to_json(flagged_data, deck_name, DECK_DATA_JSON_PATH)
            
    

#TODO: get rid of row[0] workaround
def find_note_ids_from_file(file_path, deck_name):
    with open(file_path, 'r', encoding = 'utf-8') as csv_file:
        csvReader = csv.reader(csv_file)

        note_ids = {}

        for row in csvReader:

            row_id = find_notes_for_deck(deck_name, row[0], "Front")

            if not row_id:
                print("Skipping empty rows...")
                continue

            print(f"Found noteIds for {row[0]}: {row_id}")
            note_ids[row[0]] = row_id[0]
        
        return note_ids

#TODO: write a function that uses find_note_ids_from_file and finds these ids in deck_data json and Flags them for changing audio (i.e. Flag: change audio)
def flag_notes_for_audio_change(note_ids: Dict[str, int], deck_name, json_path: str):

    deck_data = load_data_from_json(json_path, deck_name)

    for id in note_ids.values():
        if id in deck_data:
            print(f"{id} found in deck_data: {deck_data[id]}")
            deck_data[id]["Flag"] = "Change audio"
            print(f"Flagged card {id} for audio change...")

    #TODO: add saving updated data back to json
    save_deck_data_to_json(deck_data, deck_name, DECK_DATA_JSON_PATH)

#TODO: optimize, think about field identification process, add anki note creation
def create_notes_from_csv_file(csv_file_path, deck_name): #create anki cards from specific columns from csv file
    try:
        with open(csv_file_path, 'r', encoding = 'utf-8') as csv_file:
            csvReader = csv.DictReader(csv_file)
            
            field_names = csvReader.fieldnames

            if not field_names:
                print("CSV file doesn't have field names or is incorrectly formatted")
                return
            
            front_field_name, back_field_name = DECKS_PRIMARY_FIELDS[deck_name]
            model_name = ANKI_MODELS[deck_name]

            if front_field_name not in field_names or back_field_name not in field_names:
                print("Required fields are missing in the CSV file...")
                return

            print("All the requred data is present. Starting Anki card creation...")

            for row in csvReader:
            
                front = row.get(front_field_name, "").strip()
                back = row.get(back_field_name, "").strip()

                if '\n' in back:
                    back = back.split('\n')[0]
                
                note_id = add_note(deck_name, model_name, {front_field_name: front, back_field_name: back}, NoteOptions())
                print(f"Created anki card: {note_id}")

    except FileNotFoundError:
        print(f"{csv_file_path} was not found")
    except Exception as e:
        print(f"Unknown exception occurred: {e}")


def parse_flagged_content_to_json(deck_name, json_path):
    parsed_data = parse_data_from_deck(deck_name)
    flagged_data = find_patterns_for_deck(parsed_data, deck_name)

    save_deck_data_to_json(flagged_data, deck_name, json_path)

def update_json_for_audio_change(file_path, deck_name, json_path):
    note_ids = find_note_ids_from_file(file_path, deck_name)
    flag_notes_for_audio_change(note_ids, deck_name, json_path)


def load_entries_for_flag(flag, deck_name, json_path):
    deck_data = load_data_from_json(json_path, deck_name)

    entries_for_flag = []

    for entry in deck_data.values():
        if entry["Flag"] == flag:
            entries_for_flag.append(entry)

    return entries_for_flag

