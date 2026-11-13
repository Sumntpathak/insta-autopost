const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const sharp = require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/sharp' : 'sharp');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {Lift} = require('./scene.cjs');

const index = Number(process.argv[2]);
const svg = f => Buffer.from(renderToStaticMarkup(React.createElement(Lift,{f,index})));

async function main(){

  const p=spawn('ffmpeg',['-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1080x1920','-framerate','30','-i','-','-i','score.wav','-c:v','libx264','-threads','4','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t','15','-movflags','+faststart',process.argv[3]],{stdio:['pipe','inherit','inherit']});
  const done=once(p,'close');
  for(let start=0;start<450;start+=6){
    const batch=await Promise.all(Array.from({length:Math.min(6,450-start)},(_,i)=>sharp(svg(start+i)).removeAlpha().raw().toBuffer()));
    for(const frame of batch) if(!p.stdin.write(frame))await once(p.stdin,'drain');
  }
  p.stdin.end();
  const [code]=await done;
  if(code) throw Error('FFmpeg failed');
}
main().catch(e=>{console.error(e);process.exitCode=1});
