import os

from dotenv import load_dotenv
from pathlib import Path

#project variables
BASE_PROJECT_DIR = Path(__file__).resolve().parent.parent
CSV_FILE_PATH = BASE_PROJECT_DIR / "static" / "test.csv"
DECK_DATA_JSON_PATH = BASE_PROJECT_DIR / "static" / "deck_data.json"

#global variables
load_dotenv()

ANKI_MEDIA_FOLDER = Path(os.getenv('ANKI_MEDIA_FOLDER'))
AUDIO_BASE_PATH = Path(os.getenv('AUDIO_BASE_PATH'))
URL_ADDRESS = os.getenv('URL_ADDRESS')

#other constants
AUDIO_SOURCES = ("jpod_files", "nhk16_files", "forvo_files") #sources for finding audio. upd. made it tuple instead of a list for immutability

#TODO: move constant below to separate JSON file and write function to add new entries from code
DECKS_PRIMARY_FIELDS = { #used for retrieval of primary fields when parsing data from a deck
    "Monolingual": ["Sentence","New words"],
    "AnkiConnectAPI": ["Front", "Back"],
    "Japanese": ["Front", "Back"]
}

ANKI_MODELS = { #list of models for decks
    "Monolingual": "12434324",
    "AnkiConnectAPI": "AnkiConnectAPI_test",
    "Japanese": "Basic-1ba65"
}


#constants for pattern identification
PATTERN_BASIC_CARD = r"\～*[\u3040-\u309F]+|[\u30A0-\u30FF]+|[\u4E00-\u9FFF]+" #pattern for finding either hiragana, katakana or kanji in a pattern + optional ~
PATTERN_REVERSE_CARD = r"\(*[a-zA-Z]+|[0-9]+|[０-９]+" #all english letters and numbers + number on japanese font + optional "(" at the beginning
PATTERN_FIELD_AUDIO = r"\[sound:"
PATTERN_FIELD_AUDIO_FULL = r"\[sound:.+\]"
PATTERN_REVERSE_CARD_BACK = r"(.+?)（(.+?)）"

#TODO: add constants for regex pattern for find_notes_for_deck