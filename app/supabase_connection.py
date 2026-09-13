"""Shared Supabase HTTP configuration for Railway and local execution."""

import time

import httpx
from supabase import ClientOptions, create_client as _create_client


class ReadRetryClient(httpx.Client):
    """Retry interrupted reads only; never replay database writes."""

    def send(self, request, **kwargs):
        attempts = 3 if request.method in {"GET", "HEAD"} else 1
        for attempt in range(attempts):
            try:
                return super().send(request, **kwargs)
            except (httpx.NetworkError, httpx.TimeoutException, httpx.RemoteProtocolError):
                if attempt == attempts - 1:
                    raise
                time.sleep(0.5 * (attempt + 1))


def create_client(url, key):
    # Avoid HTTP/2 ConnectionTerminated failures on the database connection.
    http_client = ReadRetryClient(
        http2=False,
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    )
    try:
        return _create_client(url, key, options=ClientOptions(httpx_client=http_client))
    except Exception:
        http_client.close()
        raise
