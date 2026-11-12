// Matter.js handles motion and collisions; Canvas draws the portrait art direction.
import Matter from 'matter-js';
import {createCanvas,GlobalFonts} from '@napi-rs/canvas';
import {mkdirSync,writeFileSync,existsSync,unlinkSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import path from 'node:path';
import {soundtrack} from './soundtrack.mjs';
const [scene='spinner',seedText='1',output='reel.mp4']=process.argv.slice(2);
if(!['spinner','orbit','splitter'].includes(scene))throw Error('Unknown scene');
const seed=Number(seedText);if(!Number.isSafeInteger(seed)||seed<0)throw Error('Invalid seed');
const W=Number(process.env.REEL_WIDTH||1080),H=W*16/9,FPS=30,FRAMES=450;
if(!Number.isInteger(H)||W%2||H%2)throw Error('Expected even 9:16 dimensions');
for(const [file,name] of [['DejaVuSans-Bold.ttf','ReelBold'],['DejaVuSans.ttf','ReelSans'],['DejaVuSansMono.ttf','ReelMono']]){
 const f='/usr/share/fonts/truetype/dejavu/'+file;if(existsSync(f))GlobalFonts.registerFromPath(f,name);
}
mkdirSync(path.dirname(output),{recursive:true});
const canvas=createCanvas(W,H),ctx=canvas.getContext('2d'),S=W/1080;
const {Engine,Bodies,Body,Composite,Events}=Matter;
const engine=Engine.create({gravity:{x:0,y:0},positionIterations:8,velocityIterations:8});
let randomSeed=seed>>>0;const random=()=>{randomSeed=(1664525*randomSeed+1013904223)>>>0;return randomSeed/4294967296;};
const R=441,CX=540,CY=962,MAX=600,particles=[],walls=[],paddles=[],impacts=[];
const palettes=[['#73f5ff','#c494ff','#ff78be','#fff3a2'],['#80ffbd','#56cfff','#ffab6b','#eeeaff'],['#ff8daf','#bb8dff','#64e9ed','#ffe2b0']];
const colors=palettes[seed%palettes.length];
const sprites=Object.fromEntries(colors.map(color=>{
 const sprite=createCanvas(64,64),c=sprite.getContext('2d');
 const glow=c.createRadialGradient(32,32,4,32,32,31);glow.addColorStop(0,color+'a0');glow.addColorStop(.5,color+'25');glow.addColorStop(1,color+'00');c.fillStyle=glow;c.fillRect(0,0,64,64);
 c.beginPath();c.arc(32,32,11,0,Math.PI*2);c.fillStyle=color;c.fill();
 c.beginPath();c.arc(29,29,3,0,Math.PI*2);c.fillStyle='#ffffff90';c.fill();return [color,sprite];
}));
let queue=0,hits=0,frameTime=0,lastImpact=-1;
for(let i=0;i<96;i++){
 const a=i*Math.PI*2/96;
 const wall=Bodies.rectangle(Math.cos(a)*R,Math.sin(a)*R,2*Math.PI*R/96+3,18,{isStatic:true,angle:a+Math.PI/2,label:'wall',restitution:1,friction:0});
 walls.push(wall);
}
Composite.add(engine.world,walls);
if(scene!=='orbit')for(let i=0;i<(scene==='splitter'?3:2);i++){
 const p=Bodies.rectangle(0,0,174,14,{isStatic:true,label:'paddle',restitution:1.02,friction:0});paddles.push(p);Composite.add(engine.world,p);
}
function spawnBall(){
 if(particles.length>=MAX)return;
 const a=random()*Math.PI*2,dist=particles.length===0?R*.67:25+random()*85;
 const body=Bodies.circle(Math.cos(a)*dist,Math.sin(a)*dist,particles.length===0?12:8+random()*3,{label:'particle',friction:0,frictionAir:0,restitution:1,collisionFilter:{group:-1}});
 const v=12+random()*5;Body.setVelocity(body,{x:Math.cos(a+Math.PI*.15)*v,y:Math.sin(a+Math.PI*.15)*v});
 particles.push({body,color:colors[Math.floor(random()*colors.length)],trail:[]});Composite.add(engine.world,body);
}
spawnBall();
Events.on(engine,'collisionStart',event=>{
 for(const pair of event.pairs){
  if(pair.bodyA.label===pair.bodyB.label)continue;
  if(pair.bodyA.label!=='particle'&&pair.bodyB.label!=='particle')continue;
  hits++;queue++;if(frameTime-lastImpact>.07){impacts.push({time:frameTime});lastImpact=frameTime;}
 }
});
function text(str,x,y,size,color='#f2f5fc',font='ReelBold',align='left'){
 ctx.font=`${size}px ${font}`;ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(str,x,y);
}
function rounded(x,y,w,h,r,fill){ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fillStyle=fill;ctx.fill();}
function draw(frame){
 frameTime=frame/FPS;
 for(let sub=0;sub<2;sub++){
  const t=(frame*2+sub)/60;
  if(frame===300&&sub===0)for(const p of particles)Body.setVelocity(p.body,{x:-p.body.velocity.x,y:-p.body.velocity.y});
  const turn=t<10?t:20-t;
  paddles.forEach((p,i)=>{
   const a=turn*(scene==='splitter'?-.82:1.08)+i*Math.PI*2/paddles.length+.3;
   Body.setPosition(p,{x:Math.cos(a)*306,y:Math.sin(a)*306},true);Body.setAngle(p,a,true);
  });
  Engine.update(engine,1000/60);
  // Queue additions after collision callbacks, capped for stable export time.
  for(let n=0,add=Math.min(queue,MAX-particles.length);n<add;n++)spawnBall();queue=0;
  for(const p of particles){
   const b=p.body,d=Math.hypot(b.position.x,b.position.y);
   if(d>R-9){const nx=b.position.x/d,ny=b.position.y/d,dot=b.velocity.x*nx+b.velocity.y*ny;Body.setPosition(b,{x:nx*(R-12),y:ny*(R-12)});if(dot>0)Body.setVelocity(b,{x:b.velocity.x-2*dot*nx,y:b.velocity.y-2*dot*ny});}
   const speed=Math.hypot(b.velocity.x,b.velocity.y);
   if(speed<10||speed>19)Body.setVelocity(b,{x:b.velocity.x/(speed||1)*15,y:b.velocity.y/(speed||1)*15});
  }
 }
 ctx.save();ctx.scale(S,S);
 const bg=ctx.createLinearGradient(0,0,1080,1920);bg.addColorStop(0,'#0d1022');bg.addColorStop(.5,'#050811');bg.addColorStop(1,'#0a0e1d');ctx.fillStyle=bg;ctx.fillRect(0,0,1080,1920);
 // Quiet grid behind the arena; no empty landscape-video frame.
 ctx.strokeStyle='#ffffff05';ctx.lineWidth=1;
 for(let x=0;x<1080;x+=60){ctx.beginPath();ctx.moveTo(x,450);ctx.lineTo(x,1480);ctx.stroke();}
 for(let y=450;y<1480;y+=60){ctx.beginPath();ctx.moveTo(36,y);ctx.lineTo(1044,y);ctx.stroke();}
 text('COLLISION / CIRCUIT',72,157,22,'#8e9bb6','ReelMono');
 rounded(846,130,162,41,20,'#172637');text('SOUND ON',927,158,18,'#8deaff','ReelBold','center');
 const filled=particles.length>=MAX;
 text(frame>=300?'NOW REVERSE.':filled?`${MAX} BALLS.`:'ONE BOUNCE.',72,270,79);
 text(frame>=300?'WATCH THE SHIFT.':filled?'ONE CIRCLE.':'ONE MORE BALL.',72,359,79,colors[0]);
 text(frame>=300?'Same circle. A different direction.':'The direction flips at 10 seconds.',75,416,28,'#93a3bc','ReelSans');
 const beat=Math.exp(-((frameTime%(60/128))/.12));
 const glow=ctx.createRadialGradient(CX,CY,200,CX,CY,510);glow.addColorStop(0,'#11203818');glow.addColorStop(.85,'#283a6825');glow.addColorStop(1,'#15274800');ctx.fillStyle=glow;ctx.fillRect(20,CY-520,1040,1040);
 ctx.beginPath();ctx.arc(CX,CY,R+3,0,Math.PI*2);ctx.strokeStyle='#4acbff';ctx.lineWidth=2.5+beat*1.5+(frame>=300&&frame<310?6*(310-frame)/10:0);ctx.shadowColor='#39c7ff';ctx.shadowBlur=12+beat*9;ctx.stroke();ctx.shadowBlur=0;
 ctx.save();ctx.beginPath();ctx.arc(CX,CY,R-8,0,Math.PI*2);ctx.clip();
 for(const p of particles){
  const {x,y}=p.body.position;p.trail.push({x,y});if(p.trail.length>7)p.trail.shift();
  if(particles.length<190){ctx.beginPath();p.trail.forEach((q,i)=>i?ctx.lineTo(CX+q.x,CY+q.y):ctx.moveTo(CX+q.x,CY+q.y));ctx.strokeStyle=p.color+'35';ctx.lineWidth=3;ctx.stroke();}
  const radius=p.body.circleRadius+(particles.length<8?3:0),size=radius*5.8;
  ctx.drawImage(sprites[p.color],CX+x-size/2,CY+y-size/2,size,size);
 }
 for(const p of paddles){
  ctx.beginPath();ctx.moveTo(CX,CY);ctx.lineTo(CX+p.position.x,CY+p.position.y);ctx.strokeStyle='#7f94b4';ctx.lineWidth=5;ctx.stroke();
  ctx.save();ctx.translate(CX+p.position.x,CY+p.position.y);ctx.rotate(p.angle);
  const g=ctx.createLinearGradient(-87,0,87,0);g.addColorStop(0,'#9cb8d0');g.addColorStop(.5,'#edf5ff');g.addColorStop(1,'#647d9b');rounded(-87,-7,174,14,6,g);
  ctx.fillStyle='#0b122433';for(let x=-70;x<80;x+=13)ctx.fillRect(x,-6,2,12);ctx.restore();
 }
 if(paddles.length){ctx.beginPath();ctx.arc(CX,CY,17,0,Math.PI*2);ctx.fillStyle='#e4f1ff';ctx.fill();ctx.beginPath();ctx.arc(CX,CY,7,0,Math.PI*2);ctx.fillStyle='#344860';ctx.fill();}
 ctx.restore();
 rounded(72,1478,936,6,3,'#1c263c');rounded(72,1478,Math.max(6,936*particles.length/MAX),6,3,colors[0]);
 text('BALLS',72,1542,20,'#8595b0','ReelMono');text(String(particles.length).padStart(3,'0'),72,1624,74);
 text('COLLISIONS',420,1542,20,'#8595b0','ReelMono');text(String(hits).padStart(3,'0'),420,1624,74);
 text('15 SECONDS',1008,1542,20,'#8595b0','ReelMono','right');text(`${(15-frameTime).toFixed(1)}s`,1008,1624,60,'#c5d1e6','ReelMono','right');
 text('@shipstack_',72,1740,25,'#71809b','ReelSans');
 // Beat marks mirror the eight-bar soundtrack, not a fake loading indicator.
 for(let k=0;k<32;k++){const active=k<=frameTime/(60/128);rounded(710+k*9,1721,4,active?18:7,2,active?colors[0]:'#2c374e');}
 ctx.restore();return canvas.toBuffer('image/png');
}
const silent=output+'.silent.mp4',wav=output+'.wav';let encoder;
try{
 encoder=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',silent],{stdio:['pipe','ignore','inherit']});
 let error;encoder.on('error',e=>error=e);encoder.stdin.on('error',e=>error=e);
 const completion=once(encoder,'close');completion.catch(()=>{});
 for(let frame=0;frame<FRAMES;frame++){
  if(error)throw error;const data=draw(frame);
  if(!encoder.stdin.write(data))await Promise.race([once(encoder.stdin,'drain'),completion.then(()=>{throw Error('Encoder stopped');})]);
 }
 encoder.stdin.end();const [code]=await completion;if(code!==0)throw Error('Video encode failed');
 const music=soundtrack(wav,impacts,seed);
 const mux=spawn('ffmpeg',['-y','-v','error','-i',silent,'-i',wav,'-map','0:v','-map','1:a','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-c:a','aac','-b:a','192k','-t','15','-movflags','+faststart',output],{stdio:'inherit'});
 const [muxCode]=await once(mux,'close');if(muxCode!==0)throw Error('Audio mux failed');
 writeFileSync(output+'.json',JSON.stringify({scene,seed,width:W,height:H,fps:FPS,seconds:15,finalBalls:particles.length,collisions:hits,impactSounds:impacts.length,music},null,2));
 unlinkSync(silent);unlinkSync(wav);console.log(`Rendered ${output}: ${particles.length} balls, ${hits} hits, original music`);
}finally{if(encoder&&encoder.exitCode===null)encoder.kill();Engine.clear(engine);}
