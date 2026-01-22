/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { TextField, textField } from "@web/views/fields/text/text_field";
import { markup, onMounted, onPatched, onWillUnmount, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const escapeHtml = (text) => {
    if (!text) {
        return "";
    }
    return text.replace(/[&<>"']/g, (char) => {
        switch (char) {
            case "&":
                return "&amp;";
            case "<":
                return "&lt;";
            case ">":
                return "&gt;";
            case '"':
                return "&quot;";
            case "'":
                return "&#39;";
            default:
                return char;
        }
    });
};

const applyInlineFormatting = (text) => {
    let html = escapeHtml(text);
    html = html.replace(/!\[(.+?)\]\((.+?)\)/g, '<img src="$2" alt="$1" width="50%"/>');
    html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noreferrer noopener">$1</a>');
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");
    html = html.replace(/~~(.+?)~~/g, "<del>$1</del>");
    html = html.replace(/\*(?!\*)([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/_(?!_)([^_]+)_/g, "<em>$1</em>");
    // Allow explicit <br> tokens for line breaks (escaped earlier).
    html = html.replace(/&lt;br\s*\/?&gt;/gi, "<br/>");
    return html;
};

const renderSimpleMarkdown = (value) => {
    const htmlParts = [];
    let paragraphBuffer = [];
    let codeBuffer = [];
    let inCodeBlock = false;
    let inTable = false;
    let listRoot = null;
    let indentStack = [];
    let itemsStack = [];
    let tableBuffer = null;
    let tableAlignments = [];

    const resetTable = () => {
        tableBuffer = null;
        tableAlignments = [];
        inTable = false;
    };

    const flushParagraph = () => {
        if (!paragraphBuffer.length) {
            return;
        }
        const paragraph = paragraphBuffer.map((line) => applyInlineFormatting(line)).join("<br/>");
        htmlParts.push(`<p>${paragraph}</p>`);
        paragraphBuffer = [];
    };

    const flushList = () => {
        if (!listRoot || !listRoot.length) {
            listRoot = null;
            indentStack = [];
            itemsStack = [];
            return;
        }
        const renderItems = (items) =>
            items
                .map((item) => {
                    const children = item.children.length ? `<ul>${renderItems(item.children)}</ul>` : "";
                    return `<li>${item.content}${children}</li>`;
                })
                .join("");
        htmlParts.push(`<ul>${renderItems(listRoot)}</ul>`);
        listRoot = null;
        indentStack = [];
        itemsStack = [];
    };

    const ensureListRoot = () => {
        if (listRoot) {
            return;
        }
        listRoot = [];
        indentStack = [-1];
        itemsStack = [listRoot];
    };

    const addListItem = (indentation, content) => {
        ensureListRoot();
        const normalizedIndent = indentation.replace(/\t/g, "    ").length;
        while (indentStack.length && normalizedIndent <= indentStack[indentStack.length - 1]) {
            indentStack.pop();
            itemsStack.pop();
        }
        const parentItems = itemsStack[itemsStack.length - 1];
        const newItem = { content: applyInlineFormatting(content.trim()), children: [] };
        parentItems.push(newItem);
        indentStack.push(normalizedIndent);
        itemsStack.push(newItem.children);
    };

    const flushCode = () => {
        if (!codeBuffer.length) {
            return;
        }
        const code = escapeHtml(codeBuffer.join("\n"));
        htmlParts.push(`<pre><code>${code}</code></pre>`);
        codeBuffer = [];
    };

    const splitTableRow = (line) => line.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());

    const parseAlignments = (line) => {
        const cells = splitTableRow(line);
        if (!cells.length) {
            return null;
        }
        const aligns = [];
        for (const cell of cells) {
            const trimmed = cell.trim();
            if (!/^:?-{3,}:?$/.test(trimmed)) {
                return null;
            }
            if (trimmed.startsWith(":") && trimmed.endsWith(":")) {
                aligns.push("center");
            } else if (trimmed.endsWith(":")) {
                aligns.push("right");
            } else {
                aligns.push("left");
            }
        }
        return aligns;
    };

    const getTableStart = (currentLine, separatorLine) => {
        if (!separatorLine || !currentLine.includes("|")) {
            return null;
        }
        const headerCells = splitTableRow(currentLine);
        if (headerCells.length < 2) {
            return null;
        }
        const alignments = parseAlignments(separatorLine);
        if (!alignments || alignments.length !== headerCells.length) {
            return null;
        }
        return { headerCells, alignments };
    };

    const addTableRowCells = (cells) => {
        if (!cells.length) {
            return;
        }
        if (!tableBuffer) {
            tableBuffer = [];
        }
        tableBuffer.push(cells.map((cell) => applyInlineFormatting(cell)));
    };

    const flushTable = () => {
        if (!tableBuffer?.length) {
            resetTable();
            return;
        }
        const [headers, ...rows] = tableBuffer;
        const renderRow = (cells, tagName) =>
            cells
                .map((cell, index) => {
                    const align = tableAlignments[index];
                    const alignAttr = align ? ` align="${align}"` : "";
                    return `<${tagName}${alignAttr}>${cell}</${tagName}>`;
                })
                .join("");
        const body = rows.map((row) => `<tr>${renderRow(row, "td")}</tr>`).join("");
        const bodyHtml = body ? `<tbody>${body}</tbody>` : "";
        htmlParts.push(`<div class="table-responsive"><table class="table table-striped table-hover"><thead><tr style="color:#999">${renderRow(headers, "th")}</tr></thead>${bodyHtml}</table></div></br>`);
        resetTable();
    };

    const lines = value.split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith("```")) {
            if (inCodeBlock) {
                flushCode();
            } else {
                flushParagraph();
                flushList();
                flushTable();
            }
            inCodeBlock = !inCodeBlock;
            continue;
        }

        if (inCodeBlock) {
            codeBuffer.push(line);
            continue;
        }

        const trimmed = line.trim();

        if (inTable) {
            const cells = splitTableRow(line);
            if (line.includes("|") && cells.length > 1) {
                addTableRowCells(cells);
                continue;
            }
            flushTable();
            i -= 1;
            continue;
        }

        if (!trimmed) {
            flushParagraph();
            flushList();
            flushTable();
            continue;
        }

        const potentialTableStart = getTableStart(line, lines[i + 1]);
        if (potentialTableStart) {
            flushParagraph();
            flushList();
            tableAlignments = potentialTableStart.alignments;
            addTableRowCells(potentialTableStart.headerCells);
            inTable = true;
            i += 1; // Skip the separator line
            continue;
        }

        const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
        if (headingMatch) {
            flushParagraph();
            flushList();
            flushTable();
            htmlParts.push(
                `<h${headingMatch[1].length}>${applyInlineFormatting(headingMatch[2])}</h${headingMatch[1].length}>`
            );
            continue;
        }

        if (/^\s*[-*]\s+/.test(line)) {
            flushParagraph();
            const match = line.match(/^(\s*)([-*])\s+(.*)$/);
            if (match) {
                addListItem(match[1], match[3]);
            }
            continue;
        }

        if (/^>+\s+/.test(line)) {
            flushParagraph();
            flushList();
            flushTable();
            htmlParts.push(`<blockquote>${applyInlineFormatting(line.replace(/^>+\s+/, ""))}</blockquote>`);
            continue;
        }

        if (/^([-*_]){3,}$/.test(trimmed)) {
            flushParagraph();
            flushList();
            flushTable();
            htmlParts.push("<hr/>");
            continue;
        }

        flushList();
        paragraphBuffer.push(line);
    }

    if (inCodeBlock) {
        flushCode();
        inCodeBlock = false;
    }

    flushParagraph();
    flushList();
    flushTable();

    return htmlParts.join("");
};

