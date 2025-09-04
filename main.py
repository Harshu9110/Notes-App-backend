from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import NoteIn, NoteOut
from database import notes_collection
from bson import ObjectId
import uuid

app = FastAPI()

# ⚡ CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://notes-app-frontend-jox5huups.vercel.app",
    "https://notes-app-frontend-coral.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ✅ allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Notes API is running 🚀"}


def note_helper(note) -> dict:
    return {
        "id": str(note["_id"]),
        "title": note["title"],
        "content": note["content"],
        "share_id": note.get("share_id"),
        "share_url": f"https://notes-app-backend.onrender.com/share/{note.get('share_id')}" if note.get("share_id") else None
    }


# Create
@app.post("/notes", response_model=NoteOut)
async def create_note(note: NoteIn):
    note_data = note.dict()
    note_data["share_id"] = str(uuid.uuid4())  # unique share link
    new_note = await notes_collection.insert_one(note_data)
    created = await notes_collection.find_one({"_id": new_note.inserted_id})
    return note_helper(created)


# Read all
@app.get("/notes")
async def get_notes():
    notes = []
    async for n in notes_collection.find():
        notes.append(note_helper(n))
    return notes


# Read one
@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: str):
    note = await notes_collection.find_one({"_id": ObjectId(note_id)})
    if note:
        return note_helper(note)
    raise HTTPException(404, "Note not found")


# Update (preserve share_id)
@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, data: NoteIn):
    existing = await notes_collection.find_one({"_id": ObjectId(note_id)})
    if not existing:
        raise HTTPException(404, "Note not found")

    update_data = data.dict()
    update_data["share_id"] = existing.get("share_id", str(uuid.uuid4()))

    await notes_collection.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": update_data}
    )

    updated = await notes_collection.find_one({"_id": ObjectId(note_id)})
    return note_helper(updated)


# Delete by note_id
@app.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    result = await notes_collection.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 1:
        return {"message": "Note deleted"}
    raise HTTPException(404, "Note not found")


# Delete by share_id (NEW)
@app.delete("/share/{share_id}")
async def delete_shared(share_id: str):
    result = await notes_collection.delete_one({"share_id": share_id})
    if result.deleted_count == 1:
        return {"message": "Shared note deleted"}
    raise HTTPException(404, "Shared note not found")


# Get by share_id
@app.get("/share/{share_id}", response_model=NoteOut)
async def get_shared_note(share_id: str):
    note = await notes_collection.find_one({"share_id": share_id})
    if note:
        return note_helper(note)
    raise HTTPException(404, "Shared note not found")
