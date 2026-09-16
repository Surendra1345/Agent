import os
import re
import pymupdf
from rapidocr import RapidOCR

def extract_chunks(pdf_path: str) -> list[str]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # -----------------------------
    # 1. Extract text using OCR
    # -----------------------------
    ocr = RapidOCR()
    pdf = pymupdf.open(pdf_path)

    all_text = []

    for page_number, page in enumerate(pdf, start=1):
        page_text = page.get_text().strip()

        # If page has no selectable text, use OCR
        if not page_text:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            image_bytes = pix.tobytes("png")

            result = ocr(image_bytes)

            if hasattr(result, "txts"):
                page_text = "\n".join(result.txts or [])

        if page_text:
            all_text.append(page_text)

    pdf.close()

    text = "\n".join(all_text)

    print("OCR text extracted")
    print("=" * 80)
    print(f"Extracted text length: {len(text)} characters")

    # -----------------------------
    # 2. Structure-aware chunking
    # -----------------------------
    # Matches R1, R2, ... R12
    rule_pattern = re.compile(
        r"(?<![A-Za-z0-9])R(1[0-2]|[1-9])(?![A-Za-z0-9])",
        re.IGNORECASE
    )

    matches = list(rule_pattern.finditer(text))

    chunks = []

    for i, match in enumerate(matches):
        start = match.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

    # -----------------------------
    # 3. Display chunks
    # -----------------------------
    print("\n" + "=" * 80)
    print(f"TOTAL RULE CHUNKS: {len(chunks)}")
    print("=" * 80)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- CHUNK {i} ---")
        print(chunk)

    return chunks