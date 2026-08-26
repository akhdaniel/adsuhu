/** @odoo-module **/

import { Component } from "@odoo/owl";

export class Stepper extends Component {
    static template = "vit_adsuhu_ui.Stepper";
    static props = {
        stages: { type: Array },
        current: { type: String },
        onSelect: { type: Function },
    };

    onStageClick(ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        const key = btn.dataset.key;
        const status = btn.dataset.status;
        if (status === "blocked") {
            return;
        }
        this.props.onSelect(key);
    }
}
