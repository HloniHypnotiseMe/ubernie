// FLEX sidebar - beside page, not on top
function toggleSidebar(force){
  var s=document.getElementById('sidebar'); if(!s) return false;
  var b=document.getElementById('menuBtn');
  var willOpen = (force!==undefined) ? force : s.classList.contains('closed');
  s.classList.toggle('open', willOpen);
  s.classList.toggle('closed', !willOpen);
  document.body.classList.toggle('sidebar-open', willOpen);
  document.body.classList.toggle('sidebar-closed', !willOpen);
  if(b) b.textContent = willOpen ? '✕ Close' : '☰ Categories';
  try{ localStorage.setItem('ubernie_sidebar', willOpen ? 'open':'closed'); }catch(e){}
  return false;
}
document.addEventListener('keydown', function(e){
  if((e.ctrlKey||e.metaKey) && e.shiftKey && e.key.toLowerCase()==='s'){ e.preventDefault(); toggleSidebar(); }
  if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='b' && !e.shiftKey){ e.preventDefault(); toggleSidebar(); }
  if(e.key==='Escape') toggleSidebar(false);
});
document.addEventListener('DOMContentLoaded', function(){
  // 1. Wrap everything except sidebar/overlay into #pageWrap - this is what makes it sit BESIDE
  var s=document.getElementById('sidebar'); if(!s) return;
  if(!document.getElementById('pageWrap')){
    var wrap=document.createElement('div'); wrap.id='pageWrap';
    var kids=[...document.body.children];
    kids.forEach(function(el){ if(el.id!=='sidebar' && el.id!=='sidebarOverlay' && el.tagName!=='SCRIPT') wrap.appendChild(el); });
    document.body.appendChild(wrap);
  }
  var startOpen = window.innerWidth > 900;
  try{ var saved=localStorage.getItem('ubernie_sidebar'); if(saved) startOpen=(saved==='open'); }catch(e){}
  toggleSidebar(startOpen);
  var btn=document.getElementById('menuBtn'); if(btn) btn.onclick=function(e){ e.preventDefault(); toggleSidebar(); };
  var close=document.getElementById('sidebarClose'); if(close) close.onclick=function(e){ e.preventDefault(); toggleSidebar(false); };
});
