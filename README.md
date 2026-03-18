# 🧠 AI Study Notes Summarizer

A beautiful Streamlit web app that uses OpenAI to turn study notes into summaries, key points, important terms, quiz questions, and flashcards.

## 📁 Project Structure

```
ai-study-notes-summarizer/
├── app.py              # Main application (UI + AI logic)
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
├── .env                # Your actual API key (create this)
└── README.md           # This file
```

## 🚀 Quick Setup

### 1. Install dependencies

```bash
cd ai-study-notes-summarizer
pip install -r requirements.txt
```

### 2. Add your OpenAI API key

```bash
cp .env.example .env
```

Then edit `.env` and replace `your_openai_api_key_here` with your actual key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

### 3. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## ✨ Features

- **📝 Summary** — Concise, student-friendly note summaries
- **🎯 Key Points** — 5–7 bullet point takeaways
- **🔑 Important Terms** — 8–12 keywords with badge styling
- **❓ Quiz Questions** — 5 questions with reveal-able answers
- **🃏 Flashcards** — 5 flip cards for quick revision
- **📋 Copy Results** — Export all results as plain text

## 🛠️ Tech Stack

| Tech | Purpose |
|------|---------|
| Python | Backend logic |
| Streamlit | Web UI framework |
| OpenAI API | AI text generation (gpt-4o-mini) |
| python-dotenv | Environment variable management |

## 📝 Notes

- Requires a valid OpenAI API key (charges apply per usage)
- Uses `gpt-4o-mini` for fast, cost-effective responses
- Paste at least 100 words for best results
- Works with any subject — science, history, CS, and more

---

*Built for students using AI ❤️*
