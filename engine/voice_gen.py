#!/usr/bin/env python3
"""Voice generation module using Microsoft Edge TTS.

Generates natural-sounding speech from text using edge-tts (free, no API key).
Supports multiple voice presets and outputs MP3/WAV audio files.
"""

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

try:
    import edge_tts
except ImportError:
    edge_tts = None

# Voice preset mapping to Edge TTS voice names
VOICE_PRESETS = {
    "af_heart": "en-US-JennyNeural",         # American female - warm, friendly
    "am_michael": "en-US-GuyNeural",          # American male - confident, clear
    "bf_emma": "en-GB-SoniaNeural",           # British female - polished, articulate
    "am_davis": "en-US-DavisNeural",          # American male - deep, authoritative
    "af_aria": "en-US-AriaNeural",            # American female - expressive, dramatic
    "am_andrew": "en-US-AndrewNeural",        # American male - calm, narrator
}

# Rate adjustment: edge-tts uses percentage strings like "+10%" or "-5%"
def _speed_to_rate(speed: float) -> str:
    """Convert a speed multiplier (e.g. 1.1) to edge-tts rate string (e.g. '+10%')."""
    pct = int((speed - 1.0) * 100)
    if pct >= 0:
        return f"+{pct}%"
    return f"{pct}%"


async def _generate_voice_async(
    text: str,
    output_path: str,
    voice: str = "af_heart",
    speed: float = 1.0,
) -> str:
    """Async implementation of voice generation using edge-tts.

    Args:
        text: The text to convert to speech.
        output_path: File path where the output audio will be saved.
        voice: Voice preset key from VOICE_PRESETS.
        speed: Speech speed multiplier (0.5 = half speed, 2.0 = double speed).

    Returns:
        The output file path.
    """
    if voice not in VOICE_PRESETS:
        raise ValueError(
            f"Unknown voice '{voice}'. Available voices: {list(VOICE_PRESETS.keys())}"
        )

    voice_name = VOICE_PRESETS[voice]
    rate = _speed_to_rate(speed)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print(f"[voice_gen] Generating voice with '{voice_name}' at rate {rate}...")
    print(f"[voice_gen] Text: {text[:100]}...")

    # Generate audio using edge-tts
    communicate = edge_tts.Communicate(text, voice_name, rate=rate)

    # edge-tts outputs MP3 by default
    mp3_path = output_path
    if output_path.endswith('.wav'):
        mp3_path = output_path.replace('.wav', '.mp3')

    await communicate.save(mp3_path)

    # Convert MP3 to WAV if requested (using ffmpeg or pydub)
    if output_path.endswith('.wav') and mp3_path != output_path:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(output_path, format="wav")
            os.unlink(mp3_path)
            print(f"[voice_gen] Converted to WAV: {output_path}")
        except Exception:
            # Fallback: try ffmpeg directly
            try:
                subprocess.run(
                    ["ffmpeg", "-i", mp3_path, "-y", output_path],
                    capture_output=True, check=True
                )
                os.unlink(mp3_path)
            except Exception:
                # If conversion fails, just use MP3
                output_path = mp3_path
                print("[voice_gen] Warning: Could not convert to WAV, using MP3")

    print(f"[voice_gen] Saved voice audio to: {output_path}")
    return output_path


def generate_voice(
    text: str,
    output_path: str,
    voice: str = "af_heart",
    speed: float = 1.0,
) -> str:
    """Generate speech audio from text using Microsoft Edge TTS.

    This is a synchronous wrapper around the async edge-tts library.
    The generated voices are studio-quality neural voices, completely free.

    Args:
        text: The text to convert to speech.
        output_path: File path where the output audio will be saved (.mp3 or .wav).
        voice: Voice preset key. One of: "af_heart", "am_michael", "bf_emma",
               "am_davis", "af_aria", "am_andrew".
        speed: Speech speed multiplier (0.5 = half speed, 2.0 = double speed).

    Returns:
        The output file path (same as output_path).

    Raises:
        ImportError: If edge-tts library is not installed.
        ValueError: If the voice preset is not recognized.
        RuntimeError: If TTS generation fails.
    """
    if edge_tts is None:
        raise ImportError(
            "edge-tts library is not installed. "
            "Install it with: pip install edge-tts"
        )

    try:
        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If we're already in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    _generate_voice_async(text, output_path, voice, speed)
                )
                return future.result()
        else:
            return asyncio.run(
                _generate_voice_async(text, output_path, voice, speed)
            )
    except Exception as e:
        raise RuntimeError(f"Voice generation failed: {e}") from e


async def list_voices(language: str = "en") -> list[dict]:
    """List available edge-tts voices for a given language.

    Args:
        language: Language code prefix (e.g., "en" for English).

    Returns:
        List of voice dictionaries with Name, ShortName, Gender, Locale.
    """
    if edge_tts is None:
        raise ImportError("edge-tts is not installed")

    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith(language)]


if __name__ == "__main__":
    # Test voice generation
    test_text = (
        "Welcome to the world of AI-generated videos. "
        "In this short, we'll explore how artificial intelligence "
        "is changing content creation forever. "
        "Stay tuned for some mind-blowing facts!"
    )

    output = "output/test_voice.mp3"
    print("=" * 60)
    print("Voice Generation Test (Edge TTS)")
    print("=" * 60)
    print(f"Text: {test_text}")
    print(f"Output: {output}")
    print()

    try:
        result = generate_voice(test_text, output, voice="am_michael", speed=1.05)
        print(f"\nSuccess! Audio saved to: {result}")

        # Print file info
        file_size = os.path.getsize(result)
        print(f"File size: {file_size / 1024:.1f} KB")
    except ImportError as e:
        print(f"\nSkipped (edge-tts not installed): {e}")
    except Exception as e:
        print(f"\nError: {e}")
