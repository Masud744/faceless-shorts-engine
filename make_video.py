#!/usr/bin/env python3
"""
make_video.py – Master orchestrator for the Faceless AI Shorts engine.

Usage:
    python make_video.py --topic "Your topic text" --style tall_tale_3d --duration 35

This script ties together every engine module:
    1. Load style template
    2. Generate script (script_writer)
    3. Generate voice audio (voice_gen) — or use custom audio
    4. Generate word-level captions (caption_sync)
    5. Generate SFX audio (sfx_mixer)
    6. Mix all audio tracks (sfx_mixer.mix_audio)
    7. Compose video with scenes + captions (scene_composer)
    8. Save final MP4 to output/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Engine imports (sibling modules)
# ---------------------------------------------------------------------------

from engine.script_writer import generate_script

# The following modules are imported lazily so make_video.py can be used for
# script-only workflows even before the heavier dependencies are installed.

def _import_voice_gen():
    try:
        from engine.voice_gen import generate_voice
        return generate_voice
    except ImportError:
        return None

def _import_caption_sync():
    try:
        from engine.caption_sync import generate_captions
        return generate_captions
    except ImportError:
        return None

def _import_sfx_mixer():
    try:
        from engine.sfx_mixer import generate_sfx, mix_audio
        return generate_sfx, mix_audio
    except ImportError:
        return None, None

def _import_scene_composer():
    try:
        from engine.scene_composer import compose_video
        return compose_video
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_template(style: str) -> dict:
    """Load a style template JSON by name."""
    path = TEMPLATES_DIR / f"{style}.json"
    if not path.exists():
        available = sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))
        print(f"❌ Template '{style}' not found.")
        print(f"   Available styles: {', '.join(available)}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _timestamp_name() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def make_video(
    topic: str,
    style: str = "tall_tale_3d",
    duration: int = 35,
    output_name: str | None = None,
    custom_audio: str | None = None,
) -> str:
    """Run the full video-creation pipeline.

    Parameters
    ----------
    topic : str
        The story / explanation text to turn into a video.
    style : str
        Template name (one of the JSON files in ``templates/``).
    duration : int
        Target video length in seconds.
    output_name : str, optional
        Base name for the output file.  A timestamp is used if omitted.
    custom_audio : str, optional
        Path to a pre-recorded narration audio file.  When provided the
        voice-generation step is skipped.

    Returns
    -------
    str
        Absolute path to the generated MP4 file.
    """

    start_time = time.time()
    print()
    print("=" * 60)
    print("🎬  Faceless AI Shorts – Video Engine")
    print("=" * 60)

    # -- Step 1: Load template -------------------------------------------
    print(f"\n📐 Loading style template: {style}")
    template = load_template(style)
    print(f"   → {template['name']}: {template['description']}")

    # -- Step 2: Generate script -----------------------------------------
    print("\n✍️  Writing script …")
    script = generate_script(topic, style=style, duration=duration)
    print(f"   → Title : {script['title']}")
    print(f"   → Scenes: {len(script['scenes'])}")
    print(f"   → Words : {len(script['full_script'].split())}")

    # -- Step 3: Generate voice audio ------------------------------------
    voice_path: str | None = None
    generate_voice = _import_voice_gen()

    if custom_audio:
        print(f"\n🎙️  Using custom audio: {custom_audio}")
        voice_path = custom_audio
    elif generate_voice is not None:
        print("\n🎙️  Generating voice with Edge TTS …")
        voice_cfg = {
            "voice": template.get("voice", "am_michael"),
            "speed": template.get("voice_speed", 1.0),
        }
        timestamp = _timestamp_name()
        voice_path = str(OUTPUT_DIR / f"voice_{timestamp}.mp3")
        voice_path = generate_voice(
            text=script["full_script"],
            output_path=voice_path,
            **voice_cfg,
        )
        print(f"   → Voice saved to: {voice_path}")
    else:
        print("\n🎙️  voice_gen module not available – skipping voice generation.")
        print("   ℹ️  Install Kokoro and create engine/voice_gen.py to enable.")

    # -- Step 4: Generate word-level captions ----------------------------
    captions = None
    generate_captions = _import_caption_sync()

    if voice_path and generate_captions is not None:
        print("\n💬 Generating word-level captions …")
        captions = generate_captions(voice_path, script.get("full_script", ""))
        print(f"   → {len(captions)} caption segments generated.")
    else:
        print("\n💬 caption_sync module not available – skipping caption generation.")

    # -- Step 5: Generate SFX audio --------------------------------------
    sfx_path: str | None = None
    generate_sfx, mix_audio_fn = _import_sfx_mixer()

    if generate_sfx is not None:
        print("\n🔊 Generating SFX audio …")
        sfx_profile = template.get("sfx_profile", "comedy")
        sfx_path = generate_sfx(
            scenes=script["scenes"],
            profile=sfx_profile,
            duration=duration,
            output_dir=str(OUTPUT_DIR),
        )
        print(f"   → SFX saved to: {sfx_path}")
    else:
        print("\n🔊 sfx_mixer module not available – skipping SFX generation.")

    # -- Step 6: Mix all audio tracks ------------------------------------
    mixed_audio_path: str | None = None

    if mix_audio_fn is not None and voice_path:
        print("\n🎛️  Mixing audio tracks …")
        tracks = [t for t in [voice_path, sfx_path] if t]
        mixed_audio_path = mix_audio_fn(
            tracks=tracks,
            output_dir=str(OUTPUT_DIR),
        )
        print(f"   → Mixed audio: {mixed_audio_path}")
    else:
        mixed_audio_path = voice_path  # fallback: voice only
        if mixed_audio_path:
            print("\n🎛️  Using voice track as final audio (no SFX mixer).")

    # -- Step 7: Compose video -------------------------------------------
    compose_video = _import_scene_composer()
    final_name = output_name or f"{style}_{_timestamp_name()}"
    output_path = str(OUTPUT_DIR / f"{final_name}.mp4")

    if compose_video is not None:
        print("\n🎥 Composing video …")
        output_path = compose_video(
            script=script,
            template=template,
            audio_path=mixed_audio_path,
            captions=captions,
            output_path=output_path,
            duration=duration,
        )
        print(f"   → Video saved to: {output_path}")
    else:
        print("\n🎥 scene_composer module not available – skipping video composition.")
        print(f"   ℹ️  Final video would be saved to: {output_path}")

    # -- Step 8: Summary -------------------------------------------------
    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print("✅  Pipeline complete!")
    print(f"   📄 Script  : {script['title']}")
    print(f"   🎨 Style   : {template['name']}")
    print(f"   ⏱️  Duration: ~{duration}s")
    print(f"   📁 Output  : {output_path}")
    print(f"   🕐 Elapsed : {elapsed:.1f}s")
    print("=" * 60)
    print()

    return output_path


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    available_styles = sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))

    parser = argparse.ArgumentParser(
        description="Faceless AI Shorts – Generate short-form videos from text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""\
            Available styles:
              {chr(10).join(f'  • {s}' for s in available_styles)}

            Examples:
              python make_video.py --topic "The guy who sold the Eiffel Tower twice"
              python make_video.py --topic "What happens if you swallow gum" --style deep_dive_3d
              python make_video.py --topic "Your story" --duration 60 --output my_video
        """),
    )
    parser.add_argument(
        "--topic", "-t",
        required=True,
        help="The story or explanation text for the video.",
    )
    parser.add_argument(
        "--style", "-s",
        default="tall_tale_3d",
        choices=available_styles,
        help=f"Visual style template (default: tall_tale_3d).",
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=35,
        help="Target video duration in seconds (default: 35).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        dest="output_name",
        help="Output file base name (without extension).",
    )
    parser.add_argument(
        "--audio", "-a",
        default=None,
        dest="custom_audio",
        help="Path to custom narration audio (skips voice generation).",
    )

    args = parser.parse_args()

    make_video(
        topic=args.topic,
        style=args.style,
        duration=args.duration,
        output_name=args.output_name,
        custom_audio=args.custom_audio,
    )


if __name__ == "__main__":
    main()
