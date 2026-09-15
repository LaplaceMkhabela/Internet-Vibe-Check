"""Processor: transform raw YouTube comments into labeled sentiments via the Groq API.

Standard keyword matching struggles with internet slang and sarcasm, so we use a
high-speed LLM to evaluate the true meaning behind the text.
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from groq import Groq

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"
PAUSE_BETWEEN_CALLS = 0.5
RATE_LIMIT_BACKOFF = 0.8

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


def analyze_single_comment(client, comment, retries=3):
    """Analyze one comment, retrying on rate-limit errors, and return the parsed result."""
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": comment},
                ],
            )
            raw = response.choices[0].message.content
            parsed = parse_analysis(raw)
            if parsed is not None:
                return parsed
            raise ValueError(f"Malformed JSON from model: {raw!r}")
        except Exception as exc:
            if attempt >= retries:
                return {"comment": comment, "sentiment": "Neutral", "summary": "Analysis failed"}
            print(f"    ... retrying in {RATE_LIMIT_BACKOFF * (attempt + 1)}s after error: {exc}")
            time.sleep(RATE_LIMIT_BACKOFF * (attempt + 1))


def parse_analysis(raw):
    """Parse strict JSON from the model output, tolerating stray code fences."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    sentiment = data.get("sentiment")
    if sentiment not in {"Hyped", "Angry", "Amused", "Neutral"}:
        return None
    return {
        "sentiment": sentiment,
        "summary": data.get("summary", ""),
    }


def process_comments_batch(client, comments):
    """Iterate through comments, pass each to the Groq API with pauses to respect limits."""
    results = []
    for index, comment in enumerate(comments, start=1):
        print(f"[{index}/{len(comments)}] Analyzing: {comment[:60]!r}")
        results.append(analyze_single_comment(client, comment))
        if index < len(comments):
            time.sleep(PAUSE_BETWEEN_CALLS)
    return results


def main():
    client = get_client()
    comments = [
        input("Enter a comment to analyze: ").strip(),
        input("Enter another comment to analyze: ").strip(),
    ]
    for result in process_comments_batch(client, comments):
        print(result)


if __name__ == "__main__":
    main()