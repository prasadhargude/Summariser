"""
PDF Content Extractor
Uses PyMuPDF (fitz) to extract text from every page of a PDF file.
Preserves paragraph structure by inserting double newlines between pages.
"""

import fitz  # PyMuPDF


def extract_pdf_content(uploaded_file) -> dict:
    """
    Extract all text from an uploaded PDF file object.

    Args:
        uploaded_file: A Streamlit UploadedFile object for a .pdf file.

    Returns:
        dict with keys: title, content, source_type, word_count.

    Raises:
        RuntimeError: If the PDF cannot be read or is corrupted.
    """
    filename = getattr(uploaded_file, "name", "unknown.pdf")

    try:
        # Read the raw bytes from the Streamlit upload
        pdf_bytes = uploaded_file.read()

        # Open the PDF document from memory
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to open PDF file '{filename}'. "
            f"The file may be corrupted or not a valid PDF. Details: {exc}"
        ) from exc

    # Extract text page-by-page, keeping double-newline separators
    page_texts = []
    for page_number in range(len(doc)):
        page = doc[page_number]
        text = page.get_text("text")  # plain-text extraction
        if text.strip():
            page_texts.append(text.strip())

    doc.close()

    full_text = "\n\n".join(page_texts)

    # Edge case: PDF with no extractable text (e.g. scanned images)
    if not full_text.strip():
        raise RuntimeError(
            f"No extractable text found in '{filename}'. "
            "The PDF may contain only images or scanned pages."
        )

    word_count = len(full_text.split())

    return {
        "title": filename,
        "content": full_text,
        "source_type": "pdf",
        "word_count": word_count,
    }
