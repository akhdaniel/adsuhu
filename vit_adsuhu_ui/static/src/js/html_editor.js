/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { loadWysiwygFromTextarea } from "@web_editor/js/frontend/loadWysiwygFromTextarea";

export class HtmlEditor extends Component {
    static template = "vit_adsuhu_ui.HtmlEditor";
    static props = {
        value: { type: String, optional: true },
        register: { type: Function },
    };

    setup() {
        this.textareaRef = useRef("textarea");
        this._wysiwyg = null;
        onMounted(() => this._init());
    }

    async _init() {
        const textarea = this.textareaRef.el;
        if (!textarea) {
            return;
        }
        try {
            this._wysiwyg = await loadWysiwygFromTextarea(this, textarea, {
                value: this.props.value || "",
            });
            this.props.register(() => {
                try {
                    return this._wysiwyg.getValue();
                } catch (e) {
                    return textarea.value || "";
                }
            });
        } catch (err) {
            console.error("Failed to init WYSIWYG editor:", err);
            this.props.register(() => textarea.value || "");
        }
    }
}
