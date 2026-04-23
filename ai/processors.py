"""
AI Content Processors
High-level functions that use GeminiClient to generate structured
summaries, study notes, and Q&A quizzes from extracted content.
"""

import json
import re

from ai.gemini_client import AIClient


def _truncate_at_sentence(text: str, max_chars: int = 12000) -> str:
    """
    Truncate text to approximately *max_chars* characters, cutting at
    the last sentence boundary rather than mid-word.

    Args:
        text:      The original text.
        max_chars: Target maximum character count.

    Returns:
        The (possibly shortened) text.
    """
    if len(text) <= max_chars:
        return text

    chunk = text[: max_chars + 200]

    for i in range(min(len(chunk) - 1, max_chars + 199), max_chars - 200, -1):
        if chunk[i] in ".!?" and (
            i + 1 >= len(chunk) or chunk[i + 1] in (" ", "\n")
        ):
            return chunk[: i + 1]

    space_idx = text.rfind(" ", 0, max_chars)
    if space_idx > 0:
        return text[:space_idx]

    return text[:max_chars]


def _extract_json(raw: str) -> dict:
    """
    Robustly parse a JSON object from a raw string that may contain
    leading/trailing markdown fences or whitespace.

    Args:
        raw: Raw string from the model.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If no valid JSON object is found.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find the first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from model response: {cleaned[:300]}")


class ContentProcessor:
    """
    Orchestrates AI analysis tasks (summary, notes, Q&A) by combining
    prompt templates with the AIClient.
    """

    def __init__(self, client: AIClient) -> None:
        """
        Args:
            client: An initialised AIClient instance.
        """
        self._client = client

    # ── Summary ──────────────────────────────────────────────────────

    def summarize(self, content: str, source_type: str) -> dict:
        """
        Generate a comprehensive, detailed academic summary of the content.

        Args:
            content:     The raw extracted text.
            source_type: One of youtube, pdf, word, text.

        Returns:
            dict with keys: summary (str), token_estimate (int).
        """
        trimmed = _truncate_at_sentence(content)

        prompt = (
            f"You are an expert academic summarizer and educator. "
            f"Analyze the following {source_type} content THOROUGHLY and produce "
            "a comprehensive, detailed summary that covers EVERY major topic and subtopic. "
            "Do not skip any important information.\n\n"
            f"Content:\n{trimmed}\n\n"
            "Respond in this exact format:\n\n"
            "## 📌 Overview\n"
            "[4-6 sentence comprehensive high-level summary covering the main thesis, "
            "scope, and significance of the content]\n\n"
            "## 📑 Topic-by-Topic Breakdown\n"
            "[For EACH major topic/section found in the content, create a subsection like this:]\n"
            "### [Topic Name]\n"
            "[3-5 sentence detailed explanation of this topic, including key arguments, "
            "evidence, and conclusions]\n\n"
            "[Repeat for ALL topics — do not limit yourself to just 2-3 topics. "
            "Cover everything discussed in the content.]\n\n"
            "## 🔑 Key Points & Arguments\n"
            "- **[Point 1 title]**: [2-3 sentence detailed explanation]\n"
            "- **[Point 2 title]**: [2-3 sentence detailed explanation]\n"
            "- **[Point 3 title]**: [2-3 sentence detailed explanation]\n"
            "- [Continue for ALL key points — aim for at least 8-10 points]\n\n"
            "## 📊 Important Data, Facts & Figures\n"
            "- [Any statistics, dates, numbers, percentages, or measurable data mentioned]\n"
            "- [List ALL data points found in the content]\n\n"
            "## 🔗 Connections & Relationships\n"
            "[Explain how the different topics relate to each other. "
            "What cause-effect relationships exist? What are the dependencies?]\n\n"
            "## 💡 Critical Takeaways\n"
            "[5-7 sentences on the most important lessons, conclusions, and implications. "
            "What should the reader absolutely remember?]\n\n"
            "## 📖 Study Recommendations\n"
            "- **Deep study areas**: [Topics that need careful attention]\n"
            "- **Quick review areas**: [Topics that are straightforward]\n"
            "- **Further reading**: [What related topics should be explored next]"
        )

        summary_text = self._client.generate(prompt, max_tokens=4096)
        token_estimate = int(len(trimmed.split()) * 0.75)

        return {
            "summary": summary_text,
            "token_estimate": token_estimate,
        }

    # ── Smart Notes ──────────────────────────────────────────────────

    def generate_notes(self, content: str, source_type: str) -> dict:
        """
        Generate comprehensive, exam-ready study notes covering ALL topics.

        Args:
            content:     The raw extracted text.
            source_type: One of youtube, pdf, word, text.

        Returns:
            dict with key: notes (str).
        """
        trimmed = _truncate_at_sentence(content)

        prompt = (
            f"You are an expert professor creating comprehensive study notes for students "
            f"from the following {source_type} content. "
            "Your notes must cover EVERY topic and subtopic thoroughly — "
            "students should be able to study ONLY from these notes and pass an exam.\n\n"
            f"Content:\n{trimmed}\n\n"
            "Create detailed study notes in this exact format:\n\n"
            "# 📚 Study Notes: [Infer the main subject/title]\n\n"
            "---\n\n"
            "[For EACH topic/section in the content, create a complete section like this:]\n\n"
            "## 📖 [Topic 1 Name]\n\n"
            "### What is it?\n"
            "[Clear 2-4 sentence explanation of this topic in simple language]\n\n"
            "### Key Concepts\n"
            "| Concept | Explanation | Why It Matters |\n"
            "|---------|-------------|----------------|\n"
            "| [Term 1] | [Clear definition] | [Practical importance] |\n"
            "| [Term 2] | [Clear definition] | [Practical importance] |\n"
            "[Include ALL relevant concepts — do not limit the table rows]\n\n"
            "### Detailed Explanation\n"
            "[Thorough 4-8 sentence explanation with examples. "
            "Explain the how and why, not just the what. "
            "Include any formulas, processes, or step-by-step procedures.]\n\n"
            "### Important Points to Remember\n"
            "- ⭐ [Critical point 1 — something likely to appear on an exam]\n"
            "- ⭐ [Critical point 2]\n"
            "- ⭐ [Critical point 3]\n"
            "[List ALL important points]\n\n"
            "### Examples\n"
            "- 💡 [Concrete example or real-world application]\n"
            "- 💡 [Another example]\n\n"
            "---\n\n"
            "[REPEAT the above structure for EVERY topic found in the content. "
            "Do NOT skip any topics. Each topic deserves its own full section.]\n\n"
            "---\n\n"
            "## 📊 Key Data & Figures\n"
            "| Data Point | Value | Context |\n"
            "|-----------|-------|----------|\n"
            "| [Statistic/Date/Number] | [Value] | [Why it matters] |\n"
            "[List ALL numerical data, dates, statistics from the content]\n\n"
            "## 🔗 How Topics Connect\n"
            "[Explain the relationships between the different topics. "
            "Draw connections, show cause-and-effect chains, explain dependencies.]\n\n"
            "## ⚠️ Common Mistakes & Misconceptions\n"
            "- ❌ [Common mistake 1] → ✅ [Correct understanding]\n"
            "- ❌ [Common mistake 2] → ✅ [Correct understanding]\n\n"
            "## 🧠 Quick Revision Checklist\n"
            "- [ ] [Can you explain Topic 1?]\n"
            "- [ ] [Do you know the key terms?]\n"
            "- [ ] [Can you give examples?]\n"
            "[Create a checklist covering ALL topics]\n\n"
            "## 💡 Memory Aids & Mnemonics\n"
            "[Create 2-3 memory tricks, acronyms, or visual associations to help "
            "remember the most important concepts]\n\n"
            "## ⚡ The 5 Most Important Things to Remember\n"
            "1. [Most critical takeaway]\n"
            "2. [Second most critical]\n"
            "3. [Third]\n"
            "4. [Fourth]\n"
            "5. [Fifth]"
        )

        notes_text = self._client.generate(prompt, max_tokens=4096)

        return {"notes": notes_text}

    # ── Q&A Generator ────────────────────────────────────────────────

    def generate_qna(
        self,
        content: str,
        source_type: str,
        difficulty: str = "Mixed",
        num_questions: int = 5,
    ) -> dict:
        """
        Generate an interactive quiz with mixed MCQ and short-answer
        questions based on the content.

        Args:
            content:       The raw extracted text.
            source_type:   One of youtube, pdf, word, text.
            difficulty:    "Easy", "Medium", "Hard", or "Mixed".
            num_questions: 5, 10, or 15.

        Returns:
            dict with keys: qna (list[dict]), quiz_title (str).

        Raises:
            RuntimeError: If JSON cannot be parsed after one retry.
        """
        trimmed = _truncate_at_sentence(content)

        def _build_prompt(extra_instruction: str = "") -> str:
            """Build the quiz prompt, optionally with an extra JSON reminder."""
            return (
                f"You are an expert educator creating a quiz based on {source_type} content. "
                f"Generate exactly {num_questions} {difficulty}-level questions with detailed answers.\n\n"
                f"Content:\n{trimmed}\n\n"
                f"{extra_instruction}"
                'Respond ONLY in this exact JSON format (no markdown, no extra text):\n'
                "{\n"
                '  "quiz_title": "Quiz on [topic]",\n'
                f'  "difficulty": "{difficulty}",\n'
                '  "questions": [\n'
                '    {\n'
                '      "id": 1,\n'
                '      "question": "Question text here?",\n'
                '      "type": "mcq",\n'
                '      "options": ["A) option1", "B) option2", "C) option3", "D) option4"],\n'
                '      "correct_answer": "A) option1",\n'
                '      "explanation": "Explanation of why this is correct"\n'
                "    },\n"
                "    {\n"
                '      "id": 2,\n'
                '      "question": "Question text here?",\n'
                '      "type": "short_answer",\n'
                '      "options": [],\n'
                '      "correct_answer": "Detailed answer here",\n'
                '      "explanation": "Why this is the correct answer"\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Mix MCQ and short_answer types. Make questions test understanding, not just memory."
            )

        # First attempt
        raw = self._client.generate(_build_prompt(), max_tokens=4096)

        try:
            data = _extract_json(raw)
        except ValueError:
            # Retry once with an explicit JSON-only reminder
            raw = self._client.generate(
                _build_prompt(
                    extra_instruction=(
                        "IMPORTANT: Your response must be ONLY valid JSON. "
                        "Do NOT include any markdown, code fences, or explanatory text.\n\n"
                    )
                ),
                max_tokens=4096,
            )
            try:
                data = _extract_json(raw)
            except ValueError as exc:
                raise RuntimeError(
                    "Gemini returned malformed JSON for the quiz after two attempts. "
                    f"Details: {exc}"
                ) from exc

        questions = data.get("questions", [])
        quiz_title = data.get("quiz_title", "StudyMate Quiz")

        return {
            "qna": questions,
            "quiz_title": quiz_title,
        }
