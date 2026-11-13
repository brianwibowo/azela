"""Generator Buku Panduan lengkap (PDF & Word) dengan screenshot Playwright per laman dan langkah."""

import base64
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from api import Api
from db import init_db
from paths import web_dir


DOCS_DIR = ROOT_DIR / "docs"
SCREENSHOT_DIR = DOCS_DIR / "screenshots"


SECTIONS = [
    {
        "judul": "1. Pendahuluan & Cara Menjalankan Aplikasi",
        "intro": (
            "Aplikasi Sistem Informasi Akuntansi (SIA) Azela Bakery & Pastry adalah aplikasi desktop "
            "untuk mencatat transaksi pembelian, penjualan, dan jurnal umum serta menyusun Neraca Saldo "
            "dan Laporan Laba Rugi secara otomatis."
        ),
        "steps": [
            "Pastikan file aplikasi (AzelaSIA.exe di Windows atau main.py saat mode Python) berada pada folder yang memiliki izin tulis.",
            "Saat pertama kali dijalankan, aplikasi otomatis membuat file database SQLite lokal bernama azela.db di folder yang sama.",
            "Database azela.db langsung berisi akun login bawaan, 43 Daftar Akun sesuai rancangan Excel kelompok, serta 15 transaksi contoh untuk keperluan presentasi.",
            "Untuk membuka isi database saat presentasi, buka file azela.db menggunakan aplikasi DB Browser for SQLite.",
        ],
        "shots": [],
    },
    {
        "judul": "2. Halaman Masuk Aplikasi (Login)",
        "intro": (
            "Halaman pertama yang muncul saat aplikasi dibuka adalah halaman Masuk Aplikasi. "
            "Halaman ini menampilkan logo Azela Bakery & Pastry (web/assets/logo.png) serta formulir autentikasi pengelola."
        ),
        "steps": [
            "Buka aplikasi sehingga tampil halaman Masuk Aplikasi.",
            "Masukkan Username bawaan: admin.",
            "Masukkan Password bawaan: admin123.",
            "Klik tombol 'Masuk ke Dashboard' atau tekan Enter pada keyboard.",
            "Jika username atau password salah, aplikasi akan menampilkan pesan peringatan berwarna merah dan mencegah akses ke Dashboard.",
        ],
        "shots": [
            ("01_login.png", "Gambar 2.1 Tampilan awal halaman Masuk Aplikasi."),
            ("02_login_error.png", "Gambar 2.2 Pesan validasi ketika username atau password tidak sesuai."),
        ],
    },
    {
        "judul": "3. Halaman Dashboard",
        "intro": (
            "Setelah berhasil masuk, pengguna diarahkan ke Dashboard utama AZELA BAKERY & PASTRY. "
            "Dashboard menyajikan ringkasan keuangan real-time dari database azela.db, akses cepat ke seluruh modul, "
            "lokasi file database, serta daftar transaksi terbaru."
        ),
        "steps": [
            "Periksa kartu utama gelap di kiri atas untuk melihat Laba / Rugi Berjalan serta status keseimbangan Neraca Saldo.",
            "Lihat kartu metrik di sebelah kanan untuk memantau Penjualan Bersih, Pembelian Bersih, Saldo Kas & Bank, dan status azela.db.",
            "Klik salah satu ubin pada bagian 'Akses Cepat Modul' atau gunakan menu navigasi di sidebar kiri untuk membuka modul tujuan.",
            "Pantau tabel 'Transaksi Terbaru' di bagian bawah untuk mengecek 8 transaksi terakhir yang tercatat di database.",
        ],
        "shots": [
            ("03_dashboard.png", "Gambar 3.1 Halaman Dashboard utama dengan ringkasan keuangan dan transaksi terbaru."),
        ],
    },
    {
        "judul": "4. Mengelola Daftar Akun",
        "intro": (
            "Menu Daftar Akun berisi kode akun (No. Akun), Nama Akun, Saldo Normal (Db/Kr), dan jumlah baris pemakaian di jurnal. "
            "Akun baru dengan awalan 4, 5, 6, 8, atau 9 otomatis masuk ke Neraca Saldo dan Laporan Laba Rugi."
        ),
        "steps": [
            "Klik menu 'Daftar Akun' di sidebar atau kartu akses cepat di Dashboard.",
            "Untuk menambah akun baru, isi No. Akun dengan format X-XXX (contoh: 6-210), isi Nama Akun (contoh: Beban Kemasan Khusus), pilih Saldo Normal (Db atau Kr), lalu klik 'Tambah Akun'.",
            "Akun baru langsung muncul di tabel Daftar Akun dan otomatis tersedia pada pilihan akun di Transaksi Lainnya, Neraca Saldo, serta Laba Rugi.",
            "Untuk mengubah nama atau saldo normal akun, klik tombol 'Ubah' pada baris akun yang diinginkan sehingga jendela pop-up terbuka, perbarui datanya, lalu klik 'Simpan Perubahan'.",
            "Untuk menghapus akun yang salah input, klik 'Hapus' lalu konfirmasi. Akun yang sudah dipakai pada transaksi jurnal tidak dapat dihapus agar integritas laporan terjaga.",
            "Klik 'Kembali ke Dashboard' di kanan atas kapan saja untuk pulang ke halaman utama.",
        ],
        "shots": [
            ("04_akun_daftar.png", "Gambar 4.1 Halaman Daftar Akun beserta formulir tambah akun baru."),
            ("05_akun_tambah_baru.png", "Gambar 4.2 Akun baru (6-210 Beban Kemasan Khusus) berhasil ditambahkan ke tabel."),
            ("06_akun_ubah_modal.png", "Gambar 4.3 Jendela modal Ubah Data Akun (dapat ditutup dengan tombol Batal atau Escape)."),
        ],
    },
    {
        "judul": "5. Mencatat Pembelian (Tunai & Kredit)",
        "intro": (
            "Modul Pembelian memiliki dua sub-tab di bagian atas halaman: 'Pembelian Tunai' dan 'Pembelian Kredit'. "
            "Nomor bukti disarankan otomatis (PBT-XXX untuk tunai, PBK-XXX untuk kredit) dan seluruh nominal ditampilkan dalam format Rupiah (Rp)."
        ),
        "steps": [
            "Buka menu 'Pembelian' dari sidebar atau Dashboard.",
            "Pilih sub-tab 'Pembelian Tunai' di bagian atas untuk pembelian yang dibayar langsung lewat Kas (1-110) atau Bank (1-120).",
            "Isi Tanggal, Keterangan, pilih Sumber Pembayaran (1-110 Kas atau 1-120 Bank), masukkan Nominal (Rp), lalu klik 'Simpan Transaksi'.",
            "Transaksi langsung muncul di tabel Pembelian Tunai beserta baris TOTAL di bagian bawah.",
            "Klik sub-tab 'Pembelian Kredit' di bagian atas untuk mencatat pembelian bahan baku secara utang (Debit 5-110 Pembelian, Kredit 2-110 Utang Usaha).",
            "Untuk menghapus transaksi yang salah, klik tombol 'Hapus' pada baris transaksi lalu konfirmasi.",
            "Klik 'Export ke Excel' di pojok kanan atas untuk mengunduh file .xlsx yang berisi sheet Pembelian Tunai dan Pembelian Kredit.",
        ],
        "shots": [
            ("07_pembelian_tunai.png", "Gambar 5.1 Sub-tab Pembelian Tunai dengan kolom 5-110 Pembelian, 1-110 Kas, dan 1-120 Bank."),
            ("08_pembelian_kredit.png", "Gambar 5.2 Sub-tab Pembelian Kredit dengan kolom 5-110 Pembelian dan 2-110 Utang Usaha."),
        ],
    },
    {
        "judul": "6. Mencatat Penjualan (Tunai & Kredit)",
        "intro": (
            "Modul Penjualan juga menempatkan sub-tab 'Penjualan Tunai' dan 'Penjualan Kredit' di bagian atas halaman, "
            "sesuai rancangan pada file Excel kelompok."
        ),
        "steps": [
            "Buka menu 'Penjualan' dari sidebar atau Dashboard.",
            "Pada sub-tab 'Penjualan Tunai', isi No. Bukti (otomatis PJT-XXX), Tanggal, Keterangan, pilih akun penerimaan (1-110 Kas atau 1-120 Bank), dan Nominal (Rp), lalu klik 'Simpan Transaksi'.",
            "Pada sub-tab 'Penjualan Kredit', transaksi otomatis mendebit 1-130 Piutang Usaha dan mengkredit 4-110 Penjualan.",
            "Periksa hasil transaksi yang langsung masuk ke tabel dan menjumlah pada baris TOTAL.",
            "Gunakan tombol 'Hapus' jika ada kesalahan input, atau 'Export ke Excel' untuk menyimpan laporan penjualan ke file .xlsx.",
        ],
        "shots": [
            ("09_penjualan_tunai.png", "Gambar 6.1 Sub-tab Penjualan Tunai dengan akun penerima Kas/Bank dan Kredit 4-110 Penjualan."),
            ("10_penjualan_kredit.png", "Gambar 6.2 Sub-tab Penjualan Kredit yang mencatat Debit 1-130 Piutang Usaha."),
        ],
    },
    {
        "judul": "7. Transaksi Lainnya (Jurnal Umum)",
        "intro": (
            "Menu Transaksi Lainnya digunakan untuk mencatat transaksi di luar pembelian dan penjualan rutin, "
            "seperti setoran modal, pembelian peralatan, pembayaran gaji, tagihan listrik, retur, atau pelunasan utang."
        ),
        "steps": [
            "Buka menu 'Transaksi Lainnya' di sidebar.",
            "Isi Tanggal, No. Bukti (otomatis JU-XXX), dan Keterangan transaksi.",
            "Pada setiap baris akun, pilih No. Akun dari dropdown. Kolom Nama Akun akan terisi otomatis.",
            "Masukkan nominal pada kolom Debit atau Kredit. Jika satu transaksi melibatkan lebih dari 2 akun, klik '+ Tambah Baris Akun'.",
            "Perhatikan indikator di bawah tabel baris: tombol 'Simpan Jurnal' hanya aktif apabila Total Debit sama dengan Total Kredit (status 'Seimbang').",
            "Klik 'Simpan Jurnal' untuk menyimpan ke database. Riwayat lengkap beserta baris TOTAL muncul di tabel bagian bawah.",
        ],
        "shots": [
            ("11_transaksi_lainnya.png", "Gambar 7.1 Formulir Transaksi Lainnya dengan pemilihan akun otomatis dan indikator keseimbangan."),
        ],
    },
    {
        "judul": "8. Memeriksa Neraca Saldo",
        "intro": (
            "Halaman Neraca Saldo menampilkan rekapitulasi saldo akhir Debit dan Kredit untuk seluruh akun yang terdaftar di Daftar Akun, "
            "dihitung otomatis dari semua modul transaksi."
        ),
        "steps": [
            "Buka menu 'Neraca Saldo' dari sidebar atau Dashboard.",
            "Periksa lencana status di kanan judul: pastikan tampil status 'Seimbang' (Total Debit sama dengan Total Kredit).",
            "Gunakan dropdown 'Periode' di kanan atas untuk menyaring saldo berdasarkan bulan tertentu (misalnya November 2026) atau 'Semua Periode'.",
            "Klik 'Export ke Excel' untuk mengunduh tabel Neraca Saldo berformat .xlsx.",
        ],
        "shots": [
            ("12_neraca_saldo.png", "Gambar 8.1 Laporan Neraca Saldo dengan status Seimbang dan filter periode."),
        ],
    },
    {
        "judul": "9. Membaca Laporan Laba Rugi",
        "intro": (
            "Laporan Laba Rugi mengelompokkan akun secara otomatis berdasarkan kode awalannya: "
            "Pendapatan Bersih (4-xxx), Pembelian Bersih (5-xxx), Beban Operasional (6-xxx), Pendapatan Tambahan (8-xxx), dan Beban Lain-lain (9-xxx)."
        ),
        "steps": [
            "Buka menu 'Laba Rugi' dari sidebar atau Dashboard.",
            "Tinjau subtotal tiap kelompok akun mulai dari Pendapatan Bersih hingga Beban Lain-lain.",
            "Akun baru yang ditambahkan pada Daftar Akun dengan kode awalan 4, 5, 6, 8, atau 9 otomatis masuk ke kelompok masing-masing.",
            "Lihat baris paling bawah 'LABA / RUGI BERSIH' dan lencana status di bagian atas untuk mengetahui apakah periode tersebut menghasilkan Laba Bersih atau Rugi Bersih.",
            "Gunakan filter Periode jika ingin melihat laporan bulan tertentu, lalu klik 'Export ke Excel' bila ingin mencetak atau melampirkan file Excel.",
        ],
        "shots": [
            ("13_laba_rugi.png", "Gambar 9.1 Laporan Laba Rugi lengkap dengan pengelompokan akun 4, 5, 6, 8, 9."),
        ],
    },
    {
        "judul": "10. Fitur Persiapan Presentasi (Reset Data Demo & Ganti Logo)",
        "intro": (
            "Untuk menjaga demo presentasi tetap rapi setelah uji coba input transaksi, tersedia tombol 'Reset Data Demo' di bagian bawah sidebar."
        ),
        "steps": [
            "Klik tombol 'Reset Data Demo' di sidebar kiri.",
            "Pada jendela konfirmasi yang muncul, klik 'Ya, Reset' untuk mengembalikan seluruh akun dan transaksi ke kondisi contoh awal.",
            "Untuk mengganti logo placeholder dengan logo resmi Azela, timpa file web/assets/logo.png sebelum melakukan build .exe, atau letakkan file logo.png di sebelah AzelaSIA.exe.",
            "Untuk membangun file .exe di komputer Windows, jalankan file build.bat atau gunakan workflow GitHub Actions pada .github/workflows/build-windows.yml.",
        ],
        "shots": [
            ("14_konfirmasi_reset.png", "Gambar 10.1 Dialog konfirmasi Reset Data Demo sebelum mengembalikan data awal."),
        ],
    },
]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def capture_screenshots() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        temp_db = Path(tmp) / "manual_demo.db"
        conn = init_db(temp_db)
        api = Api(conn)

        handler = partial(QuietHandler, directory=str(web_dir()))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                context = browser.new_context(
                    viewport={"width": 1280, "height": 820},
                    device_scale_factor=2,
                )
                page = context.new_page()

                def call_api(method_name: str, args: list):
                    fn = getattr(api, method_name)
                    return fn(*args)

                page.expose_function("__callPyApi", call_api)
                page.add_init_script(
                    """
                    const methodNames = [
                      "get_app_info", "login", "get_dashboard",
                      "list_akun", "create_akun", "update_akun", "delete_akun",
                      "next_no_bukti", "list_pembelian", "create_pembelian_tunai", "create_pembelian_kredit",
                      "list_penjualan", "create_penjualan_tunai", "create_penjualan_kredit",
                      "list_transaksi_lainnya", "create_transaksi_lainnya", "delete_jurnal",
                      "list_periode", "get_neraca_saldo", "get_laba_rugi",
                      "reset_demo_data", "export_excel"
                    ];
                    const proxyApi = {};
                    for (const name of methodNames) {
                      proxyApi[name] = (...args) => window.__callPyApi(name, args);
                    }
                    window.pywebview = { api: proxyApi };
                    """
                )

                page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
                page.wait_for_timeout(300)

                def clean_shot(filename: str, full_page: bool = False) -> None:
                    page.mouse.move(0, 0)
                    page.evaluate("document.getElementById('toast').classList.add('hidden')")
                    page.wait_for_timeout(200)
                    page.screenshot(path=str(SCREENSHOT_DIR / filename), full_page=full_page)

                # 01 Login awal
                clean_shot("01_login.png")

                # 02 Login error
                page.fill("#login-username", "admin")
                page.fill("#login-password", "salah123")
                page.click("#login-submit")
                page.wait_for_selector("#login-error:not(.hidden)")
                clean_shot("02_login_error.png")

                # 03 Login berhasil -> Dashboard
                page.fill("#login-username", "admin")
                page.fill("#login-password", "admin123")
                page.click("#login-submit")
                page.wait_for_selector("#app-shell:not(.hidden)")
                page.wait_for_selector(".hero-summary")
                clean_shot("03_dashboard.png", full_page=True)

                # 04 Daftar Akun
                page.click('[data-view="akun"]')
                page.wait_for_selector("#form-add-akun")
                clean_shot("04_akun_daftar.png")

                # 05 Tambah Akun Baru
                page.fill("#akun-no", "6-210")
                page.fill("#akun-nama", "Beban Kemasan Khusus")
                page.select_option("#akun-saldo", "Db")
                page.click('#form-add-akun button[type="submit"]')
                page.wait_for_selector('.btn-edit-akun[data-kode="6-210"]')
                page.mouse.move(0, 0)
                page.wait_for_timeout(200)
                page.screenshot(path=str(SCREENSHOT_DIR / "05_akun_tambah_baru.png"))

                # 06 Modal Ubah Akun
                page.click('.btn-edit-akun[data-kode="6-210"]')
                page.wait_for_selector("#edit-akun-modal:not(.hidden)")
                clean_shot("06_akun_ubah_modal.png")
                page.click("#edit-akun-cancel")
                page.wait_for_selector("#edit-akun-modal", state="hidden")

                # 07 Pembelian Tunai
                page.click('[data-view="pembelian"]')
                page.wait_for_selector("text=Debit: 5-110 Pembelian")
                page.wait_for_selector("text=Kredit: 1-110 Kas")
                clean_shot("07_pembelian_tunai.png")

                # 08 Pembelian Kredit
                page.click('.subtab-btn[data-tab="kredit"]')
                page.wait_for_selector("text=Kredit: 2-110 Utang Usaha")
                clean_shot("08_pembelian_kredit.png")

                # 09 Penjualan Tunai
                page.click('[data-view="penjualan"]')
                page.wait_for_selector("text=Debit: 1-110 Kas")
                page.wait_for_selector("text=Kredit: 4-110 Penjualan")
                clean_shot("09_penjualan_tunai.png")

                # 10 Penjualan Kredit
                page.click('.subtab-btn[data-tab="kredit"]')
                page.wait_for_selector("text=Debit: 1-130 Piutang Usaha")
                clean_shot("10_penjualan_kredit.png")

                # 11 Transaksi Lainnya (isi contoh baris agar terlihat cara pakainya)
                page.click('[data-view="transaksi_lainnya"]')
                page.wait_for_selector("#form-ju")
                page.wait_for_selector(".ju-akun-select")
                page.fill("#ju-ket", "Pembelian kemasan dus tambahan")
                selects = page.locator(".ju-akun-select")
                selects.nth(0).select_option("6-210")
                selects.nth(1).select_option("1-110")
                page.locator(".ju-debit").nth(0).fill("150000")
                page.locator(".ju-kredit").nth(1).fill("150000")
                page.wait_for_selector("#ju-balance-summary .status-ok")
                clean_shot("11_transaksi_lainnya.png", full_page=True)

                # 12 Neraca Saldo
                page.click('[data-view="neraca_saldo"]')
                page.wait_for_selector("#ns-periode")
                page.wait_for_selector("text=Seimbang")
                clean_shot("12_neraca_saldo.png", full_page=True)

                # 13 Laba Rugi
                page.click('[data-view="laba_rugi"]')
                page.wait_for_selector("#lr-periode")
                page.wait_for_selector("text=LABA / RUGI BERSIH")
                clean_shot("13_laba_rugi.png", full_page=True)

                # 14 Dialog Konfirmasi Reset Data Demo
                page.click("#btn-reset-demo")
                page.wait_for_selector("#confirm-modal:not(.hidden)")
                clean_shot("14_konfirmasi_reset.png")
                page.click("#confirm-cancel")

                browser.close()
        finally:
            server.shutdown()
            conn.close()


