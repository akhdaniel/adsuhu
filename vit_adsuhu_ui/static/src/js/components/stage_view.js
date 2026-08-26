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
}
