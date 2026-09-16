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
            if result and getattr(result, "txts", None):
                page_text = "\n".join([t for t in result.txts if t])

        if page_text:
            all_text.append(page_text)

    pdf.close()

    text = "\n".join(all_text)

    print("Text extracted from PDF")
    print("=" * 80)
    print(f"Extracted text length: {len(text)} characters")

    # -----------------------------
    # 2. Structure-aware / fallback chunking
    # -----------------------------
    # Matches R1, R2, ... R12 rule section markers
    rule_pattern = re.compile(
        r"(?<![A-Za-z0-9])R(1[0-2]|[1-9])(?![A-Za-z0-9])",
        re.IGNORECASE
    )

    matches = list(rule_pattern.finditer(text))

    chunks = []

    if matches:
        for i, match in enumerate(matches):
            start = match.start()

            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)

            chunk = text[start:end].strip()

            if chunk:
                if "Notes for Reviewers / Agent" in chunk:
                    rule_text, notes = chunk.split(
                        "Notes for Reviewers / Agent",
                        1,
                    )
                    if rule_text.strip():
                        chunks.append(rule_text.strip())
                    if notes.strip():
                        chunks.append("NOTES\n" + notes.strip())
                else:
                    chunks.append(chunk)
    else:
        # Fallback chunking for general documents (e.g., contract PDFs)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        current_chunk = []
        current_len = 0

        for line in lines:
            if current_len + len(line) > 800 and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = len(line)
            else:
                current_chunk.append(line)
                current_len += len(line)

        if current_chunk:
            chunks.append("\n".join(current_chunk))

    # -----------------------------
    # 3. Display chunks
    # -----------------------------
    print("\n" + "=" * 80)
    print(f"TOTAL CHUNKS: {len(chunks)}")
    print("=" * 80)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- CHUNK {i} ---")
        print(chunk[:150] + ("..." if len(chunk) > 150 else ""))

    return chunks