#!/usr/bin/env python3
"""
engine/scene_mapper.py – Dynamic 3D Scene Engine & Shot Generator for Faceless Shorts.

Analyzes generated narrative scripts and dynamically synthesizes a complete,
deterministic Three.js 3D shot list (`src/shots.js`) with camera choreography,
anatomical props, visual HUD callouts, and frame-synced Foley sound cues.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def detect_scene_beat(text: str, index: int, total: int) -> Dict[str, Any]:
    """Classify a narrative line into an appropriate 3D scene beat and camera action."""
    t = text.lower()

    if index == 0:
        return {
            "type": "hook",
            "note": "kitchen close-up: chew chew, gulp, shocked eyes",
            "camera": "face_dolly",
            "hud": "HOOK_PILL",
            "sfx": ["gulp", "whoosh"],
        }
    elif index == total - 1:
        return {
            "type": "takeaway",
            "note": "wide takeaway: silhouette with final warning badge",
            "camera": "wide_pullback",
            "hud": "TAKEAWAY_PILL",
            "sfx": ["ding", "whoosh"],
        }
    elif any(w in t for w in ["blood", "vessel", "cell", "flow", "oxygen", "heart", "vein"]):
        return {
            "type": "vessel",
            "note": "microscopic vessel: red blood cells flowing through vascular tunnel",
            "camera": "vessel_travel",
            "hud": "VESSEL_LABEL",
            "sfx": ["sparkle", "tock"],
        }
    elif any(w in t for w in ["acid", "bubble", "melt", "dissolve", "burn", "digest", "stomach"]):
        return {
            "type": "stomach",
            "note": "macro stomach closeup: acidic reaction and churning motion",
            "camera": "stomach_macro",
            "hud": "ACID_LABEL",
            "sfx": ["bubbles", "sizzle"],
        }
    elif any(w in t for w in ["block", "clump", "danger", "warning", "fatal", "harm", "trap", "stuck"]):
        return {
            "type": "warning",
            "note": "x-ray red warning: blockage alert and flashing red silhouette",
            "camera": "warning_orbit",
            "hud": "RED_ALERT",
            "sfx": ["alarm", "impact"],
        }
    elif any(w in t for w in ["throat", "swallow", "slide", "down", "travel", "esophagus", "inside"]):
        return {
            "type": "esophagus",
            "note": "x-ray descent: object slides down the esophagus into torso",
            "camera": "torso_pan",
            "hud": "ESOPHAGUS_LABEL",
            "sfx": ["whoosh", "slide"],
        }
    else:
        return {
            "type": "xray_organ",
            "note": "x-ray rotating organ view with glowing skeleton",
            "camera": "organ_orbit",
            "hud": "ORGAN_LABEL",
            "sfx": ["whoosh"],
        }


def generate_shots_js(script_data: Dict[str, Any], project_dir: Path) -> str:
    """Dynamically synthesize a complete Three.js src/shots.js tailored to script lines."""
    lines = script_data.get("lines", [])
    title = script_data.get("title", "Animated Explainer")
    total = len(lines)

    shots_code = f"""// Auto-Generated Dynamic 3D Scene Architecture for: {title}
// Synthesized by Faceless Shorts Engine Scene Mapper
import * as THREE from 'three';
import {{ ctx, W, H, clamp, lerp, seg, eo, eio, eob }} from './core/lib.js';
import {{ L, Wd, T }} from './core/timing.js';
import {{ camera }} from './core/engine.js';
import {{ Human }} from './core/human.js';
import * as SETS from './core/sets.js';
import {{ label, pill, warning, blackout }} from './core/look2d.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
function screen(p, cam) {{ const v = p.clone().project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; }}

