// Shared client for the vatback backend. Both pages load this file.
// The backend runs on port 8000 of the same host that serves the pages.
(() => {
  "use strict";

  const API_PORT = 8000;
  const REQUEST_TIMEOUT_MS = 10000;
  // The local AI needs time to read a PDF or a photo.
  const UPLOAD_TIMEOUT_MS = 300000;
  const API_BASE = `${window.location.protocol}//${window.location.hostname || "localhost"}:${API_PORT}`;

  const request = async (
    path,
    options = {},
    timeoutMs = REQUEST_TIMEOUT_MS,
  ) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        signal: controller.signal,
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        const reasons = body?.detail?.reasons ?? [
          `The backend returned status ${response.status}.`,
        ];
        throw Object.assign(new Error(reasons.join(" ")), { reasons });
      }
      return body;
    } catch (error) {
      if (error.reasons) {
        throw error;
      }
      const reason = `The backend at ${API_BASE} is not reachable.`;
      throw Object.assign(new Error(reason), { reasons: [reason] });
    } finally {
      clearTimeout(timer);
    }
  };

  const formatters = new Map();

  const formatMoney = (value, currency = "EUR") => {
    if (!formatters.has(currency)) {
      formatters.set(
        currency,
        new Intl.NumberFormat(undefined, { style: "currency", currency }),
      );
    }
    const number = Number(value);
    return formatters
      .get(currency)
      .format(Number.isFinite(number) ? number : 0);
  };

  // Sums amounts per currency. The result keeps the first-seen currency order.
  const sumByCurrency = (items, readAmount) => {
    const totals = new Map();
    items.forEach((item) => {
      const amount = Number(readAmount(item));
      const current = totals.get(item.currency) ?? 0;
      totals.set(
        item.currency,
        current + (Number.isFinite(amount) ? amount : 0),
      );
    });
    return totals;
  };

  const formatTotals = (totals) => {
    if (totals.size === 0) {
      return formatMoney(0);
    }
    return Array.from(totals, ([currency, amount]) =>
      formatMoney(amount, currency),
    ).join(" · ");
  };

  window.vatbackApi = {
    baseUrl: API_BASE,
    listReceipts: () => request("/receipts"),
    getClaims: () => request("/claims"),
    // The browser downloads the ZIP file. The server sends it as an attachment.
    packageUrl: (country, year) =>
      `${API_BASE}/claims/package?country=${encodeURIComponent(country)}&year=${encodeURIComponent(year)}`,
    uploadInvoice: (documentFile, imageDataUrl) => {
      const form = new FormData();
      form.append("document", documentFile);
      if (imageDataUrl) {
        form.append("image_data_url", imageDataUrl);
      }
      return request(
        "/invoices/upload",
        { method: "POST", body: form },
        UPLOAD_TIMEOUT_MS,
      );
    },
    formatMoney,
    formatTotals,
    sumByCurrency,
  };
})();
