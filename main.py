"""Entry point aplikasi desktop SIA Azela Bakery & Pastry."""

import webview

from api import Api
from db import init_db
from paths import web_dir


def main() -> None:
    conn = init_db()
    api = Api(conn)
    index_file = web_dir() / "index.html"

    window = webview.create_window(
        title="Azela Bakery & Pastry - Sistem Informasi Akuntansi",
        url=index_file.as_uri(),
        js_api=api,
        width=1280,
        height=820,
        min_size=(960, 640),
    )
    api.attach_window(window)

    try:
        webview.start(debug=False)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

