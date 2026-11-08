#!/usr/bin/env python3
"""
engine/ai_script.py – High-Retention AI Script Generator for Faceless Shorts Engine.

Uses Groq API (openai/gpt-oss-120b / qwen/qwen3.8-27b) to generate viral,
retention-engineered 30-45s vertical video scripts formatted with visual
cues and word emphasis for Three.js WebGL and faster-whisper.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any

# Root paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_MODELS = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]


def get_groq_api_key() -> str:
    """Retrieve Groq API key from environment or .env file."""
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key.strip().strip("'\"")

    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GROQ_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    if val:
                        return val

    raise ValueError(
        "GROQ_API_KEY not found in environment or .env file. "
        "Please add GROQ_API_KEY='gsk_...' to your .env file."
    )


def build_system_prompt(language: str = "en", style: str = "deep-dive") -> str:
    """Construct prompt optimized for viral short-form retention."""
    lang_instruction = (
        "Write the script strictly in Bengali (বাংলা) language with natural colloquial phrasing suitable for viral video narration."
        if language in ("bn", "bangla")
        else "Write the script strictly in energetic, natural American English."
    )

    return f"""You are a master viral YouTube Shorts / TikTok director and scriptwriter.
{lang_instruction}

Generate a 30 to 40-second vertical video script about the user's topic for a 3D animated explainer (style: {style}).

CRITICAL RETENTION RULES:
1. Line 1 MUST be an irresistible Hook: an unexpected question, shocking myth, or jarring visual statement.
2. Lines 2-7 are the Body: punchy, fast-paced facts. Use vivid, physical action words that describe physical interactions (swallowing, sliding, melting, burning, colliding, floating).
3. Line 8-9 is the Twist/Climax or Seamless Loop: an eye-opening realization or punchy warning.
4. Total narration word count MUST be between 65 and 90 words (~30-35 seconds spoken time).
5. For EVERY line, produce:
   - "text": The clean spoken narration sentence without any special formatting.
   - "caps": The exact on-screen caption representation of that sentence.
     * Put an asterisk * directly before 1 or 2 high-impact words per phrase (e.g. *stomach, *acid, *melts).
     * Separate short 3-5 word screen cards using the pipe symbol | (e.g. "What *happens | if you *swallow | your *gum?").
     * The words in "caps" MUST match the spoken words in "text".

OUTPUT FORMAT:
Return ONLY a valid JSON object matching this schema without any markdown wrappers or commentary:
{{
  "title": "Short, punchy video title (max 6 words)",
  "voice": "am_michael",
  "speed": 1.0,
  "lead": 0.35,
  "outro": 1.0,
  "gap": 0.28,
  "music": "tension",
  "sources": [
    "Reputable source or study 1",
    "Reputable source or study 2"
  ],
  "lines": [
    {{
      "text": "What happens if you swallow your gum?",
      "caps": "What *happens | if you *swallow | your *gum?"
    }}
  ]
}}
"""


def generate_script(
    topic: str,
    style: str = "deep-dive",
    language: str = "en",
    voice: Optional[str] = None,
    music: str = "tension"
) -> Dict[str, Any]:
    """Call Groq API to generate an animated video script JSON."""
    api_key = get_groq_api_key()
    system_prompt = build_system_prompt(language=language, style=style)
    user_prompt = f"Topic: {topic}\nTarget Style: {style}"

    # Default voice based on language if not specified
    if not voice:
        voice = "bn-BD-PradeepNeural" if language in ("bn", "bangla") else "am_michael"

    last_error = None
    for model in DEFAULT_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "FacelessShortsEngine/1.0"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                script_json = json.loads(content)

                # Ensure required fields exist
                script_json["style"] = style
                script_json["voice"] = voice
                script_json["music"] = script_json.get("music", music)
                script_json.setdefault("speed", 1.0)
                script_json.setdefault("lead", 0.35)
                script_json.setdefault("outro", 1.0)
                script_json.setdefault("gap", 0.28)
                script_json.setdefault("sources", ["Scientific literature"])

                # Sanitize lines
                if "lines" not in script_json or not isinstance(script_json["lines"], list):
                    raise ValueError("Generated script missing 'lines' array")

                for line in script_json["lines"]:
                    if "text" not in line:
                        line["text"] = ""
                    if "caps" not in line:
                        # Auto-create caps if missing
                        words = line["text"].split()
                        line["caps"] = " ".join(f"*{w}" if i == 0 else w for i, w in enumerate(words))

                return script_json

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Failed to generate script across all Groq models. Error: {last_error}")


def save_script(script_data: Dict[str, Any], output_path: Path) -> Path:
    """Save script data to destination JSON file."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate AI script using Groq for Faceless Shorts Engine")
    parser.add_argument("--topic", required=True, help="Video topic / subject")
    parser.add_argument("--style", default="deep-dive", help="Animation style (deep-dive, tall-tale, inside-out, etc.)")
    parser.add_argument("--lang", default="en", choices=["en", "bn"], help="Language: en (English) or bn (Bengali)")
    parser.add_argument("--voice", default=None, help="TTS voice override")
    parser.add_argument("--music", default="tension", help="Background music mood (tension, dark, upbeat)")
    parser.add_argument("--out", default=None, help="Output script.json path")

    args = parser.parse_args()

    try:
        print(f"🤖 Generating viral {args.lang.upper()} script via Groq for: '{args.topic}'...")
        script = generate_script(
            topic=args.topic,
            style=args.style,
            language=args.lang,
            voice=args.voice,
            music=args.music
        )

        if args.out:
            dest = save_script(script, Path(args.out))
            print(f"✅ Successfully wrote script to: {dest}")
        else:
            print("\n" + json.dumps(script, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

