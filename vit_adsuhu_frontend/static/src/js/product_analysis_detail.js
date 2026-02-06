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
            ads_copy: (id) => `/regenerate_status/hook/${id}`,
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

        const nextStep = button.dataset.regenerate

        console.log('nextStep', nextStep)
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

            $("#loading-skeleton-"+nextStep).show()
        } else {
            button.innerText = button.dataset.originalText || "Regenerate";
            button.disabled = false;
            button.classList.remove("adsuhu-btn-loading");
            $("#loading-skeleton-"+nextStep).hide()
        }
    },
    _titleizeKey(value) {
        if (!value) {
            return "";
        }
        return value
            .toString()
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
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
    async _pollRegenerateStatus({ regenerateType, recordId, /*section, withSection,*/ button }) {
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
                // window.location.reload();
                // return;
                
                const outputs = result?.result || [];

                
                this._insertOutputSection({
                    recordId,
                    outputs,
                    sourceButton: button,
                });

                //hide generaet button
                if (button) {
                    button.style.display = "none";
                }

                
                
                this._setButtonState(button, false);
                return;
                
            }
        }
        throw new Error("Regenerate timed out. Please try again.");
    },
    _insertOutputSection({ recordId, outputs, sourceButton, container, nestedKey }) {
        if (!outputs || !Array.isArray(outputs) || outputs.length === 0) {
            return;
        }

        const isWorkflow = outputs?.[0]?.current_step !== undefined;
        if (!isWorkflow) {
            const target = container;
            if (!target) {
                return;
            }
            const prefix = nestedKey || "result";
            outputs.forEach((item, index) => {
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

                target.appendChild(generated);
            });
            this._injectClearButtons();
            return;
        }

        const tocMap = {
            market_map_analysis: "market_mapper",
            audience_profile_analysis: "audience_profiler",
            angle_hook: "angle_hook",
            ads_copy: "ads_copy",
        };
        
        let newSection
        const currentStepSection = $('#section-'+outputs[0].current_step)
        const parentSection = document.createElement("div");
        const prev_step = outputs[0].prev_step=='hook'?'angle_hook':outputs[0].prev_step;
        parentSection.id = `${prev_step}-${outputs[0].current_step}-${recordId}`;
        console.log('parentSection', parentSection);
        currentStepSection.append(parentSection);

        [...outputs].forEach((output) => {
            
            const prevStep = output.prev_step
            const currentStep = output.current_step
            const nextStep = output.next_step
            const withSection = output.with_section===false ? false: true

            if (withSection){ // normail sections
                newSection = document.createElement("section");
                newSection.className = "adsuhu-section";

                const outputId = output?.id ?? "";
                newSection.id = `section-${currentStep}-${outputId}`;
                newSection.style.scrollMarginTop = "6rem";

                const titleEl = document.createElement("h2");
                titleEl.className = "adsuhu-section-title";
                titleEl.textContent = output.name;
                newSection.appendChild(titleEl);

                const contentEl = document.createElement("div");
                contentEl.className = "adsuhu-content";
                contentEl.innerHTML = output.output_html || "";
                newSection.appendChild(contentEl);

                const withNextButton = output.with_next_button === false? false: true
                const buttonWrap = document.createElement("div");
                
                // generate back button
                const backTitle = output.back_title
                if (backTitle){
                    const backButton = document.createElement("a");
                    backButton.className = "btn btn-secondary";
                    backButton.href = `#section-${output.prev_step}-${recordId}`;
                    backButton.innerHTML = `<i class="fa fa-arrow-left me-1"></i> Back to ${backTitle}`;
                    buttonWrap.appendChild(backButton);
                }
                
                // generate next button
                if (withNextButton && nextStep ) {
                    const nextTitle = this._titleizeKey(nextStep);

                    buttonWrap.className = "d-flex align-items-center justify-content-center";

                    // generate next button
                    const nextButton = document.createElement("button");
                    nextButton.className = "btn btn-secondary js-regenerate";
                    nextButton.id = `regenerate_${nextStep}`;
                    nextButton.dataset.id = output.id;
                    nextButton.dataset.regenerate = nextStep;
                    nextButton.style.display = (currentStep=='angle_hook'?'none':'block')
                    nextButton.innerHTML = `<i class="fa fa-send me-1"></i> me=${output.id} Generate ${nextTitle}`;
                    buttonWrap.appendChild(nextButton);
                    
                   
                    //append button
                    newSection.appendChild(buttonWrap);
                    
                }

                // view next button
                const viewTargetButton = document.createElement("a");
                const viewTargetTitle = nextStep;
                viewTargetButton.id = `view-target-${nextStep}-${output.id}`;
                viewTargetButton.className = "btn btn-primary ms-2";
                viewTargetButton.href = `#${currentStep}-${nextStep}-${output.id}`;
                viewTargetButton.style.display = (currentStep=='angle_hook'?'block':'none')
                viewTargetButton.innerHTML = `<i class="fa fa-send me-1"></i> View ${viewTargetTitle}`;
                buttonWrap.appendChild(viewTargetButton);

                //append section
                $(parentSection).append(newSection);

                if (output.clear_url) {
                    newSection.dataset.clearUrl = output.clear_url;
                }

                //add toc
                const tocKey = tocMap[currentStep] || currentStep;
                this._appendTocItem(this.tocLists[tocKey], titleEl.textContent, newSection.id);            

                this._injectClearButtons();


                console.log('currentStep', currentStep, output)

                if (currentStep === "ads_copy") {
                    this._insertOutputSection({
                        recordId: output.id,
                        outputs: output.images || [],
                        sourceButton,
                        container: document.getElementById("section-images"),
                        nestedKey: "img",
                    });
                    this._insertOutputSection({
                        recordId: output.id,
                        outputs: output.lps || [],
                        sourceButton,
                        container: document.getElementById("section-landing-page"),
                        nestedKey: "lp",
                    });
                    this._insertOutputSection({
                        recordId: output.id,
                        outputs: output.videos || [],
                        sourceButton,
                        container: document.getElementById("section-video-script"),
                        nestedKey: "vid",
                    });
                }
                if (currentStep === "angle_hook") {
                    this._insertOutputSection({
                        recordId: output.id,
                        outputs: output.hooks || [],
                        sourceButton,
                        container: document.getElementById("section-hook"),
                        nestedKey: "hook",
                    });
                }


                // show View button after next process done. 
                // eg: Maket Map -> AP 12 (generate angle) -> Angles
                //           show view-target-ap-angles-12 <- done
                const viewTragetButton = `#view-target-${output.current_step}-${output.record_id}`;
                console.log(viewTragetButton);
                $(viewTragetButton).show()
            } 
            else
            { //image 
                newSection = document.createElement("div");
                newSection.className="col-md-6 gap-2 mb-2"
                newSection.innerHTML = output.output_html || "";
                newSection.id = `section-${currentStep}`;

                $(parentSection).append(newSection);
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
            
            const statusEndpointFactory = this.statusEndpoints[regenerateType];
            if (statusEndpointFactory) {
                usesPolling = true;
                await this._pollRegenerateStatus({
                    regenerateType,
                    recordId,
                    button,
                });
                return;
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
