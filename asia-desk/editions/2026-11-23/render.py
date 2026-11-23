import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PAPER, INK, MUTED, RED = "#f5ecd9", "#25221f", "#655749", "#843c3c"
W, H = 1080, 1350
LEFT, RIGHT = 72, 1008

def font(path, size):
    return ImageFont.truetype(path, size)

def wrap(draw, value, face, width):
    lines = [""]
    for word in value.split():
        test = f"{lines[-1]} {word}".strip()
        if lines[-1] and draw.textlength(test, font=face) > width:
            lines.append(word)
        else:
            lines[-1] = test
    return "\n".join(lines)

def draw_block(draw, value, y, face, color, spacing=7):
    text = wrap(draw, value, face, RIGHT - LEFT)
    draw.multiline_text((LEFT, y), text, font=face, fill=color, spacing=spacing)
    return draw.multiline_textbbox((LEFT, y), text, font=face, spacing=spacing)[3]

def art_crop(img, col, row):
    w, h = img.size
    return img.crop((col*w//2+3, row*h//4+3, (col+1)*w//2-3, (row+1)*h//4-3))

def frame(data, index, art, story=None):
    page = Image.new("RGB", (W,H), PAPER)
    d = ImageDraw.Draw(page)
    def rule(y, width=2, fill=INK):
        d.line((LEFT,y,RIGHT,y), fill=fill, width=width)
    d.text((LEFT,53),"ASIA DESK",font=font(BOLD,25),fill=RED)
    d.text((RIGHT,55),data["edition"].upper(),font=font(SANS,23),fill=MUTED,anchor="ra")
    rule(105,3)
    if story is None:
        d.text((LEFT,137),"THE DAILY EDITION",font=font(BOLD,23),fill=RED)
        draw_block(d,"Asia in Seven Headlines",194,font(SERIF,100),INK)
        draw_block(d,"Seven newspapers across Asia. One 24-hour briefing.",447,font(SANS,32),MUTED)
        top,bottom = 528,1072
        d.text((LEFT,1112),"DIPLOMACY   /   TECHNOLOGY   /   PUBLIC LIFE",font=font(BOLD,22),fill=RED)
        d.text((LEFT,1156),"Edition cut-off  ·  "+data["cutoff"],font=font(SANS,24),fill=MUTED)
    else:
        d.text((LEFT,140),story["desk"]+"   /   "+story["label"],font=font(BOLD,24),fill=RED)
        for size in (72,68,64,60):
            heading = font(SERIF,size)
            wrapped = wrap(d,story["headline"],heading,RIGHT-LEFT)
            if wrapped.count("\n") < 3:
                break
        end = draw_block(d,story["headline"],191,heading,INK,8)
        end = draw_block(d,story["deck"],end+31,font(SANS,32),MUTED,9)
        top,bottom = max(486,end+29),1098
        d.text((LEFT,1135),story["source"],font=font(BOLD,27),fill=INK)
        d.text((LEFT,1180),story["time"],font=font(SANS,22),fill=MUTED)
    assert bottom-top >= 385
    page.paste(ImageOps.fit(art,(RIGHT-LEFT,bottom-top),method=Image.Resampling.LANCZOS),(LEFT,top))
    rule(1232,2)
    d.text((LEFT,1260),"AI EDITORIAL ILLUSTRATION",font=font(BOLD,19),fill=MUTED)
    d.text((RIGHT,1256),f"{index:02d} / 08",font=font(BOLD,24),fill=RED,anchor="ra")
    return page

def render(sheet, supplemental, out):
    data = json.loads((ROOT/"edition.json").read_text())
    base = Image.open(sheet).convert("RGB")
    extra = Image.open(supplemental).convert("RGB")
    ew,eh = extra.size
    japan = extra.crop((3,3,ew-3,eh//2-3))
    manila = extra.crop((3,eh//2+3,ew-3,eh-3))
    art = [art_crop(base,0,0),japan,art_crop(base,0,1),art_crop(base,1,1),
           art_crop(base,0,2),art_crop(base,1,2),manila,art_crop(base,1,3)]
    out.mkdir(exist_ok=True,parents=True)
    for index,(visual,story) in enumerate(zip(art,[None]+data["stories"],strict=True),1):
        frame(data,index,visual,story).save(out/f"{index:02d}.jpg",quality=87,optimize=True)

if __name__ == "__main__":
    render(sys.argv[1],sys.argv[2],Path(sys.argv[3]))
