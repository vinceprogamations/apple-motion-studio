// motion-core.js — the ONE spring implementation of apple-motion-studio (classic <script> or ES module; also require()-able).
// Closed-form damped spring from 0 to 1 (position), time in seconds, deterministic (no integration, no state).
//
// Parametrisations (all reduce to natural angular frequency ω0 and damping ratio ζ):
//   apple(duration, bounce)  SwiftUI/Apple model: duration = perceptual duration = undamped PERIOD (ω0 = 2π/duration),
//                            bounce 0 = critical, 0<bounce<1 → ζ = 1 − bounce (under-damped), bounce<0 → ζ = 1/(1+bounce) (over-damped).
//                            NOTE: duration is NOT the settling time (smooth 0.5 s settles at ~0.46 s to 2 %).
//   freq(f, zeta)            f in Hz (ω0 = 2πf), zeta = damping ratio.            physics(mass, stiffness, damping)  ω0 = √(k/m), ζ = c/(2√(km)).
//   + optional initial velocity v0 (units of "distance to target per second").
//
// Behaviour families (no universal overshoot rule — choose by perceived mass, scale, function):
//   heavy   product / hero object landing     freq(1.0, 0.72)  ≈ 3.9 % overshoot
//   soft    cards, panels, scene elements     freq(1.5, 0.82)  ≈ 1.1 %
//   ui      small UI pops, checks, toasts     freq(2.3, 0.45)  ≈ 20 %  (small elements only, never text/logo/camera)
//   snap    touch feedback                    freq(2.6, 0.60)  ≈ 9.5 %
//   smooth  Apple .smooth                     apple(0.5, 0)    0 %     snappy apple(0.5, 0.15) ≈ 0.6 %   bouncy apple(0.5, 0.3) ≈ 4.6 %
//   camera  any camera move                   apple(dur, 0) or ζ ≥ 1 (critical/over-damped: never reverses)
// Legacy adapters keep approved films bit-identical: legacySpringApple (canvas films, templates/film.html), legacySpringFZ (early canvas
// films, no critical branch), legacySprDOM (DOM films / templates/dom/anim.js, with critical branch). See tests/run_springs.mjs.
(function (root, factory) {
  const M = factory();
  if (typeof module === 'object' && module.exports) module.exports = M;
  root.MotionCore = M;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const TAU = 2 * Math.PI;
  const apple = (duration, bounce = 0) => ({ w: TAU / duration, z: bounce >= 0 ? 1 - bounce : 1 / (1 + bounce) });
  const freq = (f, zeta) => ({ w: TAU * f, z: zeta });
  const physics = (mass, stiffness, damping) => ({ w: Math.sqrt(stiffness / mass), z: damping / (2 * Math.sqrt(stiffness * mass)) });
  // position x(t) from 0 to 1, e(t) = x - 1, e(0) = -1, e'(0) = v0
  function value(t, p, v0 = 0) {
    if (t <= 0) return 0;
    const { w, z } = p, e0 = -1;
    if (Math.abs(z - 1) < 1e-9) return 1 + Math.exp(-w * t) * (e0 + (v0 + w * e0) * t);
    if (z < 1) { const wd = w * Math.sqrt(1 - z * z); return 1 + Math.exp(-z * w * t) * (e0 * Math.cos(wd * t) + ((v0 + z * w * e0) / wd) * Math.sin(wd * t)); }
    const s = w * Math.sqrt(z * z - 1), r1 = -z * w + s, r2 = -z * w - s, c2 = (v0 - r1 * e0) / (r2 - r1), c1 = e0 - c2;
    return 1 + c1 * Math.exp(r1 * t) + c2 * Math.exp(r2 * t);
  }
  const velocity = (t, p, v0 = 0, h = 1e-5) => (value(t + h, p, v0) - value(Math.max(0, t - h), p, v0)) / (t > h ? 2 * h : h);
  function metrics(p, v0 = 0, tol = 0.02) {   // overshoot %, settle time to ±tol, peak time — measured on a 0.1 ms grid
    let peak = 0, tPeak = 0, settle = 0;
    for (let i = 1; i <= 100000; i++) { const t = i * 1e-4, x = value(t, p, v0); if (x > peak) { peak = x; tPeak = t; } if (Math.abs(x - 1) > tol) settle = t; }
    return { overshoot: Math.max(0, (peak - 1) * 100), settle, tPeak };
  }
  const FAMILIES = { heavy: freq(1.0, 0.72), soft: freq(1.5, 0.82), ui: freq(2.3, 0.45), snap: freq(2.6, 0.6), cam: freq(0.7, 1),
                     smooth: apple(0.5, 0), snappy: apple(0.5, 0.15), bouncy: apple(0.5, 0.3), gentle: apple(0.8, 0), quick: apple(0.3, 0), hero: apple(0.7, 0.3) };
  // ---- legacy adapters (exact formulas of the approved films) ----
  function legacySpringApple(t, duration = 0.5, bounce = 0) {           // canvas films / templates/film.html
    if (t <= 0) return 0; const w = TAU / duration, z = 1 - bounce;
    if (z >= 1) return 1 - Math.exp(-w * t) * (1 + w * t);
    const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  }
  function legacySpringFZ(t, f, z) {                                     // early canvas films (ζ < 1 only)
    if (t <= 0) return 0; const w = TAU * f, wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  }
  function legacySprDOM(t, f = 1.6, z = 0.75) {                          // DOM films / templates/dom/anim.js
    if (t <= 0) return 0; const w = TAU * f; if (z >= 1) return 1 - Math.exp(-w * t) * (1 + w * t);
    const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  }
  return { apple, freq, physics, value, velocity, metrics, FAMILIES, legacySpringApple, legacySpringFZ, legacySprDOM,
           family: (t, name, v0 = 0) => value(t, FAMILIES[name], v0) };
});
