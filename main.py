from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
import whisper
from database import SessionLocal, Entry
from fastapi.middleware.cors import CORSMiddleware
import uuid
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from textblob import TextBlob



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the Whisper model once (medium model is more accurate but slower)
model = whisper.load_model("tiny")  # you can try "small" or "medium" too

@app.post("/entries")
@app.post("/entries")
async def upload_entry(file: UploadFile = File(...)):
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_location = os.path.join(UPLOAD_FOLDER, unique_filename)

    # Save file to disk
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Transcribe the audio
    result = model.transcribe(file_location,task="transcribe", language=None)
    transcript = result["text"]
    d_language=result["language"]

    blob = TextBlob(transcript)
    polarity = blob.sentiment.polarity

    # Simple sentiment
    if polarity > 0.2:
        sentiment = "Positive"
    elif polarity < -0.2:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    # Save to DB
    db = SessionLocal()
    db_entry = Entry(
        file_path=file_location,
        transcript=transcript,
        sentiment=sentiment,
        language=d_language,
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    db.close()

    return JSONResponse(content={
        "message": "File uploaded and transcribed successfully.",
        "entry_id": db_entry.id,
        "file_path": file_location,
        "transcript": transcript,
        "sentiment": sentiment,
        "language":d_language,
    })



# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/entries")
def get_entries(db: Session = Depends(get_db)):
    records = db.query(Entry).order_by(Entry.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "file_path": e.file_path,
            "transcript": e.transcript,
            "sentiment": e.sentiment,
            "language":e.language,
            "created_at": e.created_at.isoformat()
        }
        for e in records
    ]


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int):
    db = SessionLocal()
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if entry is None:
        db.close()
        raise HTTPException(status_code=404, detail="Entry not found")

    # Optionally: delete the audio file from disk
    if os.path.exists(entry.file_path):
        os.remove(entry.file_path)

    db.delete(entry)
    db.commit()
    db.close()
    return {"message": "Entry deleted successfully"}