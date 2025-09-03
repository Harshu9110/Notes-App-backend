from pydantic import BaseModel
from typing import Optional

class NoteIn(BaseModel):
    title: str
    content: str

class NoteOut(NoteIn):
    id: str
    share_id: Optional[str]
