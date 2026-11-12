"""Adapt MIT-licensed Pythonic Life scenes into verified 15-second @shipstack_ reels."""
import argparse
import ast
import functools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import types
import wave

import numpy as np
from PIL import Image, ImageFont, ImageDraw

HERE=Path(__file__).resolve().parent
UPSTREAM=HERE/'upstream'
SCENES={
 'pl-ring':'14-ring-escape/ring_escape.py',
 'pl-marble':'10-marble-race/marble_race.py',
 'pl-last':'17-last-ball/last_ball.py',
 'pl-floor':'18-crumbling-floor/crumbling_floor.py',
 'pl-balloon':'19-balloon-pop/balloon_pop.py',
}
_original_font=ImageFont.truetype

def font_fallback(font,size=10,*args,**kwargs):
    if isinstance(font,(str,Path)) and not Path(font).is_file():
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    return _original_font(font,max(1,int(size)),*args,**kwargs)

ImageFont.truetype=font_fallback

class Adapt(ast.NodeTransformer):
    def visit_Constant(self,node):
        if isinstance(node.value,str):
            text=node.value.replace('PYTHONIC LIFE','@shipstack_')
            if text=='PYTHONIC ':text='SHIP'
            elif text=='LIFE':text='STACK'
            text=text.replace('Full code: link in profile','Follow @shipstack_ for more')
            return ast.copy_location(ast.Constant(text),node)
        return node

def load_scene(scene,variant=0,seed=None):
    if scene not in SCENES:raise ValueError('Unsupported Pythonic Life format')
    path=UPSTREAM/SCENES[scene]
    source=path.read_text()
    if scene=='pl-ring':
        offset=50*variant if seed is None else int(seed)%1000000
        source=source.replace('range(1, 400)',f'range({1+offset}, {401+offset})')
    elif seed is not None and scene!='pl-marble':
        # Shift only the seed-search loop, never simulation frame/ball ranges.
        import re
        offset=int(seed)%1000000
        source=re.sub(r'for seed in \(range\((\d+), (\d+)\) if V2 else range\((\d+), (\d+)\)\):',
            lambda m:f'for seed in range({offset+1}, {offset+3001}):',source)
    tree=Adapt().visit(ast.parse(source,filename=str(path)))
    kept=[]
    for node in tree.body:
        # The marble script exports at module scope; keep its renderer but remove that exporter.
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='proc_frames' for t in node.targets):break
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='Popen':continue
        kept.append(node)
    tree.body=kept;ast.fix_missing_locations(tree)
    module=types.ModuleType('shipstack_'+scene.replace('-','_')+'_'+str(variant))
    module.__file__=str(path)
    old_argv=sys.argv[:];old_v2=os.environ.get('V2')
    os.environ['V2']='1' if variant%2 else '0'
    sys.path.insert(0,str(path.parent));sys.path.insert(0,str(UPSTREAM/'shared'))
    if scene=='pl-marble':sys.argv=[str(path),str((1 if variant%2==0 else 15) if seed is None else int(seed)%50000+1)]
    else:sys.argv=[str(path)]
    try:
        exec(compile(tree,str(path),'exec'),module.__dict__)
    finally:
        sys.argv=old_argv
        if old_v2 is None:os.environ.pop('V2',None)
        else:os.environ['V2']=old_v2
    winner=getattr(module,'WIN',None)
    win_time=getattr(module,'T_WIN',getattr(module,'T_FIN',None))
    if winner is None or win_time is None or not math.isfinite(float(win_time)):
        raise RuntimeError('Simulation has no verified outcome; refusing to render')
    # Stop before upstream source-code end cards; keep the actual outcome visible.
    end=float(getattr(module,'T_END',win_time+1.4))-.025
    return module,dict(scene=scene,variant=variant,seed_used=int(module.SEED),winner=int(winner)+1,
                       source_win_seconds=float(win_time),source_seconds=end,seconds=15,
                       provider='Pythonic Life',source_commit='e062d70f067afa7b99a58f375e9a064582b5959f')

def render(scene,variant,output,seed=None,probe=False):
    module,info=load_scene(scene,variant,seed)
    if probe:
        # Exercise a first frame and the result frame, including font availability.
        for t in (0,info['source_win_seconds']+.6):
            img=module.render(int(t*module.FPS))
            assert img.shape==(1920,1080,3),img.shape
        print(json.dumps(info));return info
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    silent=output.with_suffix('.silent.mp4');wav=output.with_suffix('.wav')
    proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-',
       '-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
    first=None
    try:
        for f in range(450):
            source_t=info['source_seconds']*f/449
            frame=module.render(int(source_t*module.FPS))
            branded=Image.fromarray(frame).copy()
            draw=ImageDraw.Draw(branded)
            light=float(np.mean(frame[0,0]))>150
            draw.text((540,1760),'@shipstack_',font=font_fallback('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',30),
                      fill=(105,112,128) if light else (134,148,170),anchor='mm')
            frame=np.asarray(branded)
            if first is None:first=frame.copy()
            # A brief loop transition comes after the winner is shown.
            if f>=443:
                k=(f-443)/6;frame=(frame.astype(np.float32)*(1-k)+first.astype(np.float32)*k).astype(np.uint8)
            proc.stdin.write(np.ascontiguousarray(frame).tobytes())
        proc.stdin.close()
        if proc.wait():raise RuntimeError('Video encoding failed')
    except BaseException:
        proc.kill();raise
    audio=getattr(module,'audio',None)
    if callable(audio):audio=audio()
    elif audio is None:audio=module.synth_audio()
    audio=np.asarray(audio,dtype=np.float32)
    peak=float(np.max(np.abs(audio)))
    if peak<1e-6:raise RuntimeError('Source audio is silent')
    if peak>.97:audio=audio/peak*.94
    with wave.open(str(wav),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(module.SR);f.writeframes((np.clip(audio,-1,1)*32767).astype(np.int16).tobytes())
    tempo=info['source_seconds']/15
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(wav),'-map','0:v','-map','1:a',
       '-c:v','copy','-af',f'atempo={tempo:.9f},apad,atrim=duration=15,afade=t=out:st=14.88:d=0.12,loudnorm=I=-16:TP=-1.5:LRA=7',
       '-ar','48000','-c:a','aac','-b:a','192k','-t','15','-movflags','+faststart',str(output)],check=True)
    output.with_suffix('.mp4.json').write_text(json.dumps(info,indent=2)+'\n')
    silent.unlink();wav.unlink();print('Rendered '+str(output));return info

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scene',choices=list(SCENES),required=True);p.add_argument('--variant',type=int,default=0)
    p.add_argument('--seed',type=int);p.add_argument('--out',default='reels/out/pythonic.mp4');p.add_argument('--probe',action='store_true')
    a=p.parse_args();render(a.scene,a.variant,a.out,a.seed,a.probe)
