from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class NoteOptions:
    allow_duplicate: bool = True
    duplicate_scope: str = "deck"

    def to_dict(self):
        return {
            "allowDuplicate": self.allow_duplicate,
            "duplicateScope": self.duplicate_scope
            }
        


@dataclass
class AddNotePayload:
    deck_name: str
    model_name: str
    fields: Dict[str, str]
    options: NoteOptions

    def to_dict(self):
        return {
            "note":{
                "deckName": self.deck_name,
                "modelName": self.model_name,
                "fields": self.fields,
                "options": self.options.to_dict()
            }
        }


@dataclass
class NotesInfoPayload:
    notes: List[int] #Have to instantiate like [3232323232] and lot like 3232323232

    def to_dict(self):
        return {
                "notes": self.notes
            }


#TODO: modify dataclass and add field to look for field: query. Figure out how to add this not to disturb other functionality
#TODO: rewrite it to add field_name and if field_name is not present, then use normal functionality like now/ if its provided switch to exact match        
@dataclass
class FindNotesPayload:
    deck: str
    query: Optional[str] = None
    field: Optional[str] = None
    regex: Optional[bool] = False


    def to_dict(self):
        query_parts = []

        if self.deck:
            query_parts.append(f'deck:{self.deck}')
        if self.field and self.query:
            field_query = f"re:{self.query}" if self.regex else self.query #add option for regex
            query_parts.append(f'{self.field}:{field_query}')
        if self.query and not self.field:
            query_parts.append(self.query)

        
        return {
            "query": " ".join(query_parts)
        }
  
@dataclass
class UpdateNoteFieldsPayload:
    id: int
    fields: Dict[str, str]

    def to_dict(self):
        return {
            "note":{
                "id": self.id,
                "fields": self.fields
            }
        }
    