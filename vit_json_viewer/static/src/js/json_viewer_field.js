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
        const renderValue = (val, indent = 0) => {
            const pad = "  ".repeat(indent);
            const nextPad = "  ".repeat(indent + 1);
            if (Array.isArray(val)) {
                if (!val.length) {
                    return "[]";
                }
                const items = val.map((item, index) => {
                    const comma = index < val.length - 1 ? "," : "";
                    return `${nextPad}${renderValue(item, indent + 1)}${comma}`;
                });
                return `[\n${items.join("\n")}\n${pad}]`;
            }
            if (val && typeof val === "object") {
                const entries = Object.entries(val);
                if (!entries.length) {
                    return "{}";
                }
                const items = entries.map(([key, value], index) => {
                    const comma = index < entries.length - 1 ? "," : "";
                    const renderedKey = `<span class="o_json_key" style="color:#f87171">"${escapeHtml(key)}"</span>`;
                    return `${nextPad}${renderedKey}: ${renderValue(value, indent + 1)}${comma}`;
                });
                return `{\n${items.join("\n")}\n${pad}}`;
            }
            if (typeof val === "string") {
                return `<span class="o_json_string" style="color:#22c55e">"${escapeHtml(val)}"</span>`;
            }
            if (typeof val === "number") {
                return `<span class="o_json_number" style="color:#f59e0b">${val}</span>`;
            }
            if (typeof val === "boolean") {
                return `<span class="o_json_boolean" style="color:#60a5fa">${val}</span>`;
            }
            if (val === null) {
                return `<span class="o_json_null" style="color:#f472b6">null</span>`;
            }
            return escapeHtml(String(val));
        };

        try {
            const parsed = JSON.parse(jsonString);
            return renderValue(parsed, 0);
        } catch {
            return escapeHtml(jsonString);
        }
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
