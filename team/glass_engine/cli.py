import argparse
import json
from pathlib import Path
import shutil
import subprocess
from .engine import ROOT, TRACKS, load
from .premium import Scene


def render(c, output, width=720, fps=30):
    if width not in (360,720,1080) or fps not in (15,24,30,60):
        raise ValueError("width must be 360, 720 or 1080; fps must be 15, 24, 30 or 60")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Install FFmpeg before rendering")
    track=ROOT/"assets/audio"/TRACKS[c["music"]][0]
    if not track.exists(): raise FileNotFoundError(track)
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    height=width*16//9
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{width}x{height}","-framerate",str(fps),"-i","pipe:0","-stream_loop","-1","-i",str(track),"-map","0:v:0","-map","1:a:0","-t",str(c["duration"]),"-c:v","libx264","-preset","fast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-af",f"afade=t=out:st={max(0,c['duration']-.7)}:d=0.7","-movflags","+faststart",str(output)]
    scene=Scene(c)
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        import math
        for i in range(math.ceil(c["duration"]*fps)):
            frame=scene.frame(i/fps)
            if width!=720: frame=frame.resize((width,height))
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        error=proc.stderr.read().decode()
        if proc.wait(): raise RuntimeError(error)
    except BaseException:
        proc.kill(); proc.wait()
        raise
    output.with_suffix(".manifest.json").write_text(json.dumps({"engine_version":"0.2.1","visual_renderer":"clear-glass-blender-sprites","composition":c,"width":width,"height":height,"fps":fps,"music_bpm":TRACKS[c["music"]][1],"music_start_offset":0},indent=2))
    return output


def main():
    p=argparse.ArgumentParser(description="Render ShipStack JSON compositions")
    p.add_argument("command",choices=["validate","preview","render"])
    p.add_argument("composition")
    p.add_argument("--output",default=None)
    p.add_argument("--time",type=float,default=0)
    p.add_argument("--width",type=int,default=720)
    p.add_argument("--fps",type=int,default=30)
    a=p.parse_args(); c=load(a.composition)
    if a.command=="validate": print("Valid composition")
    elif a.command=="preview":
        out=Path(a.output or "output/preview.png"); out.parent.mkdir(parents=True,exist_ok=True)
        Scene(c).frame(a.time).save(out); print(out)
    else: print(render(c,a.output or "output/reel.mp4",a.width,a.fps))


if __name__=="__main__": main()
