"""Clear-glass compositions with physically lit, original Blender assets."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
from .engine import Scene as BaseScene, ROOT, COLORS, INK, cup_state


@lru_cache(maxsize=64)
def sprite(name):
    path=ROOT/'assets/sprites'/f'{name}.png'
    if not path.exists(): return None
    im=Image.open(path).convert('RGBA')
    bounds=im.getchannel('A').getbbox()
    return im.crop(bounds)


class Scene(BaseScene):
    def background(self):
        # Broad, distinct pools of colour make the clear glass visible.
        small=Image.new('RGB',(90,160)); px=small.load()
        for y in range(160):
            for x in range(90):
                warm=math.exp(-((x-86)**2/1000+(y-40)**2/1700))
                blue=math.exp(-((x-2)**2/1000+(y-95)**2/1500))
                mint=math.exp(-((x-83)**2/1900+(y-157)**2/1000))
                px[x,y]=(int(246-14*warm-53*blue-52*mint),int(246-48*warm-22*blue-7*mint),int(251-83*warm-3*blue-23*mint))
        im=small.resize((720,1280),Image.Resampling.BICUBIC).convert('RGBA')
        # Abstract blurred colour fields, with no competing decorative sparkles.
        layer=Image.new('RGBA',im.size); d=ImageDraw.Draw(layer)
        d.ellipse((510,220,910,670),fill=(255,174,124,82))
        d.ellipse((-190,720,180,1080),fill=(104,165,255,60))
        return Image.alpha_composite(im,layer.filter(ImageFilter.GaussianBlur(65)))

    def glass(self,box,radius=30):
        x0,y0,x1,y1=map(int,box); w=x1-x0; h=y1-y0
        mask=Image.new('L',(w,h)); ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius,fill=255)
        # A floating, diffused shadow replaces the hard offset silhouette.
        shadow=Image.new('RGBA',self.im.size)
        ImageDraw.Draw(shadow).rounded_rectangle((x0+2,y0+12,x1+2,y1+18),radius,fill=(44,64,104,27))
        self.im=Image.alpha_composite(self.im,shadow.filter(ImageFilter.GaussianBlur(15)))
        # Slight magnification and blur simulate the lens-like optical surface.
        crop=self.im.crop((x0,y0,x1,y1))
        zoom=crop.resize((w+12,h+12),Image.Resampling.BICUBIC).crop((6,6,w+6,h+6))
        crop=Image.blend(crop,zoom.filter(ImageFilter.GaussianBlur(7)),.7)
        wash=Image.new('RGBA',(w,h),(255,255,255,40))
        crop=Image.alpha_composite(crop,wash)
        sheen=Image.new('RGBA',(w,h)); sd=ImageDraw.Draw(sheen)
        for row in range(min(h,90)):
            sd.line((0,row,w,row),fill=(255,255,255,int(40*(1-row/min(h,90))**2)))
        crop=Image.alpha_composite(crop,sheen)
        self.im.paste(crop,(x0,y0),mask)
        self.d=ImageDraw.Draw(self.im)
        self.d.rounded_rectangle(box,radius,outline=(255,255,255,190),width=2)
        self.d.arc((x0+2,y0+2,x0+radius*2,y0+radius*2),180,270,fill='white',width=2)

    def shadow(self,x,y,rx,ry,alpha=36):
        layer=Image.new('RGBA',(int(rx*3),int(ry*6)))
        d=ImageDraw.Draw(layer)
        d.ellipse((rx*.5,ry*2,rx*2.5,ry*4),fill=(38,53,81,alpha))
        layer=layer.filter(ImageFilter.GaussianBlur(max(2,ry*.65)))
        self.im.alpha_composite(layer,(int(x-rx*1.5),int(y-ry*3)))
        self.d=ImageDraw.Draw(self.im)

    def reflection(self,asset,x,floor,width,height,opacity=.12):
        reflection=ImageOps.flip(asset).resize((int(width),int(height)),Image.Resampling.LANCZOS)
        fade=Image.new('L',reflection.size); fd=ImageDraw.Draw(fade)
        for row in range(reflection.height):
            fd.line((0,row,reflection.width,row),fill=int(255*opacity*(1-row/reflection.height)**2))
        reflection.putalpha(ImageChops.multiply(reflection.getchannel('A'),fade))
        self.im.alpha_composite(reflection,(round(x-width/2),round(floor)))
        self.d=ImageDraw.Draw(self.im)

    def marble(self,x,y,r,color,look=1,emotion='happy',blink=False,floor=None,squash=1):
        name='sunny' if color==COLORS[2] else 'blu' if color==COLORS[1] else None
        asset=sprite(f'{name}-'+('blink' if blink else emotion)) if name else None
        if asset is None:
            return super().marble(x,y,r,color,look,emotion,blink)
        size=int(r*2.1)
        im=asset.resize((int(size/squash),int(size*squash)),Image.Resampling.LANCZOS)
        # Small tilts and squash/stretch are expressed through the whole model.
        tilt=math.sin(self.t*3.2)*4 if getattr(self,'t',None) is not None else 0
        im=im.rotate(tilt,resample=Image.Resampling.BICUBIC,expand=True)
        floor=y+r+6 if floor is None else floor
        altitude=max(0,floor-y-r)
        self.shadow(x+altitude*.16,floor,r*(.72+altitude*.004),5+altitude*.08,max(12,45-int(altitude*.45)))
        if floor<820:
            self.reflection(asset,x,floor+3,r*1.8,26,.1*math.exp(-altitude/50))
        self.im.alpha_composite(im,(round(x-im.width/2),round(y-im.height/2)))
        self.d=ImageDraw.Draw(self.im)

    def frame(self,t):
        self.t=t; c=self.c; reveal=t>=c['reveal_at']
        self.im=self.bg.copy(); self.d=ImageDraw.Draw(self.im)
        self.text((360,103),'S H I P S T A C K',19,(54,67,88))
        self.text((360,159),'A LITTLE PLAY. A SHARPER DAY.',12,(87,101,122))
        self.text((360,230),c['title'].title(),43,(22,37,61))
        self.text((360,284),c['instruction'],24,(66,81,101))
        self.glass((263,324,457,364),20)
        self.d.ellipse((280,340,288,348),fill=(25,157,125) if reveal else (235,145,38))
        self.text((370,344),'THE REVEAL' if reveal else 'WATCH CLOSELY',12,(54,68,87))
        self.glass((35,398,685,842),38)
        self.puzzle(t)
        remain=max(0,c['reveal_at']-t)
        self.d.rounded_rectangle((110,896,610,902),3,fill=(180,193,205))
        self.d.rounded_rectangle((110,896,110+max(3,500*remain/c['reveal_at']),902),3,fill=(56,113,195))
        label=self.answer() if reveal else f'{math.ceil(remain):02d}  /  SECONDS TO GUESS'
        self.text((360,941),label,22,(35,53,77))
        self.glass((130,1010,645,1102),28)
        elapsed=t-c['reveal_at']
        self.marble(86,1059-math.sin(t*2.1)*2,48,COLORS[1],emotion='happy' if reveal else 'curious',blink=t%3.4<.12,floor=1111)
        self.text((389,1044),'GOT IT?',12,(89,103,121))
        self.text((389,1073),c['cta'],21,(29,46,71),max_width=460)
        self.text((360,1173),'PLAY  /  FOCUS  /  REPEAT',12,(103,117,136))
        return self.im.convert('RGB')

    def puzzle(self,t):
        if self.c['format']!='follow_ball':
            return super().puzzle(t)
        c=self.c; reveal=t>=c['reveal_at']; intro=t<2
        order,positions,arcs,slot=cup_state(c,t)
        # Lift smoothly, instead of teleporting the cups at phase boundaries.
        if intro:
            p=min(1,max(0,(t-1.35)/.65))
            lift=1-p*p*(3-2*p)
        elif reveal:
            p=min(1,(t-c['reveal_at'])/.55)
            lift=1-(1-p)**3
        else: lift=0
        cup=sprite('cup')
        # Painter's order follows depth, so a back cup cannot cover a front cup.
        for i in sorted(range(3),key=lambda i:arcs[i]):
            x=180+positions[i]*180
            depth=arcs[i]*1.5
            scale=1+depth*.001
            y=612+depth
            floor=700+depth
            self.shadow(x+lift*13,floor,65*scale+lift*12,6+lift*8,int(52-lift*27))
            if order[i]==0 and (intro or reveal):
                elapsed=t-c['reveal_at'] if reveal else t
                # Two diminishing ballistic hops followed by a settled pose.
                flight=max(0,elapsed-.23)
                jump=0; squash=1
                if reveal and flight<1.35:
                    cycle=int(flight/.45); phase=(flight%.45)/.45
                    jump=4*phase*(1-phase)*32*(.48**cycle)
                    squash=1-.07*math.exp(-phase*16)*(.48**cycle)
                self.marble(x+math.sin(elapsed*2)*2,650-jump,50*scale,COLORS[2],emotion='surprised' if reveal and elapsed<.55 else 'happy' if reveal else 'curious',blink=elapsed%2.6>2.47,floor=floor,squash=squash)
            if cup:
                self.reflection(cup,x,floor+3,142*scale,40,.11*(1-lift*.8))
                im=cup.resize((int(142*scale),int(177*scale)),Image.Resampling.LANCZOS)
                # Restrained banking gives the moving objects a sense of weight.
                tilt=arcs[i]*.075
                im=im.rotate(tilt,resample=Image.Resampling.BICUBIC,expand=True)
                self.im.alpha_composite(im,(round(x-im.width/2),round(y-im.height/2-lift*124)))
                self.d=ImageDraw.Draw(self.im)
            else:
                raise FileNotFoundError('Regenerate assets/sprites/cup.png with scripts/render_characters.py')
            self.text((180+i*180,800),f'0{i+1}',18,(70,87,111))
        if reveal and t-c['reveal_at']>.6:
            x=180+slot*180
            self.d.rounded_rectangle((x-29,822,x+29,826),2,fill=(25,164,126))
