#!/usr/bin/env python3
"""Offline contract tests for Agent Handoff Bridge."""

import importlib.util
import io
import pathlib
from email.message import Message
import unittest
from unittest import mock
import urllib.error


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_handoff", ROOT / "agent_handoff.py")
agent_handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_handoff)


class EnvelopeTests(unittest.TestCase):
    def test_round_trip(self):
        envelope = agent_handoff.make_envelope(
            "planner", "executor", "task", "Check the deployment", {"environment": "staging"}, "work-42"
        )
        decoded = agent_handoff.decode_envelope(agent_handoff.encode_envelope(envelope))
        self.assertEqual(decoded, envelope)

    def test_rejects_unversioned_or_malformed_text(self):
        self.assertIsNone(agent_handoff.decode_envelope("ordinary Slack message"))
        self.assertIsNone(agent_handoff.decode_envelope("[agent-handoff/v1] not-json"))
        self.assertIsNone(agent_handoff.decode_envelope("[agent-handoff/v1] {\"version\":2}"))

    def test_rejects_invalid_agent_name(self):
        with self.assertRaises(agent_handoff.BridgeError):
            agent_handoff.make_envelope("bad name", "executor", "task", "x", {})

    def test_allows_broadcast(self):
        envelope = agent_handoff.make_envelope("planner", "broadcast", "status", "Ready", {})
        self.assertEqual(agent_handoff.decode_envelope(agent_handoff.encode_envelope(envelope))["to"], "broadcast")


class SlackTransportTests(unittest.TestCase):
    def test_retries_once_after_rate_limit(self):
        headers = Message()
        headers["Retry-After"] = "0"
        limited = urllib.error.HTTPError(
            agent_handoff.AUTH_TEST_URL,
            429,
            "Too Many Requests",
            headers,
            io.BytesIO(b'{"ok":false,"error":"ratelimited"}'),
        )

        class SuccessResponse:
            headers = Message()

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def getcode(self):
                return 200

            def read(self):
                return b'{"ok":true,"user_id":"U0123456789"}'

        with mock.patch.object(
            agent_handoff.urllib.request, "urlopen", side_effect=[limited, SuccessResponse()]
        ) as urlopen, mock.patch.object(agent_handoff.time, "sleep") as sleep:
            result = agent_handoff.slack_call(agent_handoff.AUTH_TEST_URL, {}, "test-token")

        self.assertTrue(result["ok"])
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
