#!/usr/bin/env python3
"""Narrow Gmail CLI adapter for the Agent Handoff Bridge.

This module intentionally delegates OAuth to an already-installed Gmail CLI.
It never accepts, prints, or stores a mail credential.
"""

from __future__ import annotations

import json
import subprocess
import sys
from email.utils import parseaddr
from pathlib import Path
from typing import Any

ENVELOPE_PREFIX = "[agent-handoff/email-v1]"


class BridgeError(Exception):
    """A predictable, safe-to-display bridge error."""


def error_json(error: str) -> str:
    return json.dumps({"ok": False, "error": error}, separators=(",", ":"))


def parse_envelope(body: str) -> dict[str, Any] | None:
    """Return a validated envelope, or None for ordinary email."""
    if not isinstance(body, str) or not body.startswith(ENVELOPE_PREFIX):
        return None
    raw = body[len(ENVELOPE_PREFIX) :].lstrip("\r\n ")
    try:
        envelope, _ = json.JSONDecoder().raw_decode(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(envelope, dict):
        return None
    for field in ("id", "from", "to", "kind", "summary"):
        if not isinstance(envelope.get(field), str) or not envelope[field].strip():
            return None
    return envelope


def normalized_address(value: str) -> str:
    return parseaddr(value)[1].strip().lower()


def allowed_sender(sender: str, allowed: set[str]) -> bool:
    return normalized_address(sender) in allowed


def cli_json(gmail_cli: str, account: str, arguments: list[str]) -> list[dict[str, Any]]:
    """Run the supplied Gmail CLI and parse newline-delimited JSON output."""
    result = subprocess.run(
        [sys.executable, gmail_cli, "--account", account, *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or "Gmail CLI failed").strip().splitlines()[-1]
        raise BridgeError("gmail_cli_failed: " + detail[:240])

    output = result.stdout.strip()
    if output:
        try:
            whole_output = json.loads(output)
        except json.JSONDecodeError:
            whole_output = None
        if isinstance(whole_output, dict):
            return [whole_output]

    records: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BridgeError("gmail_cli_returned_non_json") from exc
        if not isinstance(record, dict):
            raise BridgeError("gmail_cli_returned_non_object")
        records.append(record)
    return records


def load_state(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError("invalid_state_file") from exc
    if not isinstance(value, dict) or not isinstance(value.get("processed"), list):
        raise BridgeError("invalid_state_file")
    return {item for item in value["processed"] if isinstance(item, str)}


def save_processed(path: Path, message_id: str) -> None:
    processed = load_state(path)
    processed.add(message_id)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {"processed": sorted(processed)[-1000:]}
    path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    path.chmod(0o600)
