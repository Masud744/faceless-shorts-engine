#!/usr/bin/env python3
"""Scene composition and video export module.

Composes final vertical (9:16) short-form videos by combining background
visuals, text overlays, animated captions, and audio using MoviePy 2.x.
"""

import os
import math
import random
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)
import moviepy.video.fx as fx

from engine.caption_sync import render_captions_on_frame, DEFAULT_STYLE_CONFIG

# Video constants
WIDTH = 1080
HEIGHT = 1920
FPS = 30
RESOLUTION = (WIDTH, HEIGHT)


# --- Background generators ---

def _create_gradient_frame(
    color_top: tuple[int, int, int],
    color_bottom: tuple[int, int, int],
    width: int = WIDTH,
    height: int = HEIGHT,
) -> np.ndarray:
    """Create a vertical gradient background image as a numpy array."""
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        gradient[y, :] = [r, g, b]
    return gradient


# Preset gradient palettes for different scene moods
GRADIENT_PRESETS = {
    "intro": ((20, 20, 80), (60, 10, 90)),         # deep blue to purple
    "fact": ((10, 40, 60), (20, 80, 100)),          # dark teal
    "dramatic": ((40, 0, 0), (100, 20, 20)),        # dark red
    "conclusion": ((10, 10, 50), (50, 20, 80)),     # navy to purple
    "default": ((15, 15, 40), (40, 40, 80)),        # neutral dark blue
    "comedy": ((50, 20, 60), (80, 40, 100)),        # purple-ish
    "eerie": ((5, 15, 10), (20, 40, 30)),           # dark green
}


