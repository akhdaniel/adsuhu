/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

const TERMINAL = new Set(["done", "failed"]);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export class GenerateButton extends Component {
    static template = "vit_adsuhu_ui.GenerateButton";
    static props = {
        action: { type: Object },
        hasContent: { type: Boolean },
        onDone: { type: Function, optional: true },
        disabled: { type: Boolean, optional: true },
        compact: { type: Boolean, optional: true },
    };

    setup() {
        this.state = useState({ started: false, error: "" });
    }

    get label() {
        return this.props.hasContent ? "Regenerate" : "Generate";
    }

    get loading() {
        return this.state.started || this.props.action.status === "processing";
    }

    get failed() {
        return !this.loading && this.props.action.status === "failed";
    }

    _csrf() {
        const el = document.getElementById("adsuhu-csrf-token");
        return el ? el.value : (odoo && odoo.csrf_token) || "";
    }

    async onClick() {
        if (this.loading || this.props.disabled) {
            return;
        }
        this.state.error = "";
        this.state.started = true;
        try {
            const response = await fetch(this.props.action.gen_route, {
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
                throw new Error(text || "Generation failed to start.");
            }
            this._pollStatus();
        } catch (err) {
            this.state.error = err.message || "Generation failed to start.";
            this.state.started = false;
        }
    }

    async _pollStatus() {
        const { status_route } = this.props.action;
        if (!status_route) {
            return;
        }
        for (let i = 0; i < 120; i++) {
            await sleep(2500);
            try {
                const response = await fetch(status_route, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": this._csrf(),
                    },
                    credentials: "same-origin",
                    body: JSON.stringify({}),
                });
                const json = await response.json();
                const status = json?.status || "idle";
                if (TERMINAL.has(status)) {
                    if (status === "failed") {
                        this.state.error = json?.error || "Generation failed.";
                    }
                    this.state.started = false;
                    this.props.onDone?.();
                    return;
                }
                if (status === "processing") {
                    this.props.onDone?.();
                }
            } catch (err) {
                // keep polling; network hiccups are common
            }
        }
        this.state.started = false;
    }
}
