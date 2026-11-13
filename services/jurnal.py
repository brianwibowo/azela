"""Layanan transaksi Pembelian, Penjualan, dan Jurnal Umum (Transaksi Lainnya)."""

import sqlite3
from typing import Any, Dict, List


PREFIX_MAP = {
    "PEMBELIAN_TUNAI": "PBT",
    "PEMBELIAN_KREDIT": "PBK",
    "PENJUALAN_TUNAI": "PJT",
    "PENJUALAN_KREDIT": "PJK",
    "UMUM": "JU",
}


def next_no_bukti(conn: sqlite3.Connection, jenis: str) -> str:
    """Hasilkan nomor bukti berikutnya berdasarkan jenis transaksi."""
    prefix = PREFIX_MAP.get(jenis, "TR")
    rows = conn.execute(
        "SELECT no_bukti FROM jurnal WHERE no_bukti LIKE ?", (f"{prefix}-%",)
    ).fetchall()
    max_num = 0
    for row in rows:
        tail = row["no_bukti"].split("-", 1)[1]
        if tail.isdigit():
            max_num = max(max_num, int(tail))
    return f"{prefix}-{max_num + 1:03d}"


def list_jurnal_by_jenis(conn: sqlite3.Connection, jenis: str) -> Dict[str, Any]:
    """Ambil daftar transaksi per modul khusus (Pembelian/Penjualan) beserta totalnya."""
    rows = conn.execute(
        """
        SELECT
            j.id,
            j.no_bukti,
            j.tanggal,
            j.keterangan,
            jd.no_akun,
            jd.debit,
            jd.kredit
        FROM jurnal j
        JOIN jurnal_detail jd ON jd.jurnal_id = j.id
        WHERE j.jenis = ?
        ORDER BY j.tanggal ASC, j.id ASC, jd.id ASC
        """,
        (jenis,),
    ).fetchall()

    items_map: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        jid = row["id"]
        if jid not in items_map:
            items_map[jid] = {
                "id": jid,
                "no_bukti": row["no_bukti"],
                "tanggal": row["tanggal"],
                "keterangan": row["keterangan"],
                "akun_5110": 0,
                "akun_1110": 0,
                "akun_1120": 0,
                "akun_2110": 0,
                "akun_1130": 0,
                "akun_4110": 0,
            }
        item = items_map[jid]
        kode = row["no_akun"]
        nominal = row["debit"] if row["debit"] > 0 else row["kredit"]
        if kode == "5-110":
            item["akun_5110"] += nominal
        elif kode == "1-110":
            item["akun_1110"] += nominal
        elif kode == "1-120":
            item["akun_1120"] += nominal
        elif kode == "2-110":
            item["akun_2110"] += nominal
        elif kode == "1-130":
            item["akun_1130"] += nominal
        elif kode == "4-110":
            item["akun_4110"] += nominal

    items = list(items_map.values())
    totals = {
        "akun_5110": sum(i["akun_5110"] for i in items),
        "akun_1110": sum(i["akun_1110"] for i in items),
        "akun_1120": sum(i["akun_1120"] for i in items),
        "akun_2110": sum(i["akun_2110"] for i in items),
        "akun_1130": sum(i["akun_1130"] for i in items),
        "akun_4110": sum(i["akun_4110"] for i in items),
    }
    return {"items": items, "totals": totals}


