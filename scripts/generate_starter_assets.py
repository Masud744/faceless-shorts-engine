#!/usr/bin/env python3
"""Generate starter visual and audio assets for Faceless AI Shorts.

Creates:
1. Character sprites with transparency (cartoon face & expressions, stick figures)
2. High-res vertical background textures (1080x1920)
3. Procedural Lo-Fi background music track
"""

import math
import os
import wave
import numpy as np
from PIL import Image, ImageDraw

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
CHARACTERS_DIR = os.path.join(ASSETS_DIR, "characters")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

for d in [CHARACTERS_DIR, BACKGROUNDS_DIR, MUSIC_DIR]:
    os.makedirs(d, exist_ok=True)


def create_character(expression="neutral", filename="character.png"):
    """Draw a clean, viral 2D cartoon cutout character with transparent background."""
    size = (600, 800)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center_x = 300
    head_y = 260
    head_r = 130

    # Body / Hoodie
    body_color = (235, 87, 87)       # Bright modern coral red
    skin_color = (255, 224, 189)      # Warm skin tone
    shadow_skin = (230, 195, 160)
    outline = (25, 25, 30)

    # Torso
    draw.rounded_rectangle(
        [center_x - 140, head_y + 100, center_x + 140, 780],
        radius=40,
        fill=body_color,
        outline=outline,
        width=8,
    )
    # Hoodie strings
    draw.line([center_x - 30, head_y + 120, center_x - 35, head_y + 240], fill=(255, 255, 255), width=6)
    draw.line([center_x + 30, head_y + 120, center_x + 35, head_y + 240], fill=(255, 255, 255), width=6)

    # Neck
    draw.rectangle([center_x - 40, head_y + 80, center_x + 40, head_y + 120], fill=shadow_skin, outline=outline, width=6)

    # Head
    draw.ellipse([center_x - head_r, head_y - head_r, center_x + head_r, head_y + head_r], fill=skin_color, outline=outline, width=8)

    # Hair (stylish swept-back)
    hair_color = (40, 30, 25)
    draw.chord([center_x - head_r - 5, head_y - head_r - 20, center_x + head_r + 5, head_y + 10], 175, 365, fill=hair_color, outline=outline, width=8)

    # Eyes & Eyebrows
    eye_y = head_y - 10
    eye_offset = 45

    if expression == "shocked":
        # Wide open round eyes
        for ex in [center_x - eye_offset, center_x + eye_offset]:
            draw.ellipse([ex - 22, eye_y - 22, ex + 22, eye_y + 22], fill=(255, 255, 255), outline=outline, width=5)
            draw.ellipse([ex - 8, eye_y - 8, ex + 8, eye_y + 8], fill=(10, 10, 10))
        # Raised high eyebrows
        draw.arc([center_x - eye_offset - 25, eye_y - 50, center_x - eye_offset + 25, eye_y - 30], 190, 350, fill=outline, width=8)
        draw.arc([center_x + eye_offset - 25, eye_y - 50, center_x + eye_offset + 25, eye_y - 30], 190, 350, fill=outline, width=8)
        # O-shaped mouth
        draw.ellipse([center_x - 22, head_y + 45, center_x + 22, head_y + 85], fill=(50, 10, 10), outline=outline, width=6)

    elif expression == "talking":
        # Expressive eyes
        for ex in [center_x - eye_offset, center_x + eye_offset]:
            draw.ellipse([ex - 18, eye_y - 18, ex + 18, eye_y + 18], fill=(255, 255, 255), outline=outline, width=5)
            draw.ellipse([ex - 6, eye_y - 6, ex + 6, eye_y + 6], fill=(10, 10, 10))
        # Eyebrows
        draw.line([center_x - eye_offset - 25, eye_y - 35, center_x - eye_offset + 25, eye_y - 30], fill=outline, width=7)
        draw.line([center_x + eye_offset - 25, eye_y - 30, center_x + eye_offset + 25, eye_y - 35], fill=outline, width=7)
        # Open talking smile
        draw.chord([center_x - 35, head_y + 40, center_x + 35, head_y + 85], 0, 180, fill=(220, 50, 50), outline=outline, width=6)
        # Teeth highlight
        draw.rectangle([center_x - 20, head_y + 42, center_x + 20, head_y + 52], fill=(255, 255, 255))

    elif expression == "thinking":
        # One eye squinted, one eye up
        draw.line([center_x - eye_offset - 20, eye_y, center_x - eye_offset + 20, eye_y], fill=outline, width=6)
        draw.ellipse([center_x + eye_offset - 18, eye_y - 18, center_x + eye_offset + 18, eye_y + 18], fill=(255, 255, 255), outline=outline, width=5)
        draw.ellipse([center_x + eye_offset - 4, eye_y - 14, center_x + eye_offset + 8, eye_y - 2], fill=(10, 10, 10))
        # Wavy mouth
        draw.arc([center_x - 25, head_y + 50, center_x + 25, head_y + 70], 20, 160, fill=outline, width=6)

    else:  # neutral / default smile
        for ex in [center_x - eye_offset, center_x + eye_offset]:
            draw.ellipse([ex - 16, eye_y - 16, ex + 16, eye_y + 16], fill=(255, 255, 255), outline=outline, width=5)
            draw.ellipse([ex - 6, eye_y - 6, ex + 6, eye_y + 6], fill=(10, 10, 10))
            draw.ellipse([ex + 2, eye_y - 8, ex + 6, eye_y - 4], fill=(255, 255, 255))  # glimmer
        draw.line([center_x - eye_offset - 20, eye_y - 30, center_x - eye_offset + 20, eye_y - 32], fill=outline, width=6)
        draw.line([center_x + eye_offset - 20, eye_y - 32, center_x + eye_offset + 20, eye_y - 30], fill=outline, width=6)
        # Gentle smile
        draw.arc([center_x - 28, head_y + 45, center_x + 28, head_y + 75], 25, 155, fill=outline, width=7)

    # Cheerful blush marks
    draw.ellipse([center_x - eye_offset - 35, head_y + 20, center_x - eye_offset - 5, head_y + 35], fill=(255, 170, 170, 140))
    draw.ellipse([center_x + eye_offset + 5, head_y + 20, center_x + eye_offset + 35, head_y + 35], fill=(255, 170, 170, 140))

    out_path = os.path.join(CHARACTERS_DIR, filename)
    img.save(out_path, "PNG")
    print(f"✅ Generated character: {out_path}")


