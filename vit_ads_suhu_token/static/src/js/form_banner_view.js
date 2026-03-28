/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { STAGES, getStageImageSrc } from "./stage_config";

const existingFormView = registry.category("views").get("ads_form_with_banner");
const BaseFormController = existingFormView?.Controller || FormController;

export class BannerFormRenderer extends BaseFormController {
    static template = "vit_ads_suhu_inherit.BannerFormRenderer";
    static props = {...BaseFormController.props};

    setup(){
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.tokenBalance = null;
        onWillStart(async () => {
            await this._loadTokenBalance();
        });
        const currentAction = this.actionService.currentController?.action;
        const currentUrl = window.location.href;
        const url = new URL(currentUrl);
        const segments = url.pathname.split("/").filter(Boolean);
        this._urlParts = [];
        if (segments.length) {
            this._urlParts.push(`${url.origin}/${segments[0]}`);
            for (let i = 1; i < segments.length; i += 2) {
                const pair = segments.slice(i, i + 2).join("/");
                if (pair) {
                    this._urlParts.push(pair);
                }
            }
        }
        if (url.searchParams.has("debug")) {
            this._urlParts.push(`debug=${url.searchParams.get("debug")}`);
        }
        console.log("inherited form view", {currentAction, currentUrl, urlParts: this._urlParts });
    }

    get urlParts() {
        return this._urlParts || [];
    }

    get stages() {
        return STAGES;
    }

    get imageSrc() {
        return getStageImageSrc(this.props.resModel);
    }

    get tokenDisplay() {
        if (this.tokenBalance === null || this.tokenBalance === undefined) {
            return "-";
        }
        return this.tokenBalance;
    }

    async _loadTokenBalance() {
        try {
            const balance = await this.orm.call(
                "res.users",
                "get_my_token_balance",
                []
            );
            this.tokenBalance = balance ?? 0;
        } catch (err) {
            this.tokenBalance = null;
        }
    }

    async openTokenLog() {
        try {
            await this.actionService.doAction(
                "vit_ads_suhu_token.action_vit_ai_token_log"
            );
        } catch (err) {
            // no-op
        }
    }

    // No redirect for now; display-only box.
}

export const bannerFormView = {
    ...(existingFormView || formView),
    Controller: BannerFormRenderer,
};

if (existingFormView) {
    existingFormView.Controller = BannerFormRenderer;
} else {
    registry.category('views').add('ads_form_with_banner', bannerFormView);
}
