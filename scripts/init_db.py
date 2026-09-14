#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize the SFGE database from schema.sql (re-runnable)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from db import get_db

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "sfge.db"
    db = get_db(path)
    db.init_schema()
    print(f"DB ready at {db.path}")
    for t in ["jobs", "reviews", "opportunities", "content",
              "ai_visibility_checks", "audit_findings"]:
        print(f"  {t}: {db.scalar('SELECT COUNT(*) FROM ' + t)} rows")
    db.close()

if __name__ == "__main__":
    main()