def list_transaksi_lainnya(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Ambil semua baris jurnal umum (Transaksi Lainnya) lengkap dengan nama akun."""
    rows = conn.execute(
        """
        SELECT
            j.id AS jurnal_id,
            j.no_bukti,
            j.tanggal,
            j.keterangan,
            jd.id AS detail_id,
            jd.no_akun,
            a.nama AS nama_akun,
            jd.debit,
            jd.kredit
        FROM jurnal j
        JOIN jurnal_detail jd ON jd.jurnal_id = j.id
        JOIN akun a ON a.no_akun = jd.no_akun
        WHERE j.jenis = 'UMUM'
        ORDER BY j.tanggal ASC, j.id ASC, jd.id ASC
        """
    ).fetchall()
    items = [dict(r) for r in rows]
    total_debit = sum(r["debit"] for r in items)
    total_kredit = sum(r["kredit"] for r in items)
    return {
        "items": items,
        "totals": {"debit": total_debit, "kredit": total_kredit},
    }


def _insert_jurnal(
    conn: sqlite3.Connection,
    no_bukti: str,
    tanggal: str,
    keterangan: str,
    jenis: str,
    lines: List[Dict[str, Any]],
) -> Dict[str, Any]:
    bukti = (no_bukti or "").strip()
    tgl = (tanggal or "").strip()
    ket = (keterangan or "").strip()

    if not bukti:
        return {"ok": False, "error": "No. Bukti wajib diisi."}
    if not tgl:
        return {"ok": False, "error": "Tanggal transaksi wajib diisi."}
    if not ket:
        return {"ok": False, "error": "Keterangan transaksi wajib diisi."}
    if len(lines) < 2:
        return {"ok": False, "error": "Transaksi minimal memiliki 2 baris akun (Debit & Kredit)."}

    dup = conn.execute("SELECT 1 FROM jurnal WHERE no_bukti = ?", (bukti,)).fetchone()
    if dup:
        return {"ok": False, "error": f"No. Bukti {bukti} sudah ada."}

    total_debit = 0
    total_kredit = 0
    clean_lines = []
    for idx, line in enumerate(lines, start=1):
        kode = (line.get("no_akun") or "").strip()
        debit = int(line.get("debit") or 0)
        kredit = int(line.get("kredit") or 0)
        if not kode:
            return {"ok": False, "error": f"Baris {idx}: No. Akun belum dipilih."}
        exists = conn.execute("SELECT 1 FROM akun WHERE no_akun = ?", (kode,)).fetchone()
        if not exists:
            return {"ok": False, "error": f"Baris {idx}: Akun {kode} tidak ditemukan."}
        if debit < 0 or kredit < 0:
            return {"ok": False, "error": f"Baris {idx}: Nominal tidak boleh negatif."}
        if debit == 0 and kredit == 0:
            return {"ok": False, "error": f"Baris {idx}: Isi nominal Debit atau Kredit."}
        if debit > 0 and kredit > 0:
            return {"ok": False, "error": f"Baris {idx}: Satu baris hanya boleh Debit atau Kredit."}
        total_debit += debit
        total_kredit += kredit
        clean_lines.append((kode, debit, kredit))

    if total_debit == 0 or total_debit != total_kredit:
        return {
            "ok": False,
            "error": f"Total Debit (Rp {total_debit:,}) harus sama dengan Total Kredit (Rp {total_kredit:,}).".replace(",", "."),
        }

    cur = conn.execute(
        "INSERT INTO jurnal (no_bukti, tanggal, keterangan, jenis) VALUES (?, ?, ?, ?)",
        (bukti, tgl, ket, jenis),
    )
    jurnal_id = cur.lastrowid
    for kode, debit, kredit in clean_lines:
        conn.execute(
            "INSERT INTO jurnal_detail (jurnal_id, no_akun, debit, kredit) VALUES (?, ?, ?, ?)",
            (jurnal_id, kode, debit, kredit),
        )
    conn.commit()
    return {"ok": True, "id": jurnal_id}


def create_pembelian_tunai(
    conn: sqlite3.Connection,
    no_bukti: str,
    tanggal: str,
    keterangan: str,
    akun_pembayaran: str,
    nominal: int,
) -> Dict[str, Any]:
    """Catat pembelian tunai (Debit 5-110 Pembelian, Kredit 1-110 Kas atau 1-120 Bank)."""
    if akun_pembayaran not in ("1-110", "1-120"):
        return {"ok": False, "error": "Metode pembayaran harus Kas (1-110) atau Bank (1-120)."}
    try:
        amount = int(nominal)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Nominal harus berupa angka bulat."}
    if amount <= 0:
        return {"ok": False, "error": "Nominal pembelian harus lebih dari Rp 0."}

    return _insert_jurnal(
        conn,
        no_bukti,
        tanggal,
        keterangan,
        "PEMBELIAN_TUNAI",
        [
            {"no_akun": "5-110", "debit": amount, "kredit": 0},
            {"no_akun": akun_pembayaran, "debit": 0, "kredit": amount},
        ],
    )


def create_pembelian_kredit(
    conn: sqlite3.Connection,
    no_bukti: str,
    tanggal: str,
    keterangan: str,
    nominal: int,
) -> Dict[str, Any]:
    """Catat pembelian kredit (Debit 5-110 Pembelian, Kredit 2-110 Utang Usaha)."""
    try:
        amount = int(nominal)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Nominal harus berupa angka bulat."}
    if amount <= 0:
        return {"ok": False, "error": "Nominal pembelian harus lebih dari Rp 0."}

    return _insert_jurnal(
        conn,
        no_bukti,
        tanggal,
        keterangan,
        "PEMBELIAN_KREDIT",
        [
            {"no_akun": "5-110", "debit": amount, "kredit": 0},
            {"no_akun": "2-110", "debit": 0, "kredit": amount},
        ],
    )


def create_penjualan_tunai(
    conn: sqlite3.Connection,
    no_bukti: str,
    tanggal: str,
    keterangan: str,
    akun_penerimaan: str,
    nominal: int,
) -> Dict[str, Any]:
    """Catat penjualan tunai (Debit 1-110 Kas atau 1-120 Bank, Kredit 4-110 Penjualan)."""
    if akun_penerimaan not in ("1-110", "1-120"):
        return {"ok": False, "error": "Akun penerimaan harus Kas (1-110) atau Bank (1-120)."}
    try:
        amount = int(nominal)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Nominal harus berupa angka bulat."}
    if amount <= 0:
        return {"ok": False, "error": "Nominal penjualan harus lebih dari Rp 0."}

    return _insert_jurnal(
        conn,
        no_bukti,
        tanggal,
        keterangan,
        "PENJUALAN_TUNAI",
        [
            {"no_akun": akun_penerimaan, "debit": amount, "kredit": 0},
            {"no_akun": "4-110", "debit": 0, "kredit": amount},
        ],
    )


def create_penjualan_kredit(
    conn: sqlite3.Connection,
    no_bukti: str,
    tanggal: str,
    keterangan: str,
    nominal: int,
) -> Dict[str, Any]:
    """Catat penjualan kredit (Debit 1-130 Piutang Usaha, Kredit 4-110 Penjualan)."""
    try:
        amount = int(nominal)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Nominal harus berupa angka bulat."}
    if amount <= 0:
        return {"ok": False, "error": "Nominal penjualan harus lebih dari Rp 0."}

    return _insert_jurnal(
        conn,
        no_bukti,
        tanggal,
        keterangan,
        "PENJUALAN_KREDIT",
        [
            {"no_akun": "1-130", "debit": amount, "kredit": 0},
            {"no_akun": "4-110", "debit": 0, "kredit": amount},
        ],
    )


def create_transaksi_lainnya(
    conn: sqlite3.Connection,
    no_bukti: str,
    tanggal: str,
    keterangan: str,
    lines: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Catat transaksi jurnal umum multi-baris."""
    return _insert_jurnal(conn, no_bukti, tanggal, keterangan, "UMUM", lines)


def delete_jurnal(conn: sqlite3.Connection, jurnal_id: int) -> Dict[str, Any]:
    """Hapus satu transaksi jurnal beserta seluruh baris detailnya."""
    cur = conn.execute("DELETE FROM jurnal WHERE id = ?", (int(jurnal_id),))
    if cur.rowcount == 0:
        return {"ok": False, "error": "Transaksi tidak ditemukan."}
    conn.commit()
    return {"ok": True}

