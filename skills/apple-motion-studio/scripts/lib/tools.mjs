// Executable discovery shared by the Node scripts (render.mjs, render_dom.mjs, doctor).
// Order: explicit env var (FFMPEG / FFPROBE / CHROME / BLENDER) -> PATH -> known install locations per OS
// (WinGet Gyan.FFmpeg, Program Files, /Applications, Homebrew, /usr/bin). No user-specific paths are hard-coded.
import { existsSync, readdirSync } from 'node:fs';
import { join, delimiter } from 'node:path';
import { homedir } from 'node:os';

const WIN = process.platform === 'win32', EXE = WIN ? '.exe' : '';
function onPath(name) {
  for (const d of (process.env.PATH || '').split(delimiter)) { if (!d) continue; const p = join(d, name + EXE); if (existsSync(p)) return p; }
  return null;
}
function wingetFfmpeg(bin) {   // %LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\<bin>.exe
  if (!WIN) return null;
  const base = join(process.env.LOCALAPPDATA || join(homedir(), 'AppData', 'Local'), 'Microsoft', 'WinGet', 'Packages');
  if (!existsSync(base)) return null;
  for (const pkg of readdirSync(base).filter(n => /^Gyan\.FFmpeg/i.test(n)).sort().reverse()) {
    const pdir = join(base, pkg);
    for (const sub of readdirSync(pdir).filter(n => /^ffmpeg-/i.test(n)).sort().reverse()) { const p = join(pdir, sub, 'bin', bin + '.exe'); if (existsSync(p)) return p; }
  }
  return null;
}
const CANDIDATES = {
  ffmpeg: () => [wingetFfmpeg('ffmpeg'), '/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'],
  ffprobe: () => [wingetFfmpeg('ffprobe'), '/opt/homebrew/bin/ffprobe', '/usr/local/bin/ffprobe', '/usr/bin/ffprobe'],
  chrome: () => ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'],
  blender: () => {
    const out = ['/Applications/Blender.app/Contents/MacOS/Blender', '/usr/bin/blender', '/snap/bin/blender'];
    const pf = 'C:/Program Files/Blender Foundation';
    if (WIN && existsSync(pf)) for (const v of readdirSync(pf).sort().reverse()) out.unshift(join(pf, v, 'blender.exe'));
    return out;
  },
};
const ENV = { ffmpeg: 'FFMPEG', ffprobe: 'FFPROBE', chrome: 'CHROME', blender: 'BLENDER' };
export function findTool(name, { required = true } = {}) {
  const env = process.env[ENV[name]];
  if (env && existsSync(env)) return env;
  const hit = onPath(name === 'chrome' ? 'chrome' : name) || CANDIDATES[name]().find(p => p && existsSync(p));
  if (!hit && required) throw new Error(`${name} não encontrado. Defina ${ENV[name]}=<caminho> ou instale (rode: python scripts/studio.py doctor).`);
  return hit || null;
}
