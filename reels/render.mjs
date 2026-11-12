// Existing Matter.js 0.20.0 example scenes; only styling, seeding and export live here.
import {createCanvas, GlobalFonts} from '@napi-rs/canvas';
import vm from 'node:vm';
import {readFileSync, mkdirSync, writeFileSync, existsSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
for(const font of ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']){if(existsSync(font)){GlobalFonts.registerFromPath(font,'ReelSans');break;}}
const here=path.dirname(fileURLToPath(import.meta.url));
const config=JSON.parse(readFileSync(path.join(here,'config.json')));
const [scene='ballPool', seedText='1', output='reel.mp4']=process.argv.slice(2);
if (!config.scenes.includes(scene)) throw Error('Unknown scene');
const seed=Number(seedText);
if(!Number.isSafeInteger(seed)||seed<0) throw Error('Seed must be a positive integer');
const width=Number(process.env.REEL_WIDTH||1080), height=width*16/9, fps=30;
if(!Number.isInteger(height)||width%2||height%2) throw Error('Use an even 9:16 resolution');
mkdirSync(path.dirname(output),{recursive:true});
const nativeCanvas=()=>{
 const c=createCanvas(800,600);c.style={};c.setAttribute=()=>{};c.getAttribute=()=>null;c.addEventListener=()=>{};
 return c;
};
const outputCanvas=createCanvas(width,height);
const sandbox={console,document:{body:{},createElement:nativeCanvas,getElementById:()=>outputCanvas}};
sandbox.window=sandbox;
vm.createContext(sandbox);
vm.runInContext(readFileSync(path.join(here,'node_modules/matter-js/build/matter.min.js'),'utf8'),sandbox);
vm.runInContext(readFileSync(path.join(here,'vendor',scene+'.js'),'utf8'),sandbox);
let encoder;
try {
 const setup=({scene,seed,width,height})=>{
  const M=window.Matter;
  M.Common._seed=seed;
  M.Render.run=()=>{}; M.Runner.run=()=>{};
  const sim=window.Example[scene]();

  Object.assign(sim.render.options,{wireframes:false,background:'#0c0b17',showAngleIndicator:false,showCollisions:false,showVelocity:false});
  const palettes=[['#71e7ff','#b294ff','#ff81a6','#fff2a8'],['#58edb2','#59afff','#e8e8ff','#ffbf69'],['#ff95c5','#9f87ff','#83e5e4','#fff8ee']];
  const palette=palettes[seed%palettes.length];
  const bodies=M.Composite.allBodies(sim.engine.world);
  bodies.forEach((b,i)=>{
   b.render.fillStyle=b.isStatic?'#636a83':palette[i%palette.length];
   b.render.strokeStyle=b.isStatic?'#b4bbd3':b.render.fillStyle;
   b.render.lineWidth=b.isStatic?1.5:0;
   if(!b.isStatic && !['chains','newtonsCradle'].includes(scene)) {
    M.Body.setVelocity(b,{x:M.Common.random(-1.5,1.5),y:M.Common.random(-1,1)});
   }
  });
  M.Composite.allConstraints(sim.engine.world).forEach(c=>{if(c.render.visible!==false)Object.assign(c.render,{strokeStyle:'#858ca8',lineWidth:2});});
  sim.engine.gravity.scale*=0.8+(seed%7)*0.05;
  const canvas=document.getElementById('output');canvas.width=width;canvas.height=height;
  const ctx=canvas.getContext('2d');
  window.frame=(index)=>{
   // Re-energize free bodies to retain motion; constrained scenes use upstream physics untouched.
   if(index>0 && index%120===0 && ['ballPool','restitution'].includes(scene)) {
    bodies.filter(b=>!b.isStatic).forEach(b=>M.Body.setVelocity(b,{x:M.Common.random(-3,3),y:M.Common.random(-7,-3)}));
   }
   M.Engine.update(sim.engine,1000/60);M.Engine.update(sim.engine,1000/60);
   // Optional matter-wrap plugin is not needed: recycle fallen balls for a continuous scene.
   if(['avalanche','ballPool'].includes(scene)) bodies.filter(b=>!b.isStatic).forEach(b=>{
    if(b.position.y>800||b.position.x < -150||b.position.x>950){M.Body.setPosition(b,{x:M.Common.random(60,700),y:-40});M.Body.setVelocity(b,{x:0,y:0});}
   });
   M.Render.world(sim.render,sim.engine.timing.timestamp);
   ctx.fillStyle='#0c0b17';ctx.fillRect(0,0,width,height);
   const margin=width*.035,scale=(width-2*margin)/800;
   const sceneHeight=600*scale,top=(height-sceneHeight)/2;
   ctx.drawImage(sim.render.canvas,margin,top,width-2*margin,sceneHeight);
   ctx.fillStyle='#dadbed';ctx.textAlign='center';ctx.font=`500 ${width*.043}px ReelSans`;
   const labels={ballPool:'A little chaos. A lot of motion.',newtonsCradle:'Watch the energy move.',avalanche:'One path. Hundreds of collisions.',restitution:'Same fall. Different bounce.',chains:'Everything is connected.'};
   ctx.fillText(labels[scene],width/2,top-width*.12);
   ctx.fillStyle='#85869c';ctx.font=`${width*.025}px ReelSans`;
   ctx.fillText('@shipstack_',width/2,top+sceneHeight+width*.10);
   return canvas.toBuffer('image/png');
  };
 };
 vm.runInContext(`(${setup.toString()})(${JSON.stringify({scene,seed,width,height})})`,sandbox);
 encoder=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate',String(fps),'-i','pipe:0','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t',String(config.duration_seconds),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',output],{stdio:['pipe','ignore','inherit']});
 let encoderError; encoder.on('error',e=>{encoderError=e;});encoder.stdin.on('error',e=>{encoderError=e;});
 const completion=once(encoder,'close');
 for(let i=0;i<fps*config.duration_seconds;i++){
  if(encoderError)throw encoderError;
  const data=sandbox.frame(i);
  if(!encoder.stdin.write(data))await Promise.race([once(encoder.stdin,'drain'),completion.then(()=>{throw Error('Encoder stopped early');})]);
 }
 encoder.stdin.end();
 const [code]=await completion;if(code!==0)throw Error(`ffmpeg exited ${code}`);
 writeFileSync(output+'.json',JSON.stringify({scene,seed,width,height,fps,seconds:config.duration_seconds,source:'liabru/matter-js@0.20.0'},null,2));
 console.log(`Rendered ${output}`);
} finally {if(encoder && encoder.exitCode===null)encoder.kill();}
