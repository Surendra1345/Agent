from pathlib import Path
import shutil
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import logging

from agent.services.chat_agent import process_chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("api")

app = FastAPI(title="Construction Contract Review & AI Agent API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads" / "contracts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mount uploads statically for viewing PDFs
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Construction Contract & Invoice Review Agent",
        "endpoints": {
            "POST /api/chat": "Unified single endpoint for prompt typing, document upload, RAG review, validation, save, and queries.",
        },
    }


@app.post("/api/chat")
def chat(
    message: str = Form(default=""),
    file: UploadFile | None = File(default=None),
    session_id: str | None = Form(default=None),
):
    """The single unified endpoint for the entire application. Handles prompts, PDF uploads, RAG reviews, validations, and saving."""
    filename = file.filename if file and file.filename else None
    logger.info(f"Incoming POST /api/chat | session_id='{session_id}' | file='{filename}' | message='{message[:80]}'")
    try:
        file_path = None
        file_url = None

        if file and file.filename:
            if not file.filename.lower().endswith(".pdf"):
                logger.warning(f"Rejected non-PDF file upload: {file.filename}")
                raise HTTPException(status_code=400, detail="Only PDF documents are supported.")

            # Guardrail 1: Check Magic Bytes (%PDF-)
            header = file.file.read(5)
            file.file.seek(0)  # Rewind after reading header
            if header != b"%PDF-":
                logger.warning(f"Rejected file with invalid magic bytes: {file.filename}")
                raise HTTPException(status_code=400, detail="Invalid PDF file: Missing %PDF- signature.")

            # Guardrail 2: Enforce 25MB File Size Cap
            file.file.seek(0, 2)  # Seek to end
            file_size_bytes = file.file.tell()
            file.file.seek(0)  # Rewind to start
            MAX_SIZE = 25 * 1024 * 1024  # 25 MB
            if file_size_bytes > MAX_SIZE:
                logger.warning(f"File {file.filename} exceeds 25MB limit: {file_size_bytes} bytes")
                raise HTTPException(status_code=413, detail="File too large. Maximum supported size is 25 MB.")

            filename = Path(file.filename).name
            saved_file_path = UPLOAD_DIR / filename

            with saved_file_path.open("wb") as output_file:
                shutil.copyfileobj(file.file, output_file)

            file_path = str(saved_file_path)
            file_url = f"/uploads/contracts/{filename}"
            logger.info(f"Uploaded file saved to: {file_path} ({file_size_bytes / 1024 / 1024:.2f} MB)")


        response = process_chat(
            message=message,
            file_path=file_path,
            file_url=file_url,
            session_id=session_id,
        )
        logger.info(f"Completed /api/chat | session_id='{session_id}' | action='{response.get('action')}'")
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /api/chat for session '{session_id}': {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc