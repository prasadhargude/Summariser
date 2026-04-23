"""
Word Document Content Extractor
Uses python-docx to extract paragraph text from .docx files.
"""

import io
from docx import Document


def extract_word_content(uploaded_file) -> dict:
    """
    Extract all paragraph text from an uploaded .docx file.

    Args:
        uploaded_file: A Streamlit UploadedFile object for a .docx file.

    Returns:
        dict with keys: title, content, source_type, word_count.

    Raises:
        RuntimeError: If the file cannot be parsed as a valid .docx.
    """
    filename = getattr(uploaded_file, "name", "unknown.docx")

    try:
        # Read bytes and wrap in a BytesIO stream for python-docx
        file_bytes = uploaded_file.read()
        doc = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise RuntimeError(
            f"Failed to open Word document '{filename}'. "
            f"The file may be corrupted or not a valid .docx. Details: {exc}"
        ) from exc

    # Collect non-empty paragraphs, preserving structure with newlines
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    full_text = "\n\n".join(paragraphs)

    # Edge case: document with no text content
    if not full_text.strip():
        raise RuntimeError(
            f"No text content found in '{filename}'. The document appears to be empty."
        )

    word_count = len(full_text.split())

    return {
        "title": filename,
        "content": full_text,
        "source_type": "word",
        "word_count": word_count,
    }
