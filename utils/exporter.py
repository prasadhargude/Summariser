"""
Export System
Converts StudyMate AI output (summary, notes, Q&A) into
downloadable TXT, Markdown, and styled HTML formats.
"""

from datetime import datetime


def _qna_to_text(qna: list) -> str:
    """
    Render a list of Q&A dicts as plain text.

    Args:
        qna: List of question dicts from ContentProcessor.generate_qna().

    Returns:
        Formatted plain-text string.
    """
    if not qna:
        return "No quiz generated."

    lines = []
    for i, q in enumerate(qna, 1):
        lines.append(f"Q{i}: {q.get('question', '')}")
        q_type = q.get("type", "")
        if q_type == "mcq" and q.get("options"):
            for opt in q["options"]:
                lines.append(f"   {opt}")
        lines.append(f"Answer: {q.get('correct_answer', '')}")
        lines.append(f"Explanation: {q.get('explanation', '')}")
        lines.append("")
    return "\n".join(lines)


def _qna_to_md(qna: list) -> str:
    """
    Render a list of Q&A dicts as Markdown.

    Args:
        qna: List of question dicts.

    Returns:
        Formatted Markdown string.
    """
    if not qna:
        return "_No quiz generated._"

    lines = []
    for i, q in enumerate(qna, 1):
        q_type = q.get("type", "mcq")
        badge = "🔵 MCQ" if q_type == "mcq" else "✏️ Short Answer"
        lines.append(f"### Q{i} — {badge}")
        lines.append(f"**{q.get('question', '')}**")
        if q_type == "mcq" and q.get("options"):
            lines.append("")
            for opt in q["options"]:
                lines.append(f"- {opt}")
        lines.append("")
        lines.append(f"> ✅ **Answer:** {q.get('correct_answer', '')}")
        lines.append(f"> 💬 **Explanation:** {q.get('explanation', '')}")
        lines.append("")
    return "\n".join(lines)


def _qna_to_html(qna: list) -> str:
    """
    Render a list of Q&A dicts as styled HTML rows.

    Args:
        qna: List of question dicts.

    Returns:
        HTML fragment string.
    """
    if not qna:
        return "<p><em>No quiz generated.</em></p>"

    rows = []
    for i, q in enumerate(qna, 1):
        q_type = q.get("type", "mcq")
        badge_color = "#3b82f6" if q_type == "mcq" else "#8b5cf6"
        badge_label = "MCQ" if q_type == "mcq" else "Short Answer"

        opts_html = ""
        if q_type == "mcq" and q.get("options"):
            opts = "".join(
                f'<li style="margin:2px 0;color:#475569;">{opt}</li>'
                for opt in q["options"]
            )
            opts_html = f'<ul style="margin:6px 0 8px 18px;padding:0;">{opts}</ul>'

        rows.append(
            f'<div style="background:#f8fafc;border:1px solid #e2e8f0;'
            f'border-radius:10px;padding:16px;margin-bottom:14px;">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
            f'<span style="background:#667eea;color:#fff;border-radius:20px;'
            f'padding:2px 10px;font-size:12px;font-weight:700;">Q{i}</span>'
            f'<span style="background:{badge_color};color:#fff;border-radius:20px;'
            f'padding:2px 10px;font-size:11px;">{badge_label}</span>'
            f'</div>'
            f'<p style="font-weight:600;color:#1e293b;margin:0 0 6px 0;">'
            f'{q.get("question", "")}</p>'
            f'{opts_html}'
            f'<div style="background:#dcfce7;border-left:3px solid #16a34a;'
            f'padding:8px 12px;border-radius:0 6px 6px 0;margin-top:8px;">'
            f'<strong style="color:#15803d;">✅ Answer:</strong> '
            f'<span style="color:#166534;">{q.get("correct_answer", "")}</span>'
            f'</div>'
            f'<div style="background:#eff6ff;border-left:3px solid #3b82f6;'
            f'padding:8px 12px;border-radius:0 6px 6px 0;margin-top:6px;">'
            f'<strong style="color:#1d4ed8;">💬 Explanation:</strong> '
            f'<span style="color:#1e3a5f;">{q.get("explanation", "")}</span>'
            f'</div>'
            f'</div>'
        )
    return "\n".join(rows)


# ── Public export functions ───────────────────────────────────────────

def export_to_txt(title: str, summary: str, notes: str, qna: list) -> bytes:
    """
    Export all AI-generated content as plain UTF-8 text.

    Args:
        title:   Document/source title.
        summary: Summary markdown string.
        notes:   Notes markdown string.
        qna:     List of question dicts.

    Returns:
        UTF-8 encoded bytes suitable for st.download_button.
    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = [
        f"STUDYMATE STUDY SHEET",
        f"{'=' * 60}",
        f"Title   : {title}",
        f"Generated: {date_str}",
        f"{'=' * 60}",
        "",
        "SUMMARY",
        "-" * 40,
        summary,
        "",
        "STUDY NOTES",
        "-" * 40,
        notes,
        "",
        "QUIZ",
        "-" * 40,
        _qna_to_text(qna),
    ]
    return "\n".join(sections).encode("utf-8")


def export_to_md(title: str, summary: str, notes: str, qna: list) -> bytes:
    """
    Export all AI-generated content as formatted Markdown.

    Args:
        title:   Document/source title.
        summary: Summary markdown string.
        notes:   Notes markdown string.
        qna:     List of question dicts.

    Returns:
        UTF-8 encoded bytes.
    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = [
        f"# 📚 StudyMate — Study Sheet",
        f"",
        f"**Source:** {title}  ",
        f"**Generated:** {date_str}",
        f"",
        f"---",
        f"",
        f"## 📋 Summary",
        f"",
        summary,
        f"",
        f"---",
        f"",
        f"## 📝 Smart Notes",
        f"",
        notes,
        f"",
        f"---",
        f"",
        f"## 🎯 Quiz",
        f"",
        _qna_to_md(qna),
    ]
    return "\n".join(sections).encode("utf-8")


