import express from "express";
import multer from "multer";
import sqlite3 from "sqlite3";
import cors from "cors";
import fs from "fs";
const app = express();
app.use(cors()); app.use(express.json());
const upload = multer({ dest: "uploads/" });
const db = new sqlite3.Database("ubernie.db");
db.exec(`CREATE TABLE IF NOT EXISTS claims(id INTEGER PRIMARY KEY AUTOINCREMENT, business_id TEXT, business_name TEXT, owner TEXT, phone TEXT, email TEXT, id_number TEXT, bank TEXT, description TEXT, hours TEXT, area TEXT, status TEXT DEFAULT 'PENDING', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS kyc_docs(id INTEGER PRIMARY KEY AUTOINCREMENT, claim_id INTEGER, type TEXT, path TEXT);`);

// 1. Business submits claim + KYC docs
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
// 2. Admin lists Pending claims
app.get("/api/claims", (req,res)=>{
  if(req.headers["x-admin-key"]!==process.env.ADMIN_KEY) return res.status(401).json({error:"unauthorized"});
  db.all(`SELECT * FROM claims ORDER BY created_at DESC`, [], (e,rows)=>res.json(rows));
});
// 3. Admin approves / rejects
app.post("/api/claims/:id/:action", (req,res)=>{
  if(req.headers["x-admin-key"]!==process.env.ADMIN_KEY) return res.status(401).json({error:"unauthorized"});
  const status = req.params.action==="approve" ? "VERIFIED" : "REJECTED";
  db.run(`UPDATE claims SET status=? WHERE id=?`,[status, req.params.id], ()=>res.json({ok:true, status}));
});
// 4. Public - get verified status for a business
app.get("/api/business/:id/status", (req,res)=>{
  db.get(`SELECT status FROM claims WHERE business_id=? ORDER BY created_at DESC LIMIT 1`,[req.params.id],(e,row)=>res.json(row||{status:"UNCLAIMED"}));
});
app.listen(3000, ()=>console.log("Backend on :3000"));
