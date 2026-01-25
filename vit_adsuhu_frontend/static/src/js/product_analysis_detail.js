/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuRegenerate = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-regenerate": "_onRegenerateClick",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        this.endpoints = {
            product_value_analysis: (id) => `/product_analysis/${id}/regenerate`,
            market_mapper: (id) => `/product_analysis/${id}/market_mapper/regenerate`,
            audience_profiler: (id) => `/product_analysis/audience_profiler/${id}/regenerate`,
            angle_hook: (id) => `/product_analysis/angle_hook/${id}/regenerate`,
            hook: (id) => `/product_analysis/hook/${id}/regenerate`,
            ads_copy: (id) => `/product_analysis/ads_copy/${id}/regenerate`,
        };
        this.nextChain = {
            product_value_analysis: "market_mapper",
            market_mapper: "audience_profiler",
            audience_profiler: "angle_hook",
            angle_hook: "hook",
            hook: "ads_copy",
        };
        return this._super(...arguments);
    },
    _setButtonState(button, loading) {
        if (!button) {
            return;
        }
        if (loading) {
            button.dataset.originalText = button.innerText;
            button.innerText = "Regenerating...";
            button.disabled = true;
        } else {
            button.innerText = button.dataset.originalText || "Regenerate";
            button.disabled = false;
        }
    },
    async _onRegenerateClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const regenerateType = button.dataset.regenerate;
        const recordId = button.dataset.id;
        const endpointFactory = this.endpoints[regenerateType];
        if (!endpointFactory || !recordId) {
            return;
        }

        this._setButtonState(button, true);
        try {
            const response = await fetch(endpointFactory(recordId), {
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
                throw new Error(errorText || "Failed to regenerate.");
            }
            const json = await response.json();
            const outputHtml = json?.result?.output_html ?? json?.output_html ?? "";
            const section = button.closest(".adsuhu-section");
            if (section) {
                const titleEl = section.querySelector(".adsuhu-section-title");
                const modelTitle = regenerateType ? regenerateType.trim() : "Result";
                const modelKey = regenerateType || "result";
                const nextModel = button.dataset.nextModel || "";
                const newSection = document.createElement("section");
                newSection.className = "adsuhu-section";
                newSection.id = `section-${modelKey}`;
                newSection.style.scrollMarginTop = "6rem";
                newSection.innerHTML = `
                    <h2 class="adsuhu-section-title">${modelTitle}</h2>
                    <div class="adsuhu-content">${outputHtml || ""}</div>
                `;
                if (nextModel) {
                    const nextTitle = nextModel
                        .split("_")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ");
                    const nextButton = document.createElement("button");
                    nextButton.className = "btn btn-secondary js-regenerate";
                    nextButton.id = `regenerate_${nextModel}`;
                    nextButton.dataset.id = button.dataset.id || "";
                    nextButton.dataset.regenerate = nextModel;
                    nextButton.dataset.nextModel = this.nextChain[nextModel] || "";
                    nextButton.innerHTML = `<i class="fa fa-send me-1"></i> Analyze ${nextTitle}`;
                    const buttonWrap = document.createElement("div");
                    buttonWrap.className = "d-flex align-items-center justify-content-center";
                    buttonWrap.appendChild(nextButton);
                    newSection.appendChild(buttonWrap);
                }
                section.insertAdjacentElement("afterend", newSection);
            }
        } catch (err) {
            console.error(err);
            alert(err.message || "Regenerate failed.");
        } finally {
            this._setButtonState(button, false);
        }
    },
});
