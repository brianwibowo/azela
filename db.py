"""Manajemen koneksi SQLite, skema tabel, dan data demo awal Azela Bakery & Pastry."""

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Optional

from paths import db_path


DEFAULT_ACCOUNTS = [
    ("1-110", "Kas", "Db"),
    ("1-120", "Bank", "Db"),
    ("1-130", "Piutang Usaha", "Db"),
    ("1-131", "Cadangan Kerugian Piutang", "Kr"),
    ("1-140", "Perlengkapan", "Db"),
    ("1-150", "Sewa Dibayar Dimuka", "Db"),
    ("1-210", "Tanah", "Db"),
    ("1-220", "Peralatan", "Db"),
    ("1-221", "Akumulasi Penyusutan Peralatan", "Kr"),
    ("1-230", "Kendaraan", "Db"),
    ("1-231", "Akumulasi Penyusutan Kendaraan", "Kr"),
    ("1-240", "Gedung", "Db"),
    ("1-241", "Akumulasi Penyusutan Gedung", "Kr"),
    ("2-110", "Utang Usaha", "Kr"),
    ("2-120", "Utang Gaji", "Kr"),
    ("2-130", "Utang Bunga", "Kr"),
    ("2-140", "Pendapatan Diterima Dimuka", "Kr"),
    ("2-210", "Utang Bank Jangka Panjang", "Kr"),
    ("3-110", "Modal Pemilik", "Kr"),
    ("3-120", "Prive", "Db"),
    ("4-110", "Penjualan", "Kr"),
    ("4-120", "Retur Penjualan", "Db"),
    ("4-130", "Potongan Penjualan", "Db"),
    ("5-110", "Pembelian", "Db"),
    ("5-120", "Retur Pembelian", "Kr"),
    ("5-130", "Potongan Pembelian", "Kr"),
    ("5-140", "Beban Angkut Pembelian", "Db"),
    ("6-110", "Beban Iklan", "Db"),
    ("6-120", "Beban Sewa", "Db"),
    ("6-130", "Beban Listrik, Air, dan Telepon", "Db"),
    ("6-140", "Beban Perlengkapan", "Db"),
    ("6-150", "Beban Penyusutan Peralatan", "Db"),
    ("6-160", "Beban Penyusutan Kendaraan", "Db"),
    ("6-170", "Beban Penyusutan Gedung", "Db"),
    ("6-180", "Beban Gaji", "Db"),
    ("6-190", "Beban Angkut Penjualan", "Db"),
    ("6-200", "Beban Piutang Tak Tertagih", "Db"),
    ("8-110", "Pendapatan Bunga", "Kr"),
    ("8-120", "Pendapatan Sewa", "Kr"),
    ("8-130", "Laba Penjualan Aset Tetap", "Kr"),
    ("9-110", "Beban Bunga", "Db"),
    ("9-120", "Beban Administrasi Bank", "Db"),
    ("9-130", "Rugi Penjualan Aset Tetap", "Db"),
]


DEMO_JOURNALS = [
    (
        "JU-001",
        "2026-11-01",
        "Setoran modal awal pemilik Azela Bakery & Pastry",
        "UMUM",
        [
            ("1-110", 15000000, 0),
            ("1-120", 10000000, 0),
            ("3-110", 0, 25000000),
        ],
    ),
    (
        "JU-002",
        "2026-11-02",
        "Pembelian oven deck dan mixer adonan",
        "UMUM",
        [
            ("1-220", 8000000, 0),
            ("1-120", 0, 8000000),
        ],
    ),
    (
        "PBT-001",
        "2026-11-03",
        "Pembelian tepung terigu protein tinggi dan ragi",
        "PEMBELIAN_TUNAI",
        [
            ("5-110", 1250000, 0),
            ("1-110", 0, 1250000),
        ],
    ),
    (
        "PBT-002",
        "2026-11-04",
        "Pembelian mentega, keju cheddar, dan cokelat",
        "PEMBELIAN_TUNAI",
        [
            ("5-110", 1850000, 0),
            ("1-120", 0, 1850000),
        ],
    ),
    (
        "PBK-001",
        "2026-11-05",
        "Pembelian stok gula pasir dan susu UHT (Supplier Makmur)",
        "PEMBELIAN_KREDIT",
        [
            ("5-110", 1600000, 0),
            ("2-110", 0, 1600000),
        ],
    ),
    (
        "PJT-001",
        "2026-11-06",
        "Penjualan harian roti manis dan croissant",
        "PENJUALAN_TUNAI",
        [
            ("1-110", 2400000, 0),
            ("4-110", 0, 2400000),
        ],
    ),
    (
        "PJT-002",
        "2026-11-07",
        "Penjualan paket pastry dan danish via transfer bank",
        "PENJUALAN_TUNAI",
        [
            ("1-120", 3150000, 0),
            ("4-110", 0, 3150000),
        ],
    ),
    (
        "PJK-001",
        "2026-11-08",
        "Pesanan snack box rapat (Kantor Dinas Pangan)",
        "PENJUALAN_KREDIT",
        [
            ("1-130", 1750000, 0),
            ("4-110", 0, 1750000),
        ],
    ),
    (
        "PBT-003",
        "2026-11-09",
        "Pembelian kemasan dus kue dan paper bag",
        "PEMBELIAN_TUNAI",
        [
            ("5-110", 450000, 0),
            ("1-110", 0, 450000),
        ],
    ),
    (
        "PBK-002",
        "2026-11-10",
        "Pembelian bahan selai buah dan almond slice",
        "PEMBELIAN_KREDIT",
        [
            ("5-110", 950000, 0),
            ("2-110", 0, 950000),
        ],
    ),
    (
        "PJT-003",
        "2026-11-11",
        "Penjualan kue tart dan bolu gulung akhir pekan",
        "PENJUALAN_TUNAI",
        [
            ("1-110", 2850000, 0),
            ("4-110", 0, 2850000),
        ],
    ),
    (
        "PJK-002",
        "2026-11-11",
        "Pesanan hampers roti mitra kafe",
        "PENJUALAN_KREDIT",
        [
            ("1-130", 1400000, 0),
            ("4-110", 0, 1400000),
        ],
    ),
    (
        "JU-003",
        "2026-11-12",
        "Pembayaran tagihan listrik, air, dan gas toko",
        "UMUM",
        [
            ("6-130", 420000, 0),
            ("1-110", 0, 420000),
        ],
    ),
    (
        "JU-004",
        "2026-11-12",
        "Pembayaran gaji karyawan bakery",
        "UMUM",
        [
            ("6-180", 2200000, 0),
            ("1-120", 0, 2200000),
        ],
    ),
    (
        "JU-005",
        "2026-11-13",
        "Pelunasan sebagian utang ke Supplier Makmur",
        "UMUM",
        [
            ("2-110", 1000000, 0),
            ("1-120", 0, 1000000),
        ],
    ),
]


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Buat hash password PBKDF2-HMAC-SHA256 dengan salt acak."""
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifikasi password terhadap hash yang tersimpan."""
    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return expected.hex() == digest_hex
    except ValueError:
        return False


