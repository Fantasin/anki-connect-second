import copy
import base64
from pathlib import Path
import shutil
import json


class BaseAnkiNote:
    anki_media_folder = Path("C:\\Users\\user\\AppData\\Roaming\\Anki2\\User 1\\collection.media") #anki media folder for audio creation
    AUDIO_BASE_PATH = Path(f"C:\\Users\\user\\Desktop\\LocalAudioJP\\local-yomichan-audio-collection-2023-06-11-mp3\\user_files")
    AUDIO_SOURCES = ("jpod_files", "nhk16_files", "forvo_files") #sources for finding audio. upd. made it tuple instead of a list for immutability

    def __init__(self, new_words, sentence):
        self.fields = { #basic required fields for anki card creation
            "New words": new_words,
            "Sentence": sentence        
        } 
        
    #PAYLOAD MANAGEMENT SECTION
    #Utility function for copying base_payload for sending to ankiConnectApi
    @staticmethod
    def copyBaseCardTemplate(base_card_template):
        return copy.deepcopy(base_card_template)


    #TODO: Modify this function/make a new one to support other api actions other than addNote
    #main function for basic card creation: creates a note with word, translation and audio for word if it exists
    def createPayload(self, base_card_template, translation = None):  #extra fields for things like pitch accent and furigana
        card_payload = BaseAnkiNote.copyBaseCardTemplate(base_card_template)
        fields_to_update = self.fields.copy() #copy fields of instance to avoid modifying the original

        if translation: #if translation is passed to createPayload 
            fields_to_update["Translation"] = translation #add it to card

        audio_file_name = self.copyAudioToFolderMaster() #copy target word to anki media folder

        if audio_file_name: #if audio file for a word exists
            fields_to_update["Audio"] = f"[sound:{audio_file_name}]" #update audio with filename.mp3

        card_payload["params"]["note"]["fields"].update(fields_to_update) #update fields in copied payload with instance attributes

        return card_payload
    
    #SCREENSHOT SECTION
    #TODO: Make a search method to find specific screenshots in a folder (match screenshot filename with target word)

    #convert screenshot in folder to base64
    def convertScreenshotToBase64(self, path_to_screenshot):
        try:
            with open (path_to_screenshot, 'rb') as original_file:
                f_content = original_file.read() #read file contents as binary file
                base64_file_data = base64.b64encode(f_content).decode('utf-8') #encode to byte-objects, decode as utf-8 string-> return resulting string

            return base64_file_data #use return value in addScreenshotToCard
        except FileNotFoundError:
            print(f"File at {path_to_screenshot} was not found...")
            return None
    
    #returns picture block with base64 encoded screenshot data
    def getScreenshotBlock(self, path_to_screenshot): 
        base64_screenshot_data = self.convertScreenshotToBase64(path_to_screenshot) #convert screenshots to base64

        return {"picture": [{
                "filename": "screenshot.png",  # The filename that will be stored in Anki
                "data": base64_screenshot_data,         # Base64 encoded image data
                "fields": ["Screenshot"]            # The fields where this image should appear
            }]}

    #AUDIO SECTION
    def findAudioNameMaster(self): #find and return filename of an audio file and a source where it was found
        sources = BaseAnkiNote.AUDIO_SOURCES 

        for source in sources: #check for every source
            filename = self.process_audio_files(source)
            
            if filename:
                print(f"Returning {filename} found in {source}")
                return filename, source

        return None, None
    
    def copyAudioToFolderMaster(self): #copy audio file from local audio files to anki media folder

        filename, source = self.findAudioNameMaster() 

        if filename is None or source is None: #check for None after execution findAudioNameMaster
            print("Filename or source is  None. Cannot construct a path")
            return None

        origin_media_folder = filename if source == "forvo_files" else self.AUDIO_BASE_PATH / source / "audio" / filename  #construct path to copy from      
        target_filename =  filename.name if source == "forvo_files" else filename #manage filename for every source
        full_target_path = BaseAnkiNote.anki_media_folder / target_filename #constuct full path to copy file to

        if full_target_path.exists():
            print(f"File {target_filename} already exists in {full_target_path}")
            return target_filename
        
        shutil.copy(origin_media_folder , full_target_path)
        print(f"Copied file {target_filename} to {full_target_path}")
        return target_filename #return file name to add to card
              
    #FUNCTIONS FOR FINDING AUDIO FILENAMES IN SPECIFIC SOURCE
    def process_audio_files(self, source): #process audio sources, find and return audio file name
        target_word = self.fields["New words"]
        json_path = self.AUDIO_BASE_PATH / source / "index.json"
        forvo_folder = self.AUDIO_BASE_PATH / source

        if source == "jpod_files": #parse jpod_files json
            with open(json_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)

            if target_word in data["headwords"]:
                print(f"Found filename for {target_word} in {source}...Returning filename...")
                return data["headwords"][target_word][0]
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


