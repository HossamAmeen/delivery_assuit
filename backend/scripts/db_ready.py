"""Exit 0 if the database in DATABASE_URL is reachable (or needs no network), else 1."""

import os
import socket
import sys
from urllib.parse import urlparse

DEFAULT_PORTS = {"postgres": 5432, "postgresql": 5432, "mysql": 3306}


def database_ready(url: str | None, timeout: float = 2.0) -> bool:
    if not url:
        return True
    parsed = urlparse(url)
    scheme = parsed.scheme.split("+")[0]
    if scheme == "sqlite":
        return True
    host = parsed.hostname
    port = parsed.port or DEFAULT_PORTS.get(scheme)
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(0 if database_ready(os.environ.get("DATABASE_URL")) else 1)
