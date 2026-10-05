import pymupdf
from rapidocr import RapidOCR


def extract_pages(file_path: str) -> list[dict]:
    """
    Extract text from a PDF while preserving page numbers.

    PyMuPDF is used first.
    RapidOCR is used when a page has no selectable text.
    """

    ocr = RapidOCR()
    pages = []

    with pymupdf.open(file_path) as pdf:

        for page_number, page in enumerate(pdf, start=1):

            # Try normal PDF text extraction first
            page_text = page.get_text().strip()

            # If no selectable text, use RapidOCR
            if not page_text:

                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2)
                )

                image_bytes = pixmap.tobytes("png")

                result = ocr(image_bytes)

                if result and getattr(result, "txts", None):
                    page_text = "\n".join(
                        text
                        for text in result.txts
                        if text
                    )

            if page_text:
                pages.append(
                    {
                        "page": page_number,
                        "text": page_text,
                    }
                )

    if not pages:
        raise ValueError(
            "No text could be extracted from the document"
        )

    return pages

def extract_text(file_path: str) -> str:
    """
    Extract the complete document text.

    Page numbers are preserved internally by extract_pages().
    This function returns one combined string for services
    that only need the document text.
    """
    pages = extract_pages(file_path)

    return "\n".join(
        page["text"]
        for page in pages
    )