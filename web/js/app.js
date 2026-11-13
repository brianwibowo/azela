/* Logika UI SPA Azela Bakery & Pastry */

(function () {
  const F = window.AzelaFormat;
  const Api = window.AzelaApi;

  const state = {
    user: null,
    view: "dashboard",
    pembelianTab: "tunai",
    penjualanTab: "tunai",
    periodeNeraca: "ALL",
    periodeLabaRugi: "ALL",
    dbPath: "",
    akunList: [],
    journalLines: [],
  };

  const VIEW_META = {
    dashboard: {
      title: "AZELA BAKERY & PASTRY",
      caption: "Ringkasan kondisi keuangan dan navigasi modul pembukuan",
    },
    akun: {
      title: "Daftar Akun",
      caption: "Kelola nomor akun, nama akun, dan saldo normal. Akun 4, 5, 6, 8, 9 otomatis masuk ke Laba Rugi.",
    },
    pembelian: {
      title: "Jurnal Pembelian",
      caption: "Pencatatan Pembelian Tunai dan Pembelian Kredit",
    },
    penjualan: {
      title: "Jurnal Penjualan",
      caption: "Pencatatan Penjualan Tunai dan Penjualan Kredit",
    },
    transaksi_lainnya: {
      title: "Transaksi Lainnya (Jurnal Umum)",
      caption: "Catat transaksi selain pembelian/penjualan dengan validasi Debit = Kredit",
    },
    neraca_saldo: {
      title: "Neraca Saldo",
      caption: "Rekap saldo akhir seluruh akun terdaftar dari seluruh transaksi",
    },
    laba_rugi: {
      title: "Laporan Laba Rugi",
      caption: "Perhitungan Pendapatan Bersih, Pembelian Bersih, Beban, dan Laba/Rugi Bersih",
    },
  };

  const el = {
    loginScreen: document.getElementById("login-screen"),
    loginForm: document.getElementById("login-form"),
    loginUsername: document.getElementById("login-username"),
    loginPassword: document.getElementById("login-password"),
    loginError: document.getElementById("login-error"),
    loginLogo: document.getElementById("login-logo"),
    appShell: document.getElementById("app-shell"),
    sidebar: document.getElementById("sidebar"),
    sidebarLogo: document.getElementById("sidebar-logo"),
    activeUserName: document.getElementById("active-user-name"),
    pageTitle: document.getElementById("page-title"),
    pageCaption: document.getElementById("page-caption"),
    topbarActions: document.getElementById("topbar-actions"),
    viewRoot: document.getElementById("view-root"),
    btnMobileMenu: document.getElementById("btn-mobile-menu"),
    btnResetDemo: document.getElementById("btn-reset-demo"),
    btnLogout: document.getElementById("btn-logout"),
    confirmModal: document.getElementById("confirm-modal"),
    confirmTitle: document.getElementById("confirm-title"),
    confirmMessage: document.getElementById("confirm-message"),
    confirmCancel: document.getElementById("confirm-cancel"),
    confirmOk: document.getElementById("confirm-ok"),
    editAkunModal: document.getElementById("edit-akun-modal"),
    editAkunForm: document.getElementById("edit-akun-form"),
    editNoAkun: document.getElementById("edit-no-akun"),
    editNamaAkun: document.getElementById("edit-nama-akun"),
    editSaldoNormal: document.getElementById("edit-saldo-normal"),
    editAkunCancel: document.getElementById("edit-akun-cancel"),
    toast: document.getElementById("toast"),
  };

  let toastTimer = null;
  function showToast(message, isError = false) {
    el.toast.textContent = message;
    el.toast.classList.toggle("toast-error", isError);
    el.toast.classList.remove("hidden");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      el.toast.classList.add("hidden");
    }, 4000);
  }

  let confirmResolve = null;
  function askConfirm(title, message, okLabel = "Ya, Hapus") {
    el.confirmTitle.textContent = title;
    el.confirmMessage.textContent = message;
    el.confirmOk.textContent = okLabel;
    el.confirmModal.classList.remove("hidden");
    el.confirmCancel.focus();
    return new Promise((resolve) => {
      confirmResolve = resolve;
    });
  }

  function closeConfirm(result) {
    el.confirmModal.classList.add("hidden");
    if (confirmResolve) {
      const fn = confirmResolve;
      confirmResolve = null;
      fn(result);
    }
  }

  el.confirmCancel.addEventListener("click", () => closeConfirm(false));
  el.confirmOk.addEventListener("click", () => closeConfirm(true));

  function closeEditAkunModal() {
    el.editAkunModal.classList.add("hidden");
  }

  el.editAkunCancel.addEventListener("click", closeEditAkunModal);

  document.addEventListener("keydown", (evt) => {
    if (evt.key === "Escape") {
      if (!el.confirmModal.classList.contains("hidden")) {
        closeConfirm(false);
      } else if (!el.editAkunModal.classList.contains("hidden")) {
        closeEditAkunModal();
      } else if (el.sidebar.classList.contains("open")) {
        el.sidebar.classList.remove("open");
      }
    }
  });

  function setLoading(label = "Memuat data pembukuan...") {
    el.viewRoot.innerHTML = `
      <div class="state-box">
        <strong>${F.esc(label)}</strong>
        <p>Sedang membaca data dari database SQLite lokal.</p>
      </div>
    `;
  }

  function setViewError(message, retryFn) {
    el.viewRoot.innerHTML = `
      <div class="state-box">
        <strong>Gagal memuat halaman</strong>
        <p>${F.esc(message)}</p>
        <button id="btn-retry-view" type="button" class="btn btn-primary">Coba Lagi</button>
      </div>
    `;
    document.getElementById("btn-retry-view").addEventListener("click", retryFn);
  }

  function updateNavActive() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === state.view);
    });
  }

  function renderTopbar(exportModul = null, periode = "ALL") {
    const meta = VIEW_META[state.view];
    el.pageTitle.textContent = meta.title;
    el.pageCaption.textContent = meta.caption;
    el.topbarActions.innerHTML = "";

    if (exportModul) {
      const expBtn = document.createElement("button");
      expBtn.type = "button";
      expBtn.className = "btn btn-secondary";
      expBtn.textContent = "Export ke Excel";
      expBtn.addEventListener("click", async () => {
        expBtn.disabled = true;
        try {
          const res = await Api.call("export_excel", exportModul, periode);
          if (res.ok) {
            showToast(`Berhasil disimpan ke ${res.path}`);
          } else if (!res.cancelled) {
            showToast(res.error || "Gagal mengekspor Excel.", true);
          }
        } catch (err) {
          showToast(err.message, true);
        } finally {
          expBtn.disabled = false;
        }
      });
      el.topbarActions.appendChild(expBtn);
    }

    if (state.view !== "dashboard") {
      const backBtn = document.createElement("button");
      backBtn.type = "button";
      backBtn.className = "btn btn-secondary";
      backBtn.textContent = "Kembali ke Dashboard";
      backBtn.addEventListener("click", () => navigate("dashboard"));
      el.topbarActions.appendChild(backBtn);
    }
  }

  async function navigate(view) {
    state.view = view;
    el.sidebar.classList.remove("open");
    updateNavActive();
    if (view === "dashboard") return renderDashboard();
    if (view === "akun") return renderAkun();
    if (view === "pembelian") return renderPembelian();
    if (view === "penjualan") return renderPenjualan();
    if (view === "transaksi_lainnya") return renderTransaksiLainnya();
    if (view === "neraca_saldo") return renderNeracaSaldo();
    if (view === "laba_rugi") return renderLabaRugi();
  }

  // ---------- 1. DASHBOARD ----------

  async function renderDashboard() {
    renderTopbar(null);
    setLoading("Memuat ringkasan Dashboard...");
    try {
      const res = await Api.call("get_dashboard");
      const d = res.data;

      const recentRows = d.recent.length
        ? d.recent
            .map(
              (r) => `
              <tr>
                <td><strong>${F.esc(r.no_bukti)}</strong></td>
                <td>${F.tanggal(r.tanggal)}</td>
                <td>${F.esc(F.jenisLabel(r.jenis))}</td>
                <td>${F.esc(r.keterangan)}</td>
                <td class="text-right tabular">${F.rupiah(r.nominal)}</td>
              </tr>`
            )
            .join("")
        : `<tr><td colspan="5" class="text-center">Belum ada transaksi tercatat.</td></tr>`;

      el.viewRoot.innerHTML = `
        <section class="hero-summary">
          <div class="focal-card">
            <div>
              <div class="focal-label">Laba / Rugi Berjalan</div>
              <div class="focal-value tabular">${F.rupiah(d.laba_rugi)}</div>
              <div>Status Neraca Saldo: <strong>${d.seimbang ? "Seimbang" : "Tidak Seimbang"}</strong></div>
            </div>
            <div class="focal-meta">
              <div><span>Total Transaksi</span><strong>${d.total_transaksi} jurnal</strong></div>
              <div><span>Akun Terdaftar</span><strong>${d.total_akun} akun</strong></div>
              <div><span>Piutang Usaha</span><strong class="tabular">${F.rupiah(d.piutang_usaha)}</strong></div>
              <div><span>Utang Usaha</span><strong class="tabular">${F.rupiah(d.utang_usaha)}</strong></div>
            </div>
          </div>

          <div class="metric-stack">
            <div class="metric-box">
              <span>Penjualan Bersih</span>
              <strong class="tabular">${F.rupiah(d.penjualan_bersih)}</strong>
            </div>
            <div class="metric-box">
              <span>Pembelian Bersih</span>
              <strong class="tabular">${F.rupiah(d.pembelian_bersih)}</strong>
            </div>
            <div class="metric-box">
              <span>Saldo Kas &amp; Bank</span>
              <strong class="tabular">${F.rupiah(d.kas_bank)}</strong>
            </div>
            <div class="metric-box">
              <span>File Database Lokal</span>
              <strong style="font-size: 13px;">azela.db Aktif</strong>
            </div>
          </div>
        </section>

        <section class="quick-nav-grid" aria-label="Akses Cepat Modul">
          <button type="button" class="quick-tile" data-jump="pembelian">
            <strong>Pembelian (Tunai / Kredit)</strong>
            <span>Catat pembelian bahan baku dan perlengkapan bakery</span>
          </button>
          <button type="button" class="quick-tile" data-jump="penjualan">
            <strong>Penjualan (Tunai / Kredit)</strong>
            <span>Catat penjualan kasir, transfer bank, dan piutang</span>
          </button>
          <button type="button" class="quick-tile" data-jump="transaksi_lainnya">
            <strong>Transaksi Lainnya</strong>
            <span>Jurnal umum biaya gaji, listrik, atau pelunasan utang</span>
          </button>
          <button type="button" class="quick-tile" data-jump="akun">
            <strong>Daftar Akun</strong>
            <span>Tambah, ubah, atau hapus akun akuntansi</span>
          </button>
          <button type="button" class="quick-tile" data-jump="neraca_saldo">
            <strong>Neraca Saldo</strong>
            <span>Cek keseimbangan Debit dan Kredit seluruh akun</span>
          </button>
          <button type="button" class="quick-tile" data-jump="laba_rugi">
            <strong>Laporan Laba Rugi</strong>
            <span>Lihat rincian pendapatan, pembelian, beban, dan laba bersih</span>
          </button>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Transaksi Terbaru</h2>
            <span class="db-path-note">DB: ${F.esc(state.dbPath)}</span>
          </div>
          <div class="table-scroll">
            <table class="ledger">
              <thead>
                <tr>
                  <th>No. Bukti</th>
                  <th>Tanggal</th>
                  <th>Modul</th>
                  <th>Keterangan</th>
                  <th class="text-right">Nominal</th>
                </tr>
              </thead>
              <tbody>${recentRows}</tbody>
            </table>
          </div>
        </section>
      `;

      el.viewRoot.querySelectorAll("[data-jump]").forEach((btn) => {
        btn.addEventListener("click", () => navigate(btn.dataset.jump));
      });
    } catch (err) {
      setViewError(err.message, renderDashboard);
    }
  }

  // ---------- 2. DAFTAR AKUN ----------

  async function renderAkun() {
    renderTopbar(null);
    setLoading("Memuat daftar akun...");
    try {
      const res = await Api.call("list_akun");
      state.akunList = res.items;

      const rowsHtml = state.akunList.length
        ? state.akunList
            .map(
              (a) => `
              <tr>
                <td><strong>${F.esc(a.no_akun)}</strong></td>
                <td>${F.esc(a.nama)}</td>
                <td>${F.esc(a.saldo_normal)}</td>
                <td class="tabular">${a.jumlah_transaksi} baris</td>
                <td class="text-right" style="white-space: nowrap;">
                  <button type="button" class="btn btn-secondary btn-sm btn-edit-akun" data-kode="${F.esc(a.no_akun)}">Ubah</button>
                  <button type="button" class="btn btn-danger-ghost btn-del-akun" data-kode="${F.esc(a.no_akun)}">Hapus</button>
                </td>
              </tr>`
            )
            .join("")
        : `<tr><td colspan="5" class="text-center">Belum ada akun terdaftar. Gunakan formulir di atas untuk menambah akun pertama.</td></tr>`;

      el.viewRoot.innerHTML = `
        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Tambah Akun Baru</h2>
          </div>
          <form id="form-add-akun" class="form-grid">
            <div class="field-group">
              <label for="akun-no">No. Akun (Format X-XXX)</label>
              <input id="akun-no" class="input" type="text" placeholder="Contoh: 6-210" required>
            </div>
            <div class="field-group">
              <label for="akun-nama">Nama Akun</label>
              <input id="akun-nama" class="input" type="text" placeholder="Contoh: Beban Kemasan" required>
            </div>
            <div class="field-group">
              <label for="akun-saldo">Saldo Normal</label>
              <select id="akun-saldo" class="select">
                <option value="Db">Db (Debit)</option>
                <option value="Kr">Kr (Kredit)</option>
              </select>
            </div>
            <div>
              <button type="submit" class="btn btn-primary">Tambah Akun</button>
            </div>
          </form>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Daftar Akun (${state.akunList.length} akun)</h2>
          </div>
          <div class="table-scroll">
            <table class="ledger">
              <thead>
                <tr>
                  <th>No. Akun</th>
                  <th>Nama Akun</th>
                  <th>Saldo Normal</th>
                  <th>Dipakai di Jurnal</th>
                  <th class="text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          </div>
        </section>
      `;

      document.getElementById("form-add-akun").addEventListener("submit", async (evt) => {
        evt.preventDefault();
        const noAkun = document.getElementById("akun-no").value;
        const nama = document.getElementById("akun-nama").value;
        const saldo = document.getElementById("akun-saldo").value;
        const out = await Api.call("create_akun", noAkun, nama, saldo);
        if (!out.ok) {
          showToast(out.error, true);
          return;
        }
        showToast(`Akun ${noAkun.trim()} berhasil ditambahkan.`);
        renderAkun();
      });

      el.viewRoot.querySelectorAll(".btn-edit-akun").forEach((btn) => {
        btn.addEventListener("click", () => {
          const item = state.akunList.find((x) => x.no_akun === btn.dataset.kode);
          if (!item) return;
          el.editNoAkun.value = item.no_akun;
          el.editNamaAkun.value = item.nama;
          el.editSaldoNormal.value = item.saldo_normal;
          el.editAkunModal.classList.remove("hidden");
          el.editNamaAkun.focus();
        });
      });

      el.viewRoot.querySelectorAll(".btn-del-akun").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const kode = btn.dataset.kode;
          const ok = await askConfirm("Hapus Akun", `Hapus akun ${kode} dari daftar akun?`);
          if (!ok) return;
          const out = await Api.call("delete_akun", kode);
          if (!out.ok) {
            showToast(out.error, true);
            return;
          }
          showToast(`Akun ${kode} dihapus.`);
          renderAkun();
        });
      });
    } catch (err) {
      setViewError(err.message, renderAkun);
    }
  }

  el.editAkunForm.addEventListener("submit", async (evt) => {
    evt.preventDefault();
    const out = await Api.call(
      "update_akun",
      el.editNoAkun.value,
      el.editNamaAkun.value,
      el.editSaldoNormal.value
    );
    if (!out.ok) {
      showToast(out.error, true);
      return;
    }
    closeEditAkunModal();
    showToast(`Akun ${el.editNoAkun.value} diperbarui.`);
    if (state.view === "akun") renderAkun();
  });

  // ---------- 3. PEMBELIAN (Sub-tab Tunai | Kredit di atas) ----------

  async function renderPembelian() {
    renderTopbar("pembelian");
    setLoading("Memuat data pembelian...");
    try {
      const jenis = state.pembelianTab === "tunai" ? "PEMBELIAN_TUNAI" : "PEMBELIAN_KREDIT";
      const [data, nextRes] = await Promise.all([
        Api.call("list_pembelian"),
        Api.call("next_no_bukti", jenis),
      ]);

      const isTunai = state.pembelianTab === "tunai";
      const current = isTunai ? data.tunai : data.kredit;
      const items = current.items;
      const totals = current.totals;

      const tableHead = isTunai
        ? `<tr>
             <th>No. Bukti</th>
             <th>Tanggal</th>
             <th>Keterangan</th>
             <th class="text-right">Debit: 5-110 Pembelian</th>
             <th class="text-right">Kredit: 1-110 Kas</th>
             <th class="text-right">Kredit: 1-120 Bank</th>
             <th class="text-right">Aksi</th>
           </tr>`
        : `<tr>
             <th>No. Bukti</th>
             <th>Tanggal</th>
             <th>Keterangan</th>
             <th class="text-right">Debit: 5-110 Pembelian</th>
             <th class="text-right">Kredit: 2-110 Utang Usaha</th>
             <th class="text-right">Aksi</th>
           </tr>`;

      const rowsHtml = items.length
        ? items
            .map((it) =>
              isTunai
                ? `<tr>
                     <td><strong>${F.esc(it.no_bukti)}</strong></td>
                     <td>${F.tanggal(it.tanggal)}</td>
                     <td>${F.esc(it.keterangan)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_5110)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_1110)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_1120)}</td>
                     <td class="text-right"><button type="button" class="btn btn-danger-ghost btn-del-jurnal" data-id="${it.id}" data-bukti="${F.esc(it.no_bukti)}">Hapus</button></td>
                   </tr>`
                : `<tr>
                     <td><strong>${F.esc(it.no_bukti)}</strong></td>
                     <td>${F.tanggal(it.tanggal)}</td>
                     <td>${F.esc(it.keterangan)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_5110)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_2110)}</td>
                     <td class="text-right"><button type="button" class="btn btn-danger-ghost btn-del-jurnal" data-id="${it.id}" data-bukti="${F.esc(it.no_bukti)}">Hapus</button></td>
                   </tr>`
            )
            .join("")
        : `<tr><td colspan="${isTunai ? 7 : 6}" class="text-center">Belum ada transaksi pembelian ${isTunai ? "tunai" : "kredit"}. Tambahkan melalui formulir di atas.</td></tr>`;

      const footHtml = isTunai
        ? `<tr>
             <td colspan="3">TOTAL</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_5110)}</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_1110)}</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_1120)}</td>
             <td></td>
           </tr>`
        : `<tr>
             <td colspan="3">TOTAL</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_5110)}</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_2110)}</td>
             <td></td>
           </tr>`;

      el.viewRoot.innerHTML = `
        <div class="subtab-bar" role="tablist" aria-label="Jenis Pembelian">
          <button type="button" role="tab" aria-selected="${isTunai}" class="subtab-btn ${isTunai ? "active" : ""}" data-tab="tunai">Pembelian Tunai</button>
          <button type="button" role="tab" aria-selected="${!isTunai}" class="subtab-btn ${!isTunai ? "active" : ""}" data-tab="kredit">Pembelian Kredit</button>
        </div>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Input ${isTunai ? "Pembelian Tunai" : "Pembelian Kredit"}</h2>
          </div>
          <form id="form-pembelian" class="form-grid">
            <div class="field-group">
              <label for="pb-bukti">No. Bukti</label>
              <input id="pb-bukti" class="input" type="text" value="${F.esc(nextRes.no_bukti)}" required>
            </div>
            <div class="field-group">
              <label for="pb-tanggal">Tanggal</label>
              <input id="pb-tanggal" class="input" type="date" value="${F.todayISO()}" required>
            </div>
            <div class="field-group" style="grid-column: span 2;">
              <label for="pb-ket">Keterangan</label>
              <input id="pb-ket" class="input" type="text" placeholder="Contoh: Pembelian tepung dan mentega" required>
            </div>
            ${
              isTunai
                ? `<div class="field-group">
                     <label for="pb-akun">Sumber Pembayaran</label>
                     <select id="pb-akun" class="select">
                       <option value="1-110">1-110 Kas</option>
                       <option value="1-120">1-120 Bank</option>
                     </select>
                   </div>`
                : ""
            }
            <div class="field-group">
              <label for="pb-nominal">Nominal (Rp)</label>
              <input id="pb-nominal" class="input tabular" type="number" min="1" step="1" placeholder="500000" required>
            </div>
            <div>
              <button type="submit" class="btn btn-primary">Simpan Transaksi</button>
            </div>
          </form>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Tabel ${isTunai ? "Pembelian Tunai" : "Pembelian Kredit"} (${items.length} transaksi)</h2>
          </div>
          <div class="table-scroll">
            <table class="ledger">
              <thead>${tableHead}</thead>
              <tbody>${rowsHtml}</tbody>
              <tfoot>${footHtml}</tfoot>
            </table>
          </div>
        </section>
      `;

      el.viewRoot.querySelectorAll(".subtab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.pembelianTab = btn.dataset.tab;
          renderPembelian();
        });
      });

      document.getElementById("form-pembelian").addEventListener("submit", async (evt) => {
        evt.preventDefault();
        const bukti = document.getElementById("pb-bukti").value;
        const tanggal = document.getElementById("pb-tanggal").value;
        const ket = document.getElementById("pb-ket").value;
        const nominal = Number(document.getElementById("pb-nominal").value);

        const out = isTunai
          ? await Api.call("create_pembelian_tunai", bukti, tanggal, ket, document.getElementById("pb-akun").value, nominal)
          : await Api.call("create_pembelian_kredit", bukti, tanggal, ket, nominal);

        if (!out.ok) {
          showToast(out.error, true);
          return;
        }
        showToast(`Transaksi ${bukti.trim()} disimpan.`);
        renderPembelian();
      });

      bindDeleteJurnal(renderPembelian);
    } catch (err) {
      setViewError(err.message, renderPembelian);
    }
  }

  // ---------- 4. PENJUALAN (Sub-tab Tunai | Kredit di atas) ----------

  async function renderPenjualan() {
    renderTopbar("penjualan");
    setLoading("Memuat data penjualan...");
    try {
      const jenis = state.penjualanTab === "tunai" ? "PENJUALAN_TUNAI" : "PENJUALAN_KREDIT";
      const [data, nextRes] = await Promise.all([
        Api.call("list_penjualan"),
        Api.call("next_no_bukti", jenis),
      ]);

      const isTunai = state.penjualanTab === "tunai";
      const current = isTunai ? data.tunai : data.kredit;
      const items = current.items;
      const totals = current.totals;

      const tableHead = isTunai
        ? `<tr>
             <th>No. Bukti</th>
             <th>Tanggal</th>
             <th>Keterangan</th>
             <th class="text-right">Debit: 1-110 Kas</th>
             <th class="text-right">Debit: 1-120 Bank</th>
             <th class="text-right">Kredit: 4-110 Penjualan</th>
             <th class="text-right">Aksi</th>
           </tr>`
        : `<tr>
             <th>No. Bukti</th>
             <th>Tanggal</th>
             <th>Keterangan</th>
             <th class="text-right">Debit: 1-130 Piutang Usaha</th>
             <th class="text-right">Kredit: 4-110 Penjualan</th>
             <th class="text-right">Aksi</th>
           </tr>`;

      const rowsHtml = items.length
        ? items
            .map((it) =>
              isTunai
                ? `<tr>
                     <td><strong>${F.esc(it.no_bukti)}</strong></td>
                     <td>${F.tanggal(it.tanggal)}</td>
                     <td>${F.esc(it.keterangan)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_1110)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_1120)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_4110)}</td>
                     <td class="text-right"><button type="button" class="btn btn-danger-ghost btn-del-jurnal" data-id="${it.id}" data-bukti="${F.esc(it.no_bukti)}">Hapus</button></td>
                   </tr>`
                : `<tr>
                     <td><strong>${F.esc(it.no_bukti)}</strong></td>
                     <td>${F.tanggal(it.tanggal)}</td>
                     <td>${F.esc(it.keterangan)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_1130)}</td>
                     <td class="text-right tabular">${F.rupiahOrDash(it.akun_4110)}</td>
                     <td class="text-right"><button type="button" class="btn btn-danger-ghost btn-del-jurnal" data-id="${it.id}" data-bukti="${F.esc(it.no_bukti)}">Hapus</button></td>
                   </tr>`
            )
            .join("")
        : `<tr><td colspan="${isTunai ? 7 : 6}" class="text-center">Belum ada transaksi penjualan ${isTunai ? "tunai" : "kredit"}. Tambahkan melalui formulir di atas.</td></tr>`;

      const footHtml = isTunai
        ? `<tr>
             <td colspan="3">TOTAL</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_1110)}</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_1120)}</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_4110)}</td>
             <td></td>
           </tr>`
        : `<tr>
             <td colspan="3">TOTAL</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_1130)}</td>
             <td class="text-right tabular">${F.rupiah(totals.akun_4110)}</td>
             <td></td>
           </tr>`;

      el.viewRoot.innerHTML = `
        <div class="subtab-bar" role="tablist" aria-label="Jenis Penjualan">
          <button type="button" role="tab" aria-selected="${isTunai}" class="subtab-btn ${isTunai ? "active" : ""}" data-tab="tunai">Penjualan Tunai</button>
          <button type="button" role="tab" aria-selected="${!isTunai}" class="subtab-btn ${!isTunai ? "active" : ""}" data-tab="kredit">Penjualan Kredit</button>
        </div>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Input ${isTunai ? "Penjualan Tunai" : "Penjualan Kredit"}</h2>
          </div>
          <form id="form-penjualan" class="form-grid">
            <div class="field-group">
              <label for="pj-bukti">No. Bukti</label>
              <input id="pj-bukti" class="input" type="text" value="${F.esc(nextRes.no_bukti)}" required>
            </div>
            <div class="field-group">
              <label for="pj-tanggal">Tanggal</label>
              <input id="pj-tanggal" class="input" type="date" value="${F.todayISO()}" required>
            </div>
            <div class="field-group" style="grid-column: span 2;">
              <label for="pj-ket">Keterangan</label>
              <input id="pj-ket" class="input" type="text" placeholder="Contoh: Penjualan roti harian" required>
            </div>
            ${
              isTunai
                ? `<div class="field-group">
                     <label for="pj-akun">Diterima Ke</label>
                     <select id="pj-akun" class="select">
                       <option value="1-110">1-110 Kas</option>
                       <option value="1-120">1-120 Bank</option>
                     </select>
                   </div>`
                : ""
            }
            <div class="field-group">
              <label for="pj-nominal">Nominal (Rp)</label>
              <input id="pj-nominal" class="input tabular" type="number" min="1" step="1" placeholder="750000" required>
            </div>
            <div>
              <button type="submit" class="btn btn-primary">Simpan Transaksi</button>
            </div>
          </form>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Tabel ${isTunai ? "Penjualan Tunai" : "Penjualan Kredit"} (${items.length} transaksi)</h2>
          </div>
          <div class="table-scroll">
            <table class="ledger">
              <thead>${tableHead}</thead>
              <tbody>${rowsHtml}</tbody>
              <tfoot>${footHtml}</tfoot>
            </table>
          </div>
        </section>
      `;

      el.viewRoot.querySelectorAll(".subtab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.penjualanTab = btn.dataset.tab;
          renderPenjualan();
        });
      });

      document.getElementById("form-penjualan").addEventListener("submit", async (evt) => {
        evt.preventDefault();
        const bukti = document.getElementById("pj-bukti").value;
        const tanggal = document.getElementById("pj-tanggal").value;
        const ket = document.getElementById("pj-ket").value;
        const nominal = Number(document.getElementById("pj-nominal").value);

        const out = isTunai
          ? await Api.call("create_penjualan_tunai", bukti, tanggal, ket, document.getElementById("pj-akun").value, nominal)
          : await Api.call("create_penjualan_kredit", bukti, tanggal, ket, nominal);

        if (!out.ok) {
          showToast(out.error, true);
          return;
        }
        showToast(`Transaksi ${bukti.trim()} disimpan.`);
        renderPenjualan();
      });

      bindDeleteJurnal(renderPenjualan);
    } catch (err) {
      setViewError(err.message, renderPenjualan);
    }
  }

  // ---------- 5. TRANSAKSI LAINNYA ----------

  function initDefaultLines() {
    state.journalLines = [
      { no_akun: "", debit: 0, kredit: 0 },
      { no_akun: "", debit: 0, kredit: 0 },
    ];
  }

  async function renderTransaksiLainnya() {
    renderTopbar("transaksi_lainnya");
    setLoading("Memuat jurnal transaksi lainnya...");
    try {
      const [akunRes, listRes, nextRes] = await Promise.all([
        Api.call("list_akun"),
        Api.call("list_transaksi_lainnya"),
        Api.call("next_no_bukti", "UMUM"),
      ]);
      state.akunList = akunRes.items;
      if (!state.journalLines.length) initDefaultLines();

      const akunOptions = state.akunList
        .map((a) => `<option value="${F.esc(a.no_akun)}">${F.esc(a.no_akun)} - ${F.esc(a.nama)}</option>`)
        .join("");

      const rowsHtml = listRes.items.length
        ? listRes.items
            .map(
              (r) => `
              <tr>
                <td>${F.tanggal(r.tanggal)}</td>
                <td><strong>${F.esc(r.no_bukti)}</strong></td>
                <td>${F.esc(r.keterangan)}</td>
                <td>${F.esc(r.no_akun)}</td>
                <td>${F.esc(r.nama_akun)}</td>
                <td class="text-right tabular">${F.rupiahOrDash(r.debit)}</td>
                <td class="text-right tabular">${F.rupiahOrDash(r.kredit)}</td>
                <td class="text-right">
                  <button type="button" class="btn btn-danger-ghost btn-del-jurnal" data-id="${r.jurnal_id}" data-bukti="${F.esc(r.no_bukti)}">Hapus</button>
                </td>
              </tr>`
            )
            .join("")
        : `<tr><td colspan="8" class="text-center">Belum ada transaksi jurnal umum.</td></tr>`;

      el.viewRoot.innerHTML = `
        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Input Transaksi Lainnya</h2>
          </div>
          <form id="form-ju">
            <div class="form-grid">
              <div class="field-group">
                <label for="ju-tanggal">Tanggal</label>
                <input id="ju-tanggal" class="input" type="date" value="${F.todayISO()}" required>
              </div>
              <div class="field-group">
                <label for="ju-bukti">No. Bukti</label>
                <input id="ju-bukti" class="input" type="text" value="${F.esc(nextRes.no_bukti)}" required>
              </div>
              <div class="field-group" style="grid-column: span 2;">
                <label for="ju-ket">Keterangan</label>
                <input id="ju-ket" class="input" type="text" placeholder="Contoh: Pembayaran gaji atau listrik" required>
              </div>
            </div>

            <div class="journal-lines-box">
              <table class="journal-lines-table">
                <thead>
                  <tr>
                    <th style="width: 34%;">No. Akun (Pilih)</th>
                    <th style="width: 24%;">Nama Akun (Otomatis)</th>
                    <th style="width: 18%;">Debit (Rp)</th>
                    <th style="width: 18%;">Kredit (Rp)</th>
                    <th style="width: 6%;"></th>
                  </tr>
                </thead>
                <tbody id="ju-lines-body"></tbody>
              </table>
            </div>

            <div class="balance-bar">
              <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <button id="btn-add-line" type="button" class="btn btn-secondary btn-sm">+ Tambah Baris Akun</button>
                <span id="ju-balance-summary" class="tabular" style="font-size: 13px;"></span>
              </div>
              <button id="btn-save-ju" type="submit" class="btn btn-primary">Simpan Jurnal</button>
            </div>
          </form>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Riwayat Transaksi Lainnya</h2>
          </div>
          <div class="table-scroll">
            <table class="ledger">
              <thead>
                <tr>
                  <th>Tanggal</th>
                  <th>No. Bukti</th>
                  <th>Keterangan</th>
                  <th>No. Akun</th>
                  <th>Nama Akun</th>
                  <th class="text-right">Debit</th>
                  <th class="text-right">Kredit</th>
                  <th class="text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
              <tfoot>
                <tr>
                  <td colspan="5">TOTAL</td>
                  <td class="text-right tabular">${F.rupiah(listRes.totals.debit)}</td>
                  <td class="text-right tabular">${F.rupiah(listRes.totals.kredit)}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>
      `;

      const linesBody = document.getElementById("ju-lines-body");
      const summaryEl = document.getElementById("ju-balance-summary");
      const saveBtn = document.getElementById("btn-save-ju");

      function updateBalanceSummary() {
        const sumD = state.journalLines.reduce((acc, x) => acc + Number(x.debit || 0), 0);
        const sumK = state.journalLines.reduce((acc, x) => acc + Number(x.kredit || 0), 0);
        const balanced = sumD > 0 && sumD === sumK;
        summaryEl.innerHTML = `Total Debit: <strong>${F.rupiah(sumD)}</strong> | Total Kredit: <strong>${F.rupiah(sumK)}</strong> | <span class="status-badge ${balanced ? "status-ok" : "status-err"}">${balanced ? "Seimbang" : "Belum Seimbang"}</span>`;
        saveBtn.disabled = !balanced;
      }

      function renderLines() {
        linesBody.innerHTML = state.journalLines
          .map((line, idx) => {
            const matched = state.akunList.find((a) => a.no_akun === line.no_akun);
            return `
              <tr>
                <td>
                  <select class="select ju-akun-select" data-idx="${idx}">
                    <option value="">-- Pilih No. Akun --</option>
                    ${akunOptions}
                  </select>
                </td>
                <td class="ju-nama-cell">${matched ? F.esc(matched.nama) : "-"}</td>
                <td><input type="number" min="0" step="1" class="input tabular ju-debit" data-idx="${idx}" value="${line.debit || ""}" placeholder="0"></td>
                <td><input type="number" min="0" step="1" class="input tabular ju-kredit" data-idx="${idx}" value="${line.kredit || ""}" placeholder="0"></td>
                <td class="text-right">
                  ${
                    state.journalLines.length > 2
                      ? `<button type="button" class="btn btn-danger-ghost ju-remove" data-idx="${idx}">x</button>`
                      : ""
                  }
                </td>
              </tr>`;
          })
          .join("");

        linesBody.querySelectorAll(".ju-akun-select").forEach((sel) => {
          const idx = Number(sel.dataset.idx);
          sel.value = state.journalLines[idx].no_akun;
          sel.addEventListener("change", () => {
            state.journalLines[idx].no_akun = sel.value;
            const matched = state.akunList.find((a) => a.no_akun === sel.value);
            sel.closest("tr").querySelector(".ju-nama-cell").textContent = matched ? matched.nama : "-";
          });
        });

        linesBody.querySelectorAll(".ju-debit").forEach((inp) => {
          const idx = Number(inp.dataset.idx);
          inp.addEventListener("input", () => {
            const val = Math.max(0, Number(inp.value || 0));
            state.journalLines[idx].debit = val;
            if (val > 0) {
              state.journalLines[idx].kredit = 0;
              inp.closest("tr").querySelector(".ju-kredit").value = "";
            }
            updateBalanceSummary();
          });
        });

        linesBody.querySelectorAll(".ju-kredit").forEach((inp) => {
          const idx = Number(inp.dataset.idx);
          inp.addEventListener("input", () => {
            const val = Math.max(0, Number(inp.value || 0));
            state.journalLines[idx].kredit = val;
            if (val > 0) {
              state.journalLines[idx].debit = 0;
              inp.closest("tr").querySelector(".ju-debit").value = "";
            }
            updateBalanceSummary();
          });
        });

        linesBody.querySelectorAll(".ju-remove").forEach((btn) => {
          btn.addEventListener("click", () => {
            state.journalLines.splice(Number(btn.dataset.idx), 1);
            renderLines();
          });
        });

        updateBalanceSummary();
      }

      renderLines();

      document.getElementById("btn-add-line").addEventListener("click", () => {
        state.journalLines.push({ no_akun: "", debit: 0, kredit: 0 });
        renderLines();
      });

      document.getElementById("form-ju").addEventListener("submit", async (evt) => {
        evt.preventDefault();
        const out = await Api.call(
          "create_transaksi_lainnya",
          document.getElementById("ju-bukti").value,
          document.getElementById("ju-tanggal").value,
          document.getElementById("ju-ket").value,
          state.journalLines
        );
        if (!out.ok) {
          showToast(out.error, true);
          return;
        }
        initDefaultLines();
        showToast("Jurnal umum berhasil disimpan.");
        renderTransaksiLainnya();
      });

      bindDeleteJurnal(renderTransaksiLainnya);
    } catch (err) {
      setViewError(err.message, renderTransaksiLainnya);
    }
  }

  // ---------- 6. NERACA SALDO ----------

  async function renderNeracaSaldo() {
    renderTopbar("neraca_saldo", state.periodeNeraca);
    setLoading("Menghitung Neraca Saldo...");
    try {
      const [perRes, dataRes] = await Promise.all([
        Api.call("list_periode"),
        Api.call("get_neraca_saldo", state.periodeNeraca),
      ]);
      const data = dataRes.data;
      const periodeOpts = [`<option value="ALL">Semua Periode</option>`]
        .concat(perRes.items.map((p) => `<option value="${F.esc(p)}">${F.esc(F.periodeLabel(p))}</option>`))
        .join("");

      const rowsHtml = data.items
        .map(
          (it) => `
          <tr>
            <td><strong>${F.esc(it.no_akun)}</strong></td>
            <td>${F.esc(it.nama)}</td>
            <td class="text-right tabular">${F.rupiahOrDash(it.debit)}</td>
            <td class="text-right tabular">${F.rupiahOrDash(it.kredit)}</td>
          </tr>`
        )
        .join("");

      el.viewRoot.innerHTML = `
        <section class="panel">
          <div class="panel-header">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
              <h2 class="panel-title">Neraca Saldo (${F.esc(F.periodeLabel(data.periode))})</h2>
              <span class="status-badge ${data.seimbang ? "status-ok" : "status-err"}">
                ${data.seimbang ? "Seimbang" : "Tidak Seimbang"}
              </span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <label for="ns-periode" style="font-size: 12px; font-weight: 600;">Periode:</label>
              <select id="ns-periode" class="select" style="width: auto; min-width: 180px;">${periodeOpts}</select>
            </div>
          </div>
          <div class="table-scroll">
            <table class="ledger">
              <thead>
                <tr>
                  <th>No. Akun</th>
                  <th>Nama Akun</th>
                  <th class="text-right">Debit</th>
                  <th class="text-right">Kredit</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
              <tfoot>
                <tr>
                  <td colspan="2">TOTAL</td>
                  <td class="text-right tabular">${F.rupiah(data.total_debit)}</td>
                  <td class="text-right tabular">${F.rupiah(data.total_kredit)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>
      `;

      const sel = document.getElementById("ns-periode");
      sel.value = state.periodeNeraca;
      sel.addEventListener("change", () => {
        state.periodeNeraca = sel.value;
        renderNeracaSaldo();
      });
    } catch (err) {
      setViewError(err.message, renderNeracaSaldo);
    }
  }

  // ---------- 7. LABA RUGI ----------

  async function renderLabaRugi() {
    renderTopbar("laba_rugi", state.periodeLabaRugi);
    setLoading("Menghitung Laporan Laba Rugi...");
    try {
      const [perRes, dataRes] = await Promise.all([
        Api.call("list_periode"),
        Api.call("get_laba_rugi", state.periodeLabaRugi),
      ]);
      const data = dataRes.data;
      const periodeOpts = [`<option value="ALL">Semua Periode</option>`]
        .concat(perRes.items.map((p) => `<option value="${F.esc(p)}">${F.esc(F.periodeLabel(p))}</option>`))
        .join("");

      const groupRows = data.groups
        .map((grp) => {
          const itemRows = grp.items
            .map(
              (it) => `
              <tr>
                <td>${F.esc(it.no_akun)}</td>
                <td>${F.esc(it.nama)}</td>
                <td class="text-right tabular">${F.rupiah(it.nominal)}</td>
                <td></td>
              </tr>`
            )
            .join("");

          const signedSubtotal = grp.subtotal * grp.tanda;
          return `
            <tr class="group-row">
              <td colspan="4">${F.esc(grp.judul)}</td>
            </tr>
            ${itemRows}
            <tr class="subtotal-row">
              <td></td>
              <td>Subtotal ${F.esc(grp.judul)}</td>
              <td></td>
              <td class="text-right tabular">${F.rupiah(signedSubtotal)}</td>
            </tr>
          `;
        })
        .join("");

      const net = data.ringkasan.laba_rugi_bersih;
      const statusText = net >= 0 ? "Laba Bersih" : "Rugi Bersih";

      el.viewRoot.innerHTML = `
        <section class="panel">
          <div class="panel-header">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
              <h2 class="panel-title">Laporan Laba Rugi (${F.esc(F.periodeLabel(data.periode))})</h2>
              <span class="status-badge ${net >= 0 ? "status-ok" : "status-err"}">${statusText}: ${F.rupiah(net)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <label for="lr-periode" style="font-size: 12px; font-weight: 600;">Periode:</label>
              <select id="lr-periode" class="select" style="width: auto; min-width: 180px;">${periodeOpts}</select>
            </div>
          </div>

          <div class="table-scroll">
            <table class="ledger">
              <thead>
                <tr>
                  <th>No. Akun</th>
                  <th>Nama Akun</th>
                  <th class="text-right">Nominal Akun</th>
                  <th class="text-right">Subtotal / Hasil</th>
                </tr>
              </thead>
              <tbody>
                ${groupRows}
                <tr class="grand-total-row">
                  <td colspan="3">LABA / RUGI BERSIH</td>
                  <td class="text-right tabular">${F.rupiah(net)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      `;

      const sel = document.getElementById("lr-periode");
      sel.value = state.periodeLabaRugi;
      sel.addEventListener("change", () => {
        state.periodeLabaRugi = sel.value;
        renderLabaRugi();
      });
    } catch (err) {
      setViewError(err.message, renderLabaRugi);
    }
  }

  function bindDeleteJurnal(reloadFn) {
    el.viewRoot.querySelectorAll(".btn-del-jurnal").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const bukti = btn.dataset.bukti;
        const ok = await askConfirm(
          "Hapus Transaksi",
          `Hapus transaksi ${bukti}? Saldo Neraca dan Laba Rugi akan langsung dihitung ulang.`
        );
        if (!ok) return;
        const out = await Api.call("delete_jurnal", Number(btn.dataset.id));
        if (!out.ok) {
          showToast(out.error, true);
          return;
        }
        showToast(`Transaksi ${bukti} dihapus.`);
        reloadFn();
      });
    });
  }

  // ---------- Event Global & Bootstrap ----------

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => navigate(btn.dataset.view));
  });

  el.btnMobileMenu.addEventListener("click", () => {
    el.sidebar.classList.toggle("open");
  });

  el.btnLogout.addEventListener("click", () => {
    state.user = null;
    el.appShell.classList.add("hidden");
    el.loginScreen.classList.remove("hidden");
    el.loginPassword.value = "";
    el.loginError.classList.add("hidden");
    el.loginUsername.focus();
  });

  el.btnResetDemo.addEventListener("click", async () => {
    const ok = await askConfirm(
      "Reset Data Demo",
      "Kembalikan Daftar Akun dan seluruh transaksi ke data contoh presentasi awal? Perubahan sebelumnya akan diganti.",
      "Ya, Reset"
    );
    if (!ok) return;
    const out = await Api.call("reset_demo_data");
    if (out.ok) {
      showToast("Data demo berhasil dikembalikan.");
      navigate(state.view);
    }
  });

  el.loginForm.addEventListener("submit", async (evt) => {
    evt.preventDefault();
    el.loginError.classList.add("hidden");
    const submitBtn = document.getElementById("login-submit");
    submitBtn.disabled = true;
    try {
      const res = await Api.call("login", el.loginUsername.value, el.loginPassword.value);
      if (!res.ok) {
        el.loginError.textContent = res.error;
        el.loginError.classList.remove("hidden");
        return;
      }
      state.user = res.user;
      el.activeUserName.textContent = res.user.nama_lengkap;
      el.loginScreen.classList.add("hidden");
      el.appShell.classList.remove("hidden");
      navigate("dashboard");
    } catch (err) {
      el.loginError.textContent = err.message;
      el.loginError.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });

  async function initApp() {
    try {
      const info = await Api.call("get_app_info");
      state.dbPath = info.db_path || "";
      if (info.logo_data_url) {
        el.loginLogo.src = info.logo_data_url;
        el.sidebarLogo.src = info.logo_data_url;
      }
    } catch (err) {
      el.loginError.textContent = err.message;
      el.loginError.classList.remove("hidden");
    }
  }

  initApp();
})();