def build_docx(output_path: Path) -> None:
    doc = Document()

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x2A, 0x1C, 0x13)

    # Halaman Sampul
    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_title.paragraph_format.space_before = Pt(72)
    run_t = cover_title.add_run("BUKU PANDUAN PENGGUNAAN APLIKASI\n")
    run_t.bold = True
    run_t.font.size = Pt(22)
    run_t.font.color.rgb = RGBColor(0x38, 0x24, 0x18)

    run_sub = cover_title.add_run("SISTEM INFORMASI AKUNTANSI\nAZELA BAKERY & PASTRY")
    run_sub.bold = True
    run_sub.font.size = Pt(18)
    run_sub.font.color.rgb = RGBColor(0xB4, 0x4A, 0x14)

    logo_p = doc.add_paragraph()
    logo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    logo_p.paragraph_format.space_before = Pt(24)
    logo_p.paragraph_format.space_after = Pt(24)
    logo_file = web_dir() / "assets" / "logo.png"
    if logo_file.exists():
        logo_p.add_run().add_picture(str(logo_file), width=Inches(1.6))

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_r = meta_p.add_run(
        "Disusun berdasarkan rancangan PROJEK SIA KELOMPOK 2\n"
        "Aplikasi Desktop Python (pywebview) + HTML/CSS/JS + Database SQLite Lokal\n\n"
        "Akun Login Bawaan: admin / admin123\n"
        "File Database Otomatis: azela.db"
    )
    meta_r.font.size = Pt(11)
    meta_r.font.color.rgb = RGBColor(0x5E, 0x46, 0x38)

    doc.add_page_break()

    # Isi tiap bab
    for sec in SECTIONS:
        h = doc.add_heading(sec["judul"], level=1)
        for r in h.runs:
            r.font.color.rgb = RGBColor(0x38, 0x24, 0x18)

        intro_p = doc.add_paragraph(sec["intro"])
        intro_p.paragraph_format.space_after = Pt(6)

        step_label = doc.add_paragraph()
        sl_run = step_label.add_run("Langkah-langkah:")
        sl_run.bold = True
        sl_run.font.color.rgb = RGBColor(0xB4, 0x4A, 0x14)

        for idx, step_text in enumerate(sec["steps"], start=1):
            sp = doc.add_paragraph(style="List Number")
            sp.add_run(step_text)

        for filename, caption in sec["shots"]:
            img_path = SCREENSHOT_DIR / filename
            if not img_path.exists():
                continue
            pic_p = doc.add_paragraph()
            pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pic_p.paragraph_format.space_before = Pt(8)
            pic_p.add_run().add_picture(str(img_path), width=Inches(6.1))

            cap_p = doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap_p.paragraph_format.space_after = Pt(12)
            cr = cap_p.add_run(caption)
            cr.italic = True
            cr.font.size = Pt(9.5)
            cr.font.color.rgb = RGBColor(0x5E, 0x46, 0x38)

    doc.save(str(output_path))


