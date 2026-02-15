/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuTopupDirect = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-topup-direct": "_onTopupDirectClick",
        "click .js-topup-direct-confirm": "_onTopupDirectConfirmClick",
        "click .adsuhu-topup-option": "_onTopupOptionClick",
        "input #topup-direct-custom-amount": "_onCustomAmountInput",
        "click .js-topup-direct-close": "_onTopupDirectCloseClick",
        "click .js-topup-manual": "_onTopupManualClick",
        "click .js-topup-manual-submit": "_onTopupManualSubmitClick",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        const modalEl = document.getElementById("topup-direct-modal");
        if (modalEl) {
            modalEl.addEventListener("hidden.bs.modal", () => {
                const iframeEl = document.getElementById("topup-direct-iframe");
                if (iframeEl) {
                    iframeEl.src = "";
                }
                this._setTopupOptionsDisabled(false);
            });
        }
        this._autoOpenTopup();
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
        const customAmountEl = document.getElementById("topup-direct-custom-amount");
        const customAmountPreviewEl = document.getElementById("topup-direct-custom-rp");
        const manualEl = document.getElementById("topup-manual-instruction");
        const manualUploadEl = document.getElementById("topup-manual-upload");
        const transferProofEl = document.getElementById("topup-transfer-proof");
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
        if (manualEl) {
            manualEl.classList.add("d-none");
            manualEl.innerHTML = "";
        }
        if (manualUploadEl) {
            manualUploadEl.classList.add("d-none");
        }
        if (transferProofEl) {
            transferProofEl.value = "";
        }
        if (customAmountEl) {
            customAmountEl.value = "";
        }
        if (customAmountPreviewEl) {
            customAmountPreviewEl.textContent = "Rp 0";
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
        const manualEl = document.getElementById("topup-manual-instruction");
        const optionButtons = document.querySelectorAll(".adsuhu-topup-option");
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
        if (manualEl) {
            manualEl.classList.add("d-none");
            manualEl.innerHTML = "";
        }
        this._setTopupOptionsDisabled(true);
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
        const amountPreviewEl = document.getElementById("topup-direct-custom-rp");
        if (!amountPreviewEl || !input) {
            return;
        }
        const amount = parseFloat(input.value || "0");
        const formattedAmount = Number.isFinite(amount)
            ? `Rp ${Math.max(0, amount).toLocaleString("en-US")}`
            : "Rp 0";
        amountPreviewEl.textContent = formattedAmount;
    },
    _onTopupDirectCloseClick() {
        const modalEl = document.getElementById("topup-direct-modal");
        if (!modalEl) {
            return;
        }
        const iframeEl = document.getElementById("topup-direct-iframe");
        if (iframeEl) {
            iframeEl.src = "";
        }
        if (window.bootstrap?.Modal) {
            const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.hide();
        } else {
            modalEl.classList.remove("show");
            modalEl.style.display = "none";
            modalEl.setAttribute("aria-hidden", "true");
            document.body.classList.remove("modal-open");
            const backdrops = document.querySelectorAll(".modal-backdrop");
            backdrops.forEach((el) => el.remove());
        }
        this._setTopupOptionsDisabled(false);
    },
    async _onTopupManualClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        if (!button) {
            return;
        }
        const manualEl = document.getElementById("topup-manual-instruction");
        const manualUploadEl = document.getElementById("topup-manual-upload");
        const modalErrorEl = document.getElementById("topup-direct-modal-error");
        const iframeEl = document.getElementById("topup-direct-iframe");
        if (modalErrorEl) {
            modalErrorEl.classList.add("d-none");
            modalErrorEl.textContent = "";
        }
        if (iframeEl) {
            iframeEl.src = "";
        }
        button.disabled = true;
        const originalText = button.innerText;
        button.innerText = "Loading...";
        try {
            const response = await fetch("/payment/manual_info", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({}),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Failed to load manual payment info.");
            }
            const json = await response.json();
            if (json?.error) {
                throw new Error(json.error);
            }
            if (manualEl) {
                manualEl.innerHTML = json?.result?.message || "No manual payment instructions found.";
                manualEl.classList.remove("d-none");
            }
            if (manualUploadEl) {
                manualUploadEl.classList.remove("d-none");
            }
        } catch (err) {
            console.error(err);
            const message = err.message || "Failed to load manual payment info.";
            if (modalErrorEl) {
                modalErrorEl.textContent = message;
                modalErrorEl.classList.remove("d-none");
            } else {
                alert(message);
            }
        } finally {
            button.disabled = false;
            button.innerText = originalText;
        }
    },
    async _onTopupManualSubmitClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        if (!button) {
            return;
        }
        const modalErrorEl = document.getElementById("topup-direct-modal-error");
        const packageEl = document.querySelector(".adsuhu-topup-option.active");
        const customAmountEl = document.getElementById("topup-direct-custom-amount");
        const transferProofEl = document.getElementById("topup-transfer-proof");
        const selectedFile = transferProofEl?.files?.[0];

        if (modalErrorEl) {
            modalErrorEl.classList.add("d-none");
            modalErrorEl.textContent = "";
        }
        if (!selectedFile) {
            if (modalErrorEl) {
                modalErrorEl.textContent = "Please upload transfer proof first.";
                modalErrorEl.classList.remove("d-none");
            }
            return;
        }

        button.disabled = true;
        const originalText = button.innerText;
        button.innerText = "Submitting...";
        try {
            const packageKey = packageEl?.dataset?.package || "100000";
            const amountValue = this._resolveSelectedAmount(packageKey, customAmountEl?.value);
            const payload = new FormData();
            payload.append("csrf_token", this.csrfToken);
            payload.append("package", packageKey);
            payload.append("amount", amountValue);
            payload.append("custom_amount", customAmountEl?.value || "");
            payload.append("transfer_proof", selectedFile);

            const response = await fetch("/payment/manual_submit", {
                method: "POST",
                body: payload,
                credentials: "same-origin",
            });
            const text = await response.text();
            let json = {};
            try {
                json = text ? JSON.parse(text) : {};
            } catch (parseError) {
                throw new Error(text || "Failed to submit manual payment.");
            }
            if (!response.ok || json?.error) {
                throw new Error(json?.error || "Failed to submit manual payment.");
            }
            window.location.reload();
        } catch (err) {
            console.error(err);
            const message = err.message || "Failed to submit manual payment.";
            if (modalErrorEl) {
                modalErrorEl.textContent = message;
                modalErrorEl.classList.remove("d-none");
            } else {
                alert(message);
            }
        } finally {
            button.disabled = false;
            button.innerText = originalText;
        }
    },
    _resolveSelectedAmount(packageKey, customValue) {
        if (packageKey === "100000" || packageKey === "200000" || packageKey === "500000") {
            return packageKey;
        }
        return customValue || "";
    },
    _setTopupOptionsDisabled(disabled) {
        const optionButtons = document.querySelectorAll(".adsuhu-topup-option");
        optionButtons.forEach((el) => {
            el.disabled = disabled;
            el.classList.toggle("disabled", disabled);
        });
        const customAmountEl = document.getElementById("topup-direct-custom-amount");
        if (customAmountEl) {
            customAmountEl.disabled = disabled;
        }
    },
    _autoOpenTopup() {
        const params = new URLSearchParams(window.location.search);
        if (!params.has("topup")) {
            return;
        }
        const trigger = document.querySelector(".js-topup-direct");
        if (trigger) {
            trigger.click();
        }
    },
});
