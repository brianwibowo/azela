/* Utilitas pemformatan nominal Rupiah, tanggal, dan keamanan HTML */

window.AzelaFormat = {
  rupiah(amount) {
    const num = Number(amount || 0);
    const abs = Math.abs(Math.round(num));
    const formatted = abs.toLocaleString("id-ID");
    if (num < 0) {
      return `(Rp ${formatted})`;
    }
    return `Rp ${formatted}`;
  },

  rupiahOrDash(amount) {
    const num = Number(amount || 0);
    if (num === 0) return "-";
    return this.rupiah(num);
  },

  todayISO() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  },

  tanggal(iso) {
    if (!iso) return "-";
    const parts = String(iso).split("-");
    if (parts.length !== 3) return iso;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  },

  periodeLabel(ym) {
    if (!ym || ym === "ALL") return "Semua Periode";
    const [y, m] = ym.split("-");
    const bulan = [
      "Januari", "Februari", "Maret", "April", "Mei", "Juni",
      "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ];
    const idx = Number(m) - 1;
    if (idx >= 0 && idx < 12) {
      return `${bulan[idx]} ${y}`;
    }
    return ym;
  },

  jenisLabel(jenis) {
    const map = {
      PEMBELIAN_TUNAI: "Pembelian Tunai",
      PEMBELIAN_KREDIT: "Pembelian Kredit",
      PENJUALAN_TUNAI: "Penjualan Tunai",
      PENJUALAN_KREDIT: "Penjualan Kredit",
      UMUM: "Transaksi Lainnya",
    };
    return map[jenis] || jenis;
  },

  esc(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },
};

