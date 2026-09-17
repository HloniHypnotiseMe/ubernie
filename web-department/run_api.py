#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.engine import init_db, db_path
print("=" * 60)
print(f">>> DB FILE: {db_path()}")
print("=" * 60)

init_db()

import uvicorn
uvicorn.run("api:app", host="127.0.0.1", port=8100, reload=False, log_level="info")
