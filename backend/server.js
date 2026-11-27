import express from "express";
import multer from "multer";
import sqlite3 from "sqlite3";
import cors from "cors";
import fs from "fs";
import dotenv from "dotenv";
dotenv.config();

const app = express();
app.use(cors()); app.use(express.json());
const upload = multer({ dest: "uploads/" });
const db = new sqlite3.Database("ubernie.db");

// --- TABLES ---
db.exec(`
CREATE TABLE IF NOT EXISTS claims(id INTEGER PRIMARY KEY AUTOINCREMENT, business_id TEXT, business_name TEXT, owner TEXT, phone TEXT, email TEXT, id_number TEXT, bank TEXT, description TEXT, hours TEXT, area TEXT, status TEXT DEFAULT 'PENDING', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS kyc_docs(id INTEGER PRIMARY KEY AUTOINCREMENT, claim_id INTEGER, type TEXT, path TEXT);
CREATE TABLE IF NOT EXISTS businesses(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT UNIQUE, category TEXT DEFAULT 'spaza', area TEXT, address TEXT, status TEXT DEFAULT 'live', kyc_score INT DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS otps(id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, code TEXT, expires_at TEXT, used INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY AUTOINCREMENT, business_id INT, customer_phone TEXT, message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, direction TEXT, body TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
`);

// --- YOUR EXISTING CLAIMS - KEPT AS IS ---
app.post("/api/claims", upload.fields([{name:"idfile"},{name:"cipc"},{name:"poa"},{name:"photos"}]), (req,res)=>{
  const b=req.body;
  db.run(`INSERT INTO claims(business_id,business_name,owner,phone,email,id_number,bank,description,hours,area) VALUES(?,?,?,?,?,?,?,?,?,?)`,
  [b.id,b.biz,b.owner,b.phone,b.email,b.idnum,b.bank,b.desc,b.hours,b.area], function(err){
    if(err) return res.status(500).json({error:err.message});
    const cid=this.lastID;
    for(const [k,f] of Object.entries(req.files||{})){ for(const file of f){ db.run(`INSERT INTO kyc_docs(claim_id,type,path) VALUES(?,?,?)`,[cid,k,file.path]); } }
    res.json({ok:true, claim_id:cid, status:"PENDING", waitPos:cid+12});
  });
});
app.get("/api/claims", (req,res)=>{
  if(req.headers["x-admin-key"]!==process.env.ADMIN_KEY) return res.status(401).json({error:"unauthorized"});
  db.all(`SELECT * FROM claims ORDER BY created_at DESC`, [], (e,rows)=>res.json(rows));
});
app.post("/api/claims/:id/:action", (req,res)=>{
  if(req.headers["x-admin-key"]!==process.env.ADMIN_KEY) return res.status(401).json({error:"unauthorized"});
  const status = req.params.action==="approve" ? "VERIFIED" : "REJECTED";
  db.run(`UPDATE claims SET status=? WHERE id=?`,[status, req.params.id], ()=>res.json({ok:true, status}));
});
app.get("/api/business/:id/status", (req,res)=>{
  db.get(`SELECT status FROM claims WHERE business_id=? ORDER BY created_at DESC LIMIT 1`,[req.params.id],(e,row)=>res.json(row||{status:"UNCLAIMED"}));
});

// --- NEW: SPAZA / BUSINESS UPLOAD - THIS IS YESTERDAY'S MISSING PIECE ---
app.post("/api/businesses", (req,res)=>{
  const {name, phone, area, address, category} = req.body;
  if(!name || !phone) return res.status(400).json({error:"name + phone required"});
  db.run(`INSERT OR IGNORE INTO businesses(name,phone,category,area,address) VALUES(?,?,?,?,?)`,
  [name, phone, category||'spaza', area||'', address||''], function(err){
    if(err) return res.status(500).json({error:err.message});
    res.json({ok:true, id:this.lastID, name});
  });
});
// Bulk Spaza upload - CSV JSON array
app.post("/api/businesses/bulk", (req,res)=>{
  const list = req.body.spazas || req.body;
  if(!Array.isArray(list)) return res.status(400).json({error:"send {spazas:[{name,phone,area}]}"});
  let done=0;
  list.forEach(s=>{
    db.run(`INSERT OR IGNORE INTO businesses(name,phone,category,area,address) VALUES(?,?,?,?,?)`,
    [s.name, s.phone, s.category||'spaza', s.area||'', s.address||''], ()=>{ done++; if(done===list.length) res.json({ok:true, imported:done}); });
  });
  if(list.length===0) res.json({ok:true, imported:0});
});
app.get("/api/businesses", (req,res)=>{
  const cat = req.query.category;
  const q = cat ? `SELECT * FROM businesses WHERE category=? ORDER BY created_at DESC` : `SELECT * FROM businesses ORDER BY created_at DESC`;
  const p = cat ? [cat] : [];
  db.all(q, p, (e,rows)=>res.json(rows));
});
app.get("/api/businesses/spazas", (req,res)=>{
  db.all(`SELECT * FROM businesses WHERE category='spaza' ORDER BY id DESC`, [], (e,rows)=>{
    if(e){ console.log('SPAZA GET ERROR', e.message); return res.status(500).json({error:e.message}); }
    console.log('SPAZA GET OK', rows?.length);
    res.json(rows || []);
  });
});

// --- NEW: OTP ---
app.post("/api/otp/request", (req,res)=>{
  const {phone}=req.body; const code=String(Math.floor(100000+Math.random()*900000));
  db.run(`INSERT INTO otps(phone,code,expires_at) VALUES(?,?,datetime('now','+5 minutes'))`,[phone,code], ()=>{
    console.log(`OTP for ${phone}: ${code} - send via WhatsApp later`);
    res.json({ok:true, debug_code:code});
  });
});
app.post("/api/otp/verify", (req,res)=>{
  const {phone,code}=req.body;
  db.get(`SELECT * FROM otps WHERE phone=? AND code=? AND used=0 AND expires_at > datetime('now') ORDER BY id DESC LIMIT 1`,[phone,code],(e,row)=>{
    if(!row) return res.status(400).json({ok:false});
    db.run(`UPDATE otps SET used=1 WHERE id=?`,[row.id], ()=>res.json({ok:true}));
  });
});

// --- NEW: LEAD + WHATSAPP WEBHOOK (Whatomate replacement) ---
app.post("/api/lead", (req,res)=>{
  const {business_id, customer_phone, message}=req.body;
  db.run(`INSERT INTO leads(business_id,customer_phone,message) VALUES(?,?,?)`,[business_id,customer_phone,message||''], ()=>res.json({ok:true}));
});
app.post("/api/whatsapp/webhook", (req,res)=>{
  const msg = req.body.entry?.[0]?.changes?.[0]?.value?.messages?.[0];
  if(!msg) return res.sendStatus(200);
  const from=msg.from; const body=msg.text?.body||'';
  db.run(`INSERT INTO messages(phone,direction,body) VALUES(?,'in',?)`,[from,body]);
  if(body.toLowerCase().trim()==='yes') db.run(`UPDATE businesses SET status='live' WHERE phone=?`,[from]);
  res.sendStatus(200);
});
app.get("/api/whatsapp/webhook", (req,res)=>{
  if(req.query['hub.verify_token']===process.env.VERIFY_TOKEN) return res.send(req.query['hub.challenge']);
  res.sendStatus(403);
});

app.get("/api/health", (req,res)=>res.json({ok:true}));
app.listen(3000, ()=>console.log("Backend on :3000"));
