from pathlib import Path
from PIL import Image, ImageDraw

S = 1024
bg = (5, 8, 20, 255)
dark = (9, 14, 29, 255)
orange = (255, 133, 0, 255)
orange2 = (255, 166, 51, 255)

im = Image.new('RGBA', (S, S), bg)
d = ImageDraw.Draw(im)

# Rounded dark tile with a strong orange frame.
d.rounded_rectangle((78, 78, 946, 946), radius=235, fill=dark, outline=orange, width=48)

# Distinct PixLite "P/document" monogram. The negative-space page slit keeps
# the symbol recognizable at launcher-size while avoiding a generic letter P.
d.rounded_rectangle((250, 210, 390, 815), radius=62, fill=orange)
d.rounded_rectangle((320, 210, 785, 595), radius=175, fill=orange)
d.rounded_rectangle((420, 330, 650, 480), radius=74, fill=dark)
d.rounded_rectangle((420, 376, 630, 434), radius=26, fill=orange2)
# Lower diagonal cut gives the mark a document/page feel.
d.polygon([(250, 650), (445, 650), (330, 815), (250, 815)], fill=dark)

out = Path('assets/pixlite_icon.png')
out.parent.mkdir(parents=True, exist_ok=True)
im.save(out)
print(out)
