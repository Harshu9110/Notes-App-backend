from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import NoteIn, NoteOut
from database import notes_collection
from bson import ObjectId
import uuid
from fastapi import HTTPException

app = FastAPI()

# ⚡ Add CORS settings
origins = [
    "http://localhost:5173",  # frontend URL
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allow frontend
    allow_credentials=True,
    allow_methods=["*"],    # allow all methods (GET, POST, etc.)
    allow_headers=["*"],    # allow all headers
)

@app.get("/")
def root():
    return {"message": "Notes API is running 🚀"}

def note_helper(note) -> dict:
    return {
        "id": str(note["_id"]),
        "title": note["title"],
        "content": note["content"],
        "share_id": note.get("share_id")
    }

@app.post("/notes", response_model=NoteOut)
async def create_note(note: NoteIn):
    note_data = note.dict()
    note_data["share_id"] = str(uuid.uuid4())
    new_note = await notes_collection.insert_one(note_data)
    created = await notes_collection.find_one({"_id": new_note.inserted_id})
    return note_helper(created)

@app.get("/notes")
async def get_notes():
    notes = []
    async for n in notes_collection.find():
        notes.append(note_helper(n))
    return notes

@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: str):
    note = await notes_collection.find_one({"_id": ObjectId(note_id)})
    if note:
        return note_helper(note)
    raise HTTPException(404, "Note not found")

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, data: NoteIn):
    updated = await notes_collection.find_one_and_update(
        {"_id": ObjectId(note_id)},
        {"$set": data.dict()},
        return_document=True
    )
    if updated:
        return note_helper(updated)
    raise HTTPException(404, "Note not found")

@app.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    result = await notes_collection.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 1:
        return {"message": "Note deleted"}
    raise HTTPException(404, "Note not found")

@app.get("/share/{share_id}", response_model=NoteOut)
async def get_shared_note(share_id: str):
    note = await notes_collection.find_one({"share_id": share_id})
    if note:
        return note_helper(note)
    raise HTTPException(404, "Shared note not found")
