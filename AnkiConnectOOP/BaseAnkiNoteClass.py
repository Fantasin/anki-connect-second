import copy
import base64
from pathlib import Path
import shutil


class BaseAnkiNote:
    anki_media_folder = Path("C:\\Users\\user\\AppData\\Roaming\\Anki2\\User 1\\collection.media") #anki media folder for audio creation

    def __init__(self, sentence, translation):
        self.fields = { #basic required fields for anki card creation
            "Sentence": sentence,  
            "Translation": translation
        } 
        
    #PAYLOAD MANAGEMENT SECTION
    #Utility function for copying base_payload for sending to ankiConnectApi
    @staticmethod
    def copyBaseCardTemplate(base_card_template):
        return copy.deepcopy(base_card_template)


    #TODO: Modify this function/make a new one to support other api actions other than addNote
    #main function for basic card creation: creates a note with word, translation and audio for word if it exists
    def createPayload(self, base_card_template, extra_fields = None):  #extra fields for things like pitch accent and furigana
        card_payload = BaseAnkiNote.copyBaseCardTemplate(base_card_template)
        fields_to_update = self.fields.copy() #copy fields of instance to avoid modifying the original

        if extra_fields: #if extra_fields dict is not None
            fields_to_update.update(extra_fields)

        audio_file_name = self.copyAudioToFolder() #copy target word to anki media folder

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
    #Find audio file in local audio collection folder
    def findAudioFile(self):
        target_word = self.fields["Sentence"] #store target_word as a separate attribute to use later

        #for now baseFolder is constant
        baseFolder = Path("C:\\Users\\user\\Desktop\\LocalAudioJP\\local-yomichan-audio-collection-2023-06-11-mp3\\user_files\\forvo_files")

        audioFileList = (file_path for file_path in baseFolder.rglob(f"{target_word}.mp3") if file_path.is_file() and file_path.suffix.lower() in ['.mp3']) #set for faster lookup and O(1) complexity

        for file_path in audioFileList:
            if file_path.name:
                print(f"Found {target_word} in {file_path}")
                return file_path #file path to be used in copyAudioToFolder
            
        print(f"{target_word} not found, returning None...")
        return None

    #copy to other folder (e.g. anki media folder)
    def copyAudioToFolder(self):
        audio_file_path = self.findAudioFile() #changed from findAudioFile(target_word)
        if audio_file_path:
            full_target_path = BaseAnkiNote.anki_media_folder / audio_file_path.name #construct full path to target folder
            if full_target_path.exists():
                print(f"File {audio_file_path.name} already exists in {BaseAnkiNote.anki_media_folder}")
                return audio_file_path.name
            else:
                shutil.copy(audio_file_path , full_target_path)
                print(f"Copied file {audio_file_path.name} to {BaseAnkiNote.anki_media_folder}")
                return audio_file_path.name #return file name to add to card
        else:
            print(f"Failed to copy file. {self.fields["Sentence"]} was not found in audio folder")
