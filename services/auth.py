"""Layanan autentikasi pengguna lokal."""

import sqlite3
from typing import Dict, Any

from db import verify_password


def login(conn: sqlite3.Connection, username: str, password: str) -> Dict[str, Any]:
    """Periksa kredensial pengguna dan kembalikan info akun jika valid."""
    clean_user = (username or "").strip()
    clean_pass = password or ""
    if not clean_user or not clean_pass:
        return {"ok": False, "error": "Username dan password wajib diisi."}

    row = conn.execute(
        "SELECT id, username, nama_lengkap, password_hash FROM users WHERE username = ?",
        (clean_user,),
    ).fetchone()
    if row is None or not verify_password(clean_pass, row["password_hash"]):
        return {"ok": False, "error": "Username atau password salah."}

    return {
        "ok": True,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "nama_lengkap": row["nama_lengkap"],
        },
    }

