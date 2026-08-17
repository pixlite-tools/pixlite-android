from pathlib import Path
from PIL import Image, ImageDraw

S = 1024
bg = (5, 8, 20, 255)
dark = (9, 14, 29, 255)
orange = (255, 133, 0, 255)
orange2 = (255, 166, 51, 255)
blue = (0, 156, 246, 255)
blue2 = (42, 107, 255, 255)
violet = (109, 53, 255, 255)

im = Image.new('RGBA', (S, S), bg)
d = ImageDraw.Draw(im)

# Premium dark tile: orange keeps the monetisation/accent identity while a
# blue inner keyline reconnects the launcher icon with PixLite's UI gradient.
d.rounded_rectangle((78, 78, 946, 946), radius=235, fill=dark, outline=orange, width=46)
d.rounded_rectangle((112, 112, 912, 912), radius=205, outline=blue2, width=14)

# Build the PixLite P/document monogram as a mask, then fill it with the same
# orange -> violet -> blue family used by the app's main CTA.
mask = Image.new('L', (S, S), 0)
m = ImageDraw.Draw(mask)
m.rounded_rectangle((250, 210, 390, 815), radius=62, fill=255)
m.rounded_rectangle((320, 210, 785, 595), radius=175, fill=255)

# Horizontal brand gradient.
grad = Image.new('RGBA', (S, S), (0, 0, 0, 0))
gp = grad.load()
stops = [
    (0.00, orange),
    (0.42, violet),
    (1.00, blue),
]

def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))

for x in range(S):
    t = x / (S - 1)
    if t <= stops[1][0]:
        u = t / stops[1][0]
        c = mix(stops[0][1], stops[1][1], u)
    else:
        u = (t - stops[1][0]) / (stops[2][0] - stops[1][0])
        c = mix(stops[1][1], stops[2][1], u)
    for y in range(S):
        gp[x, y] = c
im.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(im)
# Negative-space document slit and lower page cut preserve recognisability at
# small launcher sizes.
d.rounded_rectangle((420, 330, 650, 480), radius=74, fill=dark)
d.rounded_rectangle((420, 376, 630, 434), radius=26, fill=orange2)
d.polygon([(250, 650), (445, 650), (330, 815), (250, 815)], fill=dark)

# Small blue signature block makes the blue identity remain visible even on
# launchers that downsample the icon aggressively.
d.rounded_rectangle((660, 650, 770, 760), radius=34, fill=blue)
d.rounded_rectangle((687, 677, 743, 733), radius=18, fill=dark)

out = Path('assets/pixlite_icon.png')
out.parent.mkdir(parents=True, exist_ok=True)
im.save(out)
print(out)
