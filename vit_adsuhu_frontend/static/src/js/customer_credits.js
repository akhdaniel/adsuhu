/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuTopupDirect = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-topup-direct": "_onTopupDirectClick",
        "click .js-topup-direct-confirm": "_onTopupDirectConfirmClick",
        "click .adsuhu-topup-option": "_onTopupOptionClick",
        "input #topup-direct-custom-amount": "_onCustomAmountInput",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        return this._super(...arguments);
    },
    async _onTopupDirectClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        if (!button) {
            return;
        }
        const errorEl = document.getElementById("topup-direct-error");
        const modalEl = document.getElementById("topup-direct-modal");
        const modalErrorEl = document.getElementById("topup-direct-modal-error");
        const iframeEl = document.getElementById("topup-direct-iframe");
        const packageEl = document.querySelector(".adsuhu-topup-option.active");
        const customWrap = document.querySelector(".adsuhu-topup-custom");
        if (errorEl) {
            errorEl.classList.add("d-none");
            errorEl.textContent = "";
        }
        if (modalErrorEl) {
            modalErrorEl.classList.add("d-none");
            modalErrorEl.textContent = "";
        }
        if (iframeEl) {
            iframeEl.src = "";
        }
        if (customWrap) {
            const isCustom = packageEl?.dataset?.package === "custom";
            customWrap.classList.toggle("d-none", !isCustom);
        }
        button.disabled = true;
        const originalText = button.innerText;
        button.innerText = "Opening...";
        try {
            if (modalEl && window.bootstrap?.Modal) {
                const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
            } else if (modalEl) {
                modalEl.classList.add("show");
                modalEl.style.display = "block";
            } else {
                window.location.href = url;
            }
        } catch (err) {
            console.error(err);
            const message = err.message || "Failed to create payment.";
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.classList.remove("d-none");
            } else {
                alert(message);
            }
        } finally {
            button.disabled = false;
            button.innerText = originalText;
        }
    },
    async _onTopupDirectConfirmClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        if (!button) {
            return;
        }
        const errorEl = document.getElementById("topup-direct-error");
        const modalErrorEl = document.getElementById("topup-direct-modal-error");
        const iframeEl = document.getElementById("topup-direct-iframe");
        const packageEl = document.querySelector(".adsuhu-topup-option.active");
        const customAmountEl = document.getElementById("topup-direct-custom-amount");
        if (errorEl) {
            errorEl.classList.add("d-none");
            errorEl.textContent = "";
        }
        if (modalErrorEl) {
            modalErrorEl.classList.add("d-none");
            modalErrorEl.textContent = "";
        }
        button.disabled = true;
        const originalText = button.innerText;
        button.innerText = "Creating payment...";
        try {
            const packageKey = packageEl?.dataset?.package || "100000";
            console.log('packageEl',packageEl.dataset, packageKey)
            const amountValue = packageKey === "custom"
                ? customAmountEl?.value
                : packageKey;
            const response = await fetch("/xendit/create_payment", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({
                    package: packageKey,
                    amount: amountValue || null,
                    custom_amount: customAmountEl?.value || null,
                }),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Failed to create payment.");
            }
            const json = await response.json();
            if (json?.error) {
                throw new Error(json.error);
            }
            const url = json?.result?.url || json?.url;
            if (!url) {
                throw new Error("Payment URL not available.");
            }
            if (iframeEl) {
                iframeEl.src = url;
            }
        } catch (err) {
            console.error(err);
            const message = err.message || "Failed to create payment.";
            if (modalErrorEl) {
                modalErrorEl.textContent = message;
                modalErrorEl.classList.remove("d-none");
            } else if (errorEl) {
                errorEl.textContent = message;
                errorEl.classList.remove("d-none");
            } else {
                alert(message);
            }
        } finally {
            button.disabled = false;
            button.innerText = originalText;
        }
    },
    _onTopupOptionClick(event) {
        const button = event.currentTarget;
        if (!button) {
            return;
        }
        const container = button.closest(".adsuhu-topup-options");
        if (!container) {
            return;
        }
        container.querySelectorAll(".adsuhu-topup-option").forEach((el) => {
            el.classList.remove("active");
        });
        button.classList.add("active");
        const customWrap = document.querySelector(".adsuhu-topup-custom");
        if (customWrap) {
            const isCustom = button.dataset?.package === "custom";
            customWrap.classList.toggle("d-none", !isCustom);
        }
    },
    _onCustomAmountInput(event) {
        const input = event.currentTarget;
        const creditsEl = document.getElementById("topup-direct-custom-credits");
        if (!creditsEl || !input) {
            return;
        }
        const amount = parseFloat(input.value || "0");
        const credits = Math.floor((amount / 100000) * 1000);
        creditsEl.textContent = credits.toLocaleString("en-US");
    },
});
