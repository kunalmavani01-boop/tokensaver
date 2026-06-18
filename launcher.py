from __future__ import annotations

import threading
import webbrowser

import uvicorn

from manager.server import app as manager_app


def _open_browser() -> None:
    webbrowser.open("http://127.0.0.1:3001/manager/")


if __name__ == "__main__":
    threading.Timer(1.0, _open_browser).start()
    uvicorn.run(manager_app, host="127.0.0.1", port=3001)
