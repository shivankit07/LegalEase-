import os
import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL = "models/gemini-2.5-flash"

# Thread pool to run Gemini calls outside async event loop (fixes Windows conflict)
executor = ThreadPoolExecutor(max_workers=3)

# ── Prompts ───────────────────────────────────────────────

CONTRACT_PROMPT = """
You are VakilAI, a free AI legal assistant helping ordinary middle-class people understand contracts.

Analyze the contract PDF and reply using these sections with emojis.
Detect the language from any user message and reply in that same language. Default to English.

⚖️ CONTRACT TYPE
[One line: what type of contract this is]

⚠️ RISKY CLAUSES
[List each risky clause on a new line. Explain simply why it's risky.]

✅ SAFE CLAUSES
[List fair clauses that protect the signer.]

🕵️ HIDDEN TRAPS
[Buried fine print — auto-renewals, data sharing, arbitration, penalty clauses most people miss.]

💰 FINANCIAL OBLIGATIONS
[Every way money leaves the signer's pocket — fees, penalties, deposits, repair costs, hidden charges.]

🚪 HOW TO EXIT
[Notice period required, penalties for leaving early, deposit return conditions.]

📝 PLAIN ENGLISH SUMMARY
[2-3 sentences. Write like a friend explaining it.]

💡 VERDICT: [Sign / Negotiate / Avoid]
[One sentence reason.]

Rules:
- Simple language only. Zero legal jargon.
- Be specific — use actual details from the document.
- Keep total response under 4000 characters.
"""

QA_PROMPT = """
You are VakilAI, a free AI legal assistant helping ordinary middle-class people with legal questions.

Rules:
- Detect the language the user wrote in and reply in that SAME language
- Give a clear, practical, useful answer in simple language
- Zero legal jargon
- If relevant to India, mention Indian law context
- End with one practical tip
- Never say "consult a lawyer" as your ONLY answer — give real useful info first
- Keep response under 2500 characters

User question:
"""

# ── Gemini calls (run in thread pool, not async) ──────────

def gemini_analyze_pdf(pdf_bytes: bytes, lang_hint: str = "") -> str:
    prompt = CONTRACT_PROMPT
    if lang_hint:
        prompt += f"\n\nUser wrote: '{lang_hint}' — detect and reply in that language."

    response = gemini.models.generate_content(
        model=MODEL,
        contents=[
            types.Part(
                inline_data=types.Blob(
                    mime_type='application/pdf',
                    data=base64.standard_b64encode(pdf_bytes).decode()
                )
            ),
            types.Part(text=prompt)
        ]
    )
    return response.text.strip()


def gemini_answer_question(question: str) -> str:
    response = gemini.models.generate_content(
        model=MODEL,
        contents=[QA_PROMPT + question]
    )
    return response.text.strip()


async def run_in_thread(func, *args):
    """Run a blocking function in thread pool so it doesn't block async bot."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)


# ── Message chunker ───────────────────────────────────────

def chunk_message(text: str, limit: int = 4000) -> list:
    if len(text) <= limit:
        return [text]
    parts = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        cut = text.rfind('\n', 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].strip()
    return parts


async def send_long(update: Update, text: str):
    for chunk in chunk_message(text):
        await update.message.reply_text(chunk)


# ── Command Handlers ──────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "there"
    msg = f"""⚖️ *Hey {name}! Welcome to VakilAI* — your free AI lawyer.

Most people sign contracts they don't understand. Rental agreements with hidden traps. Job offers with unfair clauses. Loan documents with buried penalties.

*I read them for you — in seconds, for free.*

━━━━━━━━━━━━━━━
🔍 *What I can do:*

📄 *Analyze any contract PDF*
Send me a PDF and I'll break it down:
  • ⚠️ Risky clauses
  • ✅ Safe clauses
  • 🕵️ Hidden traps
  • 💰 Financial obligations
  • 🚪 How to exit
  • 💡 Verdict: Sign / Negotiate / Avoid

💬 *Answer legal questions*
Just type your question — no PDF needed.

🌍 *Multilingual*
Hindi, Tamil, Telugu, Bengali, or English — I reply in your language automatically.

━━━━━━━━━━━━━━━
*Send a PDF or ask any legal question to get started!*

Type /help to see all commands."""

    await update.message.reply_text(msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """📖 *How to use VakilAI*

━━━━━━━━━━━━━━━
📄 *Analyze a contract:*
Send any PDF file directly in this chat.

Works with:
  • Rental / lease agreements
  • Job offer letters
  • Loan documents
  • Freelance contracts
  • NDAs & Terms of Service

━━━━━━━━━━━━━━━
💬 *Ask a legal question:*
Just type and send — no PDF needed.

