// WHAT HAPPENS IF YOU SWALLOW GUM? : Deep Dive 3D shot list
import * as THREE from 'three';
import { ctx, W, H, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { Human } from './core/human.js';
import * as SETS from './core/sets.js';
import { label, pill, warning, blackout } from './core/look2d.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
function screen(p, cam) { const v = p.clone().project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; }

export function buildShots(E) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
  const cam = camera(30);
  const KLOOK = { aperture: 0.003, maxblur: 0.01, bloom: 0.2 },
        XLOOK = { aperture: 0.0015, bloom: 0.55, bloomThreshold: 0.4, vignette: 0.45 },
        VLOOK = { aperture: 0.005, maxblur: 0.012, bloom: 0.6, bloomThreshold: 0.5, focus: 3.2 };

  // ── the world ──────────────────────────────────────────────────────────
  const K = SETS.kitchen(E), hero = new Human({}); hero.group.position.set(0.1, 0, -0.6); K.scene.add(hero.group);
  const X = SETS.xrayStage(E), xh = new Human({}), xmat = SETS.xrayMaterial(); xh.setBodyMaterial(xmat);
  const I = SETS.insides(); xh.spine.add(I.group); X.scene.add(xh.group);
  const VS = SETS.vessel(E);

  // 3D Pink Gum Prop
  const gumMat = new THREE.MeshPhysicalMaterial({ color: '#FF69B4', roughness: 0.25, clearcoat: 0.8, emissive: '#FF1493', emissiveIntensity: 0.15 });
  const gum = new THREE.Mesh(new THREE.SphereGeometry(0.024, 24, 24), gumMat);
  xh.spine.add(gum);

  // Clump of gum
  const clump = new THREE.Group();
  for (let i = 0; i < 7; i++) {
    const g = new THREE.Mesh(new THREE.SphereGeometry(0.018 + (i % 3) * 0.006, 16, 16), gumMat);
    g.position.set(Math.sin(i * 1.8) * 0.025, Math.cos(i * 2.2) * 0.025, Math.sin(i * 3.1) * 0.02);
    clump.add(g);
  }
  xh.spine.add(clump); clump.visible = false;

  const CYAN = new THREE.Color('#4FD1E8'), RED = new THREE.Color('#FF3B3B');
  const reset = () => {
    hero.pose({}); xh.pose({});
    gum.visible = false; clump.visible = false;
    gum.scale.set(1, 1, 1);
    xmat.uniforms.uCol.value.copy(CYAN);
  };
  const kitchenRender = (focus, extra = {}) => E.render(K.scene, cam, { ...KLOOK, focus, ...extra });
  const FACE = V3(0.1, 1.68, -0.6);

  // 1 · HOOK: Chewing gum, accidental swallow (eyes pop wide)
  { const st = cut(0);
    add({ id: 'S01', at: st, note: 'kitchen close-up: chew chew, gulp, shocked eyes', draw(lt, d, t, blit) {
      reset(); const chew = Math.sin(lt * 12);
      const k = eo(seg(lt, 0.9, 1.6));
      hero.pose({
        head: [-4 * k, chew * 3, 0],
        lid: lerp(-0.1, -0.4, k),
        look: [0, -3 * k],
      });
      cam.position.copy(lerpV(V3(0.38, 1.72, 0.45), V3(0.24, 1.7, 0.12), eio(lt / d)));
      cam.lookAt(FACE); kitchenRender(cam.position.distanceTo(FACE)); blit();
      pill('GUM SWALLOWED!', 540, 1180, eob(seg(lt, 1.0, 1.35)), '#FF69B4');
    } });
    cue(st + 0.95, 'gulp', { dur: 0.5 });
  }

  // 2 · Slides down throat into stomach (x-ray cutaway)
  { const st = cut(1);
    add({ id: 'S02', at: st, note: 'x-ray throat to stomach: gum descends esophagus', draw(lt, d, t, blit) {
      reset(); gum.visible = true;
      const progress = eio(clamp(lt / d));
      // travel from esophagus (y 0.42) down to stomach (y 0.14)
      gum.position.set(0.01 + Math.sin(progress * 4) * 0.008, lerp(0.44, 0.14, progress), 0.02);
      gum.scale.set(0.8, 1.2, 0.8); // stretch as it slides
      xh.pose({ head: [2, -4, 0] });
      cam.position.copy(lerpV(V3(0.4, 1.45, 1.3), V3(0.15, 1.35, 0.9), eio(lt / d)));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.3, 0)) }); blit();
      const [lx, ly] = screen(V3(0.02, 1.35, 0.05), cam);
      label('ESOPHAGUS', 720, 520, lx, ly, eob(seg(lt, 0.15, 0.4)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', { dur: cut(2) - st });
  }

  // 3 · Stomach acid gets to work (macro stomach view)
  { const st = cut(2);
    add({ id: 'S03', at: st, note: 'stomach closeup: acid bubbling around gum', draw(lt, d, t, blit) {
      reset(); gum.visible = true;
      gum.position.set(0.03 + Math.sin(lt * 2) * 0.005, 0.13 + Math.cos(lt * 3) * 0.004, 0.03);
      I.stomach.scale.setScalar(1 + Math.sin(lt * 4) * 0.03);
      cam.position.copy(lerpV(V3(0.18, 1.24, 0.75), V3(0.08, 1.22, 0.5), eio(lt / d)));
      cam.lookAt(0.03, 1.2, 0.02);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.65, focus: cam.position.distanceTo(V3(0.03, 1.2, 0.02)) }); blit();
      const [lx, ly] = screen(V3(0.03, 1.2, 0.02), cam);
      label('STOMACH ACID (pH 2)', 750, 480, lx, ly, eob(seg(lt, 0.2, 0.45)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'bubbles', { dur: cut(3) - st });
  }

  // 4 · Sugar dissolves, rubber base remains
  { const st = cut(3);
    add({ id: 'S04', at: st, note: 'sugars dissolve away, core stays intact', draw(lt, d, t, blit) {
      reset(); gum.visible = true;
      const k = eio(clamp(lt / d));
      gum.position.set(0.03, 0.13, 0.03);
      gum.scale.setScalar(lerp(1.2, 0.85, k)); // shrinks slightly as sugar dissolves
      cam.position.copy(lerpV(V3(-0.15, 1.25, 0.65), V3(-0.05, 1.22, 0.45), eio(lt / d)));
      cam.lookAt(0.03, 1.2, 0.02);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0.03, 1.2, 0.02)) }); blit();
      pill('SUGAR: DISSOLVED ✓', 540, 340, eob(seg(lt, 0.1, 0.3)), '#7CF29A');
      pill('BASE: INTACT', 540, 430, eob(seg(lt, 0.4, 0.65)), '#FFD43B');
    } });
    cue(st, 'whoosh'); cue(st + 0.35, 'pop', { gain: 0.5 });
  }

  // 5 · Rubbery polymer: body cannot break it down
  { const st = cut(4);
    add({ id: 'S05', at: st, note: 'molecular zoom: synthetic rubber polymer chain resists', draw(lt, d, t, blit) {
      reset(); gum.visible = true; gum.position.set(0.03, 0.13, 0.03);
      VS.update(t, -lt * 1.1, 0.2, 0);
      cam.position.set(Math.sin(lt * 0.5) * 0.08, 0, -lt * 1.1);
      cam.lookAt(0.05, 0, -lt * 1.1 - 4);
      E.render(VS.scene, cam, VLOOK); blit();
      pill('SYNTHETIC POLYMER', 540, 330, eob(seg(lt, 0.1, 0.35)), '#FFA07A');
      pill('INDIGESTIBLE', 540, 420, eob(seg(lt, 0.4, 0.65)), '#FF4D4D');
    } });
    cue(st, 'whoosh');
  }

  // 6 · 7 Years? Total myth!
  { const st = cut(5);
    add({ id: 'S06', at: st, note: 'x-ray body: red 7 YEARS? TOTAL MYTH stamp', draw(lt, d, t, blit) {
      reset(); xh.pose({ head: [-2, 8 * Math.sin(lt * 2), 0] });
      cam.position.copy(lerpV(V3(0.6, 1.45, 1.6), V3(0.2, 1.38, 1.1), eio(lt / d)));
      cam.lookAt(0, 1.28, 0);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.28, 0)) }); blit();
      pill('7 YEARS? ✕', 540, 1150, eob(seg(lt, 0.1, 0.35)), '#FF4D4D', 'rgba(10,10,15,0.85)', 78);
      pill('TOTAL MYTH', 540, 1260, eob(seg(lt, 0.4, 0.65)), '#FFD700', 'rgba(10,10,15,0.85)', 68);
    } });
    cue(st, 'whoosh'); cue(st + 0.12, 'thud', { gain: 0.7 });
  }

  // 7 · Gut keeps pushing it along (peristalsis)
  { const st = cut(6);
    add({ id: 'S07', at: st, note: 'x-ray abdomen: intestines move gum along', draw(lt, d, t, blit) {
      reset(); gum.visible = true;
      const progress = eio(clamp(lt / d));
      // moving through intestinal curves
      gum.position.set(0.04 + Math.sin(progress * 8) * 0.03, lerp(0.08, -0.02, progress), 0.04);
      cam.position.copy(lerpV(V3(-0.35, 1.2, 1.3), V3(-0.1, 1.15, 0.95), eio(lt / d)));
      cam.lookAt(0.02, 1.12, 0);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0.02, 1.12, 0)) }); blit();
      const [lx, ly] = screen(V3(0.04, 1.12, 0.04), cam);
      label('PERISTALSIS', 730, 1180, lx, ly, eob(seg(lt, 0.2, 0.45)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', { dur: cut(7) - st });
  }

  // 8 · Out of your system in a few days
  { const st = cut(7);
    add({ id: 'S08', at: st, note: 'timeline: 1 to 3 days, out safely', draw(lt, d, t, blit) {
      reset();
      cam.position.copy(lerpV(V3(0.45, 1.35, 1.4), V3(0.15, 1.3, 1.0), eio(lt / d)));
      cam.lookAt(0, 1.2, 0);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.2, 0)) }); blit();
      const day = Math.min(3, 1 + Math.floor(lt / (d * 0.35)));
      pill(`DAY ${day}`, 540, 1160, eob(seg(lt, 0.05, 0.25)), '#7CF29A', 'rgba(10,12,18,0.85)', 76);
      pill('EXPELLED SAFELY ✓', 540, 1260, eob(seg(lt, 0.35, 0.6)), '#7CF29A');
    } });
    cue(st, 'whoosh'); cue(st + 0.35, 'pop', { gain: 0.6 });
  }

  // 9 · If you swallow a lot of gum at once
  { const st = cut(8);
    add({ id: 'S09', at: st, note: 'warning: multiple gum pieces clumping together', draw(lt, d, t, blit) {
      reset(); clump.visible = true;
      clump.position.set(0.03, 0.06, 0.03);
      clump.scale.setScalar(lerp(0.6, 1.4, eio(clamp(lt / d))));
      cam.position.copy(lerpV(V3(0.3, 1.22, 0.9), V3(0.1, 1.18, 0.6), eio(lt / d)));
      cam.lookAt(0.03, 1.14, 0.03);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0.03, 1.14, 0.03)) }); blit();
      pill('TOO MUCH GUM', 540, 330, eob(seg(lt, 0.1, 0.35)), '#FFA07A');
      pill('STICKY MASS', 540, 420, eob(seg(lt, 0.4, 0.65)), '#FF4D4D');
    } });
    cue(st, 'whoosh'); cue(st + 0.3, 'thud', { gain: 0.6 });
  }

  // 10 · Block your gut (red alert, obstruction)
  { const st = cut(9);
    add({ id: 'S10', at: st, note: 'x-ray turns red: intestinal obstruction alarm', draw(lt, d, t, blit) {
      reset(); clump.visible = true; clump.position.set(0.03, 0.04, 0.03); clump.scale.setScalar(1.5);
      const pulse = 0.5 + 0.5 * Math.sin(lt * 8);
      xmat.uniforms.uCol.value.copy(CYAN).lerp(RED, clamp(lt / 0.6) * (0.6 + 0.4 * pulse));
      xh.pose({ spine: [4, 0, 0], head: [-4, 6 * Math.sin(lt * 2), 0] });
      cam.position.copy(lerpV(V3(-0.3, 1.25, 1.2), V3(-0.08, 1.2, 0.8), eio(lt / d)));
      cam.lookAt(0, 1.15, 0);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.75, focus: cam.position.distanceTo(V3(0, 1.15, 0)) }); blit();
      warning(540, 1180, eob(seg(lt, 0.1, 0.35)));
      pill('GUT BLOCKAGE', 540, 1280, eob(seg(lt, 0.3, 0.55)), '#FF3B3B');
    } });
    cue(st, 'whoosh'); cue(st + 0.2, 'alarm', { dur: cut(10) - st - 0.2 });
  }

  // 11 · Just spit it out (kitchen loop back)
  { const st = cut(10);
    add({ id: 'S11', at: st, note: 'kitchen: hero smiles and spits gum into bin, loop', draw(lt, d, t, blit) {
      reset();
      const k = eo(seg(lt, 0.1, 0.8));
      hero.pose({ head: [4, 6, 0], lid: 0.1, look: [0, 2] });
      cam.position.copy(lerpV(V3(0.3, 1.7, 0.2), V3(0.42, 1.72, 0.45), eio(lt / d)));
      cam.lookAt(FACE); kitchenRender(cam.position.distanceTo(FACE)); blit();
      pill('JUST SPIT IT OUT ✓', 540, 1180, eob(seg(lt, 0.15, 0.45)), '#7CF29A');
    } });
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', { gain: 0.6 });
  }

  return { shots: S, cues: CUES };
}
