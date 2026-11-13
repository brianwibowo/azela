"""Layanan manajemen Daftar Akun (Chart of Accounts)."""

import re
import sqlite3
from typing import Any, Dict, List

from db import kategori_dari_kode


KODE_AKUN_RE = re.compile(r"^[1-9]-\d{3}$")


def list_akun(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Ambil semua akun beserta jumlah pemakaiannya di jurnal."""
    rows = conn.execute(
        """
        SELECT
            a.no_akun,
            a.nama,
            a.saldo_normal,
            a.kategori,
            COUNT(jd.id) AS jumlah_transaksi
        FROM akun a
        LEFT JOIN jurnal_detail jd ON jd.no_akun = a.no_akun
        GROUP BY a.no_akun
        ORDER BY a.no_akun ASC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def _validate_akun_input(no_akun: str, nama: str, saldo_normal: str) -> Dict[str, Any]:
    kode = (no_akun or "").strip()
    label = (nama or "").strip()
    saldo = (saldo_normal or "").strip()

    if not KODE_AKUN_RE.match(kode):
        return {"ok": False, "error": "Format No. Akun harus X-XXX (contoh: 6-210)."}
    if not label:
        return {"ok": False, "error": "Nama akun tidak boleh kosong."}
    if saldo not in ("Db", "Kr"):
        return {"ok": False, "error": "Saldo normal harus Db atau Kr."}
    return {"ok": True, "no_akun": kode, "nama": label, "saldo_normal": saldo}


def create_akun(
    conn: sqlite3.Connection, no_akun: str, nama: str, saldo_normal: str
) -> Dict[str, Any]:
    """Tambah akun baru ke tabel akun."""
    v = _validate_akun_input(no_akun, nama, saldo_normal)
    if not v["ok"]:
        return v

    existing = conn.execute(
        "SELECT 1 FROM akun WHERE no_akun = ?", (v["no_akun"],)
    ).fetchone()
    if existing:
        return {"ok": False, "error": f"No. Akun {v['no_akun']} sudah terdaftar."}

    conn.execute(
        "INSERT INTO akun (no_akun, nama, saldo_normal, kategori) VALUES (?, ?, ?, ?)",
        (v["no_akun"], v["nama"], v["saldo_normal"], kategori_dari_kode(v["no_akun"])),
    )
    conn.commit()
    return {"ok": True}


def update_akun(
    conn: sqlite3.Connection, no_akun: str, nama: str, saldo_normal: str
) -> Dict[str, Any]:
    """Ubah nama atau saldo normal dari akun yang sudah ada."""
    v = _validate_akun_input(no_akun, nama, saldo_normal)
    if not v["ok"]:
        return v

    cur = conn.execute(
        "UPDATE akun SET nama = ?, saldo_normal = ? WHERE no_akun = ?",
        (v["nama"], v["saldo_normal"], v["no_akun"]),
    )
    if cur.rowcount == 0:
        return {"ok": False, "error": f"Akun {v['no_akun']} tidak ditemukan."}
    conn.commit()
    return {"ok": True}


def delete_akun(conn: sqlite3.Connection, no_akun: str) -> Dict[str, Any]:
    """Hapus akun jika belum pernah digunakan di transaksi jurnal."""
    kode = (no_akun or "").strip()
    used = conn.execute(
        "SELECT COUNT(*) FROM jurnal_detail WHERE no_akun = ?", (kode,)
    ).fetchone()[0]
    if used > 0:
        return {
            "ok": False,
            "error": f"Akun {kode} sudah dipakai di {used} baris transaksi dan tidak dapat dihapus.",
        }

    cur = conn.execute("DELETE FROM akun WHERE no_akun = ?", (kode,))
    if cur.rowcount == 0:
        return {"ok": False, "error": f"Akun {kode} tidak ditemukan."}
    conn.commit()
    return {"ok": True}

