"""Create a branded 4:5 news image from a generated background."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
W,H=1080,1350
def font(size,bold=False):
    names=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    return ImageFont.truetype(names[0],size) if Path(names[0]).exists() else ImageFont.load_default()
def cover(im):
    scale=max(W/im.width,H/im.height); im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    x=(im.width-W)//2; y=(im.height-H)//2
    return im.crop((x,y,x+W,y+H)).convert("RGB")
def wrap(draw,text,f,width):
    out=[]; line=""
    for word in text.split():
        trial=(line+" "+word).strip()
        if draw.textlength(trial,font=f)<=width: line=trial
        else: out.append(line); line=word
    if line: out.append(line)
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--brief",required=True); ap.add_argument("--background",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
    brief=json.loads(Path(a.brief).read_text()); im=cover(Image.open(a.background))
    im=ImageEnhance.Contrast(im).enhance(1.08); im=ImageEnhance.Color(im).enhance(.92)
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    d.rectangle((0,0,W,170),fill=(8,16,28,168)); d.rectangle((0,850,W,H),fill=(7,15,27,232))
    d.line((64,850,1016,850),fill=(92,211,190,255),width=5); d.rounded_rectangle((64,55,310,112),16,fill=(92,211,190,255))
    d.text((88,68),"SHIPSTACK NEWS",font=font(27,True),fill=(7,20,30,255))
    d.text((64,195),"VERIFIED / "+brief.get("source","SOURCE").upper(),font=font(24,True),fill=(190,220,220,255))
    y=905; f=font(58,True)
    for line in wrap(d,brief["headline"],f,900): d.text((64,y),line,font=f,fill="white",stroke_width=1,stroke_fill=(0,0,0,100)); y+=72
    y+=18; f=font(27)
    for line in wrap(d,brief.get("deck",""),f,900): d.text((64,y),line,font=f,fill=(224,234,240,255)); y+=38
    d.text((64,1260),"Source: "+brief.get("source","")+"  ·  @shipstack_",font=font(22),fill=(178,195,205,255))
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Image.alpha_composite(im.convert("RGBA"),ov).convert("RGB").save(a.output,quality=95,subsampling=0); print(a.output)
if __name__=="__main__": main()
