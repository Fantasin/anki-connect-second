import base64
import shutil
import json

from typing import Dict, List, Any
from settings import ANKI_MEDIA_FOLDER, AUDIO_BASE_PATH


#SCREENSHOT SECTION
#TODO: Make a search method to find specific screenshots in a folder (match screenshot filename with target word)

#convert screenshot in folder to base64
def convertScreenshotToBase64(path_to_screenshot):
    try:
        with open (path_to_screenshot, 'rb') as original_file:
            f_content = original_file.read() #read file contents as binary file
            base64_file_data = base64.b64encode(f_content).decode('utf-8') #encode to byte-objects, decode as utf-8 string-> return resulting string

        return base64_file_data #use return value in addScreenshotToCard
    except FileNotFoundError:
        print(f"File at {path_to_screenshot} was not found...")
        return None

#returns picture block with base64 encoded screenshot data
def getScreenshotBlock(path_to_screenshot): 
    base64_screenshot_data = convertScreenshotToBase64(path_to_screenshot) #convert screenshots to base64

    return {"picture": [{
            "filename": "screenshot.png",  # The filename that will be stored in Anki
            "data": base64_screenshot_data,         # Base64 encoded image data
            "fields": ["Screenshot"]            # The fields where this image should appear
        }]}

#AUDIO SECTION
#TODO: move sources to function call to change them
def find_audio_name_master(target_word, sources): #find and return filename of an audio file and a source where it was found 

    for source in sources: #check for every source
        filename = process_audio_files(target_word, source)
        
        if filename:
            print(f"Returning {filename} found in {source}")
            return filename, source

    return None, None

def copy_audio_to_folder_master(target_word, sources): #copy audio file from local audio files to anki media folder

    filename, source = find_audio_name_master(target_word, sources) 

    if filename is None or source is None: #check for None after execution findAudioNameMaster
        print("Filename or source is  None. Cannot construct a path")
        return None

    origin_media_folder = filename if source == "forvo_files" else AUDIO_BASE_PATH / source / "audio" / filename  #construct path to copy from      
    target_filename =  filename.name if source == "forvo_files" else filename #manage filename for every source
    full_target_path = ANKI_MEDIA_FOLDER / target_filename #constuct full path to copy file to

    if full_target_path.exists():
        print(f"File {target_filename} already exists in {full_target_path}")
        return target_filename
    
    shutil.copy(origin_media_folder , full_target_path)
    print(f"Copied file {target_filename} to {full_target_path}")
    return target_filename #return file name to add to card
            
#FUNCTIONS FOR FINDING AUDIO FILENAMES IN SPECIFIC SOURCE
def process_audio_files(target_word, source): #process audio sources, find and return audio file name
    json_path = AUDIO_BASE_PATH / source / "index.json"
    forvo_folder = AUDIO_BASE_PATH / source

    if source == "jpod_files": #parse jpod_files json
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        if target_word in data["headwords"]:
            print(f"Found filename for {target_word} in {source}...Returning filename...")
            return data["headwords"][target_word][-1] #used to be [0] instead of [-1]
        else:
            print(f"Filename for {target_word} was not found in {source}. Switching to a different audio source...")
            return None

    elif source == "nhk16_files": #parse nhk16_files json
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        for entry in data:
            if target_word in entry["kanji"]:
                print(f"Found filename for {target_word} in {source}...Returning filename...")
                return entry["accents"][0]["soundFile"]

        print(f"Filename for {target_word} was not found in {source}. Switching to a different audio source...")

    elif source == "forvo_files": #find file name in forvo_files
        audioFileList = (file_path for file_path in forvo_folder.rglob(f"{target_word}.mp3") if file_path.is_file() and file_path.suffix.lower() in ['.mp3']) #set for faster lookup and O(1) complexity

        for file_path in audioFileList:
            if file_path.name:
                print(f"Found {target_word} in {source} at {file_path}")
                return file_path #file path to be used in copyAudioToFolderMaster
                
        print(f"{target_word} not found in any of audio sources, returning None...")


#takes data from a field, copies it to media folder and returns in a format to be used in updateNoteField
def get_audio_data_from_field(field_data, sources): #assumes field_data is a word and not a sentence
    audio_file_name = copy_audio_to_folder_master(field_data, sources)

    if audio_file_name: #if audio file for a word exists
        return f"[sound:{audio_file_name}]"
    
def save_deck_data_to_json(deck_data: List[Dict[str, Any]], deck_name: str, json_file_path: str):
    """
    Save or update deck data in a JSON file.

    :param deck_data: A dictionary or a list of dictionaries representing deck notes
    :param deck_name: Name of the deck.
    :param json_file_path: Path to the JSON file where data will be saved.
    """
    try:
        # Load existing data from JSON
        all_data = load_data_from_json(json_file_path)
    except (FileNotFoundError, KeyError):
        print(f"File not found or deck '{deck_name}' does not exist. Starting with an empty structure.")
        all_data = {}

    # Ensure the deck exists in the JSON structure
    if deck_name not in all_data:
        print(f"Adding new deck '{deck_name}' to JSON.")
        all_data[deck_name] = {}

    # Ensure deck_data is a list of dictionaries
    if isinstance(deck_data, dict):
        print(f"Deck data is a dictionary, converting it to a list of dictionaries.")
        deck_data = list(deck_data.values())

    # Convert deck_data to a dictionary for easier merging
    deck_data_dict = {str(entry["noteId"]): entry for entry in deck_data if "noteId" in entry}

    # Update existing deck data or add new entries
    for note_id, updated_entry in deck_data_dict.items():
        if note_id in all_data[deck_name]:
            print(f"Updating existing note {note_id} in deck '{deck_name}'.")
        else:
            print(f"Adding new note {note_id} to deck '{deck_name}'.")
        all_data[deck_name][note_id] = updated_entry

    # Save updated data back to the JSON file
    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(all_data, file, ensure_ascii=False, indent=4)

    print(f"Deck data for '{deck_name}' has been saved to JSON file.")


def load_data_from_json(json_file_path, deck_name = None):

    with open(json_file_path, 'r', encoding= 'utf-8') as file:
        all_data = json.load(file)

    if deck_name:
        parsed_deck = {int(key): value for key, value in all_data[deck_name].items()}

        print(f"Parsed json for deck {deck_name}. Returning...")
        return parsed_deck
    
    print(f"Parsed full json data. Returning...")
    return all_data
      