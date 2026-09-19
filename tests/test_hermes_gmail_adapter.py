import importlib.util
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "examples" / "hermes-gmail" / "agent_handoff_gmail.py"
SPEC = importlib.util.spec_from_file_location("agent_handoff_gmail", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_parse_valid_envelope():
    body = '[agent-handoff/email-v1]\n{"id":"a","from":"muse","to":"hermes","kind":"task","summary":"Synthetic"}'
    assert MODULE.parse_envelope(body)["to"] == "hermes"


def test_rejects_ordinary_or_incomplete_email():
    assert MODULE.parse_envelope("hello") is None
    assert MODULE.parse_envelope('[agent-handoff/email-v1]\n{"id":"a"}') is None


def test_sender_normalization_requires_exact_address():
    allowed = {"bridge@example.com"}
    assert MODULE.allowed_sender("Bridge <bridge@example.com>", allowed)
    assert not MODULE.allowed_sender("other@example.com", allowed)


def test_state_round_trip_and_permissions(tmp_path):
    state = tmp_path / "state.json"
    MODULE.save_processed(state, "m1")
    assert MODULE.load_state(state) == {"m1"}
    assert (state.stat().st_mode & 0o777) == 0o600


def test_cli_json_accepts_pretty_printed_single_object():
    class Result:
        returncode = 0
        stdout = '{\n  "id": "m1",\n  "body": "synthetic"\n}\n'
        stderr = ""

    with patch.object(MODULE.subprocess, "run", return_value=Result()):
        assert MODULE.cli_json("/path/gmail.py", "personal", ["read", "m1"]) == [
            {"id": "m1", "body": "synthetic"}
        ]
