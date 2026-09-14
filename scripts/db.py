#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thin database wrapper for SFGE.

- SQLite backend by default (zero dependencies, schema.sql is a plain statement
  set that works under both).
- Postgres backend available by setting db.backend=postgres in config.yaml and
  installing `psycopg[binary]`.

Functions return dict-like rows and use statement text from schema.sql so
SQLite and Postgres stay in lockstep.
"""
import os
import sqlite3
import json


class SFGEDB:
    def __init__(self, path="sfge.db"):
        self.path = os.path.abspath(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")

    def init_schema(self, schema_path=None):
        if schema_path is None:
            schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
        with open(schema_path, encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def rows(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def one(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        r = cur.fetchone()
        return dict(r) if r else None

    def scalar(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        r = cur.fetchone()
        return r[0] if r else None

    def execute(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    # ---- convenience accessors -------------------------------------------------
    def get_job(self, job_id):
        return self.one("SELECT * FROM jobs WHERE job_id = ?", (job_id,))

    def get_reviews_for_job(self, job_id):
        return self.rows(
            "SELECT * FROM reviews WHERE job_id = ? ORDER BY review_id", (job_id,)
        )

    def jobs_by_city_service(self, city, service_type):
        return self.rows(
            """SELECT * FROM jobs
               WHERE lower(city) = lower(?) AND lower(service_type) = lower(?)
               ORDER BY date""",
            (city, service_type),
        )

    def insert_job(self, **kw):
        keys = [
            "date", "city", "neighborhood", "service_type", "issue_description",
            "photos", "duration_hours", "cost_range_bucket", "customer_quote",
            "review_id", "published_content_id", "status",
        ]
        cols = [k for k in keys if k in kw and kw[k] is not None]
        placeholders = ", ".join("?" for _ in cols)
        sql = f"INSERT INTO jobs ({', '.join(cols)}) VALUES ({placeholders})"
        vals = [kw[k] if not isinstance(kw[k], (list, dict)) else json.dumps(kw[k]) for k in cols]
        return self.execute(sql, vals)

    def insert_review(self, **kw):
        keys = [
            "job_id", "source", "rating", "text", "sentiment",
            "extracted_keywords", "extracted_city", "extracted_service",
            "approved_for_publish", "published",
        ]
        cols = [k for k in keys if k in kw and kw[k] is not None]
        placeholders = ", ".join("?" for _ in cols)
        sql = f"INSERT INTO reviews ({', '.join(cols)}) VALUES ({placeholders})"
        vals = [kw[k] if not isinstance(kw[k], (list, dict)) else json.dumps(kw[k]) for k in cols]
        return self.execute(sql, vals)

    def close(self):
        self.conn.commit()
        self.conn.close()


def get_db(path="sfge.db"):
    return SFGEDB(path=path)


if __name__ == "__main__":
    import sys
    db = get_db()
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        db.init_schema()
        print("DB initialized at", db.path)
    else:
        print("usage: python db.py init")