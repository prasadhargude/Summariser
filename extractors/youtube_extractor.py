"""
YouTube Transcript Extractor
Fetches the transcript of a YouTube video given its URL.
Supports both youtube.com/watch?v= and youtu.be/ URL formats.
"""

import re
from youtube_transcript_api import YouTubeTranscriptApi


def _parse_video_id(url: str) -> str:
    """
    Extract the video ID from a YouTube URL.

    Handles:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - URLs with additional query parameters or timestamps

    Args:
        url: A YouTube video URL string.

    Returns:
        The 11-character video ID.

    Raises:
        ValueError: If the URL does not match any known YouTube format.
    """
    # Pattern for standard youtube.com/watch URLs
    standard_match = re.search(r"(?:youtube\.com/watch\?.*v=)([\w-]{11})", url)
    if standard_match:
        return standard_match.group(1)

    # Pattern for shortened youtu.be URLs
    short_match = re.search(r"(?:youtu\.be/)([\w-]{11})", url)
    if short_match:
        return short_match.group(1)

    raise ValueError(
        "Invalid YouTube URL. Please provide a link in the format "
        "'https://www.youtube.com/watch?v=...' or 'https://youtu.be/...'."
    )


def extract_youtube_transcript(url: str) -> dict:
    """
    Fetch the transcript for a YouTube video and return it as a
    standardised content dictionary.

    Args:
        url: A YouTube video URL.

    Returns:
        dict with keys: title, content, source_type, word_count.

    Raises:
        ValueError: On an invalid URL.
        RuntimeError: When the transcript cannot be retrieved.
    """
    # Step 1 — resolve the video ID from the URL
    video_id = _parse_video_id(url)

    # Step 2 — fetch transcript via the API (v1.x uses instance .fetch())
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
    except Exception as exc:
        raise RuntimeError(
            f"Could not retrieve transcript for video '{video_id}'. "
            "The video may not have captions enabled, or the ID may be incorrect. "
            f"Details: {exc}"
        ) from exc

    # Step 3 — join all snippet text segments into a single string
    full_text = " ".join(snippet.text for snippet in transcript.snippets)

    # Step 4 — compute word count
    word_count = len(full_text.split())

    return {
        "title": video_id,
        "content": full_text,
        "source_type": "youtube",
        "word_count": word_count,
    }
