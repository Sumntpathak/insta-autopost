import React from 'react';
import {interpolate} from 'remotion';
import {Actor, P, SMOOTH} from './engine/stick';
import {Burst, Dust, shakeAt} from './engine/fx';

import stories from './stories.json';
const white='#f7f6ed';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const linear=(f:number,a:number,b:number,x:number,y:number)=>interpolate(f,[a,b],[x,y],clamp);
const smooth=(f:number,a:number,b:number,x:number,y:number)=>interpolate(f,[a,b],[x,y],{...clamp,easing:SMOOTH});


export const Lift:React.FC<{f:number;index:number}>=({f,index})=>{
 const [goal,obstacle,barrier,payoff,,gold]=stories[index];
 const firstHit=81+(index%5)*3, secondHit=195+(index%4)*5, win=319+index*2;
 const land1=firstHit+29, land2=secondHit+27;
 const shieldOn=land2+13;
 const shots=[{s:firstHit-27,e:firstHit,y:625,x:230},{s:secondHit-30,e:secondHit,y:507,x:229},
   {s:shieldOn+10,e:shieldOn+27,y:705,x:421},{s:shieldOn+22,e:shieldOn+41,y:584,x:421},
   {s:shieldOn+35,e:shieldOn+54,y:472,x:421}];

 const y = f<firstHit ? smooth(f,0,firstHit,978,706)
    : f<land1 ? linear(f,firstHit,land1,706,1019)
    : f<secondHit ? smooth(f,land1+10,secondHit,1019,582)
    : f<land2 ? linear(f,secondHit,land2,582,1019)
    : smooth(f,shieldOn+1,win,1019,318);
 const shake=shakeAt(f,[firstHit,land1,secondHit,land2,...shots.slice(2).map(s=>s.e),win],7,10);
 const guarded=f>=shieldOn;
 const beat=Math.min(1,Math.max(0,(f-shieldOn)/12));
 const recoil=(f>=firstHit&&f<land1)||(f>=secondHit&&f<land2);
 const message=f>=win?payoff:f>=shieldOn?barrier+' ON':recoil?'TRY AGAIN':'';
 return <svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 720 1280"
  style={{fontFamily:'DejaVu Sans, sans-serif'}}>
   <defs>
    <radialGradient id="stage"><stop stopColor="#23252d"/><stop offset="1" stopColor="#08090d"/></radialGradient>
    <radialGradient id="halo"><stop stopColor="#f7c652" stopOpacity=".35"/><stop offset="1" stopColor="#f7c652" stopOpacity="0"/></radialGradient>
    <linearGradient id="metal" x2="0%" y2="100%"><stop stopColor="#eef0f5"/><stop offset=".35" stopColor="#8f9aac"/><stop offset="1" stopColor="#363b48"/></linearGradient>
    <linearGradient id="rack"><stop stopColor="#393e49"/><stop offset="1" stopColor="#17191f"/></linearGradient>
    <linearGradient id="beam" x2="0%" y2="100%"><stop stopColor="#ffdd80" stopOpacity=".20"/><stop offset="1" stopColor="#f7c652" stopOpacity=".025"/></linearGradient>
   </defs>
   <rect width="720" height="1280" fill="url(#stage)"/>
   <text x="360" y="120" textAnchor="middle" fontSize="16" fontWeight="bold" letterSpacing="4" fill="#989ca9">SHIPSTACK</text>
   <text x="360" y="191" textAnchor="middle" fontSize={goal.length>12?43:58} fontWeight="bold" letterSpacing={goal.length>12?4:8} fill={gold}>{goal}</text>
   <g transform={`translate(${shake.x} ${shake.y})`}>
    <ellipse cx="365" cy="1091" rx="300" ry="23" fill="#030407" opacity=".66"/>
    <path d="M65 1088H655" stroke="#41434b" strokeWidth="2" opacity=".45"/>
    <circle cx="173" cy="267" r={f>=win?110:66} fill="url(#halo)"/>
    <circle cx="173" cy="267" r="35" fill={f>=win?gold:'#131318'} stroke={gold} strokeWidth="2"/>
    <path d="M158 251H188V260Q188 274 173 276Q158 274 158 260ZM158 254H149Q149 268 159 269M188 254H197Q197 268 187 269M173 276V285M163 286H183"
      fill="none" stroke={f>=win?'#211805':gold} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M173 305V1030" stroke="#a8adba" strokeWidth="7"/>
    <path d={`M173 ${y+12}V1029`} stroke={gold} strokeWidth="3"/>
    {Array.from({length:21},(_,i)=><path key={i} d={`M${i%5===0?148:156} ${316+i*34}H164`} stroke="#777e8e" opacity=".52" strokeWidth="2"/>)}
    <path d="M174 1027l-12 6 24 7-24 7 24 7-24 7 24 7-12 6" fill="none" stroke={gold} strokeWidth="3" strokeLinejoin="round"/>
    <rect x="128" y="1074" width="91" height="13" rx="4" fill="url(#metal)"/>
    <rect x="149" y={y-27} width="41" height="55" rx="8" fill="#282c36" stroke="#626a78" strokeWidth="2"/>
    <circle cx="170" cy={y-12} r="4" fill={gold}/>
    <rect x="169" y={y+12} width="120" height="13" rx="6" fill={gold}/>
    <rect x="577" y="414" width="79" height="400" rx="15" fill="url(#rack)" stroke="#393d47" strokeWidth="2"/>
    <text x="617" y="615" textAnchor="middle" transform="rotate(90 617 615)" fontSize="18" fontWeight="bold" letterSpacing="3" fill="#bfc2cd">{obstacle}</text>
    {Array.from({length:10},(_,i)=>{
      const yy=445+i*36;
      return <g key={i}><path d={`M578 ${yy}H542`} stroke="#a2a9b7" strokeWidth="4"/><path d={`M542 ${yy-7}L523 ${yy}L542 ${yy+7}Z`} fill="#eceef4"/><rect x="568" y={yy-6} width="11" height="12" rx="2" fill="#787d89"/></g>;
    })}
    {guarded&&<g opacity={beat}>
      <rect x="337" y="394" width="83" height="443" rx="40" fill="url(#beam)" stroke={gold} strokeWidth="3"/>
      <path d="M408 433V795" stroke="#ffe5a3" strokeWidth="2" opacity=".56"/>
      <text x="379" y="615" textAnchor="middle" transform="rotate(90 379 615)" fontSize="19" fontWeight="bold" letterSpacing="3" fill={gold}>{barrier}</text>
    </g>}
    {shots.map(({s,e,y:sy,x})=>{
      if(f<s||f>=e)return null;
      const left=linear(f,s,e,542,x);
      return <g key={s} transform={`translate(${left} ${sy})`}>
       <path d="M23 0H112" stroke="#aab0c1" opacity=".27" strokeWidth="2"/>
       <path d="M12 0H61" stroke="#ebedf5" strokeWidth="4"/>
       <path d="M20-9L0 0L20 9Z" fill={white}/>
      </g>;
    })}
    {shots.map(({e,y:sy,x})=><Burst key={e} x={x} y={sy} at={e} f={f} color={e>shieldOn?gold:'#ff8c62'} size={e>shieldOn?56:82}/>)}
    <Dust x={215} y={1042} at={land1} f={f} spread={82}/>
    <Dust x={215} y={1042} at={land2} f={f} spread={82}/>
    <Actor f={f} scale={.78} color={white} face={f>=win?'happy':recoil?'sad':'eyes'} trails={recoil}
      base={{x:204,y:0}}
      keys={[
       {f:0,p:{...P.sit,y:0,ra1:46,ra2:-4}},
       {f:firstHit-2,p:{head:7}},
       {f:firstHit+3,p:{...P.shock,rot:18}},
       {f:land1,p:{...P.sad,rot:0}},
       {f:land1+34,p:{...P.sit,y:0,head:0,ra1:52,ra2:-8}},
       {f:secondHit+2,p:{...P.shock,rot:22}},
       {f:land2,p:{...P.sad,rot:0}},
       {f:shieldOn+2,p:{...P.pointR,head:-4}},
       {f:shieldOn+20,p:{...P.sit,y:0,head:-7,ra1:45,ra2:-5,la1:-18,la2:8}},
       {f:win,p:{...P.cheer,lean:-4,head:-4}},
      ]} mod={(frame,pose)=>({...pose,y:y-6+Math.sin(frame*.18)*1.1})}/>
    <Burst x={174} y={269} at={win} f={f} color={gold} size={142}/>
   </g>
   {message&&<text x="360" y="1162" textAnchor="middle" fontSize="22" letterSpacing="3" fontWeight="bold" fill={gold}>{message}</text>}
 </svg>;
};
