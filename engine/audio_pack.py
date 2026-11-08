#!/usr/bin/env python3
"""
engine/audio_pack.py – Cinematic Royalty-Free BGM & Foley SFX Synthesizer.

Generates studio-quality 48kHz stereo WAV files for background music beds
(Tension, Mystery, Phonk, Upbeat) and Foley sound effects (Whoosh, Gulp,
Impact, Alarm, Ding, Sizzle, Boom) without external dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
BGM_DIR = AUDIO_DIR / "bgm"
SFX_DIR = AUDIO_DIR / "sfx"

SR = 48000
rng = np.random.default_rng(42)


def lp(x, f, o=2):
    b, a = signal.butter(o, min(f, SR / 2 - 100) / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def hp(x, f, o=2):
    b, a = signal.butter(o, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp(x, f0, f1, o=2):
    b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def env(n, a=0.01, r=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    if rest > 0:
        e[na:] = np.exp(-np.linspace(0, r or 5, rest))
    return e


# ==============================================================================
# BGM GENERATORS (48kHz Stereo, 45 seconds loopable)
# ==============================================================================

def generate_bgm_tension(dur=45.0) -> np.ndarray:
    """Dark cinematic drone with slow sub-bass minor pulse."""
    N = int(dur * SR)
    t = np.arange(N) / SR
    
    # Sub-bass drone chords (A1 = 55Hz, C2 = 65.4Hz, E2 = 82.4Hz)
    drone = (
        np.sin(2 * np.pi * 55.0 * t + np.sin(t * 0.4) * 0.5) * 0.4
        + np.sin(2 * np.pi * 65.4 * t) * 0.25
        + np.sin(2 * np.pi * 82.4 * t) * 0.2
        + np.sin(2 * np.pi * 110.0 * t) * 0.15
    )
    # Slow breathing volume envelope
    pulse = 0.5 + 0.5 * np.sin(2 * np.pi * t / 6.0) ** 2
    drone = lp(drone * pulse, 1400)

    # Minor heartbeat / radar ping every 2 seconds
    beat_dur = 2.0
    pings = np.zeros(N)
    for st in np.arange(0, dur - beat_dur, beat_dur):
        idx = int(st * SR)
        pt = np.arange(int(1.2 * SR)) / SR
        ping = (
            np.sin(2 * np.pi * 220.0 * pt) * 0.5
            + np.sin(2 * np.pi * 440.0 * pt) * 0.2
        ) * env(len(pt), a=0.005, r=4)
        pings[idx : idx + len(pt)] += ping * 0.35

    track = drone + lp(pings, 2400)
    # Stereo widening
    left = track
    right = np.roll(track, int(0.012 * SR)) * 0.95
    stereo = np.stack([left, right], axis=1)
    return stereo / (np.abs(stereo).max() + 1e-9) * 0.85


def generate_bgm_mystery(dur=45.0) -> np.ndarray:
    """Eerie atmospheric synth pad with crystal arpeggios."""
    N = int(dur * SR)
    t = np.arange(N) / SR
    
    # Celestial pad
    f_roots = [174.6, 196.0, 220.0, 164.8]  # F, G, A, E
    pad = np.zeros(N)
    bar_len = dur / 8.0
    for b in range(8):
        st = int(b * bar_len * SR)
        root = f_roots[b % len(f_roots)]
        bt = np.arange(int(bar_len * SR)) / SR
        chord = (
            np.sin(2 * np.pi * root * bt)
            + 0.5 * np.sin(2 * np.pi * root * 1.5 * bt)
            + 0.3 * np.sin(2 * np.pi * root * 2.0 * bt)
        ) * np.sin(np.pi * np.linspace(0, 1, len(bt)))
        pad[st : st + len(bt)] += chord * 0.3

    # High crystalline sparkles
    sparkles = np.zeros(N)
    for step in range(int(dur * 3)):
        idx = int((step * 0.33 + rng.uniform(-0.05, 0.05)) * SR)
        if idx >= N - SR:
            break
        note_f = rng.choice([880, 1046, 1174, 1318, 1567])
        st_t = np.arange(int(0.4 * SR)) / SR
        blip = np.sin(2 * np.pi * note_f * st_t) * env(len(st_t), a=0.002, r=7)
        sparkles[idx : idx + len(blip)] += blip * 0.15

    track = lp(pad, 1800) + bp(sparkles, 800, 4000)
    left = track
    right = np.roll(track, int(0.015 * SR))
    stereo = np.stack([left, right], axis=1)
    return stereo / (np.abs(stereo).max() + 1e-9) * 0.82


def generate_bgm_phonk(dur=45.0) -> np.ndarray:
    """Viral Phonk / Drift bass rhythm (128 BPM)."""
    N = int(dur * SR)
    bpm = 128
    beat = 60.0 / bpm
    t = np.arange(N) / SR
    
    # 808 Sub-bass distortion
    bass = np.zeros(N)
    sub_notes = [55.0, 55.0, 65.4, 49.0]
    for b in range(int(dur / (beat * 2))):
        st = int(b * beat * 2 * SR)
        f = sub_notes[b % len(sub_notes)]
        bt = np.arange(int(beat * 1.8 * SR)) / SR
        sub = np.sin(2 * np.pi * f * bt) * env(len(bt), a=0.008, r=3.5)
        # Soft saturation distortion
        sub = np.tanh(sub * 2.2)
        bass[st : st + len(bt)] += sub * 0.45

    # Cowbell melody (classic 808 cowbell simulation)
    bell = np.zeros(N)
    bell_freqs = [587, 880, 587, 784, 880, 659, 587, 784]
    for k in range(int(dur / (beat / 2))):
        st = int(k * (beat / 2) * SR)
        if st >= N - int(0.2 * SR):
            break
        bf = bell_freqs[k % len(bell_freqs)]
        bt = np.arange(int(0.18 * SR)) / SR
        tone = (
            np.sin(2 * np.pi * bf * bt)
            + 0.4 * np.sin(2 * np.pi * (bf * 1.48) * bt)
        ) * env(len(bt), a=0.001, r=10)
        bell[st : st + len(bt)] += tone * 0.28

    track = lp(bass, 600) + bp(bell, 500, 3500)
    left = track
    right = np.roll(track, int(0.008 * SR))
    stereo = np.stack([left, right], axis=1)
    return stereo / (np.abs(stereo).max() + 1e-9) * 0.88


def generate_bgm_upbeat(dur=45.0) -> np.ndarray:
    """Cheerful, bouncy acoustic/marimba explainer track (110 BPM)."""
    N = int(dur * SR)
    bpm = 110
    beat = 60.0 / bpm
    t = np.arange(N) / SR
    
    # Plucked marimba
    marimba = np.zeros(N)
    scale = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3]
    for step in range(int(dur / (beat / 2))):
        st = int(step * (beat / 2) * SR)
        if st >= N - int(0.3 * SR):
            break
        note = scale[(step * 2) % len(scale)]
        mt = np.arange(int(0.25 * SR)) / SR
        pluck = (
            np.sin(2 * np.pi * note * mt)
            + 0.3 * np.sin(2 * np.pi * note * 2 * mt)
            + 0.15 * np.sin(2 * np.pi * note * 3 * mt)
        ) * env(len(mt), a=0.002, r=8)
        marimba[st : st + len(mt)] += pluck * 0.3

    track = lp(marimba, 3200)
    left = track
    right = np.roll(track, int(0.01 * SR))
    stereo = np.stack([left, right], axis=1)
    return stereo / (np.abs(stereo).max() + 1e-9) * 0.85


# ==============================================================================
# FOLEY SFX GENERATORS (Stereo 48kHz)
# ==============================================================================

def sfx_whoosh(d=0.35) -> np.ndarray:
    n = rng.standard_normal(int(d * SR))
    lo = lp(n, 450)
    hi = bp(n, 600, 2800)
    k = np.sin(np.pi * np.linspace(0, 1, len(n)))
    x = (lo * (1 - k) + hi * k) * (k ** 1.6)
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    pan = np.linspace(-0.6, 0.6, len(x))
    return np.stack([x * (1 - pan), x * (1 + pan)], axis=1) * 0.5


def sfx_gulp(d=0.38) -> np.ndarray:
    t1 = np.arange(int(0.16 * SR)) / SR
    a = np.sin(2 * np.pi * (340 - 200 * t1 / 0.16) * t1) * env(len(t1), 0.01, 5)
    t2 = np.arange(int(0.18 * SR)) / SR
    b = np.sin(2 * np.pi * (260 - 150 * t2 / 0.18) * t2) * env(len(t2), 0.01, 5)
    sil = np.zeros(int(0.04 * SR))
    x = np.concatenate([a, sil, b])
    x = lp(x, 1900)
    x = x / (np.abs(x).max() + 1e-9) * 0.95
    return np.stack([x, x], axis=1)


def sfx_impact(d=0.45) -> np.ndarray:
    t = np.arange(int(d * SR)) / SR
    sub = np.sin(2 * np.pi * (90 * np.exp(-t * 22) + 40) * t) * env(len(t), 0.002, 6)
    noise = lp(rng.standard_normal(len(t)), 300) * env(len(t), 0.001, 10) * 0.4
    x = np.tanh(sub + noise)
    return np.stack([x, x], axis=1)


def sfx_boom(d=0.8) -> np.ndarray:
    t = np.arange(int(d * SR)) / SR
    sub = np.sin(2 * np.pi * (120 * np.exp(-t * 12) + 30) * t) * env(len(t), 0.001, 4)
    rumble = lp(rng.standard_normal(len(t)), 180) * env(len(t), 0.01, 3) * 0.5
    x = np.tanh(sub + rumble)
    return np.stack([x, x], axis=1)


def sfx_alarm(d=1.5) -> np.ndarray:
    t = np.arange(int(d * SR)) / SR
    x = np.zeros(len(t))
    beep_t = np.arange(int(0.22 * SR)) / SR
    beep = (np.sin(2 * np.pi * 880 * beep_t) + 0.3 * np.sin(2 * np.pi * 1760 * beep_t)) * env(len(beep_t), 0.01, 5)
    for st in np.arange(0, d - 0.25, 0.45):
        i = int(st * SR)
        x[i : i + len(beep)] += beep
    x = lp(x, 2600)
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    return np.stack([x, x], axis=1)


def sfx_ding(d=0.6) -> np.ndarray:
    t = np.arange(int(d * SR)) / SR
    x = (
        np.sin(2 * np.pi * 1200 * t)
        + 0.4 * np.sin(2 * np.pi * 2400 * t)
        + 0.15 * np.sin(2 * np.pi * 3600 * t)
    ) * env(len(t), 0.001, 7)
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    return np.stack([x, x], axis=1)


def sfx_sizzle(d=1.2) -> np.ndarray:
    t = np.arange(int(d * SR)) / SR
    n = bp(rng.standard_normal(len(t)), 1600, 5000)
    crackle = (rng.random(len(t)) < 0.003).astype(float) * 30
    x = (n * 0.4 + lp(crackle, 400)) * np.sin(np.pi * np.linspace(0, 1, len(t))) ** 0.5
    x = x / (np.abs(x).max() + 1e-9) * 0.8
    return np.stack([x, x], axis=1)


def build_all_assets():
    """Synthesize and save all BGM and SFX assets to disk."""
    BGM_DIR.mkdir(parents=True, exist_ok=True)
    SFX_DIR.mkdir(parents=True, exist_ok=True)

    print("🎵 Synthesizing Studio BGM Audio Pack (48kHz Stereo)...")
    bgms = {
        "tension.wav": generate_bgm_tension(),
        "mystery.wav": generate_bgm_mystery(),
        "phonk.wav": generate_bgm_phonk(),
        "upbeat.wav": generate_bgm_upbeat(),
    }
    for name, data in bgms.items():
        out = BGM_DIR / name
        wavfile.write(out, SR, (data * 32767).astype(np.int16))
        print(f"  ✓ Created BGM: {out.name} ({len(data)/SR:.1f}s)")

    print("\n⚡ Synthesizing Studio Foley SFX Audio Pack (48kHz Stereo)...")
    sfxs = {
        "whoosh.wav": sfx_whoosh(),
        "gulp.wav": sfx_gulp(),
        "impact.wav": sfx_impact(),
        "boom.wav": sfx_boom(),
        "alarm.wav": sfx_alarm(),
        "ding.wav": sfx_ding(),
        "sizzle.wav": sfx_sizzle(),
    }
    for name, data in sfxs.items():
        out = SFX_DIR / name
        wavfile.write(out, SR, (data * 32767).astype(np.int16))
        print(f"  ✓ Created SFX: {out.name} ({len(data)/SR:.2f}s)")

    print("\n✅ All audio assets built successfully in assets/audio/!")


if __name__ == "__main__":
    build_all_assets()
