import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import supabase_connection as connection


@pytest.mark.parametrize("method, failures, expected_calls", [
    ("GET", 2, 3), ("GET", 3, 3), ("POST", 1, 1),
    ("PATCH", 1, 1), ("DELETE", 1, 1),
])
def test_interrupted_reads_retry_but_writes_do_not(monkeypatch, method, failures, expected_calls):
    calls = []
    monkeypatch.setattr(connection.time, "sleep", lambda _: None)

    def handle(request):
        calls.append(request)
        if len(calls) <= failures:
            raise httpx.RemoteProtocolError("connection terminated")
        return httpx.Response(200, json=[])

    with connection.ReadRetryClient(transport=httpx.MockTransport(handle)) as client:
        if failures >= expected_calls:
            with pytest.raises(httpx.RemoteProtocolError):
                client.request(method, "https://example.test/rest/v1/competitions")
        else:
            assert client.request(method, "https://example.test/rest/v1/competitions").status_code == 200
    assert len(calls) == expected_calls


def test_permission_errors_are_not_retried():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(403)

    with connection.ReadRetryClient(transport=httpx.MockTransport(handle)) as client:
        assert client.get("https://example.test").status_code == 403
    assert len(calls) == 1


def test_supabase_uses_http1_client(monkeypatch):
    original = connection.ReadRetryClient
    settings = {}

    def build(**kwargs):
        settings.update(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(connection, "ReadRetryClient", build)
    client = connection.create_client("https://example.supabase.co", "test-key")
    try:
        assert settings["http2"] is False
        assert client.postgrest.session is client.options.httpx_client
    finally:
        client.options.httpx_client.close()
