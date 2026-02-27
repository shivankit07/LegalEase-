
# ⚖️ LegalEase — Your Free AI Lawyer

LegalEase is a free AI-powered tool that reads any legal contract and tells ordinary people exactly what they're agreeing to — in plain simple language.

Built for **TerraCode Convergence Hackathon 2025**.

---

## 🌐 What It Does

**Web App** — Upload any PDF contract and get:
- ⚠️ Risky clauses
- ✅ Safe clauses
- 🕵️ Hidden traps
- 💰 Financial obligations
- 🚪 Exit conditions
- 📝 Plain English summary
- 💡 Verdict: Sign / Negotiate / Avoid

**Telegram Bot (@VakilAI_Bot)** — Two roles:
1. Quick legal Q&A — just type any legal question, no PDF needed
2. Multilingual — auto-detects Hindi, Tamil, Telugu, Bengali, English and replies in your language

---

## 🛠️ Tech Stack

- **Backend:** Python + Flask
- **AI:** Google Gemini 2.5 Flash (reads PDFs natively)
- **Bot:** python-telegram-bot
- **Frontend:** HTML + CSS (glassmorphism UI)

---

## 🚀 Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/legalease.git
cd legalease
```

### 2. Create virtual environment
```bash
# Use Python 3.10 or 3.11
python -m venv venv

# Activate — Windows:
venv\Scripts\activate
# Activate — Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API keys
Create a `.env` file in the root folder:
```
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
```

- Get Gemini API key free at: https://aistudio.google.com
- Get Telegram token from: @BotFather on Telegram

### 5. Run the web app
```bash
python app.py
```
Visit: http://localhost:5000

### 6. Run the Telegram bot (separate terminal)
```bash
python bot.py
```

---

## 📁 Project Structure

```
legalease/
├── app.py              ← Flask web backend
├── bot.py              ← Telegram bot
├── requirements.txt    ← Python dependencies
├── .env                ← API keys (never commit this!)
├── templates/
│   └── index.html      ← Web app frontend
├── static/
│   └── style.css       ← Styles
└── uploads/            ← Temp upload folder
```

---

## ⚠️ Important Notes

- Use `google-genai` package (NOT `google-generativeai` — that is deprecated)
- Gemini model: `models/gemini-2.5-flash` (free tier — 20 requests/day)
- Never commit your `.env` file — add it to `.gitignore`
- Bot and web app run independently — both need to be running at the same time

---

## 🌍 Supported Languages

Hindi · Tamil · Telugu · Bengali · English

The bot auto-detects your language and replies in the same one.

---

## 💡 The Problem We Solve

- 4 billion people worldwide cannot afford a lawyer
- People sign rental agreements, job contracts, loan documents they don't understand
- Legal help in India costs ₹5,000–₹50,000/hour

**LegalEase gives everyone a free lawyer in their pocket.**
=======
# LegalEase-

