import glob, re
# --- VERBATIM from 0d37624^:index.html, lines 34-180 ---
# Only MY_WA changed to your real number - replace below if wrong
OLD_JS = r"""
const MY_WA="27735558440";
const REMOTEPAY = {
  paymentLinks: {
    website: 'https://pay.simplyblu.co.za/website-1499',
    photos: 'https://pay.simplyblu.co.za/photos-799',
    whatsapp: 'https://pay.simplyblu.co.za/whatsapp-499',
    google: 'https://pay.simplyblu.co.za/google-699',
    hours: 'https://pay.simplyblu.co.za/hours-499',
    featured: 'https://pay.simplyblu.co.za/featured-299',
    domain: 'https://pay.simplyblu.co.za/domain-299',
    web_hosting: 'https://pay.simplyblu.co.za/hosting-999',
    email_hosting: 'https://pay.simplyblu.co.za/email-599',
    logo: 'https://pay.simplyblu.co.za/logo-499',
    care_plan: 'https://pay.simplyblu.co.za/careplan-499',
    ad_top: 'https://pay.simplyblu.co.za/ad-top-999',
    ad_sponsored: 'https://pay.simplyblu.co.za/ad-499',
  },
  whatomateWebhook: 'https://api.whatomate.com/webhook/YOUR-WHATOMATE-ID',
  fallbackWA: MY_WA,
};
function openClaim(idx){
 let x=(typeof ALL!=='undefined'?ALL:(window.data||window.listings||[]))[idx]; if(!x){alert('Listing not found');return;}
 let au=x.audit||{missing:[],score:0};
 let services=[
  {id:'website',label:'🌐 Professional Website (1 page)',price:1499,checked:!au.has_website},
  {id:'photos',label:'📸 Professional Photos + Google Photos',price:799,checked:true},
  {id:'whatsapp',label:'💬 WhatsApp Business Setup + Button',price:499,checked:true},
  {id:'google',label:'📍 Google Business Profile Fix',price:699,checked:true},
  {id:'hours',label:'🕐 Opening Hours + Booking System',price:499,checked:true},
  {id:'featured',label:'⭐ Featured on Ubernie - Top of Search (30 days)',price:299,checked:true},
  {id:'domain',label:'🌐 Domain Registration - yourbusiness.co.za (1 year)',price:299,checked:false},
  {id:'web_hosting',label:'☁️ Web Hosting - Fast + Secure + SSL (1 year)',price:999,checked:false},
  {id:'email_hosting',label:'📧 Email Hosting - info@yourbusiness.co.za (5 mailboxes / year)',price:599,checked:false},
  {id:'logo',label:'🎨 Logo + Business Card Design',price:499,checked:false},
 ];
 window._claimServices=services; window._claimBiz=x;
 let html=`<h2>⭐ Claim: ${x.name}</h2><p style="color:#666">${x.address||''} - ${x.area||''}</p>
 <div style="background:#ffebee;padding:12px;border-radius:10px"><b>🔍 YOUR FREE AUDIT: ${au.score}/100</b><br>Missing: ${(au.missing||[]).join(', ').replaceAll('_',' ')}<br><small>You are losing customers every day without these.</small></div>
 <h3>👤 Your Details</h3>
 <input id="ownerName" placeholder="Your Full Name *"><input id="ownerPhone" placeholder="Your WhatsApp Number *"><input id="ownerEmail" placeholder="Email">
 <h3>🛒 Fix My Missing Services (Tick what you want)</h3>
 ${services.map((s,i)=>`<div class="upsell"><label><input type="checkbox" ${s.checked?'checked':''} onchange="toggleService(${i},this.checked)"> ${s.label}</label><span class="price">R${s.price}</span></div>`).join('')}
 <div style="text-align:right;font-weight:800;font-size:18px" id="total">Total: R<span id="totalVal">0</span> <small style="font-weight:400">(Claim itself is FREE)</small></div>
 <button class="btn btn-green" onclick="submitClaim()">✅ CLAIM + Send Audit on WhatsApp</button>
 <div style="text-align:center;margin:8px 0;font-size:13px;color:#666">OR Pay Instantly via RemotePay / SimplyBlu (Card) - No waiting</div>
 <button class="btn btn-dark" onclick="payNowClaim()">💳 PAY NOW - Secure Card via SimplyBlu</button>
 <div id="payLinks" style="display:none;margin-top:10px"></div>
 <button class="btn btn-dark" onclick="closeModal()">Close</button>`;
 let mc=document.getElementById('modalContent')||document.getElementById('auditModalBody');
 if(!mc){alert('No modal container');return;}
 mc.innerHTML=html; (document.getElementById('modal')||document.getElementById('auditModal')).style.display='block'; updateTotal();
}
function toggleService(i,checked){window._claimServices[i].checked=checked; updateTotal();}
function updateTotal(){let t=window._claimServices.filter(s=>s.checked).reduce((a,s)=>a+s.price,0); document.getElementById('totalVal').textContent=t;}
function submitClaim(){
 let name=document.getElementById('ownerName').value; let phone=document.getElementById('ownerPhone').value;
 if(!name||!phone){alert('Please enter your name + WhatsApp number'); return;}
 let x=window._claimBiz; let chosen=window._claimServices.filter(s=>s.checked);
 let total=chosen.reduce((a,s)=>a+s.price,0);
 let msg=`🔥 UBernie CLAIM REQUEST\n\nBusiness: ${x.name}\nArea: ${x.area}\nAddress: ${x.address}\nAudit Score: ${x.audit.score}/100\nMissing: ${(x.audit.missing||[]).join(', ')}\n\nOwner: ${name}\nPhone: ${phone}\nEmail: ${document.getElementById('ownerEmail').value}\n\nServices Wanted:\n${chosen.map(s=>`- ${s.label} - R${s.price}`).join('\n')}\n\nTOTAL UPSELL: R${total}\nClaim Fee: FREE`;
 window.open(`https://wa.me/${MY_WA}?text=${encodeURIComponent(msg)}`,'_blank');
 alert('✅ Claim sent! We will WhatsApp you with your audit + quote.'); closeModal();
}
function closeModal(){let m=document.getElementById('modal')||document.getElementById('auditModal'); if(m)m.style.display='none';}
function sendToWhatomate(payload){
  try{fetch(REMOTEPAY.whatomateWebhook, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}).catch(()=>{});}catch(e){}
  const msg = `🔥 UBernie CLAIM REQUEST\n\nBusiness: ${payload.business}\nArea: ${payload.area}\nAudit: ${payload.audit}/100\nOwner: ${payload.owner}\nPhone: ${payload.phone}\nServices: ${payload.services.map(s=>s.label+' R'+s.price).join(', ')}\nTotal: R${payload.total}`;
  window.open(`https://wa.me/${MY_WA}?text=${encodeURIComponent(msg)}`,'_blank');
}
function payNowClaim(){
  let name=document.getElementById('ownerName').value; let phone=document.getElementById('ownerPhone').value;
  if(!name||!phone){alert('Please enter your name + WhatsApp number first'); return;}
  let chosen=window._claimServices.filter(s=>s.checked);
  if(chosen.length===0){alert('Tick at least 1 service to pay for'); return;}
  sendToWhatomate({type:'claim_pay_attempt', business: window._claimBiz.name, area: window._claimBiz.area, audit: window._claimBiz.audit.score, owner: name, phone: phone, email: document.getElementById('ownerEmail').value, services: chosen, total: chosen.reduce((a,s)=>a+s.price,0)});
  let html = chosen.map(s=>{
    let link = REMOTEPAY.paymentLinks[s.id] || '#';
    return `<a href="${link}" target="_blank" style="display:block;background:#f6f6f6;padding:10px;border-radius:10px;margin:6px 0;text-decoration:none;color:#111">💳 Pay ${s.label} - <b>R${s.price}</b> → Pay via SimplyBlu</a>`;
  }).join('');
  html += `<p style="font-size:12px;color:#666">After payment, Whatomate will auto-send your receipt + next steps on WhatsApp. Powered by RemotePay.</p>`;
  document.getElementById('payLinks').innerHTML = html;
  document.getElementById('payLinks').style.display='block';
  alert('✅ Claim sent to Whatomate! Now tap a Pay link below to pay by card.');
}
"""
MODAL_HTML='<div class="modal" id="modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:99;overflow:auto"><div class="modal-content" id="modalContent" style="background:#fff;max-width:520px;margin:30px auto;padding:24px;border-radius:16px;color:#111"></div></div>'
CSS='.upsell{border:1px solid #eee;border-radius:10px;padding:10px;margin:8px 0;display:flex;justify-content:space-between;align-items:center}.upsell label{font-size:14px}.price{font-weight:800}.modal-content input{width:100%;padding:12px;margin:6px 0;border:1px solid #ddd;border-radius:10px}'
for f in glob.glob("*.html"):
    if f.startswith("index.html.OLD"): continue
    t=open(f,encoding="utf-8",errors="ignore").read()
    if "openClaim" in t and "email_hosting" in t: print("skip",f); continue
    # remove my fake auditModal if present
    t=re.sub(r'<div id="auditModal".*?</div></div></div>', '', t, flags=re.S)
    if 'id="modal"' not in t:
        t=t.replace("</body>", MODAL_HTML+"</body>") if "</body>" in t else t+MODAL_HTML
    if ".upsell{" not in t:
        t=t.replace("</style>", CSS+"</style>") if "</style>" in t else t.replace("</head>", f"<style>{CSS}</style></head>")
    if "function openClaim" not in t:
        t=t.replace("</body>", f"<script>{OLD_JS}</script></body>") if "</body>" in t else t+f"<script>{OLD_JS}</script>"
    # point Claim buttons to openClaim - keeps existing render index if it uses data.indexOf(x)
    # generic: any button/link with Claim - R... becomes openClaim
    t=re.sub(r'onclick="[^"]*Claim[^"]*"', 'onclick="openClaim(ALL.indexOf(x))"', t)
    open(f,"w",encoding="utf-8").write(t)
    print("restored",f)
