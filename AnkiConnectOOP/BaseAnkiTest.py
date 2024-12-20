from BaseAnkiNoteClass import BaseAnkiNote
import requests
from pathlib import Path
import csv


base_payload = {
    "action": "addNote", #pass action as a parameter to a function?
    "version": 6,
    "params": {
        "note": {
            "deckName": "AnkiConnectAPI",
            "modelName": "AnkiConnectAPI_test",
            "fields": {
                "Sentence": "",
                "Screenshot": "",
                "New words":"",
                "Translation": "",
                "Audio": "",
                "Pitch Accent": ""
            },
            "options": {
                "allowDuplicate": True, 
                "duplicateScope": "deck",
                },
            },
        }
    }


def createAnkiCard(target_word, sentence, translation = None): #basic card creation (word, translation and audio if it exists)
    try:
        baseAnkiNoteInstance = BaseAnkiNote(target_word, sentence) #create a basic note with word and translation
        api_payload = baseAnkiNoteInstance.createPayload(base_payload, translation) #TODO: figure out to way to pass translation more efficiently

        response = requests.post(url = 'http://127.0.0.1:8765', json = api_payload) #send payload to local ankiConnect address

        if response.status_code == 200:
            result = response.json()
            
            if result.get("error") is None: 
                print(f"Card for {target_word} created successfully")
            else:
                print(f"API error occured: {result["error"]}") #print error message in AnkiConnect JSON API
        else:
            print(f'There was an error creating a card {response.status_code}')
    except requests.exceptions.ConnectionError:
        print('Connection error occured')

 
def createAnkiCardsFromCsvFile(csv_file_path): #create anki cards from specific columns from csv file
    try:
        with open(csv_file_path, 'r', encoding = 'utf-8') as csv_file:
            cards_number = 0
            csvReader = csv.DictReader(csv_file)

            for row in csvReader:

                new_words = row.get("New words", "").strip() #changed from repeated row["New words"] checks
                sentence = row.get("Sentence", "").strip() #changed from repeated row["Sentence"] checks
                translation = row.get("Translation", "").strip() #changed from repeated row["Translation"] checks

                if not new_words or not sentence:
                    print(f"Crucial fields are not present in a row, skipping line...")
                    continue

                if '\n' in row["New words"]:
                    new_words = new_words.split('\n')[0]
                    translation = translation.split('\n')[0] if translation else "" #update translation to 1 meaning or empty string
                createAnkiCard(new_words, sentence, translation) #create anki cards from columns in a csv file
                cards_number+= 1
            print(f'Created {cards_number} of Anki cards')

    except FileNotFoundError:
        print(f"{csv_file_path} was not found")
    except Exception as e:
        print(f"Unknown exception occurred: {e}")
            
file_path = Path("C:\\Users\\user\\Desktop\\Python\\Projects\\AnkiConnectAutomation\\CardData\\test.csv")

#createAnkiCard('頑丈','月がきれいですね', 'Shrine; temple') 
createAnkiCardsFromCsvFile(file_path)

#Screenshot block below, work in progress
'''pathToScreen = Path('C:\\Users\\user\\Desktop\\Python\\Projects\\AnkiConnectAutomation\\CardData\\Screenshots\\2024-11-03-215711.png')
test_picture = baseAnkiNoteInstance.getScreenshotBlock(pathToScreen)
test_payload["params"]["note"].update(test_picture)'''