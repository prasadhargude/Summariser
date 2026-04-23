# 📚 StudyMate — Learn Anything

A free, AI-powered study tool that extracts content from YouTube videos, PDFs, Word documents, and text files — then generates summaries, smart notes, and interactive quizzes using Google Gemini 1.5 Flash.

## ✨ Features

- **Multi-Source Extraction** — YouTube transcripts, PDF, Word (.docx), and plain text files
- **AI Summary** — Structured academic summaries with key points and takeaways
- **Smart Notes** — Exam-ready study notes with concept tables and key definitions
- **Interactive Quiz** — MCQ and short-answer questions with instant grading
- **Export System** — Download study sheets as TXT, Markdown, or styled HTML
- **Session History** — Restore previous analyses from the sidebar
- **100% Free** — Uses Gemini 1.5 Flash free tier (15 req/min, 1M tokens/day)

## 🚀 Setup (5 Steps)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/studymate.git
cd studymate
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get a free Gemini API key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key — you'll paste it into the app sidebar

### 5. Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`. Paste your API key into the sidebar to unlock AI features.

## 📁 Project Structure

```
studymate/
├── app.py                     # Main Streamlit app
├── ai/
│   ├── __init__.py
│   ├── gemini_client.py       # Gemini 1.5 Flash REST API client
│   └── processors.py          # Summary, Notes, Q&A processors
├── extractors/
│   ├── __init__.py
│   ├── youtube_extractor.py   # YouTube transcript extraction
│   ├── pdf_extractor.py       # PDF text extraction (PyMuPDF)
│   ├── word_extractor.py      # Word .docx extraction
│   └── text_extractor.py      # Plain text file reader
├── utils/
│   ├── __init__.py
│   ├── file_handler.py        # Input routing
│   └── exporter.py            # TXT / MD / HTML export
├── requirements.txt
├── .env.example
└── README.md
```

## 🔑 API Key

StudyMate uses **Google Gemini 1.5 Flash** (free tier). No credit card required.

| Limit | Value |
|-------|-------|
| Requests per minute | 15 |
| Tokens per day | 1,000,000 |
| Cost | Free |

Get your key → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 📸 Screenshots

<!-- Add screenshots here -->
_Screenshots coming soon._

## 🛠 Tech Stack

- **Frontend:** Streamlit
- **AI Model:** Google Gemini 1.5 Flash (REST API)
- **PDF:** PyMuPDF (fitz)
- **Word:** python-docx
- **YouTube:** youtube-transcript-api
- **Python:** 3.9+

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

Built with ❤️ using Streamlit & Gemini
