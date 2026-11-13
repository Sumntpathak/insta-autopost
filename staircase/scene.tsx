import React from 'react';
import stories from './stories.json';

const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const smooth=(n:number)=>{const t=clamp(n);return t*t*(3-2*t)};
const ink='#25314b';
const stepX=(n:number)=>87+n*53;
const stepY=(n:number)=>1040-n*56;
const font='DejaVu Sans, sans-serif';

function Cloud({x,y,s=1,fill='#fff'}:{x:number;y:number;s?:number;fill?:string}){
 return <g transform={`translate(${x} ${y}) scale(${s})`} fill={fill}>
   <path d="M-120 30Q-138 7-115-10Q-100-29-69-24Q-54-66-9-65Q31-66 54-32Q88-43 113-19Q130-3 123 19Q119 35 93 37H-98Q-114 37-120 30Z"/>
 </g>;
}

export const Lift:React.FC<{f:number;index:number}>=({f,index})=>{
 const story=stories[Math.floor(index/2)];
 const part=index%2;
 const pair=Math.floor(index/2);
 const title=story[part?3:0], sign=story[part?4:1], payoff=story[part?5:2], glow=story[part?7:6];
 const t=f/30;
 const move=clamp((t-(part?.85:0))/7.8)*8;
 const n=Math.floor(move), phase=move-n;
 const dx=stepX(n)+53*smooth(phase);
 const dy=stepY(n)-56*smooth(phase)-17*Math.sin(Math.PI*phase);
 const reveal=smooth((t-(part?8.58:8.2))/.66);
 const reaction=smooth((t-9.05)/.34);
 const tease=smooth((t-11.1)/.55);
 const retreat=part?0:34*reaction;
 const foot=9*Math.sin(Math.PI*phase);
 const offset=part&&t<.85?-26*(1-smooth(t/.85)):0;
 const sit=pair===0&&part?reaction:0;
 const cX=dx-retreat+offset, cY=dy;
 return <svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 720 1280" style={{fontFamily:font}}>
  <defs>
    <linearGradient id="sky" x2="0%" y2="100%"><stop stopColor={part?'#dceafa':'#cbe4f7'}/><stop offset="1" stopColor="#fdf5e8"/></linearGradient>
    <linearGradient id="step" x2="0%" y2="100%"><stop stopColor="#fff9ec"/><stop offset="1" stopColor="#dcccb7"/></linearGradient>
    <linearGradient id="light" x2="100%" y2="100%"><stop stopColor={glow}/><stop offset="1" stopColor={part?'#fff3c8':'#c94f3d'}/></linearGradient>
    <radialGradient id="sun"><stop stopColor="#fff9d3"/><stop offset="1" stopColor="#f6c768" stopOpacity="0"/></radialGradient>
  </defs>
  <rect width="720" height="1280" fill="url(#sky)"/>
  <circle cx="554" cy="365" r="192" fill="url(#sun)" opacity=".79"/>
  <Cloud x={164-t*4} y={432} s={1.3} fill="#edf7ff"/><Cloud x={627-t*5} y={534} s={1.55} fill="#e8f3fd"/>
  <Cloud x={66-t*3} y={716} s={1.1} fill="#f9faf7"/><Cloud x={600-t*6} y={910} s={1.62} fill="#fffaf2"/>
  <text x="56" y="116" fill={ink} fontSize="19" fontWeight="bold" letterSpacing="3">EK MANZIL AUR</text>
  <text x="664" y="116" textAnchor="end" fill={ink} fontSize="19" fontWeight="bold">PART {part+1}</text>
  <text x="56" y="187" fontSize={title.length>17?48:55} fontWeight="bold" fill={ink}>{title}</text>
  <g transform={`translate(0 ${Math.sin(t*.85)*5})`}>
   <path d="M48 1040H101V984H154V928H207V872H260V816H313V760H366V704H419V648H472V592H645V624L154 1126Z" fill="#d8c9b8" opacity=".66"/>
   {!part&&<g opacity={tease}>
    <path d="M629 552h39v-37h27v-37h25" fill="none" stroke="#fff9e9" strokeWidth="17" strokeLinejoin="round"/>
    <path d="M681 478l17-18 17 18m-17-18v36" fill="none" stroke={ink} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
   </g>}
   {Array.from({length:9},(_,i)=>{
     const x=stepX(i)-39,y=stepY(i),w=i===8?173:106;
     return <g key={i}>
      <path d={`M${x} ${y}l27 -14h${w}l-27 14Z`} fill="#fffdf5"/>
      <rect x={x} y={y} width={w} height="33" fill="url(#step)"/>
      <path d={`M${x+w} ${y}l27 -14v33l-27 14Z`} fill="#ccbaa4"/>
     </g>;
   })}
   <g transform="translate(559 592)">
    <path d="M-63 0V-176Q-63-226 0-226Q63-226 63-176V0Z" fill="#c8a98a"/>
    <path d="M-55 0V-173Q-55-214 0-214Q55-214 55-173V0Z" fill="url(#light)"/>
    <ellipse cy="-89" rx="44" ry="67" fill="#fff8d9" opacity={reveal*.45}/>
    {pair===0&&part===0&&<path d="M-47 0Q-40-17-44-42Q-29-35-21-52Q-6-23 4-38Q17-18 28-49Q44-32 47 0Z" fill="#ffcf78" opacity={reveal}/>}
    {pair===0&&part===1&&<g opacity={reveal} fill="#fff7df">
      <path d="M-38-84Q-45-111-24-112Q-10-130 7-112Q33-123 39-99L36-64H-37Z"/>
      <rect x="-43" y="-72" width="82" height="24" rx="12"/>
      <path d="M-36-53v31m66-31v31" stroke="#ffeed0" strokeWidth="7" strokeLinecap="round"/>
    </g>}
    {pair===1&&<circle cy="-116" r="29" fill="#fff6cb" opacity={reveal}/>}
    {pair===2&&<g opacity={reveal}><ellipse cy="-50" rx="40" ry="13" fill="#f6eee0"/><circle cy="-56" r={part?20:5} fill={part?'#ce5841':'#82a848'}/></g>}
    {pair===3&&<g opacity={reveal}><rect x="-29" y="-98" width="58" height="56" rx={part?19:5} fill={part?'#d6e7f6':'#9c4d42'}/><ellipse cy="-98" rx="29" ry="12" fill="#fff1d6"/></g>}
    {pair===4&&part===1&&<g opacity={reveal}>
      <path d="M-53 0V-173Q-53-210 0-210Q53-210 53-173V0Z" fill="#cee8ff"/>
      <Cloud x={-18} y={-64} s={.27}/><Cloud x={20} y={-140} s={.22}/>
    </g>}
    {pair===4&&part===0&&<path d="M-28-68H27M8-90L31-68 8-46" stroke="#fff8de" strokeWidth="8" fill="none" opacity={reveal}/>}
    <g transform={`translate(${-55+reveal*92} 0) scale(${1-reveal*.86} 1)`}>
      <path d="M0 0V-173Q0-214 55-214Q110-214 110-173V0Z" fill="#fbefdb" stroke="#be9c7e" strokeWidth="4"/>
      <circle cx="88" cy="-72" r="5" fill="#9f7253"/>
    </g>
    <g opacity={reveal}><rect x="-90" y="-267" width="180" height="38" rx="19" fill={ink}/>
     <text y="-241" textAnchor="middle" fill="#fff7e5" fontSize={sign.length>9?16:21} fontWeight="bold">{sign}</text>
    </g>
   </g>
   <ellipse cx={cX+6} cy={cY+1} rx="29" ry="7" fill="#af9b88" opacity=".31"/>
   <g transform={`translate(${cX} ${cY-(part?reaction*6:0)+sit*8}) scale(1 ${1-sit*.12}) rotate(${(part?6:-15)*reaction} 0 -40)`}>
    <path d={`M-13 -35Q-18 -20 ${-16-foot} ${-3-foot}m29 -31Q18-18 ${foot+4} -${17+foot}`} fill="none" stroke="#9b9ba6" strokeWidth="11" strokeLinecap="round"/>
    <path d={`M-23 -46Q-33 -${32+foot} -36 -34M25 -45Q35 -${29-foot} 38 -38`} stroke="#fbf8ed" strokeWidth="10" strokeLinecap="round" fill="none"/>
    <path d="M-27-31C-36-47-29-92-7-101C18-113 38-76 32-48C29-25-10-19-27-31Z" fill="#fffdf5" stroke="#b9b8bd" strokeWidth="2"/>
    <ellipse cx="7" cy="-70" rx="3.3" ry={3.3+reaction*1.3} fill={ink}/>
    <ellipse cx="20" cy="-71" rx="3.3" ry={3.3+reaction*1.3} fill={ink}/>
    {reaction>.5&&<path d="M10-59q6 7 11 0" fill="none" stroke={ink} strokeWidth="2.3" strokeLinecap="round"/>}
   </g>
  </g>
  <Cloud x={73-t*4} y={1157} s={1.4} fill="#fffaf4"/><Cloud x={651-t*3} y={1081} s={1.3} fill="#fffaf4"/>
  <g opacity={reaction}>
   <text x="360" y="1140" textAnchor="middle" fill={ink} fontSize="36" fontWeight="bold">{payoff}</text>
  </g>
  <g opacity={tease}>
   <text x="360" y="1196" textAnchor="middle" fill={ink} fontSize="23" fontWeight="bold">{part?'FOLLOW FOR THE NEXT CLIMB':'PART 2 ON @SHIPSTACK_'}</text>
  </g>
 </svg>;
};
