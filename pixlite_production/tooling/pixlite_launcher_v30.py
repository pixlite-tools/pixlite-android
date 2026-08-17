from pathlib import Path
from PIL import Image

src=Path('assets/pixlite_icon.png')
im=Image.open(src).convert('RGBA')
res=Path('android/app/src/main/res')
for folder,size in {'mipmap-mdpi':48,'mipmap-hdpi':72,'mipmap-xhdpi':96,'mipmap-xxhdpi':144,'mipmap-xxxhdpi':192}.items():
    out=res/folder
    out.mkdir(parents=True,exist_ok=True)
    im.resize((size,size),Image.LANCZOS).save(out/'pixlite_launcher.png')
print('Generated dedicated pixlite_launcher resources')
