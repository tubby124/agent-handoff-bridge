#!/usr/bin/env python3
"""Shared stdlib-only support for the Agent Handoff Bridge CLIs."""

import json
import re
import time
import urllib.error
import urllib.request
import uuid


AUTH_TEST_URL = "https://slack.com/api/auth.test"
HISTORY_URL = "https://slack.com/api/conversations.history"
POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
ENVELOPE_PREFIX = "[agent-handoff/v1] "
AGENT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
KINDS = {"task", "question", "status", "result", "error"}


class BridgeError(Exception):
    """A safe, machine-readable error for a bridge CLI."""

    def __init__(self, code, message=None):
        self.code = code
        self.message = message
        super().__init__(message or code)


def json_error(error):
    result = {"ok": False, "error": error.code}
    if error.message:
        result["message"] = error.message
    return json.dumps(result, separators=(",", ":"))


def validate_agent_name(value, field_name):
    if not isinstance(value, str) or not AGENT_NAME.fullmatch(value):
        raise BridgeError("invalid_arguments", "%s must use letters, digits, _ or -" % field_name)
    return value


def validate_kind(value):
    if value not in KINDS:
        raise BridgeError("invalid_arguments", "kind must be one of: %s" % ", ".join(sorted(KINDS)))
    return value


def make_envelope(sender, recipient, kind, summary, payload, correlation_id=None):
    validate_agent_name(sender, "sender")
    if recipient != "broadcast":
        validate_agent_name(recipient, "recipient")
    validate_kind(kind)
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 4000:
        raise BridgeError("invalid_arguments", "summary must contain 1 to 4000 characters")
    if payload is not None and not isinstance(payload, dict):
        raise BridgeError("invalid_arguments", "payload must be a JSON object")
    if correlation_id is not None and (not isinstance(correlation_id, str) or len(correlation_id) > 128):
        raise BridgeError("invalid_arguments", "correlation_id must contain at most 128 characters")
    return {
        "version": 1,
        "id": str(uuid.uuid4()),
        "from": sender,
        "to": recipient,
        "kind": kind,
        "summary": summary,
        "payload": payload or {},
        "correlation_id": correlation_id,
    }


def encode_envelope(envelope):
    return ENVELOPE_PREFIX + json.dumps(envelope, separators=(",", ":"), sort_keys=True)


def decode_envelope(text):
    if not isinstance(text, str) or not text.startswith(ENVELOPE_PREFIX):
        return None
    try:
        envelope = json.loads(text[len(ENVELOPE_PREFIX):])
    except json.JSONDecodeError:
        return None
    if not isinstance(envelope, dict) or envelope.get("version") != 1:
        return None
    required = ("id", "from", "to", "kind", "summary", "payload")
    if any(key not in envelope for key in required):
        return None
    try:
        validate_agent_name(envelope["from"], "sender")
        if envelope["to"] != "broadcast":
            validate_agent_name(envelope["to"], "recipient")
        validate_kind(envelope["kind"])
    except BridgeError:
        return None
    if not isinstance(envelope["id"], str) or not isinstance(envelope["summary"], str):
        return None
    if not isinstance(envelope["payload"], dict):
        return None
    if envelope.get("correlation_id") is not None and not isinstance(envelope["correlation_id"], str):
        return None
    return envelope


def response_json(raw):
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise BridgeError("invalid_response", "Slack returned a non-JSON response")
    if not isinstance(result, dict):
        raise BridgeError("invalid_response", "Slack returned unexpected JSON")
    return result


def slack_call(url, payload, token):
    """Call Slack once, retrying exactly once after a rate limit response."""
    for attempt in range(2):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.getcode()
                headers = response.headers
                raw = response.read()
        except urllib.error.HTTPError as error:
            status = error.code
            headers = error.headers
            raw = error.read()
        except (urllib.error.URLError, OSError):
            raise BridgeError("network_error", "Could not reach Slack")

        if status == 429 and attempt == 0:
            try:
                retry_after = int(headers.get("Retry-After", "1"))
            except ValueError:
                retry_after = 1
            time.sleep(max(0, retry_after))
            continue

        result = response_json(raw)
        if status >= 400 or result.get("ok") is not True:
            raise BridgeError(str(result.get("error", "http_error")))
        return result
    raise BridgeError("ratelimited")


def auth_test(token):
    result = slack_call(AUTH_TEST_URL, {}, token)
    user_id = result.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise BridgeError("invalid_response", "Slack did not return this bot user ID")
    return user_id
