// Shared receipt list. Both pages load this file after api.js.
// The page must contain the receipt-list, empty-state and dialog elements.
// The employer page filters the list per country with setCountry.
(() => {
  "use strict";

  const MAX_REASONS_SHOWN = 3;
  const STATUS_BADGE_CLASS = {
    approved:
      "inline-flex h-6 items-center rounded-full bg-brand-light-green px-2 text-xs font-semibold text-brand-forest-green",
    rejected:
      "inline-flex h-6 items-center rounded-full bg-status-negative-background px-2 text-xs font-semibold text-status-negative",
  };

  const api = window.vatbackApi;
  const dateFormatter = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  });

  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  };

  const receiptIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6" aria-hidden="true"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" /><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8" /><path d="M12 17.5v-11" /></svg>`;

  const createAmounts = (receipt) => {
    const wrapper = element("div", "shrink-0 text-right tabular-nums");
    const claim = api.formatMoney(receipt.taxAmount, receipt.currency);
    const isApproved = receipt.status === "approved";
    wrapper.append(
      element(
        "p",
        isApproved
          ? "text-base font-semibold text-status-positive"
          : "text-base font-semibold text-ink-tertiary line-through",
        `+ ${claim}`,
      ),
      element(
        "p",
        "text-sm text-ink-tertiary",
        api.formatMoney(receipt.amount, receipt.currency),
      ),
    );
    return wrapper;
  };

  const createThumbnail = (receipt, openDocument) => {
    if (!receipt.imageDataUrl) {
      const circle = element(
        "div",
        "grid h-12 w-12 shrink-0 place-items-center rounded-full border border-line-neutral text-ink-primary",
      );
      circle.innerHTML = receiptIcon;
      return circle;
    }
    const button = element(
      "button",
      "shrink-0 cursor-pointer rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest-green",
    );
    button.type = "button";
    button.setAttribute("aria-label", "View receipt document");
    button.addEventListener("click", () => openDocument(receipt.imageDataUrl));
    const image = element("img", "h-12 w-12 rounded-full object-cover");
    image.src = receipt.imageDataUrl;
    image.alt = "Scanned receipt preview";
    button.appendChild(image);
    return button;
  };

  const createReceiptItem = (receipt, openDocument) => {
    const item = element("li", "flex min-h-18 items-start gap-4 py-3");

    const details = element("div", "min-w-0 flex-1");
    const metaRow = element(
      "div",
      "mt-1 flex items-center gap-2 text-sm text-ink-secondary",
    );
    metaRow.append(
      element(
        "span",
        STATUS_BADGE_CLASS[receipt.status] ?? STATUS_BADGE_CLASS.rejected,
        receipt.status === "approved" ? "Approved" : "Rejected",
      ),
      element(
        "span",
        "truncate",
        dateFormatter.format(new Date(receipt.scannedAt || 0)),
      ),
    );
    details.append(
      element(
        "p",
        "truncate text-title-item font-semibold text-ink-primary",
        receipt.merchant || "Untitled receipt",
      ),
      metaRow,
    );
    if (receipt.status !== "approved") {
      receipt.reasons.slice(0, MAX_REASONS_SHOWN).forEach((reason) => {
        details.appendChild(
          element("p", "mt-1 text-sm text-status-negative", reason),
        );
      });
    }

    item.append(
      createThumbnail(receipt, openDocument),
      details,
      createAmounts(receipt),
    );
    return item;
  };

  // The document dialog belongs to the page. The lookup happens on first use.
  const openDocument = (imageDataUrl) => {
    const documentDialog = document.getElementById("document-dialog");
    document.getElementById("document-image").src = imageDataUrl;
    documentDialog.showModal();
  };

  const createItem = (receipt) => createReceiptItem(receipt, openDocument);

  // The optional onRender callback gets the receipts before the country filter.
  const create = ({ approvedOnly, onRender }) => {
    const receiptList = document.getElementById("receipt-list");
    const emptyState = document.getElementById("empty-state");
    const backendError = document.getElementById("backend-error");
    const documentDialog = document.getElementById("document-dialog");

    let latestReceipts = [];
    let selectedCountry = null;

    documentDialog.addEventListener("click", (event) => {
      if (event.target === documentDialog) {
        documentDialog.close();
      }
    });

    const render = () => {
      const listed = approvedOnly
        ? latestReceipts.filter((receipt) => receipt.status === "approved")
        : latestReceipts;
      const shown = selectedCountry
        ? listed.filter((receipt) => receipt.country === selectedCountry)
        : listed;

      receiptList.replaceChildren(...shown.map(createItem));
      emptyState.classList.toggle("hidden", shown.length > 0);
      if (onRender) {
        onRender(listed);
      }
    };

    const refresh = async () => {
      try {
        latestReceipts = await api.listReceipts();
        backendError.classList.add("hidden");
        render();
      } catch (error) {
        backendError.textContent = error.message;
        backendError.classList.remove("hidden");
      }
    };

    const setCountry = (country) => {
      selectedCountry = country;
      render();
    };

    return { refresh, setCountry };
  };

  window.vatbackReceipts = { create, createItem };
})();
