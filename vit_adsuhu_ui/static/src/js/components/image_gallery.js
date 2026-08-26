/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

import { SocialPoster } from "./social_poster";
import { GenerateButton } from "./generate_button";

export class ImageGallery extends Component {
    static template = "vit_adsuhu_ui.ImageGallery";
    static components = { SocialPoster, GenerateButton };
    static props = {
        card: { type: Object },
        onDone: { type: Function, optional: true },
    };

    setup() {
        this.state = useState({ activeImage: null, copied: "" });
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

    openPoster(image) {
        this.state.activeImage = image;
    }

    closePoster() {
        this.state.activeImage = null;
    }
}
