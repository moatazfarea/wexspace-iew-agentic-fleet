const buttons=[...document.querySelectorAll('.workspaceFrame aside button')];
buttons.forEach(b=>b.addEventListener('click',()=>{buttons.forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelector('.workspaceTop strong').textContent='WEXSPACE / '+b.dataset.view.toUpperCase();}));
const satellites=[...document.querySelectorAll('.satellite')];
window.addEventListener('pointermove',e=>{const x=(e.clientX/window.innerWidth-.5)*8,y=(e.clientY/window.innerHeight-.5)*8;satellites.forEach((s,i)=>s.style.transform=`translate(${x*(i+1)/3}px,${y*(i+1)/3}px)`);});