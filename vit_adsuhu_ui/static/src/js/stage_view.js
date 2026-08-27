/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

import { ImageGallery } from "./image_gallery";
import { GenerateButton } from "./generate_button";


export class StageView extends Component {
    static template = "vit_adsuhu_ui.StageView";
    static components = { ImageGallery, GenerateButton };
    static props = {
        stage: { type: Object },
        hasPrev: { type: Boolean },
        hasNext: { type: Boolean },
        onPrev: { type: Function },
        onNext: { type: Function },
        onRefresh: { type: Function },
    };

    setup() {
        this.state = useState({
            copied: "",
            editingBlock: null,
            editText: "",
            saving: false,
            collapsed: {},
        });
    }

    get stage() {
        return this.props.stage;
    }

    isCollapsed(block) {
        return !!this.state.collapsed[block.edit_field + "-" + block.edit_id];
    }

    toggleCollapse(block) {
        this.state.collapsed[block.edit_field + "-" + block.edit_id] = !this.state.collapsed[
            block.edit_field + "-" + block.edit_id
        ];
    }

    isCardCollapsed(card) {
        if (!card || !card.content || !card.content.edit_model) {
            return false;
        }
        return !!this.state.collapsed["__card_" + card.content.edit_id];
    }

    toggleCardCollapse(card) {
        this.state.collapsed["__card_" + card.content.edit_id] = !this.state.collapsed[
            "__card_" + card.content.edit_id
        ];
    }

    copyText(text, key) {
        navigator.clipboard?.writeText(text || "");
        this.state.copied = key;
        setTimeout(() => {
            if (this.state.copied === key) {
                this.state.copied = "";
            }
        }, 1500);
    }

    copyBlock(ev) {
        const block = ev.currentTarget.closest(".o_adsuhu_block, .o_adsuhu_prose_wrap");
        if (!block) {
            return;
        }
        const prose = block.querySelector(".o_adsuhu_prose");
        if (!prose) {
            return;
        }
        const text = prose.innerText || prose.textContent || "";
        this.copyText(text, "block-" + (block.dataset.key || ""));
    }

    copyCard(ev) {
        const card = ev.currentTarget.closest(".o_adsuhu_card");
        if (!card) {
            return;
        }
        const blocks = card.querySelectorAll(".o_adsuhu_prose");
        const parts = [];
        blocks.forEach((p) => parts.push(p.innerText || p.textContent || ""));
        this.copyText(parts.join("\n\n"), "card-" + card.dataset.cardKey);
    }

    startEdit(block) {
        this.state.editingBlock = block.edit_field + "-" + block.edit_id;
        this.state.editText = block.edit_raw || "";
    }

    cancelEdit() {
        this.state.editingBlock = null;
        this.state.editText = "";
    }

    isEditing(block) {
        return this.state.editingBlock === block.edit_field + "-" + block.edit_id;
    }

    async saveEdit(block) {
        if (this.state.saving) {
            return;
        }
        this.state.saving = true;
        try {
            const csrf = document.getElementById("adsuhu-csrf-token")?.value || "";
            const response = await fetch("/adsui/save", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrf,
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    model: block.edit_model,
                    id: block.edit_id,
                    values: { [block.edit_field]: this.state.editText },
                }),
            });
            const json = await response.json();
            const result = json.result || json;
            if (result.error) {
                throw new Error(result.error);
            }
            this.state.editingBlock = null;
            this.state.editText = "";
            this.props.onRefresh?.();
        } catch (err) {
            console.error("Save failed:", err);
        } finally {
            this.state.saving = false;
        }
    }
}
