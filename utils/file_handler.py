"""
File Handler — Input Router
Routes incoming data to the correct extractor based on source type.
Returns a standardised content dictionary or raises a clear error.
"""

from extractors.youtube_extractor import extract_youtube_transcript
from extractors.pdf_extractor import extract_pdf_content
from extractors.word_extractor import extract_word_content
from extractors.text_extractor import extract_text_content


def route_input(source_type: str, data) -> dict:
    """
    Dispatch to the appropriate extractor based on source_type.

    Args:
        source_type: One of "youtube", "pdf", "word", or "text".
        data: Either a URL string (for YouTube) or a Streamlit
              UploadedFile object (for file-based sources).

    Returns:
        A standardised dict with keys:
            title, content, source_type, word_count.

    Raises:
        ValueError: If source_type is unrecognised or data is invalid.
        RuntimeError: Propagated from individual extractors on failure.
    """
    # Normalise and validate the source type
    source_type = source_type.strip().lower()

    if source_type == "youtube":
        if not data or not isinstance(data, str):
            raise ValueError("Please provide a valid YouTube URL.")
        return extract_youtube_transcript(data)

    elif source_type == "pdf":
        if data is None:
            raise ValueError("No PDF file was uploaded. Please upload a .pdf file.")
        return extract_pdf_content(data)

    elif source_type == "word":
        if data is None:
            raise ValueError("No Word file was uploaded. Please upload a .docx file.")
        return extract_word_content(data)

    elif source_type == "text":
        if data is None:
            raise ValueError("No text file was uploaded. Please upload a .txt file.")
        return extract_text_content(data)

    else:
        raise ValueError(
            f"Unsupported source type '{source_type}'. "
            "Supported types: youtube, pdf, word, text."
        )