/**
 * Markdown viewer widget that renders the field value as HTML while
 * falling back to the regular text editor when the field is editable.
 */
export class MarkdownViewerFieldComponent extends TextField {
    setup() {
        super.setup();
        this.rootRef = useRef("root");
        this.state = useState({
            mode: "preview",
            copyStatus: "idle",
            isReformatting: false,
        });
        this._fullWidthCells = [];
        this.orm = useService("orm");
        this.notification = useService("notification");

        onMounted(() => this.updateFieldWidth());
        onPatched(() => this.updateFieldWidth());
        onWillUnmount(() => this.cleanupFieldWidth());
    }

    willUpdateProps(nextProps) {
        super.willUpdateProps(nextProps);
        if (nextProps.readonly && this.state.mode !== "preview") {
            this.state.mode = "preview";
        }
    }

    toggleMode() {
        if (this.props.readonly) {
            return;
        }
        this.state.mode = this.state.mode === "preview" ? "markdown" : "preview";
    }

    get isPreviewMode() {
        return this.props.readonly || this.state.mode === "preview";
    }

    get toggleIconClass() {
        return this.isPreviewMode ? "fa fa-code" : "fa fa-eye";
    }

    get toggleTitle() {
        return this.isPreviewMode ? _t("Edit Markdown") : _t("Preview HTML");
    }

