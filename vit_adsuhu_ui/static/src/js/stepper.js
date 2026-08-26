/** @odoo-module **/

import { Component } from "@odoo/owl";

export class Stepper extends Component {
    static template = "vit_adsuhu_ui.Stepper";
    static props = {
        stages: { type: Array },
        current: { type: String },
        onSelect: { type: Function },
    };

    onStageClick(ev, key, status) {
        ev.preventDefault();
        if (status === "blocked") {
            return;
        }
        this.props.onSelect(key);
    }
}
