// UBERNIE global sidebar - like GPT: slides left/right, Ctrl+Shift+S toggles
function toggleSidebar(force){
  var s=document.getElementById('sidebar');
  if(!s) return false;
  var o=document.getElementById('sidebarOverlay');
  var b=document.getElementById('menuBtn');
  var willOpen = (force!==undefined) ? force : !s.classList.contains('open');
  s.classList.toggle('open', willOpen);
  s.classList.toggle('closed', !willOpen);
  if(o) o.classList.toggle('show', willOpen);
  document.body.classList.toggle('sidebar-closed', !willOpen);
  if(b) b.textContent = willOpen ? '✕ Close' : '☰ Categories';
  try{ localStorage.setItem('ubernie_sidebar', willOpen ? 'open':'closed'); }catch(e){}
  return false;
}
document.addEventListener('keydown', function(e){
  // GPT-style: Ctrl+Shift+S  (also Ctrl+B as backup)
  if((e.ctrlKey||e.metaKey) && e.shiftKey && e.key.toLowerCase()==='s'){ e.preventDefault(); toggleSidebar(); }
  if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='b' && !e.shiftKey){ e.preventDefault(); toggleSidebar(); }
  if(e.key==='Escape') toggleSidebar(false);
});
document.addEventListener('DOMContentLoaded', function(){
  var s=document.getElementById('sidebar'); if(!s) return;
  // Restore last state
  try{ if(localStorage.getItem('ubernie_sidebar')==='closed') toggleSidebar(false); }catch(e){}
  var btn=document.getElementById('menuBtn'); if(btn) btn.onclick=function(e){ e.preventDefault(); toggleSidebar(); };
  var close=document.getElementById('sidebarClose'); if(close) close.onclick=function(e){ e.preventDefault(); toggleSidebar(false); };
  var o=document.getElementById('sidebarOverlay'); if(o) o.onclick=function(){ toggleSidebar(false); };
  document.querySelectorAll('#sidebar a').forEach(function(a){ a.addEventListener('click', function(){ if(window.innerWidth<=900) toggleSidebar(false); }); });
});
