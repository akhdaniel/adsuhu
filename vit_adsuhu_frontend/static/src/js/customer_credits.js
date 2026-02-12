/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuTopupDirect = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-topup-direct": "_onTopupDirectClick",
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
        if (errorEl) {
            errorEl.classList.add("d-none");
            errorEl.textContent = "";
        }
        button.disabled = true;
        const originalText = button.innerText;
        button.innerText = "Creating payment...";
        try {
            const response = await fetch("/xendit/create_payment", {
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
                throw new Error(errorText || "Failed to create payment.");
            }
            const json = await response.json();
            if (json?.error) {
                throw new Error(json.error);
            }
            const url = json?.result?.url;
            if (!url) {
                throw new Error("Payment URL not available.");
            }
            const popup = window.open(url, "_blank", "noopener,noreferrer");
            if (!popup) {
                alert(`Please allow popups and open this URL: ${url}`);
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
});
