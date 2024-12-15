from BaseAnkiNoteClass import BaseAnkiNote
import requests
from pathlib import Path


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

def createAnkiCard(target_word, translation): #basic card creation (word, translation and audio if it exists)
    try:
        baseAnkiNoteInstance = BaseAnkiNote(target_word, translation) #create a basic note with word and translation
        api_payload = baseAnkiNoteInstance.createPayload(base_payload)

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


createAnkiCard('神社','temple') 


#Screenshot block below, work in progress
'''pathToScreen = Path('C:\\Users\\user\\Desktop\\Python\\Projects\\AnkiConnectAutomation\\CardData\\Screenshots\\2024-11-03-215711.png')
test_picture = baseAnkiNoteInstance.getScreenshotBlock(pathToScreen)
test_payload["params"]["note"].update(test_picture)'''

