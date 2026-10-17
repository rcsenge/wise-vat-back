// Shared receipt list and summary. Both pages load this file after api.js.
// The page must contain the receipt-list, empty-state and dialog elements.
// The summary elements are optional. Only the employer page shows them.
(() => {
  "use strict";

  const MAX_REASONS_SHOWN = 3;
  const STATUS_BADGE_CLASS = {
    approved:
      "rounded-full bg-[#e2f6d5] px-2 py-0.5 text-xs font-semibold text-[#163300]",
    rejected:
      "rounded-full bg-[#ffe7e5] px-2 py-0.5 text-xs font-semibold text-[#a8200d]",
  };

  const api = window.vatbackApi;
  const dateFormatter = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  };

  const createAmount = (label, text, isClaim) => {
    const wrapper = element("div", "text-right");
    wrapper.append(
      element("p", "text-xs text-[#6b7a78]", label),
      element(
        "p",
        isClaim ? "font-semibold text-[#00a4a6]" : "font-medium",
        text,
      ),
    );
    return wrapper;
  };

  const createThumbnail = (receipt, openDocument) => {
    if (!receipt.imageDataUrl) {
      return element(
        "div",
        "grid h-16 w-16 shrink-0 place-items-center rounded-xl bg-[#00a4a6]/10 text-xs font-semibold text-[#00a4a6]",
        "JSON",
      );
    }
    const button = element(
      "button",
      "shrink-0 rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00a4a6]",
    );
    button.type = "button";
    button.setAttribute("aria-label", "View receipt document");
    button.addEventListener("click", () => openDocument(receipt.imageDataUrl));
    const image = element("img", "h-16 w-16 rounded-xl object-cover");
    image.src = receipt.imageDataUrl;
    image.alt = "Scanned receipt preview";
    button.appendChild(image);
    return button;
  };

  const createReceiptItem = (receipt, openDocument) => {
    const item = element(
      "li",
      "flex items-center gap-4 rounded-2xl border border-[#e6e9ea] bg-white p-4 shadow-sm",
    );

    const details = element("div", "min-w-0 flex-1");
    const titleRow = element("div", "flex items-center gap-2");
    titleRow.append(
      element(
        "p",
        "truncate text-sm font-medium",
        receipt.merchant || "Untitled receipt",
      ),
      element(
        "span",
        STATUS_BADGE_CLASS[receipt.status] ?? STATUS_BADGE_CLASS.rejected,
        receipt.status === "approved" ? "Approved" : "Rejected",
      ),
    );
    details.append(
      titleRow,
      element(
        "p",
        "text-xs text-[#6b7a78]",
        dateFormatter.format(new Date(receipt.scannedAt || 0)),
      ),
    );
    if (receipt.status !== "approved") {
      receipt.reasons.slice(0, MAX_REASONS_SHOWN).forEach((reason) => {
        details.appendChild(element("p", "text-xs text-[#a8200d]", reason));
      });
    }

    const spend = createAmount(
      "Amount",
      api.formatMoney(receipt.amount, receipt.currency),
      false,
    );
    spend.classList.add("hidden", "sm:block");
    const claim = createAmount(
      "Claimable VAT",
      api.formatMoney(receipt.taxAmount, receipt.currency),
      true,
    );

    item.append(createThumbnail(receipt, openDocument), details, spend, claim);
    return item;
  };

  const create = ({ approvedOnly }) => {
    const receiptList = document.getElementById("receipt-list");
    const summaryClaimable = document.getElementById("summary-claimable");
    const summarySpend = document.getElementById("summary-spend");
    const summaryCount = document.getElementById("summary-count");
    const emptyState = document.getElementById("empty-state");
    const backendError = document.getElementById("backend-error");
    const documentDialog = document.getElementById("document-dialog");
    const documentImage = document.getElementById("document-image");

    const openDocument = (imageDataUrl) => {
      documentImage.src = imageDataUrl;
      documentDialog.showModal();
    };

    documentDialog.addEventListener("click", (event) => {
      if (event.target === documentDialog) {
        documentDialog.close();
      }
    });

    const render = (allReceipts) => {
      const approved = allReceipts.filter(
        (receipt) => receipt.status === "approved",
      );
      const shown = approvedOnly ? approved : allReceipts;

      if (summaryCount) {
        summaryClaimable.textContent = api.formatTotals(
          api.sumByCurrency(approved, (receipt) => receipt.taxAmount),
        );
        summarySpend.textContent = api.formatTotals(
          api.sumByCurrency(shown, (receipt) => receipt.amount),
        );
        summaryCount.textContent = String(approved.length);
      }

      receiptList.replaceChildren(
        ...shown.map((receipt) => createReceiptItem(receipt, openDocument)),
      );
      emptyState.classList.toggle("hidden", shown.length > 0);
    };

    const refresh = async () => {
      try {
        const allReceipts = await api.listReceipts();
        backendError.classList.add("hidden");
        render(allReceipts);
      } catch (error) {
        backendError.textContent = error.message;
        backendError.classList.remove("hidden");
      }
    };

    return { refresh };
  };

  window.vatbackReceipts = { create };
})();
