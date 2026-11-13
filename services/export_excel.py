"""Layanan ekspor data SIA Azela Bakery & Pastry ke file Excel (.xlsx)."""

from pathlib import Path
import sqlite3
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from services.jurnal import list_jurnal_by_jenis, list_transaksi_lainnya
from services.laporan import get_laba_rugi, get_neraca_saldo


RUPIAH_FMT = '"Rp "#,##0;("Rp "#,##0);"-"'
HEADER_FILL = PatternFill("solid", fgColor="382418")
SUBHEADER_FILL = PatternFill("solid", fgColor="EFE5D8")
TOTAL_FILL = PatternFill("solid", fgColor="F5ECE0")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="2A1C13")
SUBTITLE_FONT = Font(name="Calibri", size=11, bold=True, color="5E4638")
HEADER_FONT = Font(name="Calibri", size=10, bold=True, color="FAF6F0")
BOLD_FONT = Font(name="Calibri", size=10, bold=True, color="2A1C13")
BODY_FONT = Font(name="Calibri", size=10, color="2A1C13")
THIN_SIDE = Side(style="thin", color="C9B8A8")
CELL_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def _style_header_row(ws, row_idx: int, col_count: int) -> None:
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.border = CELL_BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _style_body_row(ws, row_idx: int, col_count: int, money_cols: tuple[int, ...] = ()) -> None:
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.font = BODY_FONT
        cell.border = CELL_BORDER
        if col in money_cols:
            cell.number_format = RUPIAH_FMT
            cell.alignment = Alignment(horizontal="right", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")


def _style_total_row(ws, row_idx: int, col_count: int, money_cols: tuple[int, ...] = ()) -> None:
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = TOTAL_FILL
        cell.font = BOLD_FONT
        cell.border = CELL_BORDER
        if col in money_cols:
            cell.number_format = RUPIAH_FMT
            cell.alignment = Alignment(horizontal="right", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")


def _autofit(ws) -> None:
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val = str(cell.value or "")
            if cell.number_format == RUPIAH_FMT and isinstance(cell.value, (int, float)):
                val = f"Rp {int(cell.value):,}"
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 45)


def export_pembelian(conn: sqlite3.Connection, output_path: Path) -> Path:
    """Ekspor Pembelian Tunai dan Pembelian Kredit ke 2 sheet dalam satu workbook."""
    wb = Workbook()

    # Sheet 1: Pembelian Tunai
    ws1 = wb.active
    ws1.title = "Pembelian Tunai"
    ws1["A1"] = "AZELA BAKERY & PASTRY"
    ws1["A1"].font = TITLE_FONT
    ws1["A2"] = "JURNAL PEMBELIAN TUNAI"
    ws1["A2"].font = SUBTITLE_FONT
    headers1 = ["No. Bukti", "Tanggal", "Keterangan", "Debit: 5-110 Pembelian", "Kredit: 1-110 Kas", "Kredit: 1-120 Bank"]
    ws1.append([])
    ws1.append(headers1)
    _style_header_row(ws1, 4, 6)

    tunai = list_jurnal_by_jenis(conn, "PEMBELIAN_TUNAI")
    for item in tunai["items"]:
        ws1.append([
            item["no_bukti"],
            item["tanggal"],
            item["keterangan"],
            item["akun_5110"],
            item["akun_1110"],
            item["akun_1120"],
        ])
        _style_body_row(ws1, ws1.max_row, 6, (4, 5, 6))

    ws1.append(["TOTAL", "", "", tunai["totals"]["akun_5110"], tunai["totals"]["akun_1110"], tunai["totals"]["akun_1120"]])
    _style_total_row(ws1, ws1.max_row, 6, (4, 5, 6))
    _autofit(ws1)

    # Sheet 2: Pembelian Kredit
    ws2 = wb.create_sheet("Pembelian Kredit")
    ws2["A1"] = "AZELA BAKERY & PASTRY"
    ws2["A1"].font = TITLE_FONT
    ws2["A2"] = "JURNAL PEMBELIAN KREDIT"
    ws2["A2"].font = SUBTITLE_FONT
    headers2 = ["No. Bukti", "Tanggal", "Keterangan", "Debit: 5-110 Pembelian", "Kredit: 2-110 Utang Usaha"]
    ws2.append([])
    ws2.append(headers2)
    _style_header_row(ws2, 4, 5)

    kredit = list_jurnal_by_jenis(conn, "PEMBELIAN_KREDIT")
    for item in kredit["items"]:
        ws2.append([
            item["no_bukti"],
            item["tanggal"],
            item["keterangan"],
            item["akun_5110"],
            item["akun_2110"],
        ])
        _style_body_row(ws2, ws2.max_row, 5, (4, 5))

    ws2.append(["TOTAL", "", "", kredit["totals"]["akun_5110"], kredit["totals"]["akun_2110"]])
    _style_total_row(ws2, ws2.max_row, 5, (4, 5))
    _autofit(ws2)

    wb.save(str(output_path))
    return output_path


def export_penjualan(conn: sqlite3.Connection, output_path: Path) -> Path:
    """Ekspor Penjualan Tunai dan Penjualan Kredit ke 2 sheet dalam satu workbook."""
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Penjualan Tunai"
    ws1["A1"] = "AZELA BAKERY & PASTRY"
    ws1["A1"].font = TITLE_FONT
    ws1["A2"] = "JURNAL PENJUALAN TUNAI"
    ws1["A2"].font = SUBTITLE_FONT
    headers1 = ["No. Bukti", "Tanggal", "Keterangan", "Debit: 1-110 Kas", "Debit: 1-120 Bank", "Kredit: 4-110 Penjualan"]
    ws1.append([])
    ws1.append(headers1)
    _style_header_row(ws1, 4, 6)

    tunai = list_jurnal_by_jenis(conn, "PENJUALAN_TUNAI")
    for item in tunai["items"]:
        ws1.append([
            item["no_bukti"],
            item["tanggal"],
            item["keterangan"],
            item["akun_1110"],
            item["akun_1120"],
            item["akun_4110"],
        ])
        _style_body_row(ws1, ws1.max_row, 6, (4, 5, 6))

    ws1.append(["TOTAL", "", "", tunai["totals"]["akun_1110"], tunai["totals"]["akun_1120"], tunai["totals"]["akun_4110"]])
    _style_total_row(ws1, ws1.max_row, 6, (4, 5, 6))
    _autofit(ws1)

    ws2 = wb.create_sheet("Penjualan Kredit")
    ws2["A1"] = "AZELA BAKERY & PASTRY"
    ws2["A1"].font = TITLE_FONT
    ws2["A2"] = "JURNAL PENJUALAN KREDIT"
    ws2["A2"].font = SUBTITLE_FONT
    headers2 = ["No. Bukti", "Tanggal", "Keterangan", "Debit: 1-130 Piutang Usaha", "Kredit: 4-110 Penjualan"]
    ws2.append([])
    ws2.append(headers2)
    _style_header_row(ws2, 4, 5)

    kredit = list_jurnal_by_jenis(conn, "PENJUALAN_KREDIT")
    for item in kredit["items"]:
        ws2.append([
            item["no_bukti"],
            item["tanggal"],
            item["keterangan"],
            item["akun_1130"],
            item["akun_4110"],
        ])
        _style_body_row(ws2, ws2.max_row, 5, (4, 5))

    ws2.append(["TOTAL", "", "", kredit["totals"]["akun_1130"], kredit["totals"]["akun_4110"]])
    _style_total_row(ws2, ws2.max_row, 5, (4, 5))
    _autofit(ws2)

    wb.save(str(output_path))
    return output_path


def export_transaksi_lainnya(conn: sqlite3.Connection, output_path: Path) -> Path:
    """Ekspor daftar Transaksi Lainnya (Jurnal Umum) ke Excel."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Transaksi Lainnya"
    ws["A1"] = "AZELA BAKERY & PASTRY"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = "JURNAL TRANSAKSI LAINNYA"
    ws["A2"].font = SUBTITLE_FONT
    ws.append([])
    ws.append(["Tanggal", "No. Bukti", "Keterangan", "No. Akun", "Nama Akun", "Debit", "Kredit"])
    _style_header_row(ws, 4, 7)

    data = list_transaksi_lainnya(conn)
    for item in data["items"]:
        ws.append([
            item["tanggal"],
            item["no_bukti"],
            item["keterangan"],
            item["no_akun"],
            item["nama_akun"],
            item["debit"],
            item["kredit"],
        ])
        _style_body_row(ws, ws.max_row, 7, (6, 7))

    ws.append(["TOTAL", "", "", "", "", data["totals"]["debit"], data["totals"]["kredit"]])
    _style_total_row(ws, ws.max_row, 7, (6, 7))
    _autofit(ws)
    wb.save(str(output_path))
    return output_path


def export_neraca_saldo(
    conn: sqlite3.Connection, output_path: Path, periode: Optional[str] = None
) -> Path:
    """Ekspor Neraca Saldo ke Excel."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Neraca Saldo"
    label_periode = "Semua Periode" if not periode or periode == "ALL" else f"Periode {periode}"
    ws["A1"] = "AZELA BAKERY & PASTRY"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = f"NERACA SALDO ({label_periode})"
    ws["A2"].font = SUBTITLE_FONT
    ws.append([])
    ws.append(["No. Akun", "Nama Akun", "Debit", "Kredit"])
    _style_header_row(ws, 4, 4)

    data = get_neraca_saldo(conn, periode)
    for item in data["items"]:
        ws.append([item["no_akun"], item["nama"], item["debit"], item["kredit"]])
        _style_body_row(ws, ws.max_row, 4, (3, 4))

    ws.append(["TOTAL", "", data["total_debit"], data["total_kredit"]])
    _style_total_row(ws, ws.max_row, 4, (3, 4))
    _autofit(ws)
    wb.save(str(output_path))
    return output_path


def export_laba_rugi(
    conn: sqlite3.Connection, output_path: Path, periode: Optional[str] = None
) -> Path:
    """Ekspor Laporan Laba Rugi ke Excel."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Laba Rugi"
    label_periode = "Semua Periode" if not periode or periode == "ALL" else f"Periode {periode}"
    ws["A1"] = "AZELA BAKERY & PASTRY"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = f"LAPORAN LABA RUGI ({label_periode})"
    ws["A2"].font = SUBTITLE_FONT
    ws.append([])
    ws.append(["No. Akun", "Nama Akun", "Nominal", "Subtotal"])
    _style_header_row(ws, 4, 4)

    data = get_laba_rugi(conn, periode)
    for group in data["groups"]:
        ws.append([group["judul"], "", "", ""])
        for col in range(1, 5):
            c = ws.cell(row=ws.max_row, column=col)
            c.fill = SUBHEADER_FILL
            c.font = BOLD_FONT
            c.border = CELL_BORDER
        for item in group["items"]:
            ws.append([item["no_akun"], item["nama"], item["nominal"], ""])
            _style_body_row(ws, ws.max_row, 4, (3,))
        sub_val = group["subtotal"] * group["tanda"]
        ws.append(["", f"Total {group['judul'].title()}", "", sub_val])
        _style_total_row(ws, ws.max_row, 4, (4,))

    ws.append(["LABA / RUGI BERSIH", "", "", data["ringkasan"]["laba_rugi_bersih"]])
    _style_total_row(ws, ws.max_row, 4, (4,))
    _autofit(ws)
    wb.save(str(output_path))
    return output_path