def _img_data_uri(path: Path) -> str:
    raw = path.read_bytes()
    return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"


def build_pdf(output_path: Path) -> None:
    logo_uri = _img_data_uri(web_dir() / "assets" / "logo.png")
    sections_html = []
    for sec in SECTIONS:
        steps_li = "".join(f"<li>{s}</li>" for s in sec["steps"])
        shots_html = "".join(
            f"""
            <figure class="shot">
              <img src="{_img_data_uri(SCREENSHOT_DIR / fname)}" alt="{cap}">
              <figcaption>{cap}</figcaption>
            </figure>
            """
            for fname, cap in sec["shots"]
            if (SCREENSHOT_DIR / fname).exists()
        )
        sections_html.append(
            f"""
            <section class="chapter">
              <h2>{sec['judul']}</h2>
              <p class="intro">{sec['intro']}</p>
              <h3>Langkah-langkah:</h3>
              <ol>{steps_li}</ol>
              {shots_html}
            </section>
            """
        )

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
  }}
  body {{
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    color: #2A1C13;
    font-size: 10.5pt;
    line-height: 1.55;
    margin: 0;
  }}
  .cover {{
    page-break-after: always;
    min-height: 245mm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: #FAF6F0;
    border: 2px solid #382418;
    border-radius: 12px;
    padding: 32px;
    box-sizing: border-box;
  }}
  .cover img {{
    width: 120px;
    height: 120px;
    margin: 24px 0;
    border-radius: 10px;
    border: 1px solid #DFD2C3;
  }}
  .cover h1 {{
    font-family: Georgia, serif;
    font-size: 24pt;
    color: #382418;
    margin: 0 0 8px 0;
  }}
  .cover .sub {{
    font-family: Georgia, serif;
    font-size: 16pt;
    font-weight: 700;
    color: #B44A14;
    margin: 0 0 18px 0;
  }}
  .cover .meta {{
    font-size: 10.5pt;
    color: #5E4638;
    border-top: 1px solid #DFD2C3;
    padding-top: 16px;
    margin-top: 16px;
  }}
  .chapter {{
    margin-bottom: 24px;
  }}
  h2 {{
    font-family: Georgia, serif;
    font-size: 14.5pt;
    color: #382418;
    border-bottom: 2px solid #B44A14;
    padding-bottom: 4px;
    margin: 18px 0 8px 0;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 10.5pt;
    color: #B44A14;
    margin: 10px 0 6px 0;
    page-break-after: avoid;
  }}
  p.intro {{
    margin: 0 0 8px 0;
  }}
  ol {{
    margin: 0 0 12px 0;
    padding-left: 20px;
  }}
  li {{
    margin-bottom: 4px;
  }}
  figure.shot {{
    margin: 12px 0 16px 0;
    text-align: center;
    page-break-inside: avoid;
  }}
  figure.shot img {{
    width: 100%;
    max-width: 170mm;
    border: 1px solid #C9B8A8;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(42, 28, 19, 0.08);
  }}
  figcaption {{
    margin-top: 6px;
    font-size: 9pt;
    font-style: italic;
    color: #5E4638;
  }}