def export_to_pdf_html(title: str, summary: str, notes: str, qna: list) -> str:
    """
    Generate a fully self-contained, print-ready HTML study sheet
    styled with inline CSS.

    Args:
        title:   Document/source title.
        summary: Summary markdown string (rendered as plain text inside HTML).
        notes:   Notes markdown string.
        qna:     List of question dicts.

    Returns:
        HTML string ready to be downloaded and opened in a browser.
    """
    date_str = datetime.now().strftime("%B %d, %Y at %H:%M")

    # Convert basic markdown to HTML for summary and notes
    def md_to_simple_html(text: str) -> str:
        """Very lightweight markdown → HTML for common patterns."""
        import re as _re
        # Headers
        text = _re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=_re.MULTILINE)
        text = _re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=_re.MULTILINE)
        # Bold
        text = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic
        text = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Blockquote
        text = _re.sub(
            r"^> (.+)$",
            r'<blockquote style="border-left:4px solid #667eea;padding:8px 16px;'
            r'color:#4b5563;background:#f0f4ff;border-radius:0 8px 8px 0;margin:8px 0;">\1</blockquote>',
            text,
            flags=_re.MULTILINE,
        )
        # Bullet lists: convert runs of "- …" lines
        text = _re.sub(r"^- (.+)$", r"<li>\1</li>", text, flags=_re.MULTILINE)
        text = _re.sub(r"(<li>.*?</li>\n?)+", r"<ul>\g<0></ul>", text, flags=_re.DOTALL)
        # Line breaks for remaining plain lines
        text = text.replace("\n\n", "</p><p>")
        text = f"<p>{text}</p>"
        return text

    summary_html = md_to_simple_html(summary)
    notes_html = md_to_simple_html(notes)
    qna_html = _qna_to_html(qna)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>StudyMate — {title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: #f1f5f9;
      color: #1e293b;
      padding: 32px 16px;
    }}
    .container {{ max-width: 860px; margin: 0 auto; }}
    .hero {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
      border-radius: 16px;
      padding: 32px;
      margin-bottom: 28px;
      text-align: center;
    }}
    .hero .logo {{ font-size: 48px; margin-bottom: 8px; }}
    .hero h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
    .hero .meta {{ font-size: 14px; opacity: 0.85; margin-top: 8px; }}
    .section {{
      background: #fff;
      border-radius: 14px;
      padding: 28px;
      margin-bottom: 24px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    .section-title {{
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 18px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e2e8f0;
      color: #1e293b;
    }}
    h2 {{ font-size: 17px; color: #4338ca; margin: 18px 0 8px; }}
    h3 {{ font-size: 15px; color: #6d28d9; margin: 14px 0 6px; }}
    p {{ line-height: 1.7; color: #374151; margin: 8px 0; }}
    ul {{ padding-left: 22px; margin: 8px 0; }}
    li {{ line-height: 1.7; color: #374151; margin: 3px 0; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 14px;
    }}
    th {{
      background: #667eea;
      color: #fff;
      padding: 10px 14px;
      text-align: left;
    }}
    td {{
      padding: 9px 14px;
      border-bottom: 1px solid #e2e8f0;
    }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    strong {{ color: #1e293b; }}
    .footer {{
      text-align: center;
      font-size: 13px;
      color: #94a3b8;
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #e2e8f0;
    }}
    @media print {{
      body {{ background: #fff; }}
      .section {{ box-shadow: none; border: 1px solid #e2e8f0; }}
    }}
  </style>
</head>
<body>
<div class="container">

  <div class="hero">
    <div class="logo">📚</div>
    <h1>StudyMate — Study Sheet</h1>
    <div><strong>{title}</strong></div>
    <div class="meta">Generated on {date_str}</div>
  </div>

  <div class="section">
    <div class="section-title">📋 Summary</div>
    {summary_html}
  </div>

  <div class="section">
    <div class="section-title">📝 Smart Notes</div>
    {notes_html}
  </div>

  <div class="section">
    <div class="section-title">🎯 Quiz</div>
    {qna_html}
  </div>

  <div class="footer">
    Generated by StudyMate v1.0.0 &nbsp;·&nbsp; Powered by Gemini 1.5 Flash &nbsp;·&nbsp; Built with ❤️ using Streamlit
  </div>

</div>
</body>
</html>"""
