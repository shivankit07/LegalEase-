import os
import json
import re
import base64
import tempfile
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ANALYSIS_PROMPT = """
You are LegalEase, an expert AI legal analyst helping ordinary middle-class people understand contracts.

Analyze the provided contract PDF and return ONLY a valid JSON object — no extra text, no markdown, no code fences.

Return this exact JSON structure:
{
  "risky_clauses": [
    {
      "title": "Short clause name",
      "detail": "Plain English explanation of why this is risky or unfair to the signer"
    }
  ],
  "safe_clauses": [
    {
      "title": "Short clause name",
      "detail": "Plain English explanation of why this clause is fair and protects the signer"
    }
  ],
  "hidden_traps": [
    {
      "title": "Short trap name",
      "detail": "Something buried most people would miss — auto-renewals, data sharing, penalty clauses, arbitration clauses, etc."
    }
  ],
  "financial_obligations": "Plain English summary of ALL the ways money can leave the signer's pocket — fees, penalties, deposits, repair costs, etc.",
  "exit_conditions": "Plain English explanation of how hard it is to get out of this contract — notice period, penalties, deposit return conditions.",
  "summary": "2-3 sentences explaining what this contract actually means for the person signing it. Write like a friend explaining it.",
  "verdict": "Sign",
  "verdict_reason": "One sentence explaining why you gave this verdict."
}

Rules:
- risky_clauses: 2-5 genuinely unfair or one-sided clauses
- safe_clauses: 2-4 fair clauses that protect the signer
- hidden_traps: 1-3 things buried in fine print most people miss
- verdict must be exactly one of: "Sign", "Negotiate", or "Avoid"
- No legal jargon. Write for someone with zero legal background.
- Return ONLY the JSON. Nothing else.
"""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'contract' not in request.files:
        return jsonify({'error': 'No file uploaded. Please select a PDF.'}), 400

    file = request.files['contract']

    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported.'}), 400

    try:
        pdf_bytes = file.read()

        if len(pdf_bytes) == 0:
            return jsonify({'error': 'The PDF file is empty. Please upload a real contract.'}), 400

        print(f"PDF received: {file.filename}, size: {len(pdf_bytes)} bytes")

        # Send as inline base64 — avoids File Upload API rate limits
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode('utf-8')

        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type='application/pdf',
                        data=pdf_b64
                    )
                ),
                types.Part(text=ANALYSIS_PROMPT)
            ]
        )

        print(f"Gemini response received")

        # Strip accidental markdown fences
        raw_text = response.text.strip()
        raw_text = re.sub(r'^```json\s*', '', raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r'^```\s*', '', raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r'\s*```$', '', raw_text.strip())

        result = json.loads(raw_text)
        return jsonify({'result': result})

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response was: {raw_text[:500]}")
        return jsonify({'error': 'Gemini returned an unexpected format. Please try again.'}), 500
    except Exception as e:
        print(f"FULL ERROR: {type(e).__name__}: {e}")
        error_msg = str(e)
        if 'API_KEY' in error_msg or 'invalid' in error_msg.lower() and 'key' in error_msg.lower():
            return jsonify({'error': 'Invalid Gemini API key. Check your .env file.'}), 500
        if 'quota' in error_msg.lower() or '429' in error_msg or 'rate' in error_msg.lower():
            return jsonify({'error': 'API rate limit hit. Please wait 60 seconds and try again.'}), 429
        return jsonify({'error': f'Analysis failed: {error_msg}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)