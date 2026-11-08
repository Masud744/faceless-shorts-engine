#!/usr/bin/env python3
"""Sound effects generation and audio mixing module.

Generates procedural SFX using sine waves and noise (no external samples needed),
and mixes voice, SFX, and optional background music into a final audio track.
"""

import os
import random
import tempfile

import numpy as np
from scipy import signal as scipy_signal
from pydub import AudioSegment

# Audio parameters
SAMPLE_RATE = 24000
BIT_DEPTH = 16


def _normalize(audio: np.ndarray, peak: float = 0.9) -> np.ndarray:
    """Normalize audio array to a target peak amplitude.

    Args:
        audio: Audio samples as float64 array.
        peak: Target peak amplitude (0.0 to 1.0).

    Returns:
        Normalized audio array.
    """
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio * (peak / max_val)
    return audio


def _fade(audio: np.ndarray, fade_in_ms: int = 5, fade_out_ms: int = 5) -> np.ndarray:
    """Apply fade-in and fade-out to an audio array to avoid clicks.

    Args:
        audio: Audio samples.
        fade_in_ms: Fade-in duration in milliseconds.
        fade_out_ms: Fade-out duration in milliseconds.

    Returns:
        Audio with fades applied.
    """
    fade_in_samples = int(SAMPLE_RATE * fade_in_ms / 1000)
    fade_out_samples = int(SAMPLE_RATE * fade_out_ms / 1000)

    if fade_in_samples > 0 and len(audio) > fade_in_samples:
        fade_in = np.linspace(0, 1, fade_in_samples)
        audio[:fade_in_samples] *= fade_in

    if fade_out_samples > 0 and len(audio) > fade_out_samples:
        fade_out = np.linspace(1, 0, fade_out_samples)
        audio[-fade_out_samples:] *= fade_out

    return audio


def _generate_sine_burst(
    freq: float, duration_ms: int, amplitude: float = 0.5
) -> np.ndarray:
    """Generate a short sine wave burst.

    Args:
        freq: Frequency in Hz.
        duration_ms: Duration in milliseconds.
        amplitude: Peak amplitude (0.0 to 1.0).

    Returns:
        Audio samples as float64 array.
    """
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    wave = amplitude * np.sin(2 * np.pi * freq * t)
    return _fade(wave, fade_in_ms=3, fade_out_ms=10)


def _generate_noise_burst(duration_ms: int, amplitude: float = 0.3) -> np.ndarray:
    """Generate a short burst of filtered noise.

    Args:
        duration_ms: Duration in milliseconds.
        amplitude: Peak amplitude.

    Returns:
        Audio samples as float64 array.
    """
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    noise = np.random.randn(n_samples) * amplitude
    # Low-pass filter to make it less harsh
    b, a = scipy_signal.butter(4, 2000 / (SAMPLE_RATE / 2), btype='low')
    filtered = scipy_signal.lfilter(b, a, noise)
    return _fade(filtered, fade_in_ms=5, fade_out_ms=15)


def _generate_comedy_sfx() -> np.ndarray:
    """Generate a random comedy sound effect (pop, boing, slide whistle).

    Returns:
        Audio samples for one comedy SFX event.
    """
    effect_type = random.choice(["pop", "boing", "slide", "honk"])

    if effect_type == "pop":
        # Quick high-frequency pop
        burst = _generate_sine_burst(
            freq=random.uniform(800, 1200),
            duration_ms=random.randint(30, 80),
            amplitude=0.6,
        )
        return burst

    elif effect_type == "boing":
        # Descending frequency sweep (boing/spring)
        duration_ms = random.randint(150, 300)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        freq_start = random.uniform(600, 1000)
        freq_end = random.uniform(150, 300)
        # Exponential frequency sweep
        freqs = freq_start * (freq_end / freq_start) ** (t / t[-1])
        phase = 2 * np.pi * np.cumsum(freqs) / SAMPLE_RATE
        wave = 0.5 * np.sin(phase)
        return _fade(wave, fade_in_ms=2, fade_out_ms=30)

    elif effect_type == "slide":
        # Ascending slide whistle
        duration_ms = random.randint(200, 400)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        freq_start = random.uniform(200, 400)
        freq_end = random.uniform(1000, 2000)
        freqs = freq_start + (freq_end - freq_start) * (t / t[-1]) ** 2
        phase = 2 * np.pi * np.cumsum(freqs) / SAMPLE_RATE
        wave = 0.4 * np.sin(phase)
        return _fade(wave, fade_in_ms=5, fade_out_ms=20)

    else:  # honk
        # Short brassy honk (two harmonics)
        duration_ms = random.randint(100, 200)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        freq = random.uniform(250, 400)
        wave = 0.4 * np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(
            2 * np.pi * freq * 2 * t
        )
        return _fade(wave, fade_in_ms=3, fade_out_ms=15)


