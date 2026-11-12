// Original 128 BPM instrumental: eight bars in exactly fifteen seconds.
// No sampled recordings or third-party music assets.
import {writeFileSync} from 'node:fs';
export function soundtrack(output, impacts=[], seed=1){
 const sr=48000,seconds=15,beat=60/128,bar=beat*4,N=sr*seconds;
 const left=new Float64Array(N),right=new Float64Array(N);
 let randomSeed=seed>>>0;
 const random=()=>{randomSeed=(1664525*randomSeed+1013904223)>>>0;return randomSeed/4294967296;};
 function add(time,duration,fn,gain=.2,pan=0){
  const start=Math.round(time*sr),end=Math.min(N,start+Math.round(duration*sr));
  for(let i=Math.max(0,start);i<end;i++){
   const t=(i-start)/sr, v=fn(t)*gain;
   left[i]+=v*Math.sqrt((1-pan)/2);right[i]+=v*Math.sqrt((1+pan)/2);
  }
 }
 const hz=m=>440*2**((m-69)/12);
 const chords=[[50,57,65],[46,53,62],[53,60,69],[48,55,64]];
 for(let b=0;b<32;b++){
  const t=b*beat;
  add(t,.34,x=>Math.sin(2*Math.PI*(49*x+115*.018*(1-Math.exp(-x/.018))))*Math.exp(-x*17),.78);
  if(b%4===1||b%4===3){
   add(t,.16,x=>(random()*2-1)*(Math.exp(-x*42)+.4*Math.exp(-Math.abs(x-.022)*150)),.19,.05);
  }
  for(let half=0;half<2;half++)add(t+beat*(half*.5+.25),.065,x=>(random()*2-1)*Math.exp(-x*95),half?.075:.055,half?.4:-.4);
 }
 for(let b=0;b<8;b++){
  const chord=chords[Math.floor(b/2)],base=chord[0]-12;
  // Warm offbeat bass; each beat ducks the sustained harmony.
  for(let k=0;k<4;k++)add(b*bar+(k+.5)*beat,.25,x=>{
   const f=hz(base);return (Math.sin(2*Math.PI*f*x)+.2*Math.sin(4*Math.PI*f*x))*Math.min(1,x/.012)*Math.exp(-x*12);
  },.38);
  for(const midi of chord)add(b*bar,bar+.18,x=>{
   const f=hz(midi+12),attack=Math.min(1,x/.15),release=Math.min(1,(bar+.18-x)/.3);
   const duck=.25+.75*Math.min(1,(x%beat)/.14);
   return (Math.sin(2*Math.PI*f*x)+.15*Math.sin(2*Math.PI*(f*1.003)*x))*attack*release*duck;
  },.055,(midi%3-1)*.35);
  const arp=[0,1,2,1,0,2,1,2];
  for(let k=0;k<8;k++){
   const midi=chord[arp[k]]+24;
   add(b*bar+k*beat/2,.26,x=>{
    const f=hz(midi);return (Math.sin(2*Math.PI*f*x)+.28*Math.sin(4*Math.PI*f*x))*Math.min(1,x/.004)*Math.exp(-x*19);
   },b<2?.105:.14,k%2?.35:-.35);
  }
 }
 // A short riser and downbeat mark the visual direction change at ten seconds.
 add(9.55,.45,x=>(random()*2-1)*(x/.45)**2,.10,-.1);
 add(10,.3,x=>Math.sin(2*Math.PI*(45*x+85*.025*(1-Math.exp(-x/.025))))*Math.exp(-x*15),.65);
 let last=-1;
 for(const impact of impacts){
  if(impact.time-last<.11)continue;last=impact.time;
  const midi=[86,89,93,96][Math.floor(random()*4)],f=hz(midi);
  add(impact.time,.16,x=>(Math.sin(2*Math.PI*f*x)+.35*Math.sin(2*Math.PI*f*2.01*x))*Math.exp(-x*45)*Math.min(1,x/.002),.06,random()*.8-.4);
 }
 let peak=0;
 for(let i=0;i<N;i++){
  const fade=Math.min(1,i/(sr*.008),(N-i)/(sr*.08));
  left[i]=Math.tanh(left[i]*1.2)*fade;right[i]=Math.tanh(right[i]*1.2)*fade;
  peak=Math.max(peak,Math.abs(left[i]),Math.abs(right[i]));
 }
 const buffer=Buffer.alloc(44+N*4);buffer.write('RIFF');buffer.writeUInt32LE(36+N*4,4);buffer.write('WAVEfmt ',8);buffer.writeUInt32LE(16,16);buffer.writeUInt16LE(1,20);buffer.writeUInt16LE(2,22);buffer.writeUInt32LE(sr,24);buffer.writeUInt32LE(sr*4,28);buffer.writeUInt16LE(4,32);buffer.writeUInt16LE(16,34);buffer.write('data',36);buffer.writeUInt32LE(N*4,40);
 for(let i=0;i<N;i++){buffer.writeInt16LE(Math.round(left[i]/Math.max(peak,.001)*.88*32767),44+i*4);buffer.writeInt16LE(Math.round(right[i]/Math.max(peak,.001)*.88*32767),46+i*4);}
 writeFileSync(output,buffer);
 return {name:'Collision Circuit',bpm:128,bars:8,source:'original synthesized instrumental',peak};
}
