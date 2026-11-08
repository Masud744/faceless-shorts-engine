// Auto-Generated Dynamic 3D Scene Architecture for: What Happens If You Swallow Gum?
// Synthesized by Faceless Shorts Engine Scene Mapper
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

  // ── 3D Environments & Sets ──────────────────────────────────────────────
  const K = SETS.kitchen(E), hero = new Human({}); hero.group.position.set(0.1, 0, -0.6); K.scene.add(hero.group);
  const X = SETS.xrayStage(E), xh = new Human({}), xmat = SETS.xrayMaterial(); xh.setBodyMaterial(xmat);
  const I = SETS.insides(); xh.spine.add(I.group); X.scene.add(xh.group);
  const VS = SETS.vessel(E);

  // 3D Animated Molecule / Object Prop
  const propMat = new THREE.MeshPhysicalMaterial({ color: '#FF69B4', roughness: 0.25, clearcoat: 0.8, emissive: '#FF1493', emissiveIntensity: 0.2 });
  const prop = new THREE.Mesh(new THREE.SphereGeometry(0.025, 24, 24), propMat);
  xh.spine.add(prop);

  const CYAN = new THREE.Color('#4FD1E8'), RED = new THREE.Color('#FF3B3B');
  const reset = () => {
    hero.pose({}); xh.pose({});
    prop.visible = false;
    xmat.uniforms.uCol.value.copy(CYAN);
  };
  const kitchenRender = (focus, extra = {}) => E.render(K.scene, cam, { ...KLOOK, focus, ...extra });
  const FACE = V3(0.1, 1.68, -0.6);

  // ── Cut 0: HOOK ──
  { const st = cut(0);
    add({ id: 'S01', at: st, note: 'kitchen close-up: chew chew, gulp, shocked eyes', draw(lt, d, t, blit) {
      reset(); const chew = Math.sin(lt * 12);
      const k = eo(seg(lt, 0.8, 1.5));
      hero.pose({ head: [-4 * k, chew * 3, 0], lid: lerp(-0.1, -0.4, k), look: [0, -3 * k] });
      cam.position.copy(lerpV(V3(0.38, 1.72, 0.45), V3(0.24, 1.7, 0.12), eio(lt / d)));
      cam.lookAt(FACE); kitchenRender(cam.position.distanceTo(FACE)); blit();
      pill('WHAT HAPPENS IF YOU SW', 540, 1180, eob(seg(lt, 0.9, 1.3)), '#FACC15');
    } });
    cue(st + 0.9, 'gulp', { dur: 0.4 });
    cue(st, 'whoosh');
  }

  // ── Cut 1: STOMACH ──
  { const st = cut(1);
    add({ id: 'S02', at: st, note: 'macro stomach closeup: acidic reaction and churning motion', draw(lt, d, t, blit) {
      reset(); prop.visible = true;
      prop.position.set(0.03 + Math.sin(lt * 2) * 0.005, 0.13 + Math.cos(lt * 3) * 0.004, 0.03);
      I.stomach.scale.setScalar(1 + Math.sin(lt * 4) * 0.03);
      cam.position.copy(lerpV(V3(0.18, 1.24, 0.75), V3(0.08, 1.22, 0.5), eio(lt / d)));
      cam.lookAt(0.03, 1.2, 0.02);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.65, focus: cam.position.distanceTo(V3(0.03, 1.2, 0.02)) }); blit();
      const [lx, ly] = screen(V3(0.03, 1.2, 0.02), cam);
      label('GASTRIC REACTION', 750, 480, lx, ly, eob(seg(lt, 0.2, 0.45)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'bubbles', { dur: cut(2) - st });
  }

  // ── Cut 2: STOMACH ──
  { const st = cut(2);
    add({ id: 'S03', at: st, note: 'macro stomach closeup: acidic reaction and churning motion', draw(lt, d, t, blit) {
      reset(); prop.visible = true;
      prop.position.set(0.03 + Math.sin(lt * 2) * 0.005, 0.13 + Math.cos(lt * 3) * 0.004, 0.03);
      I.stomach.scale.setScalar(1 + Math.sin(lt * 4) * 0.03);
      cam.position.copy(lerpV(V3(0.18, 1.24, 0.75), V3(0.08, 1.22, 0.5), eio(lt / d)));
      cam.lookAt(0.03, 1.2, 0.02);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.65, focus: cam.position.distanceTo(V3(0.03, 1.2, 0.02)) }); blit();
      const [lx, ly] = screen(V3(0.03, 1.2, 0.02), cam);
      label('GASTRIC REACTION', 750, 480, lx, ly, eob(seg(lt, 0.2, 0.45)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'bubbles', { dur: cut(3) - st });
  }

  // ── Cut 3: STOMACH ──
  { const st = cut(3);
    add({ id: 'S04', at: st, note: 'macro stomach closeup: acidic reaction and churning motion', draw(lt, d, t, blit) {
      reset(); prop.visible = true;
      prop.position.set(0.03 + Math.sin(lt * 2) * 0.005, 0.13 + Math.cos(lt * 3) * 0.004, 0.03);
      I.stomach.scale.setScalar(1 + Math.sin(lt * 4) * 0.03);
      cam.position.copy(lerpV(V3(0.18, 1.24, 0.75), V3(0.08, 1.22, 0.5), eio(lt / d)));
      cam.lookAt(0.03, 1.2, 0.02);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.65, focus: cam.position.distanceTo(V3(0.03, 1.2, 0.02)) }); blit();
      const [lx, ly] = screen(V3(0.03, 1.2, 0.02), cam);
      label('GASTRIC REACTION', 750, 480, lx, ly, eob(seg(lt, 0.2, 0.45)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'bubbles', { dur: cut(4) - st });
  }

  // ── Cut 4: ESOPHAGUS ──
  { const st = cut(4);
    add({ id: 'S05', at: st, note: 'x-ray descent: object slides down the esophagus into torso', draw(lt, d, t, blit) {
      reset(); prop.visible = true;
      const progress = eio(clamp(lt / d));
      prop.position.set(0.01 + Math.sin(progress * 4) * 0.008, lerp(0.44, 0.14, progress), 0.02);
      prop.scale.set(0.8, 1.2, 0.8);
      xh.pose({ head: [2, -4, 0] });
      cam.position.copy(lerpV(V3(0.4, 1.45, 1.3), V3(0.15, 1.35, 0.9), eio(lt / d)));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.3, 0)) }); blit();
      const [lx, ly] = screen(V3(0.02, 1.35, 0.05), cam);
      label('ESOPHAGUS DESCENT', 720, 520, lx, ly, eob(seg(lt, 0.15, 0.4)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', { dur: cut(5) - st });
  }

  // ── Cut 5: XRAY_ORGAN ──
  { const st = cut(5);
    add({ id: 'S06', at: st, note: 'x-ray rotating organ view with glowing skeleton', draw(lt, d, t, blit) {
      reset();
      const k = eio(clamp(lt / d));
      cam.position.copy(lerpV(V3(0.2, 1.4, 1.2), V3(0.35, 1.5, 1.6), k));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.4 }); blit();
      pill('FINAL TAKEAWAY', 540, 1280, eob(seg(lt, 0.15, 0.4)), '#FACC15');
    } });
    cue(st, 'ding'); cue(st + 0.1, 'whoosh');
  }

  // ── Cut 6: XRAY_ORGAN ──
  { const st = cut(6);
    add({ id: 'S07', at: st, note: 'x-ray rotating organ view with glowing skeleton', draw(lt, d, t, blit) {
      reset();
      const k = eio(clamp(lt / d));
      cam.position.copy(lerpV(V3(0.2, 1.4, 1.2), V3(0.35, 1.5, 1.6), k));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.4 }); blit();
      pill('FINAL TAKEAWAY', 540, 1280, eob(seg(lt, 0.15, 0.4)), '#FACC15');
    } });
    cue(st, 'ding'); cue(st + 0.1, 'whoosh');
  }

  // ── Cut 7: XRAY_ORGAN ──
  { const st = cut(7);
    add({ id: 'S08', at: st, note: 'x-ray rotating organ view with glowing skeleton', draw(lt, d, t, blit) {
      reset();
      const k = eio(clamp(lt / d));
      cam.position.copy(lerpV(V3(0.2, 1.4, 1.2), V3(0.35, 1.5, 1.6), k));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.4 }); blit();
      pill('FINAL TAKEAWAY', 540, 1280, eob(seg(lt, 0.15, 0.4)), '#FACC15');
    } });
    cue(st, 'ding'); cue(st + 0.1, 'whoosh');
  }

  // ── Cut 8: ESOPHAGUS ──
  { const st = cut(8);
    add({ id: 'S09', at: st, note: 'x-ray descent: object slides down the esophagus into torso', draw(lt, d, t, blit) {
      reset(); prop.visible = true;
      const progress = eio(clamp(lt / d));
      prop.position.set(0.01 + Math.sin(progress * 4) * 0.008, lerp(0.44, 0.14, progress), 0.02);
      prop.scale.set(0.8, 1.2, 0.8);
      xh.pose({ head: [2, -4, 0] });
      cam.position.copy(lerpV(V3(0.4, 1.45, 1.3), V3(0.15, 1.35, 0.9), eio(lt / d)));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.3, 0)) }); blit();
      const [lx, ly] = screen(V3(0.02, 1.35, 0.05), cam);
      label('ESOPHAGUS DESCENT', 720, 520, lx, ly, eob(seg(lt, 0.15, 0.4)));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', { dur: cut(9) - st });
  }

  // ── Cut 9: WARNING ──
  { const st = cut(9);
    add({ id: 'S10', at: st, note: 'x-ray red warning: blockage alert and flashing red silhouette', draw(lt, d, t, blit) {
      reset();
      const k = eio(clamp(lt / d));
      xmat.uniforms.uCol.value.copy(RED);
      cam.position.copy(lerpV(V3(0.35, 1.2, 0.9), V3(0.0, 1.15, 0.7), k));
      cam.lookAt(0, 1.1, 0);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.8 }); blit();
      warning('INTERNAL WARNING', 540, 1280, eob(seg(lt, 0.1, 0.35)));
    } });
    cue(st, 'alarm', { dur: 1.5 }); cue(st + 0.1, 'impact');
  }

  // ── Cut 10: TAKEAWAY ──
  { const st = cut(10);
    add({ id: 'S11', at: st, note: 'wide takeaway: silhouette with final warning badge', draw(lt, d, t, blit) {
      reset();
      const k = eio(clamp(lt / d));
      cam.position.copy(lerpV(V3(0.2, 1.4, 1.2), V3(0.35, 1.5, 1.6), k));
      cam.lookAt(0, 1.3, 0);
      E.render(X.scene, cam, { ...XLOOK, bloom: 0.4 }); blit();
      pill('FINAL TAKEAWAY', 540, 1280, eob(seg(lt, 0.15, 0.4)), '#FACC15');
    } });
    cue(st, 'ding'); cue(st + 0.1, 'whoosh');
  }

  return { shots: S, cues: CUES, duration: T || (L(10) + 1.2) };
}