def _generate_dramatic_sfx() -> np.ndarray:
    """Generate a random dramatic sound effect (rumble, hit, swell).

    Returns:
        Audio samples for one dramatic SFX event.
    """
    effect_type = random.choice(["rumble", "hit", "swell"])

    if effect_type == "rumble":
        # Low-frequency rumble
        duration_ms = random.randint(400, 800)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        freq = random.uniform(30, 80)
        wave = 0.5 * np.sin(2 * np.pi * freq * t)
        # Add some noise texture
        noise = np.random.randn(n_samples) * 0.1
        b, a = scipy_signal.butter(4, 150 / (SAMPLE_RATE / 2), btype='low')
        noise = scipy_signal.lfilter(b, a, noise)
        return _fade(wave + noise, fade_in_ms=50, fade_out_ms=100)

    elif effect_type == "hit":
        # Impact hit: sharp attack with low decay
        duration_ms = random.randint(200, 400)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        # Decaying envelope
        envelope = np.exp(-t * 8)
        freq = random.uniform(60, 120)
        wave = 0.7 * np.sin(2 * np.pi * freq * t) * envelope
        # Add transient click
        noise = _generate_noise_burst(30, amplitude=0.5)
        if len(noise) < n_samples:
            padded = np.zeros(n_samples)
            padded[: len(noise)] = noise
            wave += padded
        return _fade(wave, fade_in_ms=1, fade_out_ms=30)

    else:  # swell
        # Rising orchestral swell (sine cluster)
        duration_ms = random.randint(600, 1200)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        envelope = np.sin(np.pi * t / t[-1])  # bell curve
        base_freq = random.uniform(100, 200)
        wave = np.zeros(n_samples)
        for harmonic in [1, 1.5, 2, 3]:
            wave += (0.3 / harmonic) * np.sin(2 * np.pi * base_freq * harmonic * t)
        return _fade(wave * envelope, fade_in_ms=80, fade_out_ms=120)


