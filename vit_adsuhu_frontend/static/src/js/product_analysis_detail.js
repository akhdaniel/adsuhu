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
            market_mapper: (id) => `/product_analysis/market_mapper/${id}/regenerate`,
            audience_profiler: (id) => `/market_mapper/${id}/audience_profiler/regenerate`,
            angle_hook: (id) => `/audience_profiler/${id}/angle_hook/regenerate`,
            // hook: (id) => `/angle_hook/${id}/hook/regenerate`,
            ads_copy: (id) => `/hook/${id}/ads_copy/regenerate`,
            image_variants: (id) => `/image_generator/${id}/image_variant/regenerate`,
        };
        this.nextChain = {
            product_value_analysis: "market_mapper",
            market_mapper: "audience_profiler",
            audience_profiler: "angle_hook",
            angle_hook: "hook",
            hook: "ads_copy",
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
        } else {
            button.innerText = button.dataset.originalText || "Regenerate";
            button.disabled = false;
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
    _insertOutputSection({ section, modelTitle, modelKey, outputs, nextModel, sourceButton, withSection }) {
        if (!section) {
            return;
        }
        // const outputs = Array.isArray(outputHtml) ? outputHtml : [outputHtml];
        // console.log('outputs',outputs)

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

                if (nextModel) {
                    const nextTitle = nextModel
                        .split("_")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ");
                    const nextButton = document.createElement("button");
                    nextButton.className = "btn btn-secondary js-regenerate";
                    nextButton.id = `regenerate_${nextModel}`;
                    nextButton.dataset.id = sourceButton?.dataset?.id || "";
                    nextButton.dataset.regenerate = nextModel;
                    nextButton.dataset.nextModel = this.nextChain[nextModel] || "";
                    nextButton.innerHTML = `<i class="fa fa-send me-1"></i> Analyze ${nextTitle}`;
                    const buttonWrap = document.createElement("div");
                    buttonWrap.className = "d-flex align-items-center justify-content-center";
                    buttonWrap.appendChild(nextButton);
                    newSection.appendChild(buttonWrap);
                }

                this._appendTocItem(this.tocLists[modelKey], titleEl.textContent, newSection.id);            
                section.insertAdjacentElement("afterend", newSection);

            } 
            else
            { //image 
                newSection = document.createElement("div");
                newSection.className="col-md-6 gap-2 mb-2"
                newSection.innerHTML = output.output_html || "";
                newSection.id = `section-${modelKey}`;

                section.appendChild(newSection)
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
            const outputs = json?.result || [];
            const targetSectionId = button.dataset.targetSection || "";
            const withSection = button.dataset.regenerate === "image_variants"? false : true;
            // console.log('withSection',withSection)
            const section = targetSectionId
                ? document.getElementById(targetSectionId)
                : button.closest(".adsuhu-section");

            console.log('section',section)
            if (section) {
                const titleEl = section.querySelector(".adsuhu-section-title");
                const modelTitle = titleEl ? titleEl.textContent.trim() : regenerateType || "Result";
                const modelKey = regenerateType || "result";
                const nextModel = button.dataset.nextModel || "";
                this._insertOutputSection({
                    section,
                    modelTitle,
                    modelKey,
                    outputs,
                    nextModel,
                    sourceButton: button,
                    withSection
                });
                button.style.display = "none";
                const viewEl = document.getElementById(`view-${regenerateType}-${recordId}`);
                console.log('viewEl', viewEl)
                if (viewEl) {
                    viewEl.style.display = "block";
                }
            }
        } catch (err) {
            console.error(err);
            alert(err.message || "Regenerate failed.");
        } finally {
            this._setButtonState(button, false);
        }
    },
});