def _get_background_clip(
    scene_type: str,
    duration: float,
    style_config: dict,
) -> "ImageClip":
    """Create a background video clip for a scene."""
    bg_dir = style_config.get("backgrounds_dir", "assets/backgrounds")
    bg_image_path = None

    if os.path.isdir(bg_dir):
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            candidate = os.path.join(bg_dir, f"{scene_type}{ext}")
            if os.path.exists(candidate):
                bg_image_path = candidate
                break

        if bg_image_path is None:
            images = [
                f for f in os.listdir(bg_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
            ]
            if images:
                bg_image_path = os.path.join(bg_dir, random.choice(images))

    if bg_image_path:
        img = Image.open(bg_image_path).convert("RGB")
        img = _fit_image_to_frame(img, WIDTH, HEIGHT)
        frame_array = np.array(img)
    else:
        preset = GRADIENT_PRESETS.get(scene_type, GRADIENT_PRESETS["default"])
        frame_array = _create_gradient_frame(preset[0], preset[1])

    clip = ImageClip(frame_array).with_duration(duration)
    clip = _apply_ken_burns(clip, duration)
    return clip


def _fit_image_to_frame(
    img: Image.Image, target_w: int, target_h: int
) -> Image.Image:
    """Resize and crop an image to exactly fill the target dimensions."""
    img_w, img_h = img.size
    target_ratio = target_w / target_h
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        new_h = target_h
        new_w = int(img_w * (target_h / img_h))
    else:
        new_w = target_w
        new_h = int(img_h * (target_w / img_w))

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    return img


def _apply_ken_burns(clip, duration: float, zoom_factor: float = 0.08):
    """Apply a gentle Ken Burns effect to a clip."""
    w, h = clip.size
    pan_x = random.choice([-1, 1])
    pan_y = random.choice([-1, 1])

    def make_frame(get_frame, t):
        progress = t / max(duration, 0.01)
        progress = 0.5 - 0.5 * math.cos(math.pi * progress)
        current_zoom = 1.0 + zoom_factor * progress

        new_w = int(w / current_zoom)
        new_h = int(h / current_zoom)

        max_offset_x = (w - new_w) // 2
        max_offset_y = (h - new_h) // 2
        offset_x = int(max_offset_x + pan_x * max_offset_x * progress * 0.3)
        offset_y = int(max_offset_y + pan_y * max_offset_y * progress * 0.3)

        offset_x = max(0, min(offset_x, w - new_w))
        offset_y = max(0, min(offset_y, h - new_h))

        frame = get_frame(t)
        cropped = frame[offset_y:offset_y + new_h, offset_x:offset_x + new_w]

        pil_img = Image.fromarray(cropped).resize((w, h), Image.LANCZOS)
        return np.array(pil_img)

    return clip.transform(make_frame)


def _create_scene_title_clip(
    text: str,
    duration: float,
    style_config: dict,
) -> Optional["TextClip"]:
    """Create a text overlay clip for a scene title or keyword."""
    if not text or not text.strip():
        return None

    title = text.split(".")[0].strip()
    words = title.split()
    if len(words) > 6:
        title = " ".join(words[:6]) + "..."

    font_size = style_config.get("title_font_size", 52)
    font_color = style_config.get("title_color", "white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    try:
        txt_clip = TextClip(
            text=title,
            font_size=font_size,
            color=font_color,
            font=font_path if os.path.exists(font_path) else None,
            stroke_color="black",
            stroke_width=2,
            size=(WIDTH - 120, None),
            method="caption",
            text_align="center",
            duration=min(duration, 3.0),
        )
        txt_clip = (
            txt_clip
            .with_position(("center", int(HEIGHT * 0.15)))
            .with_effects([fx.CrossFadeIn(0.5), fx.CrossFadeOut(0.5)])
        )
        return txt_clip
    except Exception as e:
        print(f"[scene_composer] Notice: skipping title TextClip: {e}")
        return None


def compose_video(
    script_scenes: list[dict] | None = None,
    audio_path: str = "",
    captions: list[dict] | None = None,
    style_config: dict | None = None,
    output_path: str = "output/final_video.mp4",
    script: dict | None = None,
    template: dict | None = None,
    duration: float | None = None,
    **kwargs,
) -> str:
    """Compose a complete vertical short-form video from scenes, audio, and captions."""
    if script is not None and script_scenes is None:
        script_scenes = script.get("scenes", [])
    if template is not None and style_config is None:
        style_config = template
    if style_config is None:
        style_config = {}
    if captions is None:
        captions = []

    if not script_scenes:
        raise ValueError("script_scenes cannot be empty")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"[scene_composer] Composing video with {len(script_scenes)} scenes...")

    scene_clips = []
    cumulative_time = 0.0

    for i, scene in enumerate(script_scenes):
        scene_text = scene.get("text", "")
        scene_duration = float(scene.get("duration", 5.0))
        scene_type = scene.get("scene_type", "default")

        print(f"[scene_composer]   Scene {i+1}: type={scene_type}, duration={scene_duration:.1f}s")

        # 1. Background clip
        bg_clip = _get_background_clip(scene_type, scene_duration, style_config)

        # 2. Captions
        scene_start = cumulative_time
        caption_config = {**DEFAULT_STYLE_CONFIG}
        caption_config.update({
            k: v for k, v in style_config.items()
            if k in DEFAULT_STYLE_CONFIG
        })

        def make_caption_frame(get_frame, t, _start=scene_start, _caps=captions, _cfg=caption_config):
            frame_array = get_frame(t)
            current_time = _start + t
            pil_frame = Image.fromarray(frame_array)
            pil_frame = render_captions_on_frame(pil_frame, _caps, current_time, _cfg)
            return np.array(pil_frame)

        captioned_clip = bg_clip.transform(make_caption_frame)

        # 3. Layer assembly
        layers = [captioned_clip]
        title_clip = _create_scene_title_clip(scene_text, scene_duration, style_config)
        if title_clip is not None:
            layers.append(title_clip)

        # 4. Composite
        scene_clip = CompositeVideoClip(layers, size=RESOLUTION).with_duration(scene_duration)
        scene_clips.append(scene_clip)
        cumulative_time += scene_duration

    # 5. Concatenate
    print("[scene_composer] Concatenating scenes...")
    final_video = concatenate_videoclips(scene_clips, method="compose")

    # 6. Audio track
    print("[scene_composer] Adding audio track...")
    try:
        audio_clip = AudioFileClip(audio_path)
        if audio_clip.duration > final_video.duration:
            audio_clip = audio_clip.subclipped(0, final_video.duration)
        final_video = final_video.with_audio(audio_clip)
    except Exception as e:
        print(f"[scene_composer] Warning: Could not add audio: {e}")

    # 7. Render MP4
    print(f"[scene_composer] Exporting to {output_path}...")
    try:
        final_video.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="veryfast",
            bitrate="4000k",
            threads=4,
            logger="bar",
        )
    except Exception as e:
        raise RuntimeError(f"Video export failed: {e}") from e
    finally:
        final_video.close()
        for clip in scene_clips:
            clip.close()

    print(f"[scene_composer] Video saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Scene Composer Test")
    print("=" * 60)

    test_scenes = [
        {
            "text": "The Man Who Bought an Entire Bank for 1 Dollar.",
            "duration": 3.0,
            "scene_type": "intro",
        },
        {
            "text": "In 1995, a historic bank collapsed and was sold for practically nothing.",
            "duration": 4.0,
            "scene_type": "fact",
        },
    ]

    audio_file = "output/test_voice.mp3"
    if not os.path.exists(audio_file):
        from pydub import AudioSegment as AS
        silent = AS.silent(duration=7000, frame_rate=24000)
        os.makedirs("output", exist_ok=True)
        silent.export(audio_file, format="mp3")

    captions = [
        {"word": "The", "start": 0.0, "end": 0.3},
        {"word": "Man", "start": 0.3, "end": 0.7},
        {"word": "Who", "start": 0.7, "end": 1.0},
        {"word": "Bought", "start": 1.0, "end": 1.5},
        {"word": "A", "start": 1.5, "end": 1.8},
        {"word": "Bank!", "start": 1.8, "end": 2.5},
    ]

    out = compose_video(
        script_scenes=test_scenes,
        audio_path=audio_file,
        captions=captions,
        style_config={"title_color": "yellow"},
        output_path="output/test_quick.mp4",
    )
    print("Test video created:", out)