def _generate_eerie_sfx() -> np.ndarray:
    """Generate a random eerie sound effect (drone, whisper, dissonance).

    Returns:
        Audio samples for one eerie SFX event.
    """
    effect_type = random.choice(["drone", "whisper_noise", "dissonance"])

    if effect_type == "drone":
        # Low evolving drone
        duration_ms = random.randint(800, 1500)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        freq = random.uniform(50, 100)
        # Slow frequency modulation
        mod = 0.5 * np.sin(2 * np.pi * 0.3 * t)
        wave = 0.4 * np.sin(2 * np.pi * (freq + mod * 10) * t)
        return _fade(wave, fade_in_ms=150, fade_out_ms=200)

    elif effect_type == "whisper_noise":
        # Filtered noise that sounds like a ghostly whisper
        duration_ms = random.randint(400, 800)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        noise = np.random.randn(n_samples) * 0.3
        # Band-pass filter in the "whisper" range
        low = 800 / (SAMPLE_RATE / 2)
        high = min(3000 / (SAMPLE_RATE / 2), 0.99)
        b, a = scipy_signal.butter(3, [low, high], btype='band')
        filtered = scipy_signal.lfilter(b, a, noise)
        # Amplitude modulation for uneven texture
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * random.uniform(2, 6) * t
                                   if False else np.linspace(0, 1, n_samples))
        env = np.sin(np.pi * np.linspace(0, 1, n_samples))
        return _fade(filtered * env, fade_in_ms=50, fade_out_ms=100)

    else:  # dissonance
        # Two clashing frequencies for unsettling feel
        duration_ms = random.randint(500, 1000)
        n_samples = int(SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
        f1 = random.uniform(200, 350)
        f2 = f1 * random.choice([1.06, 1.12, 1.41])  # dissonant intervals
        wave = 0.3 * np.sin(2 * np.pi * f1 * t) + 0.3 * np.sin(2 * np.pi * f2 * t)
        envelope = np.sin(np.pi * t / t[-1])
        return _fade(wave * envelope, fade_in_ms=80, fade_out_ms=120)


# Map style names to their SFX generators
_SFX_GENERATORS = {
    "comedy": _generate_comedy_sfx,
    "dramatic": _generate_dramatic_sfx,
    "eerie": _generate_eerie_sfx,
}


def generate_sfx_audio(duration: float, style: str = "comedy") -> str:
    """Generate a procedural sound effects track of the given duration.

    Creates several randomly-timed SFX events throughout the duration using
    sine waves and filtered noise. No external audio samples are needed.

    Args:
        duration: Total duration in seconds.
        style: SFX style preset. One of "comedy", "dramatic", "eerie".

    Returns:
        Path to the generated SFX WAV file.

    Raises:
        ValueError: If style is not recognized.
    """
    if style not in _SFX_GENERATORS:
        raise ValueError(
            f"Unknown style '{style}'. Available: {list(_SFX_GENERATORS.keys())}"
        )

    generator = _SFX_GENERATORS[style]
    total_samples = int(SAMPLE_RATE * duration)
    output = np.zeros(total_samples)

    # Decide how many SFX events to place
    num_events = max(2, int(duration / 3))  # roughly one every 3 seconds
    num_events = min(num_events, 20)  # cap at 20

    # Generate and place events at random positions
    for _ in range(num_events):
        sfx = generator()
        # Random position, avoiding the very start and end
        margin = int(SAMPLE_RATE * 0.5)
        max_pos = total_samples - len(sfx) - margin
        if max_pos <= margin:
            pos = 0
        else:
            pos = random.randint(margin, max_pos)

        # Mix into output
        end_pos = min(pos + len(sfx), total_samples)
        sfx_trimmed = sfx[: end_pos - pos]
        output[pos:end_pos] += sfx_trimmed

    # Normalize to avoid clipping
    output = _normalize(output, peak=0.8)

    # Save as WAV
    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", f"sfx_{style}.wav")

    # Convert to int16
    audio_int16 = (np.clip(output, -1, 1) * 32767).astype(np.int16)
    segment = AudioSegment(
        data=audio_int16.tobytes(),
        sample_width=2,
        frame_rate=SAMPLE_RATE,
        channels=1,
    )
    segment.export(out_path, format="wav")

    print(f"[sfx_mixer] Generated {style} SFX track ({duration:.1f}s) -> {out_path}")
    return out_path


def generate_sfx(
    scenes: list = None,
    profile: str = "comedy",
    duration: float = 35.0,
    output_dir: str = "output",
    **kwargs,
) -> str:
    """Wrapper matching make_video invocation."""
    os.makedirs(output_dir, exist_ok=True)
    style = profile if profile in _SFX_GENERATORS else "comedy"
    return generate_sfx_audio(duration=duration, style=style)


def mix_audio(
    voice_path: str = None,
    sfx_path: str = None,
    music_path: str | None = None,
    output_path: str = "output/mixed.wav",
    tracks: list[str] = None,
    output_dir: str = None,
    **kwargs,
) -> str:
    """Mix voice, SFX, and optional background music into a single audio file.

    Voice is kept at full volume. SFX is mixed at 30% volume, and background
    music (if provided) at 15% volume to keep narration clearly audible.
    Supports either direct arguments or tracks list.
    """
    if tracks is not None:
        voice_path = tracks[0] if len(tracks) > 0 else None
        sfx_path = tracks[1] if len(tracks) > 1 else None
        if output_dir:
            output_path = os.path.join(output_dir, "mixed.wav")

    if not voice_path or not os.path.exists(voice_path):
        raise FileNotFoundError(f"Voice file not found: {voice_path}")
    if not sfx_path or not os.path.exists(sfx_path):
        # If SFX is not available, just return the voice path
        return voice_path

    # Load audio tracks
    voice = AudioSegment.from_file(voice_path)
    sfx = AudioSegment.from_file(sfx_path)

    # Target duration is the voice track length
    target_duration = len(voice)

    # Adjust SFX to match voice duration
    if len(sfx) < target_duration:
        # Loop SFX if too short
        loops_needed = (target_duration // len(sfx)) + 1
        sfx = sfx * loops_needed
    sfx = sfx[:target_duration]

    # Reduce SFX volume to 30% (-10.5 dB ≈ 30%)
    sfx = sfx - 10.5

    # Start with voice + SFX
    mixed = voice.overlay(sfx)

    # Add music if provided
    if music_path:
        if not os.path.exists(music_path):
            print(f"[sfx_mixer] Warning: Music file not found: {music_path}, skipping")
        else:
            music = AudioSegment.from_file(music_path)
            # Loop or trim music to match duration
            if len(music) < target_duration:
                loops_needed = (target_duration // len(music)) + 1
                music = music * loops_needed
            music = music[:target_duration]
            # Reduce music volume to 15% (-16.5 dB ≈ 15%)
            music = music - 16.5
            # Fade in/out music
            music = music.fade_in(1000).fade_out(1000)
            mixed = mixed.overlay(music)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Export
    mixed.export(output_path, format="wav")
    print(f"[sfx_mixer] Mixed audio saved to: {output_path}")
    print(f"[sfx_mixer]   Duration: {len(mixed) / 1000:.2f}s")

    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("SFX Mixer Test")
    print("=" * 60)

    # Test SFX generation for each style
    test_duration = 10.0  # 10 seconds

    for style in ["comedy", "dramatic", "eerie"]:
        print(f"\nGenerating {style} SFX...")
        try:
            sfx_path = generate_sfx_audio(test_duration, style)
            sfx = AudioSegment.from_file(sfx_path)
            print(f"  Duration: {len(sfx)/1000:.2f}s | File: {sfx_path}")
        except Exception as e:
            print(f"  Error: {e}")

    # Test mixing if voice file exists
    voice_file = "output/test_voice.wav"
    sfx_file = "output/sfx_comedy.wav"

    if os.path.exists(voice_file) and os.path.exists(sfx_file):
        print(f"\nMixing voice + SFX...")
        try:
            mixed = mix_audio(voice_file, sfx_file)
            print(f"Success! Mixed audio: {mixed}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"\nSkipped mix test (need {voice_file} and {sfx_file})")
        print("Run voice_gen.py first to create test voice audio.")
