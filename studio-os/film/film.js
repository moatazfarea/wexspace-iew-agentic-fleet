const scenes=[...document.querySelectorAll('.scene')],cursor=document.querySelector('.cursor'),tc=document.getElementById('timecode');
let start=null,running=false;
const points=[[.13,.75],[.32,.72],[.5,.72],[.68,.72],[.84,.72],[.76,.28],[.71,.52],[.26,.52],[.2,.36],[.55,.45],[.79,.65],[.52,.8]];
function fmt(t){let s=Math.max(0,t),m=Math.floor(s/60),sec=Math.floor(s%60),f=Math.floor((s%1)*60);return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}:${String(f).padStart(2,'0')}`}
function ease(t){return t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2}
function frame(now){
 if(!running)return;
 const t=(now-start)/1000;tc.textContent=fmt(t);
 scenes.forEach(s=>{const a=+s.dataset.start,b=+s.dataset.end;s.classList.toggle('active',t>=a&&t<b);});
 const cycle=Math.min(points.length-2,Math.max(0,Math.floor(t/9)));let q=(t-cycle*9)/9;q=Math.min(1,Math.max(0,q));q=ease(q);
 const p1=points[cycle],p2=points[cycle+1],x=(p1[0]+(p2[0]-p1[0])*q)*innerWidth,y=(p1[1]+(p2[1]-p1[1])*q)*innerHeight;
 cursor.style.opacity=t>6&&t<108?'.95':'0';cursor.style.left=x+'px';cursor.style.top=y+'px';
 const ph=document.querySelector('.scene.active .phone');if(ph){const z=1+Math.sin(t*.6)*.012;ph.style.transform=`perspective(1200px) rotateY(${Math.sin(t*.33)*1.8}deg) translateY(${Math.sin(t*.7)*4}px) scale(${z})`;}
 if(t<115.4)requestAnimationFrame(frame);
}
function go(){if(running)return;running=true;start=performance.now();document.body.classList.add('running');requestAnimationFrame(frame)}
addEventListener('keydown',e=>{if(e.key==='F9')go()});