# contact sheet for 9:16 stills: python sheet916.py <dir> <out.jpg> [cols]
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
fs = sorted([f for f in os.listdir(d) if f.endswith('.jpg')], key=lambda f: float(f[:-4]))
W, H = 300, 534; rows = (len(fs) + cols - 1) // cols
s = Image.new('RGB', (cols * W, rows * (H + 30)), '#222'); g = ImageDraw.Draw(s)
for i, f in enumerate(fs):
    x, y = (i % cols) * W, (i // cols) * (H + 30)
    s.paste(Image.open(os.path.join(d, f)).convert('RGB').resize((W - 4, H)), (x + 2, y + 28)); g.text((x + 6, y + 6), f[:-4] + ' s', fill='#fff')
s.save(out, quality=88); print(out, len(fs))
