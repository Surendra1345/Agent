import os
import re

from fastembed import TextEmbedding
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from agent.utils.document_parser import extract_pages
from agent.utils.chunking import chunk_text
from agent.config.database import engine
from agent.model.model import Base, ContractRule


load_dotenv()


# --------------------------------
# 1. Load embedding model
# --------------------------------

embedding_model = TextEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# --------------------------------
# 2. Get rulebook path
# --------------------------------

pdf_path = os.getenv("CONTRACT_RULEBOOK_PATH")

if not pdf_path:
    raise RuntimeError(
        "CONTRACT_RULEBOOK_PATH is missing from the .env file"
    )


# --------------------------------
# 3. Extract text from PDF
# --------------------------------

pages = extract_pages(pdf_path)

print("\n========== EXTRACTED PAGES ==========")

for page in pages:
    print(
        f"Page {page['page']}: "
        f"{len(page['text'])} characters"
    )

print(f"\nTotal pages with text: {len(pages)}")
print("=====================================\n")


# --------------------------------
# 4. Split text into chunks
# --------------------------------

chunks = chunk_text(pages)
print("\n========== CHUNKS ==========")
for i, chunk in enumerate(chunks, start=1):
    chunk_text_value = chunk["text"]
    page_number = chunk["page"]
    print(f"\n--- CHUNK {i} ---")
    print(f"Page: {page_number}")
    preview = chunk_text_value[:150]
    if len(chunk_text_value) > 150:
        preview += "..."
    print(preview)
    print("Length:", len(chunk_text_value))
print(f"\nTotal chunks: {len(chunks)}")
print("============================\n")
# --------------------------------
# 5. Prepare text for embeddings
# --------------------------------
texts = [
    chunk["text"]
    for chunk in chunks
]
# --------------------------------
# 6. Generate embeddings
# --------------------------------
embeddings = list(
    embedding_model.embed(texts)
)
print(f"Total embeddings: {len(embeddings)}")

if embeddings:
    print(
        f"Embedding dimension: {len(embeddings[0])}"
    )


# --------------------------------
# 7. Insert into PostgreSQL
# --------------------------------

with engine.begin() as connection:

    connection.execute(
        text(
            "CREATE EXTENSION IF NOT EXISTS vector"
        )
    )


Base.metadata.create_all(engine)
with Session(engine) as session:

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):
        # Get chunk information
        chunk_text_value = chunk["text"]
        page_number = chunk["page"]
        # Find rule section
        section = re.match(
            r"R(?:1[0-2]|[1-9])",
            chunk_text_value,
            re.IGNORECASE,
        )
        section_name = (
            section.group(0).upper()
            if section
            else "NOTES"
        )
        # Create database record
        db_rule = ContractRule(
            contract_rules=section_name,
            content=chunk_text_value,
            embedding=embedding.tolist(),
            source=pdf_path,
            page=page_number,
            section=section_name,
        )
        session.add(db_rule)
    session.commit()
print("Rules successfully stored in PostgreSQL.")