def create_stick_figure(filename="stick_figure.png"):
    """Draw a funny Zack D. / Stick Story style character."""
    size = (600, 800)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = 300, 220
    r = 90
    color = (25, 25, 30)

    # Head
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=color, width=12)
    # Eyes
    draw.ellipse([cx - 35, cy - 15, cx - 15, cy + 5], fill=color)
    draw.ellipse([cx + 15, cy - 15, cx + 35, cy + 5], fill=color)
    # Smile
    draw.arc([cx - 40, cy + 10, cx + 40, cy + 55], 20, 160, fill=color, width=9)

    # Body spine
    draw.line([cx, cy + r, cx, cy + r + 260], fill=color, width=14)

    # Arms (gesturing)
    draw.line([cx, cy + r + 50, cx - 120, cy + r + 130], fill=color, width=12)
    draw.line([cx - 120, cy + r + 130, cx - 140, cy + r + 60], fill=color, width=12)

    draw.line([cx, cy + r + 50, cx + 130, cy + r + 110], fill=color, width=12)
    draw.line([cx + 130, cy + r + 110, cx + 180, cy + r + 50], fill=color, width=12)

    # Legs
    draw.line([cx, cy + r + 260, cx - 90, 740], fill=color, width=12)
    draw.line([cx, cy + r + 260, cx + 90, 740], fill=color, width=12)

    out_path = os.path.join(CHARACTERS_DIR, filename)
    img.save(out_path, "PNG")
    print(f"✅ Generated stick figure: {out_path}")


