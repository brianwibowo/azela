"""Pengujian otomatis untuk database, akuntansi, laporan, ekspor Excel, dan API."""

from pathlib import Path
import sys
import tempfile
import unittest

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import Api
from db import init_db
from services import akun as akun_svc
from services import auth as auth_svc
from services import export_excel
from services import jurnal as jurnal_svc
from services import laporan as laporan_svc


class AzelaSiaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_file = Path(self.tmp.name) / "test_azela.db"
        self.conn = init_db(self.db_file)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_seed_created_on_init(self) -> None:
        self.assertTrue(self.db_file.exists())
        akun_list = akun_svc.list_akun(self.conn)
        self.assertEqual(len(akun_list), 43)

        neraca = laporan_svc.get_neraca_saldo(self.conn)
        self.assertTrue(neraca["seimbang"])
        self.assertGreater(neraca["total_debit"], 0)
        self.assertEqual(neraca["total_debit"], neraca["total_kredit"])

    def test_login_valid_and_invalid(self) -> None:
        bad = auth_svc.login(self.conn, "admin", "salah")
        self.assertFalse(bad["ok"])
        good = auth_svc.login(self.conn, "admin", "admin123")
        self.assertTrue(good["ok"])
        self.assertEqual(good["user"]["username"], "admin")

    def test_akun_crud_and_delete_protection(self) -> None:
        # Tidak boleh hapus akun yang sudah dipakai di transaksi demo
        blocked = akun_svc.delete_akun(self.conn, "1-110")
        self.assertFalse(blocked["ok"])

        # Tambah akun beban baru (6-210) -> harus muncul di Neraca Saldo & Laba Rugi
        created = akun_svc.create_akun(self.conn, "6-210", "Beban Kemasan Khusus", "Db")
        self.assertTrue(created["ok"])

        neraca = laporan_svc.get_neraca_saldo(self.conn)
        self.assertTrue(any(x["no_akun"] == "6-210" for x in neraca["items"]))

        lr = laporan_svc.get_laba_rugi(self.conn)
        beban_grp = next(g for g in lr["groups"] if g["kode"] == "6")
        self.assertTrue(any(x["no_akun"] == "6-210" for x in beban_grp["items"]))

        # Edit dan hapus akun baru yang belum dipakai
        updated = akun_svc.update_akun(self.conn, "6-210", "Beban Packaging", "Db")
        self.assertTrue(updated["ok"])
        deleted = akun_svc.delete_akun(self.conn, "6-210")
        self.assertTrue(deleted["ok"])

    def test_pembelian_penjualan_dan_jurnal_umum(self) -> None:
        r1 = jurnal_svc.create_pembelian_tunai(
            self.conn, "PBT-901", "2026-11-13", "Beli ragi tambahan", "1-110", 200000
        )
        self.assertTrue(r1["ok"])

        r2 = jurnal_svc.create_pembelian_kredit(
            self.conn, "PBK-901", "2026-11-13", "Beli keju kredit", 300000
        )
        self.assertTrue(r2["ok"])

        r3 = jurnal_svc.create_penjualan_tunai(
            self.conn, "PJT-901", "2026-11-13", "Jual roti sore", "1-120", 900000
        )
        self.assertTrue(r3["ok"])

        r4 = jurnal_svc.create_penjualan_kredit(
            self.conn, "PJK-901", "2026-11-13", "Pesanan kantor kredit", 600000
        )
        self.assertTrue(r4["ok"])

        # Jurnal umum tidak seimbang harus ditolak
        unbalanced = jurnal_svc.create_transaksi_lainnya(
            self.conn,
            "JU-901",
            "2026-11-13",
            "Salah input",
            [
                {"no_akun": "6-110", "debit": 100000, "kredit": 0},
                {"no_akun": "1-110", "debit": 0, "kredit": 50000},
            ],
        )
        self.assertFalse(unbalanced["ok"])

        # Retur penjualan mengurangi pendapatan bersih
        ret = jurnal_svc.create_transaksi_lainnya(
            self.conn,
            "JU-902",
            "2026-11-13",
            "Retur penjualan roti",
            [
                {"no_akun": "4-120", "debit": 100000, "kredit": 0},
                {"no_akun": "1-110", "debit": 0, "kredit": 100000},
            ],
        )
        self.assertTrue(ret["ok"])

        neraca = laporan_svc.get_neraca_saldo(self.conn)
        self.assertTrue(neraca["seimbang"])
        self.assertEqual(neraca["total_debit"], neraca["total_kredit"])

        # Hapus salah satu transaksi dan verifikasi tetap seimbang
        del_res = jurnal_svc.delete_jurnal(self.conn, r1["id"])
        self.assertTrue(del_res["ok"])
        neraca_after = laporan_svc.get_neraca_saldo(self.conn)
        self.assertTrue(neraca_after["seimbang"])

    def test_excel_exports_and_api(self) -> None:
        out_dir = Path(self.tmp.name)
        p1 = export_excel.export_pembelian(self.conn, out_dir / "pembelian.xlsx")
        p2 = export_excel.export_penjualan(self.conn, out_dir / "penjualan.xlsx")
        p3 = export_excel.export_transaksi_lainnya(self.conn, out_dir / "ju.xlsx")
        p4 = export_excel.export_neraca_saldo(self.conn, out_dir / "ns.xlsx")
        p5 = export_excel.export_laba_rugi(self.conn, out_dir / "lr.xlsx")

        for p in (p1, p2, p3, p4, p5):
            self.assertTrue(p.exists())
            wb = load_workbook(p)
            self.assertGreaterEqual(len(wb.sheetnames), 1)

        api = Api(self.conn)
        dash = api.get_dashboard()
        self.assertTrue(dash["ok"])
        self.assertEqual(dash["data"]["total_akun"], 43)


if __name__ == "__main__":
    unittest.main()

