"""
Plain-Text File Extractor
Reads the content of an uploaded .txt file and returns it in the
standardised content dictionary format.
"""


def extract_text_content(uploaded_file) -> dict:
    """
    Read all text from an uploaded .txt file.

    Args:
        uploaded_file: A Streamlit UploadedFile object for a .txt file.

    Returns:
        dict with keys: title, content, source_type, word_count.

    Raises:
        RuntimeError: If the file cannot be decoded or is empty.
    """
    filename = getattr(uploaded_file, "name", "unknown.txt")

    try:
        raw_bytes = uploaded_file.read()
        # Attempt UTF-8 first, fall back to latin-1 for broader compat
        try:
            full_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            full_text = raw_bytes.decode("latin-1")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to read text file '{filename}'. Details: {exc}"
        ) from exc

    # Edge case: completely empty file
    if not full_text.strip():
        raise RuntimeError(
            f"The file '{filename}' is empty — there is no text to extract."
        )

    word_count = len(full_text.split())

    return {
        "title": filename,
        "content": full_text,
        "source_type": "text",
        "word_count": word_count,
    }
