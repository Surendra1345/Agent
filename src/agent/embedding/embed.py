import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastembed import TextEmbedding
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from agent.utils.chunking import extract_chunks
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
# 2. Generate embeddings
# --------------------------------

pdf_path = os.getenv("CONTRACT_RULEBOOK_PATH")
if not pdf_path:
    raise RuntimeError("CONTRACT_RULEBOOK_PATH is missing from the .env file")
chunks = extract_chunks(pdf_path)
texts = chunks
print("\n========== CHUNKS ==========")

for i, chunk in enumerate(chunks, start=1):
    print(f"\n--- CHUNK {i} ---")
    print(repr(chunk))
    print("Length:", len(chunk))

print("============================\n")
embeddings = list(embedding_model.embed(texts))

print(f"Total chunks: {len(chunks)}")
print(f"Total embeddings: {len(embeddings)}")
print(f"Embedding dimension: {len(embeddings[0])}")


# --------------------------------
# 3. Insert into PostgreSQL
# --------------------------------

with engine.begin() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

Base.metadata.create_all(engine)

with Session(engine) as session:
    for chunk, embedding in zip(chunks, embeddings):
        section = re.match(r"R(?:1[0-2]|[1-9])", chunk, re.IGNORECASE)
        section_name = section.group(0).upper() if section else "NOTES"

        db_rule = ContractRule(
            contract_rules=section_name,
            content=chunk,
            embedding=embedding.tolist(),
            source=pdf_path,
            page=1,
            section=section_name,
        )

        session.add(db_rule)
    session.commit()


print("All contract rules and embeddings inserted successfully.")