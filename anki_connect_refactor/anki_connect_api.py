import requests

from typing import Dict, List, Optional

from settings import URL_ADDRESS
from models import AddNotePayload, NotesInfoPayload, UpdateNoteFieldsPayload, FindNotesPayload

'''
This file should only handle the interaction with the AnkiConnect API.

Responsibilities of anki_connect_api.py:
Send HTTP requests to AnkiConnect.
Handle the response from AnkiConnect.

IMPORTANT: Use invokeAnkiConnectRequest for every api call, other functions should ONLY be concerned with preparing payload data and calling invoke
'''

def invoke_anki_connect_request(action, params = None): #function for sending requests to AnkiConnectApi endpoint

    """
    action -> str: type of AnkiConnect request
    params -> dict, optional: can be empty or differ for every action

    supported actions: notesInfo, addNote, findNotes, updateNoteFields
    """

    payload = { 
        "action": action,
        "version": 6,
        "params": params or {} 
    }
    try:
        response = requests.post(URL_ADDRESS, json = payload)
        response.raise_for_status() #to identify request errors
        result = response.json()

        if result.get("error"):
            print(f"Error occured when sending request:{result.get("error")}")
            print(f"{result}")
            return #return None when error occurs
        
        api_result = result.get("result")

        if isinstance(api_result, list) and all(not item for item in api_result):
            print(f"Result from API call is not valid for {action}. Response: {api_result}")
            return #return in case of empty response
        
        print(f"{action} executed sucessfully")
        return result.get("result")

    except requests.exceptions.RequestException as req_err:
        print(f"HTTP Request failed: {req_err}")
    except TypeError as typo:
        print(f"One of the parameters is not correct: {typo}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")


def add_note(deck_name: str, model_name: str, fields: Dict[str, str], options) -> int:

    add_note_dict = AddNotePayload(deck_name, model_name, fields, options).to_dict()

    response = invoke_anki_connect_request("addNote", add_note_dict)
    return response


#TODO: Parse in note_parser module, remove hardcode. Keep note finding functionality here
def find_note_info(note_id: List[int])-> List[Dict[str, str]]:

    find_note_dict = NotesInfoPayload(note_id).to_dict()

    response = invoke_anki_connect_request("notesInfo", find_note_dict)

    return response


def update_note_fields(note_id: int, fields: Dict[str,str])-> None:
    update_note_fields_dict = UpdateNoteFieldsPayload(note_id, fields).to_dict()

    invoke_anki_connect_request("updateNoteFields", update_note_fields_dict)
    print(f"Updated {list(fields.keys())} field(s) for {note_id}")

#TODO: add logic for stricter regex pattern
def find_notes_for_deck(deck_name: str, query: Optional[str] = None, field: Optional[str] = None)-> List[int]: #findNotes
    find_notes_payload = FindNotesPayload(deck_name, query, field).to_dict()
    response = invoke_anki_connect_request("findNotes", find_notes_payload)

    if not response:
        print("Query yielded no result. Trying with regex...")
        find_notes_payload = FindNotesPayload(deck_name, query, field, regex = True).to_dict()
        response = invoke_anki_connect_request("findNotes", find_notes_payload)

        if len(response) > 1: #TODO: figure out the way to accurately process such cases
            print(f"Number of entries found for word {query} is {len(response)}. Skipping entry for now")
            return []

    return response if response else [] 


   