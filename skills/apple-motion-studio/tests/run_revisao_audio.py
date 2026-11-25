# Localized revision, AUDIO side: the notification delayed 6 frames must also be 6 frames (0.2 s at 30 fps) later in the
# sound of the delivered MP4, not only in the timeline/events. Mixes a cue on the page events (mix.py), muxes it into the
# v1/v2 MP4s from run_revisao_localizada.py, DECODES the audio back from each MP4 and measures the onset.
#   python tests/run_revisao_audio.py        (runs run_revisao_localizada.py first if its MP4s are missing)
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, subprocess, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib.tools import find_tool
FF = find_tool('ffmpeg'); EV = 'tests/evidence/10-revisao-localizada'; W = 'tests/_work/revisao-audio'; os.makedirs(W, exist_ok=True)
FPS, DELAY = 30, 6; SR = 48000
V = {'v1': f'{EV}/v1 aprovada.mp4', 'v2': f'{EV}/v2 notificação +6 quadros.mp4'}
if not all(os.path.exists(p) and os.path.exists(p.replace('.mp4', '.events.json')) for p in V.values()):
    subprocess.run([sys.executable, 'tests/run_revisao_localizada.py'], check=True)
# a short synthetic "tap" (sharp attack) as the cue's sound: deterministic, no library needed
lib = f'{W}/lib'; os.makedirs(lib, exist_ok=True); n = int(0.12 * SR); t = np.arange(n) / SR
tap = (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 45) * 0.6).astype(np.float32)
import wave
with wave.open(f'{lib}/toast_tap.wav', 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((tap * 32767).astype('<i2').tobytes())
json.dump([{'event': 's2.toast', 'file': 'toast_tap', 'db': -6, 'align': 'start'}], open(f'{W}/cues.json', 'w'))
res = {}
for k, mp4 in V.items():
    evs = mp4.replace('.mp4', '.events.json'); wav = f'{W}/{k}.wav'; out = f'{W}/{k} com som.mp4'
    dur = float(subprocess.run([find_tool('ffprobe'), '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4], capture_output=True, text=True).stdout)
    r = subprocess.run([sys.executable, 'scripts/mix.py', f'{W}/cues.json', wav, '--lib', lib, '--events', evs, '--len', str(dur)], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr
    subprocess.run([FF, '-v', 'error', '-y', '-i', mp4, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', out], check=True)
    raw = subprocess.run([FF, '-v', 'error', '-i', out, '-map', '0:a', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout   # decoded from the MP4
    x = np.abs(np.frombuffer(raw, np.float32)); on = int(np.argmax(x > x.max() * 0.2))
    ev_t = next(e['t'] for e in json.load(open(evs)) if e['name'] == 's2.toast')
    res[k] = {'event_s': round(ev_t, 4), 'onset_decoded_s': round(on / SR, 4), 'erro_vs_evento_ms': round((on / SR - ev_t) * 1000, 2)}
delta = res['v2']['onset_decoded_s'] - res['v1']['onset_decoded_s']
res['delta_decodificado_s'] = round(delta, 4); res['delta_esperado_s'] = round(DELAY / FPS, 4); res['delta_em_quadros'] = round(delta * FPS, 3)
ok = abs(delta - DELAY / FPS) <= 0.002 and all(abs(res[k]['erro_vs_evento_ms']) <= 25 for k in V)
res['result'] = 'PASSOU' if ok else 'FALHOU'
json.dump(res, open(f'{EV}/AUDIO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit(0 if ok else 1)
