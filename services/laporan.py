"""Layanan perhitungan laporan keuangan: Dashboard, Neraca Saldo, dan Laba Rugi."""

import sqlite3
from typing import Any, Dict, List, Optional


def list_periode(conn: sqlite3.Connection) -> List[str]:
    """Daftar bulan unik (YYYY-MM) yang memiliki transaksi untuk filter laporan."""
    rows = conn.execute(
        "SELECT DISTINCT substr(tanggal, 1, 7) AS ym FROM jurnal ORDER BY ym DESC"
    ).fetchall()
    return [r["ym"] for r in rows if r["ym"]]


def _period_clause(periode: Optional[str]) -> tuple[str, list[Any]]:
    if periode and periode != "ALL":
        return "AND substr(j.tanggal, 1, 7) = ?", [periode]
    return "", []


def get_neraca_saldo(
    conn: sqlite3.Connection, periode: Optional[str] = None
) -> Dict[str, Any]:
    """Hitung Neraca Saldo untuk semua akun terdaftar (termasuk akun baru)."""
    clause, params = _period_clause(periode)
    rows = conn.execute(
        f"""
        SELECT
            a.no_akun,
            a.nama,
            a.saldo_normal,
            COALESCE(SUM(CASE WHEN j.id IS NOT NULL THEN jd.debit ELSE 0 END), 0) AS sum_debit,
            COALESCE(SUM(CASE WHEN j.id IS NOT NULL THEN jd.kredit ELSE 0 END), 0) AS sum_kredit
        FROM akun a
        LEFT JOIN jurnal_detail jd ON jd.no_akun = a.no_akun
        LEFT JOIN jurnal j ON j.id = jd.jurnal_id {clause}
        GROUP BY a.no_akun
        ORDER BY a.no_akun ASC
        """,
        params,
    ).fetchall()

    items: List[Dict[str, Any]] = []
    total_debit = 0
    total_kredit = 0
    for row in rows:
        net = row["sum_debit"] - row["sum_kredit"]
        debit = net if net > 0 else 0
        kredit = -net if net < 0 else 0
        total_debit += debit
        total_kredit += kredit
        items.append(
            {
                "no_akun": row["no_akun"],
                "nama": row["nama"],
                "saldo_normal": row["saldo_normal"],
                "debit": debit,
                "kredit": kredit,
            }
        )

    return {
        "periode": periode or "ALL",
        "items": items,
        "total_debit": total_debit,
        "total_kredit": total_kredit,
        "seimbang": total_debit == total_kredit,
    }


