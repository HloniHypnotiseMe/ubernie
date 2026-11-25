import glob, re

# Price per missing fix - this is YOUR RemotePay price list.
# Total should roughly match audit.upsell_value in listings.json
FIX_PRICES = {
  'phone': 299,
  'website': 499,
  'whatsapp': 199,
  'photos': 199,
  'hours': 99,
  'rating': 299,
}
FIX_LABELS = {
  'phone': 'Phone number listed',
  'website': 'Website / Booking page',
  'whatsapp': 'WhatsApp Business',
  'photos': 'Photos',
  'hours': 'Opening hours',
  'rating': 'Google reviews',
}

JS = """
function auditModal(x){
  var a=x.audit||{}, missing=a.missing||[], loss=a.monthly_loss_estimate||0, score=a.score||scoreFor(x);
  var rows=missing.map(function(m){
    var p=%s[m]||199, label=%s[m]||m;
    return '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #eee"><span>❌ '+label+'</span><b>R'+p+'</b></div>';
  }).join('') || '<div>✅ Nothing missing - fully verified</div>';
  var total=missing.reduce(function(s,m){return s+(%s[m]||199)},0);
  var msg=encodeURIComponent('Hi, I want to claim '+x.name+' on Ubernie. Audit '+score+'/100, Losing ~R'+loss+'/mo. Fixes total R'+total+'. Claim for R499/mo via RemotePay.');
  document.getElementById('auditModalBody').innerHTML='<h3 style="margin:0">'+x.name+'</h3><div class="muted">'+(x.area||'')+', '+(x.province||'')+'</div><div style="margin:12px 0;padding:12px;background:#fff3cd;border-radius:8px"><b>Audit: '+score+'/100</b><br>Losing ~R'+loss+'/mo<br>Upsell value: R'+(a.upsell_value||total)+'</div>'+rows+'<div style="display:flex;justify-content:space-between;padding:10px 0"><span><b>Total fixes</b></span><b>R'+total+'</b></div><a class="claim" style="display:block;text-align:center;padding:12px" href="https://wa.me/27735558440?text='+msg+'">Claim for R499/mo via RemotePay</a><div style="text-align:center;font-size:12px;color:#666;margin-top:8px">Or pay per fix - total R'+total+'</div>';
  document.getElementById('auditModal').style.display='flex';
}
function closeAudit(){document.getElementById('auditModal').style.display='none'}
""" % (FIX_PRICES, FIX_LABELS, FIX_PRICES)

MODAL_HTML = """
<div id="auditModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9999;align-items:center;justify-content:center;padding:16px" onclick="if(event.target.id=='auditModal')closeAudit()">
<div style="background:#fff;max-width:480px;width:100%;border-radius:12px;padding:20px;max-height:90vh;overflow:auto">
<div style="text-align:right"><button onclick="closeAudit()" style="border:0;background:0;font-size:20px;cursor:pointer">×</button></div>
<div id="auditModalBody"></div>
</div></div>
"""

for f in glob.glob("*.html"):
    t=open(f,encoding="utf-8",errors="ignore").read()
    if "auditModal" in t:
        print("skip",f); continue
    # 1. inject modal before </body>
    t=t.replace("</body>", MODAL_HTML+"</body>") if "</body>" in t else t+MODAL_HTML
    # 2. inject JS before render() or before </script> last occurrence
    if "function auditModal" not in t:
        t=t.replace("function render()", JS+"\\nfunction render()")
    # 3. change Claim link to open modal: replace Claim - R499/mo link
    # Old: <a class="claim" href="'+waLink(x)+'">Claim - R499/mo</a>
    t=t.replace(
        """<a class="claim" href="'+waLink(x)+'">Claim - R499/mo</a>""",
        """<a class="claim" href="javascript:void(0)" onclick="auditModal(x)">See Audit - Claim</a>"""
    )
    open(f,"w",encoding="utf-8").write(t)
    print("fixed claim",f)
