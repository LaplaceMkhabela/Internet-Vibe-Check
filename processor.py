"""Processor: transform raw YouTube comments into labeled sentiments via the Groq API.

Standard keyword matching struggles with internet slang and sarcasm, so we use a
high-speed LLM to evaluate the true meaning behind the text.
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """\
You are a sentiment analyst who deeply understands internet culture, slang, memes,
and sarcasm in YouTube comments. Your job is to evaluate the TRUE meaning behind
the text, not just match keywords.

Analyze the provided comment and return STRICT JSON only, in this exact shape:
{"sentiment": "Hyped|Angry|Amused|Neutral", "summary": "..."}

Rules:
- "sentiment" MUST be exactly one of: "Hyped", "Angry", "Amused", or "Neutral".
- "summary" is a short one-sentence, plain-language recap of what the comment
  actually means.
- Output ONLY the JSON object. No markdown, no code fences, no extra text.
"""


def get_client():
    """Build and return the Groq client using the configured API key."""
    return Groq(api_key=GROQ_API_KEY)


def analyze_single_comment(client, comment):
    """Analyze one comment and return the raw model output text."""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": comment},
        ],
    )
    return response.choices[0].message.content


def main():
    client = get_client()
    text = input("Enter a comment to analyze: ").strip()
    raw = analyze_single_comment(client, text)
    print(raw)


if __name__ == "__main__":
    main()