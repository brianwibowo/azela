"""Jembatan API Python yang dipanggil oleh frontend JavaScript melalui pywebview."""

import base64
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

import webview

from db import seed_defaults
from paths import app_dir, db_path
from services import akun as akun_svc
from services import auth as auth_svc
from services import export_excel
from services import jurnal as jurnal_svc
from services import laporan as laporan_svc


DEFAULT_EXPORT_NAMES = {
    "pembelian": "Azela_Pembelian.xlsx",
    "penjualan": "Azela_Penjualan.xlsx",
    "transaksi_lainnya": "Azela_Transaksi_Lainnya.xlsx",
    "neraca_saldo": "Azela_Neraca_Saldo.xlsx",
    "laba_rugi": "Azela_Laba_Rugi.xlsx",
}


class Api:
    """Objek API publik untuk window.pywebview.api."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._window: Optional[webview.Window] = None

    def attach_window(self, window: webview.Window) -> None:
        """Simpan referensi jendela pywebview untuk dialog file native."""
        self._window = window

    def get_app_info(self) -> Dict[str, Any]:
        """Info lokasi database dan override logo eksternal jika tersedia."""
        external_logo = app_dir() / "logo.png"
        logo_data_url = None
        if external_logo.is_file():
            raw = external_logo.read_bytes()
            encoded = base64.b64encode(raw).decode("ascii")
            logo_data_url = f"data:image/png;base64,{encoded}"
        return {
            "db_path": str(db_path()),
            "logo_data_url": logo_data_url,
        }

    def login(self, username: str, password: str) -> Dict[str, Any]:
        return auth_svc.login(self._conn, username, password)

    def get_dashboard(self) -> Dict[str, Any]:
        return {"ok": True, "data": laporan_svc.get_dashboard_summary(self._conn)}

    def list_akun(self) -> Dict[str, Any]:
        return {"ok": True, "items": akun_svc.list_akun(self._conn)}

    def create_akun(self, no_akun: str, nama: str, saldo_normal: str) -> Dict[str, Any]:
        return akun_svc.create_akun(self._conn, no_akun, nama, saldo_normal)

    def update_akun(self, no_akun: str, nama: str, saldo_normal: str) -> Dict[str, Any]:
        return akun_svc.update_akun(self._conn, no_akun, nama, saldo_normal)

    def delete_akun(self, no_akun: str) -> Dict[str, Any]:
        return akun_svc.delete_akun(self._conn, no_akun)

    def next_no_bukti(self, jenis: str) -> Dict[str, Any]:
        return {"ok": True, "no_bukti": jurnal_svc.next_no_bukti(self._conn, jenis)}

    def list_pembelian(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "tunai": jurnal_svc.list_jurnal_by_jenis(self._conn, "PEMBELIAN_TUNAI"),
            "kredit": jurnal_svc.list_jurnal_by_jenis(self._conn, "PEMBELIAN_KREDIT"),
        }

    def create_pembelian_tunai(
        self, no_bukti: str, tanggal: str, keterangan: str, akun_pembayaran: str, nominal: int
    ) -> Dict[str, Any]:
        return jurnal_svc.create_pembelian_tunai(
            self._conn, no_bukti, tanggal, keterangan, akun_pembayaran, nominal
        )

    def create_pembelian_kredit(
        self, no_bukti: str, tanggal: str, keterangan: str, nominal: int
    ) -> Dict[str, Any]:
        return jurnal_svc.create_pembelian_kredit(
            self._conn, no_bukti, tanggal, keterangan, nominal
        )

    def list_penjualan(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "tunai": jurnal_svc.list_jurnal_by_jenis(self._conn, "PENJUALAN_TUNAI"),
            "kredit": jurnal_svc.list_jurnal_by_jenis(self._conn, "PENJUALAN_KREDIT"),
        }

    def create_penjualan_tunai(
        self, no_bukti: str, tanggal: str, keterangan: str, akun_penerimaan: str, nominal: int
    ) -> Dict[str, Any]:
        return jurnal_svc.create_penjualan_tunai(
            self._conn, no_bukti, tanggal, keterangan, akun_penerimaan, nominal
        )

    def create_penjualan_kredit(
        self, no_bukti: str, tanggal: str, keterangan: str, nominal: int
    ) -> Dict[str, Any]:
        return jurnal_svc.create_penjualan_kredit(
            self._conn, no_bukti, tanggal, keterangan, nominal
        )

    def list_transaksi_lainnya(self) -> Dict[str, Any]:
        return {"ok": True, **jurnal_svc.list_transaksi_lainnya(self._conn)}

    def create_transaksi_lainnya(
        self, no_bukti: str, tanggal: str, keterangan: str, lines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return jurnal_svc.create_transaksi_lainnya(
            self._conn, no_bukti, tanggal, keterangan, lines
        )

    def delete_jurnal(self, jurnal_id: int) -> Dict[str, Any]:
        return jurnal_svc.delete_jurnal(self._conn, jurnal_id)

    def list_periode(self) -> Dict[str, Any]:
        return {"ok": True, "items": laporan_svc.list_periode(self._conn)}

    def get_neraca_saldo(self, periode: str = "ALL") -> Dict[str, Any]:
        return {"ok": True, "data": laporan_svc.get_neraca_saldo(self._conn, periode)}

    def get_laba_rugi(self, periode: str = "ALL") -> Dict[str, Any]:
        return {"ok": True, "data": laporan_svc.get_laba_rugi(self._conn, periode)}

    def reset_demo_data(self) -> Dict[str, Any]:
        seed_defaults(self._conn, force_demo=True)
        return {"ok": True}

    def export_excel(self, modul: str, periode: str = "ALL") -> Dict[str, Any]:
        if modul not in DEFAULT_EXPORT_NAMES:
            return {"ok": False, "error": "Modul ekspor tidak dikenal."}

        default_name = DEFAULT_EXPORT_NAMES[modul]
        target_path: Optional[Path] = None

        if self._window is not None:
            dialog_type = (
                webview.FileDialog.SAVE
                if hasattr(webview, "FileDialog")
                else webview.SAVE_DIALOG
            )
            selection = self._window.create_file_dialog(
                dialog_type,
                directory=str(app_dir()),
                save_filename=default_name,
                file_types=("Excel Workbook (*.xlsx)",),
            )
            if not selection:
                return {"ok": False, "cancelled": True}
            chosen = selection[0] if isinstance(selection, (list, tuple)) else selection
            target_path = Path(chosen)
        else:
            export_folder = app_dir() / "exports"
            export_folder.mkdir(parents=True, exist_ok=True)
            target_path = export_folder / default_name

        if target_path.suffix.lower() != ".xlsx":
            target_path = target_path.with_suffix(".xlsx")

        try:
            if modul == "pembelian":
                export_excel.export_pembelian(self._conn, target_path)
            elif modul == "penjualan":
                export_excel.export_penjualan(self._conn, target_path)
            elif modul == "transaksi_lainnya":
                export_excel.export_transaksi_lainnya(self._conn, target_path)
            elif modul == "neraca_saldo":
                export_excel.export_neraca_saldo(self._conn, target_path, periode)
            elif modul == "laba_rugi":
                export_excel.export_laba_rugi(self._conn, target_path, periode)
        except OSError as exc:
            return {"ok": False, "error": f"Gagal menyimpan file Excel: {exc}"}

        return {"ok": True, "path": str(target_path)}

