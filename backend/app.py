from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3, json, datetime

app = FastAPI(title="Ubernie API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def db():
    c = sqlite3.connect("backend/ubernie.db")
    c.row_factory = sqlite3.Row
    return c

@app.on_event("startup")
def init():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS businesses(id INTEGER PRIMARY KEY, name TEXT, category TEXT, area TEXT, address TEXT, phone TEXT, lat REAL, lng REAL, status TEXT DEFAULT 'FREE', verified INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS claims(id INTEGER PRIMARY KEY, business_id INTEGER, owner_name TEXT, owner_phone TEXT, owner_email TEXT, upsells TEXT, plan TEXT, total INTEGER, status TEXT DEFAULT 'PENDING_KYC', created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY, business_id INTEGER, name TEXT, phone TEXT, message TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS deals(id INTEGER PRIMARY KEY, business_id INTEGER, title TEXT, discount TEXT, starts TEXT, ends TEXT, status TEXT DEFAULT 'PENDING')")
    c.execute("CREATE TABLE IF NOT EXISTS gigs(id INTEGER PRIMARY KEY, business_id INTEGER, title TEXT, date TEXT, time TEXT, entry TEXT, status TEXT DEFAULT 'PENDING')")
    c.commit(); c.close()

class Claim(BaseModel):
    business_id: int
    owner_name: str
    owner_phone: str
    owner_email: Optional[str] = ""
    upsells: str = ""
    plan: str = "monthly"
    total: int = 0

@app.post("/api/claim")
def create_claim(cl: Claim):
    c = db()
    c.execute("INSERT INTO claims(business_id, owner_name, owner_phone, owner_email, upsells, plan, total, created_at) VALUES(?,?,?,?,?,?,?,?)",
              (cl.business_id, cl.owner_name, cl.owner_phone, cl.owner_email, cl.upsells, cl.plan, cl.total, datetime.datetime.now().isoformat()))
    c.commit(); c.close()
    return {"ok": True, "next": "KYC"}

@app.get("/api/businesses")
def list_businesses():
    c = db()
    rows = [dict(r) for r in c.execute("SELECT * FROM businesses LIMIT 100")]
    c.close()
    return rows

@app.get("/api/health")
def health():
    return {"ok": True}