export function buildShots(E) {{
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
  const cam = camera(30);
  const KLOOK = {{ aperture: 0.003, maxblur: 0.01, bloom: 0.2 }},
        XLOOK = {{ aperture: 0.0015, bloom: 0.55, bloomThreshold: 0.4, vignette: 0.45 }},
        VLOOK = {{ aperture: 0.005, maxblur: 0.012, bloom: 0.6, bloomThreshold: 0.5, focus: 3.2 }};

  // ── 3D Environments & Sets ──────────────────────────────────────────────
  const K = SETS.kitchen(E), hero = new Human({{}}); hero.group.position.set(0.1, 0, -0.6); K.scene.add(hero.group);
  const X = SETS.xrayStage(E), xh = new Human({{}}), xmat = SETS.xrayMaterial(); xh.setBodyMaterial(xmat);
  const I = SETS.insides(); xh.spine.add(I.group); X.scene.add(xh.group);
  const VS = SETS.vessel(E);

  // 3D Animated Molecule / Object Prop
  const propMat = new THREE.MeshPhysicalMaterial({{ color: '#FF69B4', roughness: 0.25, clearcoat: 0.8, emissive: '#FF1493', emissiveIntensity: 0.2 }});
  const prop = new THREE.Mesh(new THREE.SphereGeometry(0.025, 24, 24), propMat);
  xh.spine.add(prop);

  const CYAN = new THREE.Color('#4FD1E8'), RED = new THREE.Color('#FF3B3B');
  const reset = () => {{
    hero.pose({{}}); xh.pose({{}});
    prop.visible = false;
    xmat.uniforms.uCol.value.copy(CYAN);
  }};
  const kitchenRender = (focus, extra = {{}}) => E.render(K.scene, cam, {{ ...KLOOK, focus, ...extra }});
  const FACE = V3(0.1, 1.68, -0.6);
"""

    # Generate individual scene blocks
    for i, line in enumerate(lines):
        beat = detect_scene_beat(line.get("text", ""), i, total)
        b_type = beat["type"]
        note = beat["note"]
        s_id = f"S{i+1:02d}"

        shots_code += f"\n  // ── Cut {i}: {beat['type'].upper()} ──\n"
        shots_code += f"  {{ const st = cut({i});\n"
        shots_code += f"    add({{ id: '{s_id}', at: st, note: '{note}', draw(lt, d, t, blit) {{\n"

        if b_type == "hook":
            shots_code += f"""      reset(); const chew = Math.sin(lt * 12);
      const k = eo(seg(lt, 0.8, 1.5));
      hero.pose({{ head: [-4 * k, chew * 3, 0], lid: lerp(-0.1, -0.4, k), look: [0, -3 * k] }});
      cam.position.copy(lerpV(V3(0.38, 1.72, 0.45), V3(0.24, 1.7, 0.12), eio(lt / d)));
      cam.lookAt(FACE); kitchenRender(cam.position.distanceTo(FACE)); blit();
      pill('{title.upper()[:22]}', 540, 1180, eob(seg(lt, 0.9, 1.3)), '#FACC15');
    }} }});
    cue(st + 0.9, 'gulp', {{ dur: 0.4 }});
    cue(st, 'whoosh');
  }}\n"""

        elif b_type == "esophagus":
            shots_code += f"""      reset(); prop.visible = true;
      const progress = eio(clamp(lt / d));
      prop.position.set(0.01 + Math.sin(progress * 4) * 0.008, lerp(0.44, 0.14, progress), 0.02);
      prop.scale.set(0.8, 1.2, 0.8);
      xh.pose({{ head: [2, -4, 0] }});
      cam.position.copy(lerpV(V3(0.4, 1.45, 1.3), V3(0.15, 1.35, 0.9), eio(lt / d)));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, {{ ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.3, 0)) }}); blit();
      const [lx, ly] = screen(V3(0.02, 1.35, 0.05), cam);
      label('ESOPHAGUS DESCENT', 720, 520, lx, ly, eob(seg(lt, 0.15, 0.4)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', {{ dur: cut({min(i+1, total-1)}) - st }});
  }}\n"""

        elif b_type == "stomach":
            shots_code += f"""      reset(); prop.visible = true;
      prop.position.set(0.03 + Math.sin(lt * 2) * 0.005, 0.13 + Math.cos(lt * 3) * 0.004, 0.03);
      I.stomach.scale.setScalar(1 + Math.sin(lt * 4) * 0.03);
      cam.position.copy(lerpV(V3(0.18, 1.24, 0.75), V3(0.08, 1.22, 0.5), eio(lt / d)));
      cam.lookAt(0.03, 1.2, 0.02);
      E.render(X.scene, cam, {{ ...XLOOK, bloom: 0.65, focus: cam.position.distanceTo(V3(0.03, 1.2, 0.02)) }}); blit();
      const [lx, ly] = screen(V3(0.03, 1.2, 0.02), cam);
      label('GASTRIC REACTION', 750, 480, lx, ly, eob(seg(lt, 0.2, 0.45)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.1, 'bubbles', {{ dur: cut({min(i+1, total-1)}) - st }});
  }}\n"""

        elif b_type == "vessel":
            shots_code += f"""      reset();
      const camZ = lerp(12, -4, eio(lt / d));
      cam.position.set(0, 0, camZ); cam.lookAt(0, 0, camZ - 5);
      VS.update(t, camZ, 0.2, 0);
      E.render(VS.scene, cam, {{ ...VLOOK }}); blit();
      label('VASCULAR FLOW', 540, 480, 540, 720, eob(seg(lt, 0.15, 0.4)));
    }} }});
    cue(st, 'sparkle');
  }}\n"""

        elif b_type == "warning":
            shots_code += f"""      reset();
      const k = eio(clamp(lt / d));
      xmat.uniforms.uCol.value.copy(RED);
      cam.position.copy(lerpV(V3(0.35, 1.2, 0.9), V3(0.0, 1.15, 0.7), k));
      cam.lookAt(0, 1.1, 0);
      E.render(X.scene, cam, {{ ...XLOOK, bloom: 0.8 }}); blit();
      warning('INTERNAL WARNING', 540, 1280, eob(seg(lt, 0.1, 0.35)));
    }} }});
    cue(st, 'alarm', {{ dur: 1.5 }}); cue(st + 0.1, 'impact');
  }}\n"""

        else:  # Takeaway or General Organ Orbit
            shots_code += f"""      reset();
      const k = eio(clamp(lt / d));
      cam.position.copy(lerpV(V3(0.2, 1.4, 1.2), V3(0.35, 1.5, 1.6), k));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, {{ ...XLOOK, bloom: 0.4 }}); blit();
      pill('FINAL TAKEAWAY', 540, 1280, eob(seg(lt, 0.15, 0.4)), '#FACC15');
    }} }});
    cue(st, 'ding'); cue(st + 0.1, 'whoosh');
  }}\n"""

    shots_code += f"""
  return {{ shots: S, cues: CUES, duration: T || (L({max(0, total - 1)}) + 1.2) }};
}}
"""
    return shots_code


def map_project_scenes(project_path: Path, style: str = "deep-dive") -> Path:
    """Read project script.json and write dynamically synthesized src/shots.js."""
    project_dir = Path(project_path).resolve()
    script_file = project_dir / "script.json"

    if not script_file.exists():
        raise FileNotFoundError(f"Missing script.json in {project_dir}")

    with open(script_file, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    shots_code = generate_shots_js(script_data, project_dir)
    target_shots = project_dir / "src" / "shots.js"
    target_shots.parent.mkdir(parents=True, exist_ok=True)

    with open(target_shots, "w", encoding="utf-8") as f:
        f.write(shots_code)

    print(f"🎬 Successfully mapped {len(script_data.get('lines', []))} 3D dynamic scenes to {target_shots}")
    return target_shots


def main():
    parser = argparse.ArgumentParser(description="Dynamic 3D Scene Mapper for Faceless Shorts")
    parser.add_argument("project", help="Path to project directory")
    parser.add_argument("--style", default="deep-dive", help="Animation style")
    args = parser.parse_args()

    map_project_scenes(Path(args.project), style=args.style)


if __name__ == "__main__":
    main()