    get copyButtonTitle() {
        const value = this.props.record.data[this.props.name] || "";
        if (!value) {
            return _t("Nothing to copy");
        }
        return this.state.copyStatus === "success" ? _t("Copied!") : _t("Copy Markdown");
    }

    get copyPopupText() {
        return _t("Copied");
    }

    get copyButtonDisabled() {
        const value = this.props.record.data[this.props.name] || "";
        return !value;
    }

    get reformatTitle() {
        return _t("Reformat Output");
    }

    get reformatDisabled() {
        const record = this.props.record;
        return !record?.resId || this.state.isReformatting;
    }

    get reformatIconClass() {
        return this.state.isReformatting ? "fa fa-spinner fa-spin" : "fa fa-indent";
    }

    async copyMarkdown() {
        const value = this.props.record.data[this.props.name] || "";
        if (!value) {
            return;
        }
        let copied = false;
        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(value);
                copied = true;
            }
        } catch {
            // ignored, fallback tries next
        }
        if (!copied) {
            // Fallback for browsers without Clipboard API or HTTP context.
            try {
                const textarea = document.createElement("textarea");
                textarea.value = value;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                textarea.style.pointerEvents = "none";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                copied = document.execCommand("copy");
                document.body.removeChild(textarea);
            } catch {
                copied = false;
            }
        }
        this.state.copyStatus = copied ? "success" : "error";
        setTimeout(() => {
            this.state.copyStatus = "idle";
        }, 1000);
        if (!copied) {
            this.notification.add({
                title: _t("Copy failed"),
                message: _t("Please copy the text manually."),
                type: "warning",
            });
        }
    }

    async reformatOutput() {
        const record = this.props.record;
        if (!record?.resId) {
            return;
        }
        this.state.isReformatting = true;
        try {
            const result = await this.orm.call(record.resModel, "reformat_output", [[record.resId]]);
            const formatted =
                Array.isArray(result) && result.length ? result[0] : result !== undefined ? result : "";
            if (this.props.update) {
                await this.props.update(formatted);
            } else if (record?.data) {
                record.data[this.props.name] = formatted;
            }
        } finally {
            this.state.isReformatting = false;
        }
    }

    get renderedMarkdown() {
        const value = this.props.record.data[this.props.name] || "";
        if (!value) {
            return markup("");
        }
        const rendered = renderSimpleMarkdown(value);
        const sanitizer = globalThis.DOMPurify;
        const safeHtml = sanitizer ? sanitizer.sanitize(rendered) : rendered;
        return markup(safeHtml);
    }

    get shouldShowPreview() {
        return this.isPreviewMode;
    }

    cleanupFieldWidth() {
        if (!this._fullWidthCells?.length) {
            return;
        }
        for (const cell of this._fullWidthCells) {
            cell.classList.remove("o_markdown_viewer_full_width_cell");
            cell.classList.remove("o_markdown_viewer_full_width_label");
        }
        this._fullWidthCells = [];
    }

    updateFieldWidth() {
        this.cleanupFieldWidth();
        const root = this.rootRef?.el;
        if (!root) {
            return;
        }
        const inputCell = root.closest(".o_field_md_viewer");
        if (inputCell) {
            inputCell.classList.add("o_field_text");
            this._fullWidthCells.push(inputCell);
            const labelCell = inputCell.previousElementSibling;
            if (labelCell && labelCell.classList.contains("o_wrap_label")) {
                labelCell.classList.add("o_markdown_viewer_full_width_label");
                this._fullWidthCells.push(labelCell);
            }
        }
    }
}

MarkdownViewerFieldComponent.template = "vit_md_viewer.MarkdownViewerField";
MarkdownViewerFieldComponent.props = TextField.props;

export const markdownViewerField = {
    ...textField,
    component: MarkdownViewerFieldComponent,
};



registry.category("fields").add("md_viewer", markdownViewerField);