def get_laba_rugi(
    conn: sqlite3.Connection, periode: Optional[str] = None
) -> Dict[str, Any]:
    """Hitung Laporan Laba Rugi sesuai struktur sheet LABA RUGI (akun 4, 5, 6, 8, 9)."""
    clause, params = _period_clause(periode)
    rows = conn.execute(
        f"""
        SELECT
            a.no_akun,
            a.nama,
            a.kategori,
            a.saldo_normal,
            COALESCE(SUM(CASE WHEN j.id IS NOT NULL THEN jd.debit ELSE 0 END), 0) AS sum_debit,
            COALESCE(SUM(CASE WHEN j.id IS NOT NULL THEN jd.kredit ELSE 0 END), 0) AS sum_kredit
        FROM akun a
        LEFT JOIN jurnal_detail jd ON jd.no_akun = a.no_akun
        LEFT JOIN jurnal j ON j.id = jd.jurnal_id {clause}
        WHERE a.kategori IN (4, 5, 6, 8, 9)
        GROUP BY a.no_akun
        ORDER BY a.no_akun ASC
        """,
        params,
    ).fetchall()

    sections: Dict[int, List[Dict[str, Any]]] = {4: [], 5: [], 6: [], 8: [], 9: []}
    for row in rows:
        kat = row["kategori"]
        # Untuk pendapatan (4 & 8): kredit menambah (+), debit mengurangi (-)
        # Untuk pembelian & beban (5, 6, 9): debit menambah biaya (+), kredit mengurangi (-)
        if kat in (4, 8):
            nilai = row["sum_kredit"] - row["sum_debit"]
        else:
            nilai = row["sum_debit"] - row["sum_kredit"]

        sections[kat].append(
            {
                "no_akun": row["no_akun"],
                "nama": row["nama"],
                "nominal": nilai,
            }
        )

    pendapatan_bersih = sum(x["nominal"] for x in sections[4])
    pembelian_bersih = sum(x["nominal"] for x in sections[5])
    total_beban = sum(x["nominal"] for x in sections[6])
    pendapatan_tambahan = sum(x["nominal"] for x in sections[8])
    beban_lain = sum(x["nominal"] for x in sections[9])

    laba_rugi_bersih = (
        pendapatan_bersih
        - pembelian_bersih
        - total_beban
        + pendapatan_tambahan
        - beban_lain
    )

    return {
        "periode": periode or "ALL",
        "groups": [
            {
                "kode": "4",
                "judul": "PENDAPATAN BERSIH",
                "items": sections[4],
                "subtotal": pendapatan_bersih,
                "tanda": 1,
            },
            {
                "kode": "5",
                "judul": "PEMBELIAN BERSIH",
                "items": sections[5],
                "subtotal": pembelian_bersih,
                "tanda": -1,
            },
            {
                "kode": "6",
                "judul": "BEBAN OPERASIONAL",
                "items": sections[6],
                "subtotal": total_beban,
                "tanda": -1,
            },
            {
                "kode": "8",
                "judul": "PENDAPATAN TAMBAHAN",
                "items": sections[8],
                "subtotal": pendapatan_tambahan,
                "tanda": 1,
            },
            {
                "kode": "9",
                "judul": "BEBAN LAIN-LAIN",
                "items": sections[9],
                "subtotal": beban_lain,
                "tanda": -1,
            },
        ],
        "ringkasan": {
            "pendapatan_bersih": pendapatan_bersih,
            "pembelian_bersih": pembelian_bersih,
            "total_beban": total_beban,
            "pendapatan_tambahan": pendapatan_tambahan,
            "beban_lain": beban_lain,
            "laba_rugi_bersih": laba_rugi_bersih,
        },
    }


def get_dashboard_summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Ringkasan metrik nyata dari database untuk halaman Dashboard."""
    neraca = get_neraca_saldo(conn, "ALL")
    laba_rugi = get_laba_rugi(conn, "ALL")

    saldo_map = {item["no_akun"]: item for item in neraca["items"]}
    kas = saldo_map.get("1-110", {"debit": 0, "kredit": 0})
    bank = saldo_map.get("1-120", {"debit": 0, "kredit": 0})
    piutang = saldo_map.get("1-130", {"debit": 0, "kredit": 0})
    utang = saldo_map.get("2-110", {"debit": 0, "kredit": 0})

    kas_bank = (kas["debit"] - kas["kredit"]) + (bank["debit"] - bank["kredit"])
    saldo_piutang = piutang["debit"] - piutang["kredit"]
    saldo_utang = utang["kredit"] - utang["debit"]

    total_transaksi = conn.execute("SELECT COUNT(*) FROM jurnal").fetchone()[0]
    total_akun = conn.execute("SELECT COUNT(*) FROM akun").fetchone()[0]

    recent = conn.execute(
        """
        SELECT
            j.id,
            j.no_bukti,
            j.tanggal,
            j.keterangan,
            j.jenis,
            COALESCE(SUM(jd.debit), 0) AS nominal
        FROM jurnal j
        JOIN jurnal_detail jd ON jd.jurnal_id = j.id
        GROUP BY j.id
        ORDER BY j.tanggal DESC, j.id DESC
        LIMIT 8
        """
    ).fetchall()

    return {
        "penjualan_bersih": laba_rugi["ringkasan"]["pendapatan_bersih"],
        "pembelian_bersih": laba_rugi["ringkasan"]["pembelian_bersih"],
        "kas_bank": kas_bank,
        "laba_rugi": laba_rugi["ringkasan"]["laba_rugi_bersih"],
        "piutang_usaha": saldo_piutang,
        "utang_usaha": saldo_utang,
        "total_transaksi": total_transaksi,
        "total_akun": total_akun,
        "seimbang": neraca["seimbang"],
        "recent": [dict(r) for r in recent],
    }

