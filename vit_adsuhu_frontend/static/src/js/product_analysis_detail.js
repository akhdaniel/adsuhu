/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuRegenerate = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-regenerate": "_onRegenerateClick",
        "click .js-clear-output": "_onClearOutputClick",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        this.endpoints = {
            write_with_ai: (id) => `/product_analysis/${id}/write_with_ai`,
            product_value_analysis: (id) => `/product_analysis/${id}/regenerate`,
            market_map_analysis: (id) => `/product_analysis/${id}/market_mapper/regenerate`,
            audience_profile_analysis: (id) => `/market_mapper/${id}/audience_profiler/regenerate`,
            angle_hook: (id) => `/audience_profiler/${id}/angle_hook/regenerate`,
            // hook: (id) => `/angle_hook/${id}/hook/regenerate`,
            ads_copy: (id) => `/hook/${id}/ads_copy/regenerate`,
            image_variants: (id) => `/image_generator/${id}/image_variant/regenerate`,
        };
        this.statusEndpoints = {
            product_value_analysis: (id) => `/regenerate_status/product_value_analysis/${id}`,
            market_map_analysis: (id) => `/regenerate_status/market_map_analysis/${id}`,
            audience_profile_analysis: (id) => `/regenerate_status/audience_profile_analysis/${id}`,
            angle_hook: (id) => `/regenerate_status/angle_hook/${id}`,
            ads_copy: (id) => `/regenerate_status/ads_copy/${id}`,
            image_variants: (id) => `/regenerate_status/image_variants/${id}`,
        };
        this.nextChain = {
            write_with_ai: "product_value_analysis",
            product_value_analysis: "market_map_analysis",
            market_map_analysis: "audience_profile_analysis",
            audience_profile_analysis: "angle_hook",
            angle_hook: "ads_copy",
            ads_copy: "image_variants",
        };
        this.tocLists = {
            market_mapper: "list-market-mapper",
            audience_profiler: "list-audience-profiler",
            angle_hook: "list-angle-hook",
            hook: "list-hook",
            ads_copy: "list-ads-copy",
        };
        const result = this._super(...arguments);
        this._initTocSync();
        this._injectClearButtons();
        return result;
    },
    _initTocSync() {
        this.tocRoot = document.querySelector("#toc .adsuhu-toc");
        if (!this.tocRoot) {
            return;
        }
        this._refreshTocTargets();
        this._bindTocSync();
        this._updateActiveToc();
    },
    _refreshTocTargets() {
        this.tocLinks = Array.from(this.tocRoot.querySelectorAll('a[href^="#"]'));
        this.tocSections = this.tocLinks
            .map((link) => {
                const id = link.getAttribute("href")?.slice(1) || "";
                const section = id ? document.getElementById(id) : null;
                return section ? { id, link, section } : null;
            })
            .filter(Boolean);
    },
    _bindTocSync() {
        if (this._tocScrollHandler) {
            return;
        }
        this._tocScrollHandler = () => {
            if (this._tocSyncRaf) {
                return;
            }
            this._tocSyncRaf = requestAnimationFrame(() => {
                this._tocSyncRaf = null;
                this._updateActiveToc();
            });
        };
        window.addEventListener("scroll", this._tocScrollHandler, { passive: true });
        window.addEventListener("resize", this._tocScrollHandler);
        this.tocRoot.addEventListener("click", () => {
            setTimeout(() => this._updateActiveToc(), 0);
        });
    },
    _updateActiveToc() {
        if (!this.tocSections || !this.tocSections.length) {
            return;
        }
        const scrollOffset = 96;
        let activeItem = this.tocSections[0];
        for (const item of this.tocSections) {
            const top = item.section.getBoundingClientRect().top - scrollOffset;
            if (top <= 0) {
                activeItem = item;
            } else {
                break;
            }
        }
        this.tocLinks.forEach((link) => link.classList.remove("is-active"));
        if (activeItem?.link) {
            let node = activeItem.link.parentElement;
            while (node) {
                if (node.tagName && node.tagName.toLowerCase() === "details") {
                    node.open = true;
                }
                node = node.parentElement;
            }
            activeItem.link.classList.add("is-active");
            activeItem.link.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
    },
    _setButtonState(button, loading) {
        if (!button) {
            return;
        }
        if (button.dataset.regenerate === "image_variants") {
            const generatingImage = document.getElementById("generating_image");
            if (generatingImage) {
                generatingImage.style.display = loading ? "block" : "none";
            }
        }
        if (loading) {
            button.dataset.originalText = button.innerText;
            button.innerText = "Regenerating...";
            button.disabled = true;
            button.classList.add("adsuhu-btn-loading");
        } else {
            button.innerText = button.dataset.originalText || "Regenerate";
            button.disabled = false;
            button.classList.remove("adsuhu-btn-loading");
        }
    },
    _appendTocItem(listId, title, sectionId) {
        if (!listId || !sectionId) {
            return;
        }
        const listEl = document.getElementById(listId);
        if (!listEl) {
            return;
        }
        const item = document.createElement("li");
        item.className = "list-group-item p-0";
        item.innerHTML = `
            <a class="list-group-item list-group-item-action border-0" href="#${sectionId}">
                ${title}
            </a>
        `;
        listEl.appendChild(item);
        this._refreshTocTargets();
        this._updateActiveToc();
    },
    _injectClearButtons() {
        const sections = document.querySelectorAll(".adsuhu-section");
        sections.forEach((section) => {
            const clearUrl = section.dataset.clearUrl;
            if (!clearUrl || section.querySelector(".js-clear-output")) {
                return;
            }
            const titleEl = section.querySelector(".adsuhu-section-title");
            const button = document.createElement("button");
            button.type = "button";
            button.className = "btn btn-sm btn-outline-danger ms-2 js-clear-output";
            button.title = "Clear output";
            button.innerHTML = `<i class="fa fa-trash"></i>`;
            if (titleEl) {
                titleEl.appendChild(button);
            } else {
                section.prepend(button);
            }
        });
    },
    async _onClearOutputClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const section = button.closest(".adsuhu-section");
        const clearUrl = section?.dataset?.clearUrl;
        if (!clearUrl) {
            return;
        }
        const confirmed = window.confirm("Clear this section content?");
        if (!confirmed) {
            return;
        }
        try {
            const response = await fetch(clearUrl, {
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
                throw new Error(errorText || "Failed to clear output.");
            }
            section.querySelectorAll(".adsuhu-content").forEach((el) => {
                el.innerHTML = "";
            });
        } catch (err) {
            console.error(err);
            alert(err.message || "Clear output failed.");
        }
    },
    async _pollRegenerateStatus({ regenerateType, recordId, section, withSection, button }) {
        const statusEndpointFactory = this.statusEndpoints[regenerateType];
        if (!statusEndpointFactory) {
            return;
        }

        
        const statusUrl = statusEndpointFactory(recordId);
        const maxAttempts = 200;
        const intervalMs = 5000;

        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            await new Promise((resolve) => setTimeout(resolve, intervalMs));
            const response = await fetch(statusUrl, {
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
                throw new Error(errorText || "Failed to fetch regenerate status.");
            }
            const json = await response.json();
            const result = json?.result || {};
            const status = result?.status || "idle";
            if (status === "failed") {
                throw new Error(result?.error || "Regenerate failed.");
            }
            if (status === "done") {
                const outputs = result?.result || [];
                if (section) {
                    const titleEl = section.querySelector(".adsuhu-section-title");
                    const modelTitle = titleEl ? titleEl.textContent.trim() : regenerateType || "Result";
                    const modelKey = regenerateType || "result";
                    const nextRegenerate = this.nextChain[regenerateType];
                    this._insertOutputSection({
                        section,
                        modelTitle,
                        modelKey,
                        outputs,
                        nextRegenerate,
                        sourceButton: button,
                        withSection
                    });
                }
                if (button) {
                    button.style.display = "none";
                    const viewEl = document.getElementById(`view-${regenerateType}-${recordId}`);
                    if (viewEl) {
                        viewEl.style.display = "block";
                    }
                }
                this._setButtonState(button, false);
                return;
            }
        }
        throw new Error("Regenerate timed out. Please try again.");
    },
    _insertOutputSection({ section, modelTitle, modelKey, outputs, nextRegenerate, sourceButton, withSection }) {
        if (!section) {
            return;
        }
        // const outputs = Array.isArray(outputHtml) ? outputHtml : [outputHtml];
        // console.log('outputs',outputs)

        const appendGeneratedSections = (containerId, items, prefix) => {
            if (!items || !Array.isArray(items)) {
                return;
            }
            const container = document.getElementById(containerId);
            if (!container) {
                return;
            }
            items.forEach((item, index) => {
                if (!item || !item.output_html) {
                    return;
                }
                const generated = document.createElement("section");
                generated.className = "adsuhu-section";
                const itemId = item.id ?? index;
                generated.id = `section-${prefix}-${itemId}`;
                generated.style.scrollMarginTop = "6rem";
                if (item.clear_url) {
                    generated.dataset.clearUrl = item.clear_url;
                }

                const titleEl = document.createElement("h2");
                titleEl.className = "adsuhu-section-title";
                titleEl.textContent = item.name || "Result";
                generated.appendChild(titleEl);

                const contentEl = document.createElement("div");
                contentEl.className = "adsuhu-content";
                contentEl.innerHTML = item.output_html || "";
                generated.appendChild(contentEl);

                container.appendChild(generated);
            });
            this._injectClearButtons();
        };

        outputs.forEach((output) => {
            let newSection

            if (withSection){ // normail sections
                newSection = document.createElement("section");
                newSection.className = "adsuhu-section";
                newSection.id = `section-${modelKey}`;
                newSection.style.scrollMarginTop = "6rem";

                const titleEl = document.createElement("h2");
                titleEl.className = "adsuhu-section-title";
                titleEl.textContent = output.name || "Result";
                newSection.appendChild(titleEl);

                const contentEl = document.createElement("div");
                contentEl.className = "adsuhu-content";
                contentEl.innerHTML = output.output_html || "";
                newSection.appendChild(contentEl);


                if (nextRegenerate) {
                    const nextTitle = nextRegenerate
                        .split("_")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ");

                    const nextButton = document.createElement("button");
                    nextButton.className = "btn btn-secondary js-regenerate";
                    nextButton.id = `regenerate_${nextRegenerate}`;
                    nextButton.dataset.id = sourceButton?.dataset?.id || "";
                    nextButton.dataset.regenerate = nextRegenerate;
                    nextButton.innerHTML = `<i class="fa fa-send me-1"></i> Generate ${nextTitle}`;
                    
                    const buttonWrap = document.createElement("div");
                    buttonWrap.className = "d-flex align-items-center justify-content-center";
                    buttonWrap.appendChild(nextButton);
                    newSection.appendChild(buttonWrap);
                }

                if (output.clear_url) {
                    newSection.dataset.clearUrl = output.clear_url;
                }
                this._appendTocItem(this.tocLists[modelKey], titleEl.textContent, newSection.id);            
                section.insertAdjacentElement("afterend", newSection);
                this._injectClearButtons();

                if (modelKey === "ads_copy") {
                    appendGeneratedSections("section-images", output.images, "img");
                    appendGeneratedSections("section-landing-page", output.lps, "lp");
                    appendGeneratedSections("section-video-script", output.videos, "vid");
                }
            } 
            else
            { //image 
                newSection = document.createElement("div");
                newSection.className="col-md-6 gap-2 mb-2"
                newSection.innerHTML = output.output_html || "";
                newSection.id = `section-${modelKey}`;

                section.appendChild(newSection)
                this._injectClearButtons();
            }

        });

    },
    async _onRegenerateClick(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const regenerateType = button.dataset.regenerate;
        const recordId = button.dataset.id;
        const endpointFactory = this.endpoints[regenerateType];
        console.log(regenerateType,recordId)
        if (!endpointFactory || !recordId) {
            return;
        }

        this._setButtonState(button, true);
        let usesPolling = false;
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
            const result = json?.result;
            const targetSectionId = button.dataset.targetSection || "";
            const withSection = button.dataset.regenerate === "image_variants"? false : true;
            // console.log('withSection',withSection)
            const section = targetSectionId
                ? document.getElementById(targetSectionId)
                : button.closest(".adsuhu-section");

            console.log('section',section)
            const statusEndpointFactory = this.statusEndpoints[regenerateType];
            if (statusEndpointFactory) {
                usesPolling = true;
                await this._pollRegenerateStatus({
                    regenerateType,
                    recordId,
                    section,
                    withSection,
                    button,
                });
                return;
            }
            const outputs = Array.isArray(result) ? result : [];
            if (section) {
                const titleEl = section.querySelector(".adsuhu-section-title");
                const modelTitle = titleEl ? titleEl.textContent.trim() : regenerateType || "Result";
                const modelKey = regenerateType || "result";
                // const nextRegenerate = button.dataset.nextRegenerate || "";
                const nextRegenerate = this.nextChain[regenerateType]
                console.log('nextRegenerate',nextRegenerate)
                this._insertOutputSection({
                    section,
                    modelTitle,
                    modelKey,
                    outputs,
                    nextRegenerate,
                    sourceButton: button,
                    withSection
                });
                button.style.display = "none";
                const viewEl = document.getElementById(`view-${regenerateType}-${recordId}`);
                // console.log('viewEl', viewEl)
                if (viewEl) {
                    viewEl.style.display = "block";
                }
            }
        } catch (err) {
            console.error(err);
            alert(err.message || "Regenerate failed.");
        } finally {
            if (!usesPolling) {
                this._setButtonState(button, false);
            }
        }
    },
});
