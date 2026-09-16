import sys
from pathlib import Path

from fastembed import TextEmbedding
from sqlalchemy import select
from sqlalchemy.orm import Session

# Allows imports from the src directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent.config.database import engine
from agent.model.model import ContractRule


# Use the SAME model used while storing embeddings
embedding_model = TextEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def search_rulebook(query: str, top_k: int = 1):
    """
    Search the contract rulebook using vector similarity.
    """

    # 1. Validate the user query
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # 2. Convert the user's question into an embedding
    query_embedding = list(
        embedding_model.embed([query])
    )[0].tolist()

    # 3. Calculate cosine distance between:
    #    stored rule embedding <-> query embedding
    distance = ContractRule.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    # 4. Search for the most similar chunks
    statement = (
        select(
            ContractRule,
            distance
        )
        .order_by(distance)
        .limit(top_k)
    )

    # 5. Execute the query
    with Session(engine) as session:
        results = session.execute(statement).all()

    # 6. Format and return the results
    retrieved_rules = []

    for rule, distance_value in results:
        retrieved_rules.append(
            {
                "section": rule.section,
                "content": rule.content,
                "source": rule.source,
                "page": rule.page,
                "distance": float(distance_value),
            }
        )

    return retrieved_rules


if __name__ == "__main__":

    query = "How long should a workmanship warranty last?"

    results = search_rulebook(query, top_k=1)

    print(f"\nQuestion: {query}\n")

    for index, result in enumerate(results, start=1):
        print(f"Result {index}")
        print(f"Section: {result['section']}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Content: {result['content']}")
        print("-" * 50)