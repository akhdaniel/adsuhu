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
        this.state = useState({ copied: "" });
    }

    get stage() {
        return this.props.stage;
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
        const prose = card.querySelector(".o_adsuhu_prose");
        const blocks = card.querySelectorAll(".o_adsuhu_prose");
        const parts = [];
        blocks.forEach((p) => parts.push(p.innerText || p.textContent || ""));
        this.copyText(parts.join("\n\n"), "card-" + card.dataset.cardKey);
    }
}
