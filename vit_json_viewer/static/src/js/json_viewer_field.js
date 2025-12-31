/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TextField } from "@web/views/fields/text/text_field";
import { onMounted, onPatched, useRef } from "@odoo/owl";

const escapeHtml = (value = "") =>
    value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");

class JSONViewerField extends TextField {
    static template = "vit_json_viewer.JSONViewerField";

    setup() {
        super.setup();
        this.viewerRef = useRef("viewer");
        onMounted(() => this.renderPreview());
        onPatched(() => this.renderPreview());
    }

    getRawValue() {
        const { value, record, name } = this.props;
        if (value !== undefined && value !== null) {
            return value;
        }
        return record?.data?.[name];
    }

    formatValue(value) {
        if (value === undefined || value === null) {
            return "";
        }
        if (typeof value === "string") {
            const trimmed = value.trim();
            if (!trimmed) {
                return "";
            }
            try {
                return JSON.stringify(JSON.parse(trimmed), null, 2);
            } catch {
                return trimmed;
            }
        }
        try {
            return JSON.stringify(value, null, 2);
        } catch {
            return String(value);
        }
    }

    syntaxHighlight(jsonString) {
        // Tokenize the raw string and escape each chunk to keep HTML safe.
        const pattern =
            /("(?:\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*")(\\s*:)?|\\b(?:true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?/g;
        let result = "";
        let lastIndex = 0;
        let match;
        while ((match = pattern.exec(jsonString)) !== null) {
            const [token, maybeString, maybeKey] = match;
            result += escapeHtml(jsonString.slice(lastIndex, match.index));
            let cls = "o_json_number";
            let style = "color:#f59e0b";
            if (maybeString !== undefined) {
                const isKey = Boolean(maybeKey) || token.trim().endsWith(":");
                if (isKey) {
                    cls = "o_json_key";
                    style = "color:#f87171";
                } else {
                    cls = "o_json_string";
                    style = "color:#22c55e";
                }
            } else if (token === "true" || token === "false") {
                cls = "o_json_boolean";
                style = "color:#60a5fa";
            } else if (token === "null") {
                cls = "o_json_null";
                style = "color:#f472b6";
            }
            result += `<span class="${cls}" style="${style}">${escapeHtml(token)}</span>`;
            lastIndex = pattern.lastIndex;
        }
        result += escapeHtml(jsonString.slice(lastIndex));
        return result;
    }

    renderPreview() {
        const target = this.viewerRef?.el;
        if (!target) {
            return;
        }
        const formatted = this.formatValue(this.getRawValue());
        if (!formatted) {
            target.textContent = "";
            target.classList.add("o_json_viewer_empty");
            return;
        }
        target.classList.remove("o_json_viewer_empty");
        target.innerHTML = this.syntaxHighlight(formatted);
    }
}

export const jsonViewerField = {
    component: JSONViewerField,
    supportedTypes: ["text"],
};

registry.category("fields").add("json_viewer", jsonViewerField);
