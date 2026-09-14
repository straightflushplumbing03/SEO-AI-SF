#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 — Approval-gate and autonomy settings.

Guardrail 1: never bypass human review on first launch. This module holds
the *tuning knobs* that move from "always human approval" toward
"auto-publish after N clean approvals in a row". Lance (the user) must
explicitly raise the autonomy level; the engine never does it for itself.

Settings live in the `settings` table (key/value JSON). Defaults are the
safest possible (auto_publish=False, required_clean_approvals=5).
"""
import json

DEFAULTS = {
    # If True, content with publish_status='pending_approval' that meets all
    # quality gates may be merged automatically after the operator has
    # approved `required_clean_approvals` consecutive pages.
    "auto_publish_enabled": False,
    # Consecutive human approvals before auto-publish unlocks.
    "required_clean_approvals": 5,
    # Never auto-publish Tier-2 pages (they lack real field data). Guardrail 2.
    "auto_publish_tier2_allowed": False,
}


def get_setting(db, key):
    row = db.one("SELECT value FROM settings WHERE key=?", (key,))
    if not row:
        return DEFAULTS.get(key)
    try:
        return json.loads(row["value"])
    except ValueError:
        return row["value"]


def set_setting(db, key, value):
    db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value)),
    )
    db.conn.commit()


def can_auto_publish(db, tier="tier1"):
    """Apply the approval-gate policy for a given content tier."""
    if not get_setting(db, "auto_publish_enabled"):
        return False
    if tier == "tier2" and not get_setting(db, "auto_publish_tier2_allowed"):
        return False
    # count consecutive clean approvals (human-merged pages)
    clean = db.scalar(
        "SELECT COUNT(*) FROM content "
        "WHERE publish_status='live' AND needs_field_data=0"
    ) or 0
    return clean >= int(get_setting(db, "required_clean_approvals") or 5)