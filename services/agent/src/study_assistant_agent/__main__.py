from __future__ import annotations

import uvicorn

from .app import app
from .config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        # EventSource authenticates using a query parameter on its URL.
        access_log=False,
        reload=False,
    )


if __name__ == "__main__":
    main()
