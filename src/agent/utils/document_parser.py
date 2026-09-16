import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pymupdf
from rapidocr import RapidOCR
def extract_contract_text(pdf_path: str) -> str:
    """
    Extract text from a client contract PDF.

    Uses PyMuPDF for normal PDF text.
    Uses RapidOCR for pages that contain scanned/image text.
    """
    ocr = RapidOCR()
    pdf = pymupdf.open(pdf_path)
    all_text = []
    for page_number, page in enumerate(pdf, start=1):
        # Try normal PDF text extraction first
        page_text = page.get_text().strip()
        # If no selectable text, use OCR
        if not page_text:
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2)
            )
            image_bytes = pix.tobytes("png")
            result = ocr(image_bytes)
            if result and getattr(result, "txts", None):
                page_text = "\n".join([t for t in result.txts if t])
        if page_text:
            all_text.append(page_text)
    pdf.close()
    return "\n".join(all_text)

if __name__ == "__main__":
    pdf_path = r"C:\Users\User\Downloads\construction_agreement_meridian.pdf"

    if not Path(pdf_path).is_file():
        raise FileNotFoundError(
            f"Set pdf_path to an existing contract PDF: {pdf_path}"
        )

    text = extract_contract_text(pdf_path)

    print("\n" + "=" * 80)
    print("EXTRACTED CONTRACT TEXT")
    print("=" * 80)
    print(text)