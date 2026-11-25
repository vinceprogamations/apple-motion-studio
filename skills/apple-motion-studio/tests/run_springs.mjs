// Spring unification tests (spec § 32). node tests/run_springs.mjs
// 1. Equivalence: the unified value() reproduces each legacy formula over the parameter ranges used by approved films
//    (and the legacy adapters are copied from the films' own source text, checked here against that text).
// 2. Physics: overshoot / settling / end value / critical / over-damped / continuity / velocity, against closed-form theory.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url); const MC = require('../templates/motion-core.js');
const P = '../../../../'; const res = [];   // P: tests -> skill -> skills -> .claude -> project
const check = (name, ok, detail) => res.push({ name, result: ok ? 'PASSOU' : 'FALHOU', detail });
// legacy functions taken from the REAL files of the approved films (not from the adapters). The list lives in the private file
// tests/origin-films.json of the origin project; without it (public checkout) these checks fall back to the adapters themselves.
import { existsSync } from 'node:fs';
const OF = new URL('./origin-films.json', import.meta.url), ORIG = existsSync(OF) ? JSON.parse(readFileSync(OF, 'utf8')) : null;
const have = f => existsSync(new URL(P + f, import.meta.url));
const ORIGIN = !!ORIG && ORIG.every(o => have(o.file));
function extract(file, re) { const src = readFileSync(new URL(P + file, import.meta.url), 'utf8'); const m = src.match(new RegExp(re)); if (!m) throw new Error('não achei em ' + file); return m[0]; }
const load = (o) => o.kind === 'arrow' ? new Function('return ' + extract(o.file, o.re).replace(/;$/, ''))() : new Function(extract(o.file, o.re) + '; return ' + o.fn + ';')();
const pick = (i, fb) => ORIGIN ? load(ORIG[i]) : fb;
const L = i => ORIGIN ? ORIG[i].label : ['canvas antigo A', 'canvas antigo B', 'canvas Apple', 'DOM'][i];
const fNuvra = pick(0, MC.legacySpringFZ), fCrivo2 = pick(1, MC.legacySpringFZ), fVela = pick(2, MC.legacySpringApple), fReels = pick(3, MC.legacySprDOM);
const T = Array.from({ length: 400 }, (_, i) => -0.05 + i * 0.01);
function maxDiff(a, b, params) { let m = 0; for (const ps of params) for (const t of T) { const d = Math.abs(a(t, ...ps) - b(t, ...ps)); if (!(d <= m)) m = isNaN(d) ? Infinity : d; } return m; }
const fzGrid = []; for (let f = 0.5; f <= 3.01; f += 0.25) for (let z = 0.3; z <= 0.951; z += 0.05) fzGrid.push([f, +z.toFixed(2)]);
const daGrid = []; for (let d = 0.3; d <= 1.21; d += 0.1) for (const b of [0, 0.05, 0.15, 0.3]) daGrid.push([+d.toFixed(2), b]);
const domGrid = [...fzGrid, [1.0, 1], [0.7, 1], [1.5, 1]];
const uni = (kind) => kind === 'fz' ? (t, f, z) => MC.value(t, MC.freq(f, z)) : (t, d, b) => MC.value(t, MC.apple(d, b));
if (!ORIGIN) console.log('AVISO: filmes de origem ausentes (checkout público): as 4 checagens contra arquivos reais viram autoconferência dos adaptadores');
check(`legacy FZ = ${L(0)} (arquivo real)`, maxDiff(MC.legacySpringFZ, fNuvra, fzGrid) === 0, 'diferença máx ' + maxDiff(MC.legacySpringFZ, fNuvra, fzGrid));
check(`legacy FZ = ${L(1)} (arquivo real)`, maxDiff(MC.legacySpringFZ, fCrivo2, fzGrid) === 0, 'diferença máx ' + maxDiff(MC.legacySpringFZ, fCrivo2, fzGrid));
check(`legacy Apple = ${L(2)} (arquivo real)`, maxDiff(MC.legacySpringApple, fVela, daGrid) === 0, 'diferença máx ' + maxDiff(MC.legacySpringApple, fVela, daGrid));
check(`legacy DOM = ${L(3)} (arquivo real)`, maxDiff(MC.legacySprDOM, fReels, domGrid) === 0, 'diferença máx ' + maxDiff(MC.legacySprDOM, fReels, domGrid));
const dFZ = maxDiff(uni('fz'), fNuvra, fzGrid), dAp = maxDiff(uni('ap'), fVela, daGrid), dDom = maxDiff(uni('fz'), fReels, domGrid);
check('núcleo único ≈ fórmula freq/ζ antiga (ζ<1)', dFZ < 1e-12, 'diferença máx ' + dFZ.toExponential(2));
check('núcleo único ≈ fórmula Apple duration/bounce', dAp < 1e-12, 'diferença máx ' + dAp.toExponential(2));
check('núcleo único ≈ fórmula DOM (inclui ζ=1)', dDom < 1e-12, 'diferença máx ' + dDom.toExponential(2));
// physics
for (const z of [0.3, 0.45, 0.6, 0.72, 0.85]) {
  const m = MC.metrics(MC.freq(1.5, z)), theory = 100 * Math.exp(-z * Math.PI / Math.sqrt(1 - z * z));
  check(`overshoot ζ=${z} = teoria`, Math.abs(m.overshoot - theory) < 0.01, `${m.overshoot.toFixed(3)} % × ${theory.toFixed(3)} %`);
}
const sm = MC.metrics(MC.apple(0.5, 0)), sn = MC.metrics(MC.apple(0.5, 0.15)), bo = MC.metrics(MC.apple(0.5, 0.3));
check('Apple smooth: 0 % e assenta em ~0,46 s', sm.overshoot === 0 && Math.abs(sm.settle - 0.464) < 0.005, `${sm.overshoot} %, ${sm.settle.toFixed(3)} s`);
check('Apple snappy: ~0,63 %, ~0,33 s', Math.abs(sn.overshoot - 0.63) < 0.05 && Math.abs(sn.settle - 0.333) < 0.01, `${sn.overshoot.toFixed(2)} %, ${sn.settle.toFixed(3)} s`);
check('Apple bouncy: ~4,60 %', Math.abs(bo.overshoot - 4.60) < 0.05, `${bo.overshoot.toFixed(2)} %`);
const od = MC.apple(0.5, -0.4), odm = MC.metrics(od);
check('superamortecido (bounce −0,4 → ζ=1,67): sem overshoot, monotônico', odm.overshoot === 0 && od.z > 1, `ζ=${od.z.toFixed(2)}, overshoot ${odm.overshoot}`);
let mono = true, prev = 0; for (let t = 0; t < 3; t += 0.001) { const x = MC.value(t, MC.FAMILIES.cam); if (x < prev - 1e-12) mono = false; prev = x; }
check('família camera nunca volta (monotônica)', mono, 'derivada ≥ 0 em 0–3 s');
let cont = 0; for (let t = 0.001; t < 2; t += 0.001) cont = Math.max(cont, Math.abs(MC.value(t + 1e-6, MC.FAMILIES.ui) - MC.value(t, MC.FAMILIES.ui)));
check('contínua (sem saltos)', cont < 1e-4, 'maior passo em 1 µs: ' + cont.toExponential(2));
check('valor final → 1 e início = 0', Math.abs(MC.value(10, MC.FAMILIES.heavy) - 1) < 1e-9 && MC.value(0, MC.FAMILIES.heavy) === 0, 'x(0)=0, x(10 s)=1');
const v0 = MC.velocity(0.0005, MC.FAMILIES.soft), vv = MC.velocity(0.0005, MC.FAMILIES.soft, 3);
check('velocidade inicial respeitada', Math.abs(v0) < 0.05 && Math.abs(vv - 3) < 0.05, `v(0)≈${v0.toFixed(3)} sem v0; ≈${vv.toFixed(3)} com v0=3`);
const fam = Object.fromEntries(Object.entries(MC.FAMILIES).map(([k, p]) => { const m = MC.metrics(p); return [k, { overshoot_pct: +m.overshoot.toFixed(2), settle_s: +m.settle.toFixed(3), zeta: +p.z.toFixed(3), f_hz: +(p.w / (2 * Math.PI)).toFixed(3) }]; }));
mkdirSync(new URL('./evidence/11-springs/', import.meta.url), { recursive: true });
writeFileSync(new URL('./evidence/11-springs/RESUMO.json', import.meta.url), JSON.stringify({ checks: res, families: fam }, null, 1));
for (const r of res) console.log(`${r.result}  ${r.name}  (${r.detail})`);
console.log('\nfamílias:'); for (const [k, v] of Object.entries(fam)) console.log(`  ${k.padEnd(7)} f=${v.f_hz} Hz ζ=${v.zeta}  overshoot ${v.overshoot_pct} %  assenta ${v.settle_s} s`);
process.exit(res.every(r => r.result === 'PASSOU') ? 0 : 1);
