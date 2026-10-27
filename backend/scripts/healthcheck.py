"""Container healthcheck: GET /api/v1/health/ with the token from the environment.

The token is sent as a header and is never printed. Exit 0 = healthy, 1 = unhealthy.
"""

import os
import sys
import urllib.request

HEADER = "X-Health-Check-Token"


def check(
    port: str | None = None, token: str | None = None, timeout: float = 4.0
) -> bool:
    port = port or os.environ.get("BACKEND_PORT_INTERNAL", "8000")
    token = token if token is not None else os.environ.get("HEALTH_CHECK_PASSWORD", "")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/v1/health/", headers={HEADER: token}
    )
    try:
        with urllib.request.urlopen(  # nosec B310: fixed http://127.0.0.1 URL
            request, timeout=timeout
        ) as response:
            return response.status == 200
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
