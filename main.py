import os
import sys
from pathlib import Path

# Add src to python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agent.services.contract_extract import extract_contract_details_from_pdf
from agent.services.contract_review import review_contract_with_search


def main():
    pdf_path = os.getenv(
        "CONTRACT_PDF_PATH",
        r"C:\Users\User\Downloads\construction_agreement_meridian.pdf"
    )

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

    if not Path(pdf_path).is_file():
        print(f"Error: Contract PDF file not found at: {pdf_path}")
        print("Usage: python main.py <path_to_contract_pdf>")
        return

    print("=" * 80)
    print(f"STARTING CONTRACT REVIEW FOR: {pdf_path}")
    print("=" * 80)

    print("\n1. Extracting text & details from contract PDF...")
    contract_details = extract_contract_details_from_pdf(pdf_path)
    print("\nExtracted Contract Details:")
    print(contract_details.model_dump_json(indent=2))

    print("\n2. Searching pgvector & reviewing contract against rulebook...")
    review_result = review_contract_with_search(contract_details)

    print("\n" + "=" * 80)
    print("CONTRACT REVIEW RESULT")
    print("=" * 80)
    print(review_result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
