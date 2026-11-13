/* Pembungkus pemanggilan API Python pywebview */

window.AzelaApi = {
  readyPromise: null,

  waitReady() {
    if (window.pywebview && window.pywebview.api) {
      return Promise.resolve(window.pywebview.api);
    }
    if (!this.readyPromise) {
      this.readyPromise = new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error("Koneksi ke backend Python tidak tersedia."));
        }, 8000);
        window.addEventListener("pywebviewready", () => {
          clearTimeout(timeout);
          resolve(window.pywebview.api);
        }, { once: true });
      });
    }
    return this.readyPromise;
  },

  async call(method, ...args) {
    const api = await this.waitReady();
    if (typeof api[method] !== "function") {
      throw new Error(`Metode API '${method}' tidak ditemukan.`);
    }
    return api[method](...args);
  },
};

