"""
script_writer.py – Template-based script generator for Faceless AI Shorts.

Splits a user-supplied topic into narrative scenes sized to fit the target
duration.  No LLM required – all logic is deterministic.
"""

from __future__ import annotations

import json
import math
import os
import re
import textwrap
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORDS_PER_SECOND = 2.5  # average narration pace
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Scene-type labels used by downstream modules (scene_composer, sfx_mixer)
SCENE_TYPES = {
    "hook": "hook",
    "body": "body",
    "climax": "climax",
    "cta": "cta",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_template(style: str) -> dict:
    """Load a style template JSON from the templates/ directory."""
    path = TEMPLATES_DIR / f"{style}.json"
    if not path.exists():
        available = [p.stem for p in TEMPLATES_DIR.glob("*.json")]
        raise FileNotFoundError(
            f"Template '{style}' not found. Available: {available}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    """Pull visually-relevant keywords from a sentence for image prompts."""
    # Simple heuristic: take the longest / most interesting words
    stop_words = {
        "the", "a", "an", "is", "was", "were", "are", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or", "if",
        "while", "about", "it", "its", "this", "that", "these", "those",
        "he", "she", "they", "them", "his", "her", "their", "what", "which",
        "who", "whom", "up", "down", "s", "t", "don", "didn", "won",
    }
    words = re.findall(r"[a-zA-Z]+", text.lower())
    candidates = [w for w in words if w not in stop_words and len(w) > 2]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for w in candidates:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:max_keywords]


def _split_into_sentences(text: str) -> list[str]:
    """Rough sentence splitter that handles common abbreviations."""
    # Split on period / exclamation / question followed by whitespace + capital
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    # Also split on newlines that look like paragraph breaks
    sentences: list[str] = []
    for part in parts:
        for sub in part.split("\n"):
            sub = sub.strip()
            if sub:
                sentences.append(sub)
    return sentences


def _group_sentences(sentences: list[str], n_groups: int) -> list[str]:
    """Evenly distribute sentences across *n_groups* text blocks."""
    if n_groups <= 0:
        n_groups = 1
    if len(sentences) <= n_groups:
        # Pad with empty strings so zip_longest isn't needed
        groups = sentences + [""] * (n_groups - len(sentences))
        return [g for g in groups if g]
    per_group = math.ceil(len(sentences) / n_groups)
    groups: list[str] = []
    for i in range(0, len(sentences), per_group):
        chunk = sentences[i : i + per_group]
        groups.append(" ".join(chunk))
    return groups


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_script(
    topic: str,
    style: str = "tall_tale_3d",
    duration: int = 35,
) -> dict:
    """Generate a structured short-video script from a plain-text topic.

    Parameters
    ----------
    topic : str
        Free-form topic text.  Can be a single sentence ("The guy who sold
        the Eiffel Tower") or several paragraphs of notes.
    style : str
        Name of a template in ``templates/`` (without ``.json``).
    duration : int
        Target video length in seconds (default 35).

    Returns
    -------
    dict
        {
            "title": str,
            "hook": str,
            "scenes": [
                {"text": str, "scene_type": str, "keywords": [str]},
                ...
            ],
            "full_script": str,
        }
    """
    template = _load_template(style)
    target_words = int(duration * WORDS_PER_SECOND)

    # --- Parse the topic into sentences --------------------------------
    sentences = _split_into_sentences(topic)
    if not sentences:
        sentences = [topic.strip() or "An amazing story."]

    # --- Determine scene count -----------------------------------------
    # Hook (2-3 s) + CTA (3 s) → body gets the rest
    hook_seconds = 3
    cta_seconds = 3
    body_seconds = max(duration - hook_seconds - cta_seconds, 5)
    body_scene_count = max(
        1, round(body_seconds / (60 / template.get("pacing", {}).get("cuts_per_minute", 25)))
    )

    # --- Build hook ----------------------------------------------------
    hook_text = sentences[0]

    # --- Build body scenes ---------------------------------------------
    body_sentences = sentences[1:] if len(sentences) > 1 else sentences
    body_blocks = _group_sentences(body_sentences, body_scene_count)

    # --- Build CTA / cliffhanger --------------------------------------
    cta_text = "Follow for Part 2."

    # --- Assemble scenes list ------------------------------------------
    scenes: list[dict] = []

    # Scene 1 – Hook
    scenes.append({
        "text": hook_text,
        "scene_type": SCENE_TYPES["hook"],
        "keywords": _extract_keywords(hook_text),
    })

    # Body scenes
    for idx, block in enumerate(body_blocks):
        stype = SCENE_TYPES["climax"] if idx == len(body_blocks) - 1 else SCENE_TYPES["body"]
        scenes.append({
            "text": block,
            "scene_type": stype,
            "keywords": _extract_keywords(block),
        })

    # Final scene – CTA
    scenes.append({
        "text": cta_text,
        "scene_type": SCENE_TYPES["cta"],
        "keywords": ["follow", "subscribe"],
    })

    # --- Derive a title ------------------------------------------------
    title = sentences[0]
    # Trim to something punchy (≤ 10 words)
    title_words = title.split()
    if len(title_words) > 10:
        title = " ".join(title_words[:10]) + "…"

    # --- Full script (plain narration text) ----------------------------
    full_script = " ".join(scene["text"] for scene in scenes)

    # --- Word-count sanity trim ----------------------------------------
    # If the full script exceeds the target, trim body scenes from the end
    while len(full_script.split()) > target_words and len(scenes) > 3:
        scenes.pop(-2)  # remove last body scene (keep hook + cta)
        full_script = " ".join(s["text"] for s in scenes)

    return {
        "title": title,
        "hook": hook_text,
        "scenes": scenes,
        "full_script": full_script,
    }


# ---------------------------------------------------------------------------
# Quick CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_topic = (
        "In 1925, a con man named Victor Lustig sold the Eiffel Tower. "
        "He posed as a government official and convinced scrap metal dealers "
        "the tower was being dismantled. One dealer paid him a massive bribe. "
        "Lustig fled to Vienna with the cash. The victim was too embarrassed "
        "to report it. So Lustig came back and tried to sell it AGAIN."
    )
    script = generate_script(sample_topic, style="tall_tale_3d", duration=35)
    print(json.dumps(script, indent=2))
