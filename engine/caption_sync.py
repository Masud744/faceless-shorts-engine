#!/usr/bin/env python3
"""Caption synchronization and rendering module.

Estimates word-level timing from audio duration and renders animated
word-by-word captions onto video frames with highlight effects.
"""

import os
import re
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment


# Default caption style configuration
DEFAULT_STYLE_CONFIG = {
    "font_size": 64,
    "font_path": None,  # None = use default; set to a .ttf path for custom font
    "highlight_color": (255, 215, 0),      # #FFD700 gold/yellow
    "normal_color": (255, 255, 255),        # white
    "outline_color": (0, 0, 0),             # black outline
    "outline_width": 3,
    "shadow_offset": (3, 3),
    "shadow_color": (0, 0, 0, 180),         # semi-transparent black
    "position_ratio": 0.80,                 # vertical position (0.80 = bottom 20%)
    "max_words_per_line": 5,
    "line_spacing": 12,
    "padding_x": 40,
}


def generate_captions(audio_path: str, script_text: str = "") -> list[dict]:
    """Generate word-level caption timing from audio file and script text.

    Estimates word timestamps by distributing the audio duration proportionally
    based on word character lengths (longer words take more time). A small
    padding gap is inserted between words for natural pacing.

    Args:
        audio_path: Path to the WAV/MP3 audio file.
        script_text: The original script text that was spoken.

    Returns:
        List of dicts, each with keys:
            - "word" (str): The word text.
            - "start" (float): Start time in seconds.
            - "end" (float): End time in seconds.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Get audio duration using pydub
    audio = AudioSegment.from_file(audio_path)
    total_duration = audio.duration_seconds

    script_text = (script_text or "").strip()
    if not script_text:
        # Fallback if no script text provided
        script_text = "Amazing Story That You Will Never Forget"

    # Split text into words, preserving punctuation attached to words
    words = script_text.split()
    if not words:
        return []

    # Calculate weight for each word based on character length
    # Words with punctuation get slightly less weight for the punctuation chars
    word_weights = []
    for word in words:
        # Base weight is character count; min 1
        clean = re.sub(r'[^\w]', '', word)
        weight = max(len(clean), 1)
        word_weights.append(weight)

    total_weight = sum(word_weights)

    # Small inter-word gap (percentage of total duration)
    gap_fraction = 0.01  # 1% of total duration per gap
    num_gaps = len(words) - 1
    total_gap_time = min(gap_fraction * total_duration * num_gaps, total_duration * 0.15)
    per_gap = total_gap_time / num_gaps if num_gaps > 0 else 0

    # Available time for actual words
    word_time = total_duration - total_gap_time

    captions = []
    current_time = 0.0

    for i, (word, weight) in enumerate(zip(words, word_weights)):
        # Duration proportional to weight
        duration = (weight / total_weight) * word_time
        start = current_time
        end = start + duration

        captions.append({
            "word": word,
            "start": round(start, 3),
            "end": round(end, 3),
        })

        current_time = end + (per_gap if i < num_gaps else 0)

    return captions


def _get_font(style_config: dict) -> ImageFont.FreeTypeFont:
    """Load a TrueType font based on style configuration.

    Falls back through several common system font paths if no custom
    font is specified.

    Args:
        style_config: Caption style configuration dict.

    Returns:
        A PIL FreeTypeFont instance.
    """
    font_size = style_config.get("font_size", DEFAULT_STYLE_CONFIG["font_size"])
    font_path = style_config.get("font_path", DEFAULT_STYLE_CONFIG["font_path"])

    if font_path and os.path.exists(font_path):
        return ImageFont.truetype(font_path, font_size)

    # Try common system font paths for a bold sans-serif font
    fallback_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    for fp in fallback_fonts:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, font_size)
            except (OSError, IOError):
                continue

    # Final fallback: PIL default (bitmap) font — won't scale but won't crash
    print("[caption_sync] Warning: No TrueType font found, using default bitmap font")
    return ImageFont.load_default()


def _draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color: tuple,
    outline_color: tuple,
    outline_width: int,
    shadow_offset: Optional[tuple] = None,
    shadow_color: Optional[tuple] = None,
):
    """Draw text with outline and optional shadow for readability.

    Args:
        draw: PIL ImageDraw instance.
        position: (x, y) position for the text.
        text: Text string to render.
        font: PIL font to use.
        fill_color: Main text color (R, G, B) or (R, G, B, A).
        outline_color: Outline color.
        outline_width: Width of the outline in pixels.
        shadow_offset: Optional (dx, dy) offset for drop shadow.
        shadow_color: Optional color for drop shadow.
    """
    x, y = position

    # Draw shadow first (behind everything)
    if shadow_offset and shadow_color:
        sx, sy = shadow_offset
        draw.text((x + sx, y + sy), text, font=font, fill=shadow_color)

    # Draw outline by rendering text at offsets in all directions
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    # Draw main text on top
    draw.text((x, y), text, font=font, fill=fill_color)


def render_captions_on_frame(
    frame: Image.Image,
    captions: list[dict],
    current_time: float,
    style_config: Optional[dict] = None,
) -> Image.Image:
    """Render word-by-word captions onto a video frame.

    Draws the currently-visible caption words at the bottom of the frame.
    The word being spoken at `current_time` is highlighted in yellow/gold;
    surrounding words on the same line(s) are drawn in white.

    Args:
        frame: PIL Image representing the current video frame.
        captions: List of caption dicts from generate_captions().
        current_time: Current playback time in seconds.
        style_config: Optional style overrides (merged with DEFAULT_STYLE_CONFIG).

    Returns:
        A new PIL Image with captions rendered on it.
    """
    # Merge style with defaults
    config = {**DEFAULT_STYLE_CONFIG}
    if style_config:
        config.update(style_config)

    frame = frame.copy()
    draw = ImageDraw.Draw(frame)
    font = _get_font(config)

    max_words = config["max_words_per_line"]
    highlight_color = config["highlight_color"]
    normal_color = config["normal_color"]
    outline_color = config["outline_color"]
    outline_width = config["outline_width"]
    shadow_offset = config.get("shadow_offset")
    shadow_color = config.get("shadow_color")
    position_ratio = config["position_ratio"]
    line_spacing = config["line_spacing"]
    padding_x = config["padding_x"]

    frame_w, frame_h = frame.size

    # Find which words are currently "active" — we show a window of words
    # centered around the currently-spoken word
    active_idx = None
    for i, cap in enumerate(captions):
        if cap["start"] <= current_time <= cap["end"]:
            active_idx = i
            break

    if active_idx is None:
        # If between words, find the nearest upcoming word
        for i, cap in enumerate(captions):
            if cap["start"] > current_time:
                active_idx = max(0, i - 1)
                break
        if active_idx is None:
            # Past end of captions
            return frame

    # Determine the window of words to display (centered on active word)
    total_display = max_words * 2  # show up to 2 lines
    start_idx = max(0, active_idx - total_display // 2)
    end_idx = min(len(captions), start_idx + total_display)
    # Re-adjust start if we hit the end
    start_idx = max(0, end_idx - total_display)

    display_words = captions[start_idx:end_idx]

    # Split into lines of max_words each
    lines = []
    for i in range(0, len(display_words), max_words):
        lines.append(display_words[i:i + max_words])

    # Calculate vertical starting position
    line_heights = []
    for line in lines:
        line_text = " ".join(w["word"] for w in line)
        bbox = font.getbbox(line_text)
        h = bbox[3] - bbox[1]
        line_heights.append(h)

    total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    y_start = int(frame_h * position_ratio) - total_text_height // 2

    # Render each line
    y_cursor = y_start
    for line, lh in zip(lines, line_heights):
        # Calculate total line width for centering
        line_text = " ".join(w["word"] for w in line)
        bbox = font.getbbox(line_text)
        line_width = bbox[2] - bbox[0]
        x_cursor = (frame_w - line_width) // 2

        # Draw each word individually for per-word highlighting
        for cap in line:
            word = cap["word"]
            is_active = cap["start"] <= current_time <= cap["end"]
            color = highlight_color if is_active else normal_color

            _draw_text_with_outline(
                draw,
                (x_cursor, y_cursor),
                word,
                font,
                fill_color=color,
                outline_color=outline_color,
                outline_width=outline_width,
                shadow_offset=shadow_offset,
                shadow_color=shadow_color,
            )

            # Advance x cursor
            word_bbox = font.getbbox(word + " ")
            x_cursor += word_bbox[2] - word_bbox[0]

        y_cursor += lh + line_spacing

    return frame


if __name__ == "__main__":
    # Test caption generation and rendering
    print("=" * 60)
    print("Caption Sync Test")
    print("=" * 60)

    test_script = (
        "Welcome to the world of AI generated videos. "
        "In this short we will explore how artificial intelligence "
        "is changing content creation forever."
    )

    # Test caption timing generation with a dummy audio file
    test_audio = "output/test_voice.wav"

    if os.path.exists(test_audio):
        captions = generate_captions(test_audio, test_script)
        print(f"\nGenerated {len(captions)} word captions:")
        for cap in captions[:10]:
            print(f"  [{cap['start']:.3f} - {cap['end']:.3f}] {cap['word']}")
        if len(captions) > 10:
            print(f"  ... and {len(captions) - 10} more")

        # Test rendering on a blank frame
        frame = Image.new("RGB", (1080, 1920), color=(30, 30, 60))
        mid_time = captions[5]["start"] + 0.01 if len(captions) > 5 else 0.5

        rendered = render_captions_on_frame(frame, captions, mid_time)
        out_path = "output/test_caption_frame.png"
        os.makedirs("output", exist_ok=True)
        rendered.save(out_path)
        print(f"\nRendered caption frame saved to: {out_path}")
    else:
        print(f"\nSkipped audio-based test (file not found: {test_audio})")
        print("Run voice_gen.py first to create test audio, or provide a WAV file.")

        # Demo render on a blank frame with synthetic captions
        words = test_script.split()
        fake_captions = []
        t = 0.0
        for w in words:
            dur = len(w) * 0.06
            fake_captions.append({"word": w, "start": round(t, 3), "end": round(t + dur, 3)})
            t += dur + 0.02

        frame = Image.new("RGB", (1080, 1920), color=(30, 30, 60))
        rendered = render_captions_on_frame(frame, fake_captions, 0.5)
        out_path = "output/test_caption_frame.png"
        os.makedirs("output", exist_ok=True)
        rendered.save(out_path)
        print(f"Demo caption frame saved to: {out_path}")
