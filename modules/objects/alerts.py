#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 — Alerting.

Sends high-priority signals to Slack (webhook) and/or email (SMTP) when the
operator has configured them via environment variables (never commit keys).

- SFGE_SLACK_WEBHOOK   -> POST JSON payload to a Slack incoming webhook
- SFGE_SMTP_HOST / SFGE_SMTP_USER / SFGE_SMTP_PASS / SFGE_ALERT_EMAIL

If neither is configured, alerts are logged to `reports/alerts.log` (so the
engine degrades gracefully with zero external services).
"""
import datetime as _dt
import json
import os
import smtplib
import ssl
import urllib.request


def _log(message, level="info"):
    os.makedirs("reports", exist_ok=True)
    with open("reports/alerts.log", "a", encoding="utf-8") as f:
        f.write(f"[{_dt.datetime.now().isoformat()}] {level}: {message}\n")


def _slack(text):
    webhook = os.environ.get("SFGE_SLACK_WEBHOOK", "")
    if not webhook:
        return False
    data = json.dumps({"text": text}).encode()
    req = urllib.request.Request(webhook, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30):
        return True


def _email(subject, body):
    host = os.environ.get("SFGE_SMTP_HOST", "")
    to = os.environ.get("SFGE_ALERT_EMAIL", "")
    if not (host and to):
        return False
    sender = os.environ.get("SFGE_SMTP_USER", "")
    password = os.environ.get("SFGE_SMTP_PASS", "")
    msg = f"Subject: {subject}\nFrom: {sender}\nTo: {to}\n\n{body}"
    ctx = ssl.create_default_context()
    port = int(os.environ.get("SFGE_SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as s:
        s.starttls(context=ctx)
        if sender and password:
            s.login(sender, password)
        s.sendmail(sender, [to], msg)
    return True


def alert(subject, body, level="warn"):
    """Deliver a message via configured channels; fall back to log."""
    text = f"[SFGE] {subject}\n{body}"
    delivered = _slack(text) or _email(subject, body)
    if delivered:
        _log(subject + " — delivered", level)
    else:
        _log(f"{subject}\n{body}", level)
    return delivered