def create_backgrounds():
    """Create stylish vertical background images."""
    w, h = 1080, 1920

    presets = {
        "intro.png": ((20, 24, 82), (76, 20, 97), "dots"),
        "fact.png": ((12, 38, 57), (18, 78, 92), "grid"),
        "dramatic.png": ((45, 10, 15), (95, 22, 28), "glow"),
        "conclusion.png": ((15, 12, 42), (48, 25, 78), "dots"),
        "default.png": ((18, 20, 38), (35, 38, 70), "grid"),
    }

    for fname, (top, bot, pattern) in presets.items():
        arr = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            r = y / h
            arr[y, :, 0] = int(top[0] + (bot[0] - top[0]) * r)
            arr[y, :, 1] = int(top[1] + (bot[1] - top[1]) * r)
            arr[y, :, 2] = int(top[2] + (bot[2] - top[2]) * r)

        img = Image.fromarray(arr).convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if pattern == "grid":
            step = 60
            for gx in range(0, w, step):
                draw.line([(gx, 0), (gx, h)], fill=(255, 255, 255, 12), width=1)
            for gy in range(0, h, step):
                draw.line([(0, gy), (w, gy)], fill=(255, 255, 255, 12), width=1)

        elif pattern == "dots":
            step = 50
            for gx in range(25, w, step):
                for gy in range(25, h, step):
                    draw.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(255, 255, 255, 18))

        elif pattern == "glow":
            # Radial subtle vignette glow in center
            cx, cy = w // 2, h // 2
            for radius in range(500, 50, -50):
                alpha = int(8 * (1.0 - radius / 500))
                draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(255, 200, 100, alpha))

        final_img = Image.alpha_composite(img, overlay).convert("RGB")
        out_path = os.path.join(BACKGROUNDS_DIR, fname)
        final_img.save(out_path, "PNG")
        print(f"✅ Generated background: {out_path}")


def create_ambient_music(duration_sec=40):
    """Procedurally synthesize a smooth, copyright-free background music track."""
    sample_rate = 24000
    total_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    # Chord progression: Am -> F -> C -> G
    chord_freqs = [
        [220.0, 261.63, 329.63],   # Am
        [174.61, 220.0, 261.63],   # F
        [261.63, 329.63, 392.00],  # C
        [196.00, 246.94, 293.66],  # G
    ]

    beat_dur = 2.5
    track = np.zeros(total_samples)

    for i in range(int(duration_sec / beat_dur) + 1):
        start_idx = int(i * beat_dur * sample_rate)
        end_idx = min(int((i + 1) * beat_dur * sample_rate), total_samples)
        if start_idx >= total_samples:
            break

        chord = chord_freqs[i % len(chord_freqs)]
        t_sub = t[start_idx:end_idx]

        sub_sig = np.zeros(len(t_sub))
        for f in chord:
            # Gentle soft sine with warm harmonics
            sub_sig += 0.3 * np.sin(2 * np.pi * f * t_sub)
            sub_sig += 0.1 * np.sin(2 * np.pi * (f * 2) * t_sub)

        # Smooth envelope
        env = np.ones(len(t_sub))
        fade_len = int(sample_rate * 0.15)
        if len(env) > fade_len * 2:
            env[:fade_len] = np.linspace(0.2, 1.0, fade_len)
            env[-fade_len:] = np.linspace(1.0, 0.2, fade_len)

        track[start_idx:end_idx] += sub_sig * env

    # Add gentle pinkish noise texture
    noise = np.random.normal(0, 0.015, total_samples)
    track += noise

    # Normalize
    track = track / np.max(np.abs(track)) * 0.7
    audio_int16 = (np.clip(track, -1, 1) * 32767).astype(np.int16)

    out_path = os.path.join(MUSIC_DIR, "ambient_groove.wav")
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    print(f"✅ Generated music track: {out_path}")


if __name__ == "__main__":
    print("🎨 Generating starter assets...")
    create_character("neutral", "character_neutral.png")
    create_character("talking", "character_talking.png")
    create_character("shocked", "character_shocked.png")
    create_character("thinking", "character_thinking.png")
    create_stick_figure("stick_figure.png")
    create_backgrounds()
    create_ambient_music(45)
    print("🎉 All starter assets generated successfully!")