def kategori_dari_kode(no_akun: str) -> int:
    """Ambil digit pertama nomor akun sebagai kategori akuntansi."""
    head = no_akun.strip().split("-", 1)[0]
    return int(head[0]) if head and head[0].isdigit() else 0


def get_connection(custom_path: Optional[Path] = None) -> sqlite3.Connection:
    """Buka koneksi SQLite dengan row factory dan foreign keys aktif."""
    target = custom_path or db_path()
    conn = sqlite3.connect(str(target), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Buat semua tabel jika belum tersedia."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            nama_lengkap TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS akun (
            no_akun TEXT PRIMARY KEY,
            nama TEXT NOT NULL,
            saldo_normal TEXT NOT NULL CHECK (saldo_normal IN ('Db', 'Kr')),
            kategori INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS jurnal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_bukti TEXT NOT NULL UNIQUE,
            tanggal TEXT NOT NULL,
            keterangan TEXT NOT NULL,
            jenis TEXT NOT NULL CHECK (
                jenis IN (
                    'PEMBELIAN_TUNAI',
                    'PEMBELIAN_KREDIT',
                    'PENJUALAN_TUNAI',
                    'PENJUALAN_KREDIT',
                    'UMUM'
                )
            ),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS jurnal_detail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurnal_id INTEGER NOT NULL,
            no_akun TEXT NOT NULL,
            debit INTEGER NOT NULL DEFAULT 0 CHECK (debit >= 0),
            kredit INTEGER NOT NULL DEFAULT 0 CHECK (kredit >= 0),
            FOREIGN KEY (jurnal_id) REFERENCES jurnal(id) ON DELETE CASCADE,
            FOREIGN KEY (no_akun) REFERENCES akun(no_akun) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_jurnal_tanggal ON jurnal(tanggal);
        CREATE INDEX IF NOT EXISTS idx_jurnal_jenis ON jurnal(jenis);
        CREATE INDEX IF NOT EXISTS idx_detail_akun ON jurnal_detail(no_akun);
        """
    )
    conn.commit()


def seed_defaults(conn: sqlite3.Connection, force_demo: bool = False) -> None:
    """Isi user admin, daftar akun Excel, dan data demo jika masih kosong."""
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        conn.execute(
            "INSERT INTO users (username, nama_lengkap, password_hash) VALUES (?, ?, ?)",
            ("admin", "Admin Azela Bakery", hash_password("admin123")),
        )

    akun_count = conn.execute("SELECT COUNT(*) FROM akun").fetchone()[0]
    if akun_count == 0 or force_demo:
        if force_demo:
            conn.execute("DELETE FROM jurnal_detail")
            conn.execute("DELETE FROM jurnal")
            conn.execute("DELETE FROM akun")
        for no_akun, nama, saldo_normal in DEFAULT_ACCOUNTS:
            conn.execute(
                "INSERT INTO akun (no_akun, nama, saldo_normal, kategori) VALUES (?, ?, ?, ?)",
                (no_akun, nama, saldo_normal, kategori_dari_kode(no_akun)),
            )

    jurnal_count = conn.execute("SELECT COUNT(*) FROM jurnal").fetchone()[0]
    if jurnal_count == 0 or force_demo:
        for no_bukti, tanggal, keterangan, jenis, lines in DEMO_JOURNALS:
            cur = conn.execute(
                "INSERT INTO jurnal (no_bukti, tanggal, keterangan, jenis) VALUES (?, ?, ?, ?)",
                (no_bukti, tanggal, keterangan, jenis),
            )
            jurnal_id = cur.lastrowid
            for no_akun, debit, kredit in lines:
                conn.execute(
                    "INSERT INTO jurnal_detail (jurnal_id, no_akun, debit, kredit) VALUES (?, ?, ?, ?)",
                    (jurnal_id, no_akun, debit, kredit),
                )

    conn.commit()


def init_db(custom_path: Optional[Path] = None) -> sqlite3.Connection:
    """Inisialisasi database lokal (buat tabel & seed bila baru)."""
    conn = get_connection(custom_path)
    create_schema(conn)
    seed_defaults(conn)
    return conn