</style>
</head>
<body>
  <div class="cover">
    <h1>BUKU PANDUAN PENGGUNAAN APLIKASI</h1>
    <div class="sub">SISTEM INFORMASI AKUNTANSI<br>AZELA BAKERY &amp; PASTRY</div>
    <img src="{logo_uri}" alt="Logo Azela">
    <div class="meta">
      Disusun berdasarkan rancangan <strong>PROJEK SIA KELOMPOK 2</strong><br>
      Aplikasi Desktop Python (pywebview) + HTML/CSS/JS + Database SQLite Lokal<br><br>
      Akun Login Bawaan: <strong>admin</strong> / <strong>admin123</strong><br>
      File Database Otomatis: <strong>azela.db</strong>
    </div>
  </div>
  {''.join(sections_html)}
</body>
</html>
"""
    html_file = DOCS_DIR / "_manual_render.html"
    html_file.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_file.as_uri(), wait_until="load")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=(
                '<div style="font-size:8px;color:#5E4638;width:100%;text-align:center;'
                'font-family:sans-serif;">Buku Panduan SIA Azela Bakery &amp; Pastry - Halaman '
                '<span class="pageNumber"></span> dari <span class="totalPages"></span></div>'
            ),
        )
        browser.close()
    html_file.unlink(missing_ok=True)


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    capture_screenshots()
    docx_path = DOCS_DIR / "Buku_Panduan_Azela_SIA.docx"
    pdf_path = DOCS_DIR / "Buku_Panduan_Azela_SIA.pdf"
    build_docx(docx_path)
    build_pdf(pdf_path)
    print("Generated:", docx_path)
    print("Generated:", pdf_path)


if __name__ == "__main__":
    main()