Examples:
  • "Can my landlord keep my deposit?"
  • "What is a non-compete clause?"
  • "मेरा मकान मालिक किराया बढ़ा सकता है?"

━━━━━━━━━━━━━━━
📋 *Commands:*
/start — Welcome message
/help — This guide
/analyze — Upload tips
/languages — Supported languages
/about — About this project"""

    await update.message.reply_text(msg, parse_mode='Markdown')


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """📄 *Tips for best results*

━━━━━━━━━━━━━━━
✅ *Works great with:*
  • Text-based PDFs (typed documents)
  • Rental & lease agreements
  • Employment contracts
  • Loan & finance documents
  • Terms of Service

⚠️ *May struggle with:*
  • Scanned / photographed PDFs
  • Password-protected files
  • Files over 10MB

💡 *Pro tip:* Add a caption in your language when sending the PDF — I'll reply in that language!

*Ready? Send your PDF now!* 📎"""

    await update.message.reply_text(msg, parse_mode='Markdown')


async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """🌍 *Supported Languages*

I auto-detect your language and reply in it:

🇬🇧 English
🇮🇳 Hindi — हिंदी
🇮🇳 Tamil — தமிழ்
🇮🇳 Telugu — తెలుగు
🇮🇳 Bengali — বাংলা

━━━━━━━━━━━━━━━
Just write in your language — no settings needed.

Example:
"क्या मैं बिना नोटिस के नौकरी छोड़ सकता हूँ?"
→ I'll reply in Hindi automatically."""

    await update.message.reply_text(msg, parse_mode='Markdown')


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """⚖️ *About VakilAI*

━━━━━━━━━━━━━━━
*The problem:*
4 billion people can't afford a lawyer.
In India, legal help costs ₹5,000–₹50,000/hour.

People sign rental agreements, job contracts, and loan documents they don't understand — predatory clauses trap them.

━━━━━━━━━━━━━━━
*The solution:*
VakilAI gives everyone a free lawyer in their pocket.

Upload any contract → full analysis in seconds → know exactly what you're agreeing to.

━━━━━━━━━━━━━━━
🤖 Powered by Google Gemini AI
🌐 Web app also available at legalease.com
🆓 Completely free

Built for *TerraCode Convergence Hackathon 2025*"""

    await update.message.reply_text(msg, parse_mode='Markdown')


# ── Message Handlers ──────────────────────────────────────

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not (doc.mime_type == 'application/pdf' or doc.file_name.lower().endswith('.pdf')):
        await update.message.reply_text("⚠️ Please send a *PDF* file only.", parse_mode='Markdown')
        return

    if doc.file_size > 10 * 1024 * 1024:
        await update.message.reply_text("⚠️ File too large. Please send a PDF under 10MB.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    status = await update.message.reply_text("📄 Got your contract!\n\n🔍 Analyzing every clause...\n⏳ About 15 seconds.")

    try:
        file = await context.bot.get_file(doc.file_id)
        pdf_bytes = bytes(await file.download_as_bytearray())
        lang_hint = update.message.caption or ""

        # Run Gemini in thread pool — fixes Windows async conflict
        result = await run_in_thread(gemini_analyze_pdf, pdf_bytes, lang_hint)

        await status.delete()
        await send_long(update, result)

    except Exception as e:
        await status.delete()
        err = str(e)
        print(f"PDF error: {type(e).__name__}: {e}")
        if '429' in err or 'quota' in err.lower():
            await update.message.reply_text("⚠️ Too many requests. Please wait 60 seconds and try again.")
        else:
            await update.message.reply_text("❌ Something went wrong analyzing this PDF. Please try again.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()

    if len(question) < 3:
        await update.message.reply_text("Ask me any legal question or send a PDF! ⚖️")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # Run Gemini in thread pool — fixes Windows async conflict
        answer = await run_in_thread(gemini_answer_question, question)
        await send_long(update, answer)

    except Exception as e:
        print(f"Q&A error: {type(e).__name__}: {e}")
        err = str(e)
        if '429' in err or 'quota' in err.lower():
            await update.message.reply_text("⚠️ Too many requests. Please wait 60 seconds and try again.")
        else:
            await update.message.reply_text("❌ Something went wrong. Please try again.")


# ── Setup & Main ──────────────────────────────────────────

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Welcome & feature overview"),
        BotCommand("help", "How to use VakilAI"),
        BotCommand("analyze", "Tips for uploading contracts"),
        BotCommand("languages", "Supported languages"),
        BotCommand("about", "About this project"),
    ])


def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_TOKEN not set in .env")
        return

    print("⚖️  VakilAI Bot starting...")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("languages", languages_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
