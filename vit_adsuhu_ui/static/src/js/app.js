/** @odoo-module **/

import { Component, markup, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

import { Stepper } from "./stepper";
import { StageView } from "./stage_view";

export const STAGE_ORDER = [
    "product",
    "pva",
    "market",
    "audience",
    "angle",
    "ads",
    "creatives",
];

export function cardHasContent(card) {
    const content = card.content || {};
    if ((content.html || "").trim()) {
        return true;
    }
    if ((content.blocks || []).some((b) => (b.html || "").trim())) {
        return true;
    }
    return (card.images || []).length > 0;
}

export function stageStatus(stage) {
    if (!stage.cards || !stage.cards.length) {
        return "blocked";
    }
    let anyReady = false;
    for (const card of stage.cards) {
        if (card.status === "processing") {
            return "processing";
        }
        if (card.status === "failed") {
            return "failed";
        }
        if (!cardHasContent(card)) {
            anyReady = true;
        }
    }
    return anyReady ? "ready" : "done";
}

export class App extends Component {
    static template = "vit_adsuhu_ui.App";
    static components = { Stepper, StageView };
    static props = { analysis_id: { type: Number, optional: true } };

    setup() {
        this.busService = useService("bus_service");
        this.state = useState({
            loading: true,
            error: "",
            analysis: {},
            stages: [],
            current: "product",
        });
        this._refreshTimer = null;
        this._pollTimer = null;
        onMounted(() => this._mount());
        onWillUnmount(() => {
            if (this._unsubscribe) {
                this._unsubscribe();
            }
            if (this.channel) {
                try {
                    this.busService.deleteChannel(this.channel);
                } catch (err) {
                    // ignore
                }
            }
            if (this._refreshTimer) {
                clearTimeout(this._refreshTimer);
            }
            if (this._pollTimer) {
                clearInterval(this._pollTimer);
            }
        });
    }

    async _mount() {
        this.channel = `adsuhu.analysis.${this.props.analysis_id}`;
        try {
            await this.busService.addChannel(this.channel);
        } catch (err) {
            // bus may be unavailable; the polling fallback covers it
        }
        this._unsubscribe = this.busService.subscribe(this.channel, () =>
            this.refresh()
        );
        this._pollTimer = setInterval(() => {
            if (this._anyProcessing()) {
                this.refresh();
            }
        }, 5000);
        await this.refresh();
    }

    _csrf() {
        const el = document.getElementById("adsuhu-csrf-token");
        return el ? el.value : (odoo && odoo.csrf_token) || "";
    }

    refresh() {
        clearTimeout(this._refreshTimer);
        this._refreshTimer = setTimeout(() => this._doRefresh(), 250);
    }

    async _doRefresh() {
        try {
            const response = await fetch(`/adsui/data/${this.props.analysis_id}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this._csrf(),
                },
                credentials: "same-origin",
                body: JSON.stringify({}),
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to load analysis.");
            }
            const data = await response.json();
            const payload = data.result || data;
            if (payload.error) {
                throw new Error(payload.error);
            }
            this.state.analysis = payload.analysis || {};
            this.state.stages = payload.stages || [];
            this.state.loading = false;
            this.state.error = "";
        } catch (err) {
            this.state.error = err.message || "Failed to load analysis.";
            this.state.loading = false;
        }
    }

    _anyProcessing() {
        return this.state.stages.some((s) =>
            (s.cards || []).some((c) => c.status === "processing")
        );
    }

    get stages() {
        return this.state.stages.map((s) => ({
            ...s,
            status: stageStatus(s),
            cards: (s.cards || []).map((c) => {
                const content = c.content || {};
                return {
                    ...c,
                    hasContent: cardHasContent(c),
                    content: {
                        ...content,
                        html: content.html ? markup(content.html) : "",
                        blocks: (content.blocks || []).map((b) => ({
                            ...b,
                            html: b.html ? markup(b.html) : "",
                        })),
                    },
                };
            }),
        }));
    }

    get currentStage() {
        return this.stages.find((s) => s.key === this.state.current);
    }

    get currentIndex() {
        return STAGE_ORDER.indexOf(this.state.current);
    }

    get prevStage() {
        const i = this.currentIndex - 1;
        return i >= 0 ? STAGE_ORDER[i] : "";
    }

    get nextStage() {
        const i = this.currentIndex + 1;
        return i < STAGE_ORDER.length ? STAGE_ORDER[i] : "";
    }

    onSelectStage(key) {
        this.state.current = key;
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    goNext() {
        if (this.nextStage) {
            this.onSelectStage(this.nextStage);
        }
    }

    goPrev() {
        if (this.prevStage) {
            this.onSelectStage(this.prevStage);
        }
    }
}

registry.category("public_components").add("vit_adsuhu_ui.App", App);
