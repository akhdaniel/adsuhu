/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

class MainMenuBoxes extends Component {
    setup() {
        this.simitraRef = useRef("simitra");
        this.monitoringRef = useRef("monitoring");
    }

    onSimitraClick() {
        this.env.services.action.doAction("vit_dashboard.action_kerma_dashboard");
    }

    onMonitoringClick() {
        this.env.services.action.doAction("crm.crm_lead_action_pipeline");
    }
}
MainMenuBoxes.template = "vit_kerma_tampilan.MainMenuBoxesOWL";

registry.category("actions").add("main_menu_boxes", MainMenuBoxes);