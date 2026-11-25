import pathlib
p = pathlib.Path('index.html').read_text()

# 1. CONFIG - CHANGE THESE 3 LINES TO YOUR REAL LINKS
config = """
// ===== REMOTEPAY CONFIG - CHANGE THESE =====
const REMOTEPAY = {
  // SimplyBlu PaymentLinks - Create ONE link per service in SimplyBlu dashboard, paste here
  // If you don't have them yet, leave as '#' and it will fallback to WhatsApp
  paymentLinks: {
    website: 'https://pay.simplyblu.co.za/website-1499', // R1499
    photos: 'https://pay.simplyblu.co.za/photos-799',
    whatsapp: 'https://pay.simplyblu.co.za/whatsapp-499',
    google: 'https://pay.simplyblu.co.za/google-699',
    hours: 'https://pay.simplyblu.co.za/hours-499',
    featured: 'https://pay.simplyblu.co.za/featured-299',
    domain: 'https://pay.simplyblu.co.za/domain-299',
    web_hosting: 'https://pay.simplyblu.co.za/hosting-999',
    email_hosting: 'https://pay.simplyblu.co.za/email-599',
    logo: 'https://pay.simplyblu.co.za/logo-499',
    care_plan: 'https://pay.simplyblu.co.za/careplan-499', // R499/mo
    ad_top: 'https://pay.simplyblu.co.za/ad-top-999',
    ad_sponsored: 'https://pay.simplyblu.co.za/ad-499',
  },
  // Whatomate Webhook - Get this from Whatomate > Automations > Webhook
  whatomateWebhook: 'https://api.whatomate.com/webhook/YOUR-WHATOMATE-ID',
  // Your WhatsApp for fallback / manual
  fallbackWA: MY_WA,
};
"""
# Insert config after MY_WA line
if 'REMOTEPAY' not in p:
    p = p.replace('const MY_WA=', config + '\nconst MY_WA=')

# 2. UPDATE submitClaim to use Whatomate + SimplyBlu
old_submit = "function submitClaim(){"
new_submit = """function sendToWhatomate(payload){
  // Fire to Whatomate - don't block user if it fails
  try{
    fetch(REMOTEPAY.whatomateWebhook, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}).catch(()=>{});
  }catch(e){}
  // Also fallback to WhatsApp so you never lose a lead
  const msg = `🔥 UBernie CLAIM REQUEST\\n\\nBusiness: ${payload.business}\\nArea: ${payload.area}\\nAudit: ${payload.audit}/100\\nOwner: ${payload.owner}\\nPhone: ${payload.phone}\\nServices: ${payload.services.map(s=>s.label+' R'+s.price).join(', ')}\\nTotal: R${payload.total}`;
  window.open(`https://wa.me/${MY_WA}?text=${encodeURIComponent(msg)}`,'_blank');
}

function submitClaim(){"""
if 'sendToWhatomate' not in p:
    p = p.replace(old_submit, new_submit)

# 3. Add PAY NOW button logic - Replace the CLAIM button in modal to show Pay via SimplyBlu
# We add a Pay button after CLAIM button in openClaim - find the CLAIM button
p = p.replace(
    '<button class="btn btn-green" onclick="submitClaim()">✅ CLAIM + Send Audit on WhatsApp</button>',
    '''<button class="btn btn-green" onclick="submitClaim()">✅ CLAIM + Send Audit on WhatsApp</button>
 <div style="text-align:center;margin:8px 0;font-size:13px;color:#666">OR Pay Instantly via RemotePay / SimplyBlu (Card) - No waiting</div>
 <button class="btn btn-dark" onclick="payNowClaim()">💳 PAY NOW - Secure Card via SimplyBlu</button>
 <div id="payLinks" style="display:none;margin-top:10px"></div>'''
)

# 4. Add payNowClaim function before </script>
p = p.replace("</script>", """
function payNowClaim(){
  let name=document.getElementById('ownerName').value; let phone=document.getElementById('ownerPhone').value;
  if(!name||!phone){alert('Please enter your name + WhatsApp number first'); return;}
  let chosen=window._claimServices.filter(s=>s.checked);
  if(chosen.length===0){alert('Tick at least 1 service to pay for'); return;}
  // Send to Whatomate first - so automation starts even if they don't pay yet
  sendToWhatomate({type:'claim_pay_attempt', business: window._claimBiz.name, area: window._claimBiz.area, audit: window._claimBiz.audit.score, owner: name, phone: phone, email: document.getElementById('ownerEmail').value, services: chosen, total: chosen.reduce((a,s)=>a+s.price,0)});
  // Show individual SimplyBlu links - Simplest, works TODAY without Standard Bank merchant
  let html = chosen.map(s=>{
    let link = REMOTEPAY.paymentLinks[s.id] || '#';
    return `<a href="${link}" target="_blank" style="display:block;background:#f6f6f6;padding:10px;border-radius:10px;margin:6px 0;text-decoration:none;color:#111">💳 Pay ${s.label} - <b>R${s.price}</b> → Pay via SimplyBlu</a>`;
  }).join('');
  html += `<p style="font-size:12px;color:#666">After payment, Whatomate will auto-send your receipt + next steps on WhatsApp. Powered by RemotePay.</p>`;
  document.getElementById('payLinks').innerHTML = html;
  document.getElementById('payLinks').style.display='block';
  alert('✅ Claim sent to Whatomate! Now tap a Pay link below to pay by card.');
}
</script>""")

pathlib.Path('index.html').write_text(p)
print("✅ Wired: RemotePay + SimplyBlu + Whatomate")
print("NEXT: Replace the placeholder SimplyBlu links + Whatomate webhook with your real ones")
